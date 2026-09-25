"""
MeetMind AI - thin LLM client.

Works with any OpenAI-compatible /chat/completions endpoint.
Default target: Google Gemini (free tier, AQ. key format).
Configured entirely through environment variables.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

from services.prompts import (
    EXTRACTION_SYSTEM,
    EXTRACTION_USER,
    QA_SYSTEM,
    QA_USER,
)

# ----------------------------------------------------------------------
# Load .env explicitly from the project root.
# Streamlit can change the working directory, which breaks load_dotenv()'s
# default upward search. Resolving relative to THIS file is reliable.
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

if ENV_PATH.is_file():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv()


# ----------------------------------------------------------------------
# Defaults (used only when .env is missing a value)
# ----------------------------------------------------------------------
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
REQUEST_TIMEOUT = 120

VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_STATUSES = {"Pending", "In Progress", "Completed"}

# Silent during demo. Set True if you need to debug the request payload.
DEBUG_LLM = False


class AIServiceError(Exception):
    """Friendly, user-displayable AI error."""


# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
def get_config() -> tuple[str, str, str]:
    api_key = (os.getenv("LLM_API_KEY") or "").strip()
    base_url = (os.getenv("LLM_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")
    model = (os.getenv("LLM_MODEL") or DEFAULT_MODEL).strip()
    return api_key, base_url, model


def is_configured() -> bool:
    api_key, _, _ = get_config()
    return bool(api_key) and api_key not in {
        "your_api_key_here",
        "AQ.your_actual_gemini_key_here",
    }


# ----------------------------------------------------------------------
# Transport
# ----------------------------------------------------------------------
def _chat(messages: list[dict], temperature: float = 0.0, max_tokens: int = 2500) -> str:
    api_key, base_url, model = get_config()

    if not api_key or api_key in {"your_api_key_here", "AQ.your_actual_gemini_key_here"}:
        raise AIServiceError(
            "No LLM API key found. Add LLM_API_KEY to your .env file and restart the app."
        )

    url = f"{base_url}/chat/completions"

    if DEBUG_LLM:
        print(
            f"\n[MEETMIND REQ] -> POST {url}\n"
            f"[MEETMIND REQ]    model={model!r}  key_len={len(api_key)}  "
            f"max_tokens={max_tokens}  temperature={temperature}\n",
            flush=True,
        )

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
    except requests.Timeout as exc:
        raise AIServiceError(
            "The AI service timed out. Try again with a shorter transcript."
        ) from exc
    except requests.RequestException as exc:
        raise AIServiceError(f"Could not reach the AI service: {exc}") from exc

    # ---- Provider-aware error handling ----
    if response.status_code == 400:
        raise AIServiceError(
            f"[GEMINI 400] Request rejected. {response.text[:300]}"
        )
    if response.status_code == 401:
        raise AIServiceError(
            "[GEMINI 401] API key rejected. Check LLM_API_KEY in .env."
        )
    if response.status_code == 403:
        raise AIServiceError(
            "[GEMINI 403] Access denied. Your key may be restricted by IP or referrer."
        )
    if response.status_code == 404:
        raise AIServiceError(
            f"[GEMINI 404] Model '{model}' not found on your account. "
            f"Tried: {url}. Details: {response.text[:200]}"
        )
    if response.status_code == 429:
        raise AIServiceError(
            "[GEMINI 429] Rate limit or quota exceeded. Wait a moment and retry."
        )
    if response.status_code >= 400:
        raise AIServiceError(
            f"[GEMINI {response.status_code}] Unexpected error: {response.text[:300]}"
        )

    # ---- Parse the response ----
    try:
        data = response.json()
    except ValueError as exc:
        raise AIServiceError(
            "The AI service returned a non-JSON response. Please try again."
        ) from exc

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIServiceError(
            "The AI service returned an unexpected response format."
        ) from exc

    if not content or not str(content).strip():
        raise AIServiceError("The AI returned an empty response. Please try again.")

    return content


# ----------------------------------------------------------------------
# JSON parsing helpers
# ----------------------------------------------------------------------
def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_json_response(raw: str) -> dict:
    """Extract a JSON object from an LLM response, tolerating fences and stray prose."""
    if not raw or not raw.strip():
        raise AIServiceError("The AI returned an empty response. Please try again.")

    cleaned = _strip_code_fences(raw)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise AIServiceError(
                "The AI returned malformed JSON. Try re-running the analysis."
            ) from exc

    raise AIServiceError("The AI response did not contain a valid JSON object.")


# ----------------------------------------------------------------------
# Normalisation
# ----------------------------------------------------------------------
def _as_str(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v).strip() for v in value if str(v).strip()) or fallback
    text = str(value).strip()
    return text or fallback


def _as_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            text = _as_str(item)
            if text:
                out.append(text)
        return out
    return []


def _normalise_priority(value) -> str:
    text = _as_str(value, "Medium").title()
    return text if text in VALID_PRIORITIES else "Medium"


def _normalise_status(value) -> str:
    text = _as_str(value, "Pending")
    lowered = text.lower().replace("_", " ").replace("-", " ").strip()
    mapping = {
        "pending": "Pending",
        "todo": "Pending",
        "not started": "Pending",
        "open": "Pending",
        "in progress": "In Progress",
        "inprogress": "In Progress",
        "ongoing": "In Progress",
        "doing": "In Progress",
        "completed": "Completed",
        "complete": "Completed",
        "done": "Completed",
        "closed": "Completed",
    }
    return mapping.get(lowered, "Pending")


def normalise_extraction(data: dict) -> dict:
    """Guarantee the exact schema, no matter how creative the model got."""
    if not isinstance(data, dict):
        raise AIServiceError("The AI returned an unexpected data structure.")

    action_items = []
    raw_items = data.get("action_items") or []
    if isinstance(raw_items, dict):
        raw_items = [raw_items]
    if isinstance(raw_items, list):
        for item in raw_items:
            if isinstance(item, str):
                action_items.append(
                    {
                        "task": item.strip(),
                        "assignee": "Unassigned",
                        "deadline": "No deadline",
                        "priority": "Medium",
                        "status": "Pending",
                    }
                )
                continue
            if not isinstance(item, dict):
                continue
            task = _as_str(
                item.get("task") or item.get("action") or item.get("description")
            )
            if not task:
                continue
            action_items.append(
                {
                    "task": task,
                    "assignee": _as_str(item.get("assignee"), "Unassigned"),
                    "deadline": _as_str(item.get("deadline"), "No deadline"),
                    "priority": _normalise_priority(item.get("priority")),
                    "status": _normalise_status(item.get("status")),
                }
            )

    return {
        "summary": _as_str(data.get("summary"), "No summary could be generated."),
        "key_points": _as_str_list(data.get("key_points")),
        "decisions": _as_str_list(data.get("decisions")),
        "action_items": action_items,
        "risks": _as_str_list(data.get("risks")),
        "unresolved_questions": _as_str_list(data.get("unresolved_questions")),
    }


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def extract_meeting_data(transcript: str) -> dict:
    """Send a transcript to the LLM and return a validated, normalised extraction."""
    if not transcript or not transcript.strip():
        raise AIServiceError("The transcript is empty - nothing to analyse.")
    if len(transcript.strip()) < 40:
        raise AIServiceError(
            "The transcript is too short to analyse. Paste at least a few sentences."
        )

    user_prompt = EXTRACTION_USER.replace("{transcript}", transcript.strip()[:24000])

    raw = _chat(
        [
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=3000,
    )

    return normalise_extraction(parse_json_response(raw))


def answer_question(context: str, question: str, history: list[dict] | None = None) -> str:
    """Answer a user question strictly from the supplied meeting context."""
    if not question or not question.strip():
        raise AIServiceError("Please type a question first.")
    if not context or not context.strip():
        raise AIServiceError("No meeting content is available to search.")

    messages = [{"role": "system", "content": QA_SYSTEM}]

    for turn in (history or [])[-6:]:
        role = turn.get("role")
        content = turn.get("content")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    messages.append(
        {
            "role": "user",
            "content": QA_USER.replace("{context}", context).replace(
                "{question}", question.strip()
            ),
        }
    )

    return _chat(messages, temperature=0.0, max_tokens=1200).strip()