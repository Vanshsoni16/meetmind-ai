"""
MeetMind AI - formatting, date parsing and context building helpers.
"""
from __future__ import annotations

import html
import re
from datetime import date, datetime

NO_DEADLINE_TOKENS = {
    "", "-", "n/a", "na", "none", "null", "no deadline", "tbd", "tba",
    "not specified", "unspecified", "unknown", "ongoing",
}

DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d-%b-%Y",
    "%d %b, %Y",
    "%d-%b-%y",
]


# ----------------------------------------------------------------------
# Dates
# ----------------------------------------------------------------------
def parse_deadline(value) -> date | None:
    """Best-effort parse of a free-text deadline. Returns None when not parseable."""
    if not value:
        return None
    text = str(value).strip()
    if text.lower() in NO_DEADLINE_TOKENS:
        return None

    text = re.sub(r"\s+", " ", text)
    text = text.replace("Sept", "Sep").replace("sep ", "Sep ")

    # Try "2025-03-15" style first (also matches inside longer strings)
    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    # Try to find a parseable date fragment inside a sentence
    for fmt in DATE_FORMATS:
        match = re.search(r"(\d{1,4}[-/ ]\w{2,9}[-/ ]?\d{0,4})", text)
        if match:
            try:
                return datetime.strptime(match.group(1).strip(), fmt).date()
            except ValueError:
                continue

    return None


def pretty_date(value) -> str:
    """Human friendly date for display."""
    parsed = parse_deadline(value)
    if parsed:
        return parsed.strftime("%d %b %Y")
    return str(value).strip() if value else "—"


def days_until(value) -> int | None:
    parsed = parse_deadline(value)
    if not parsed:
        return None
    return (parsed - date.today()).days


def deadline_label(value) -> str:
    """'in 3 days', 'overdue by 2 days', or '' when not parseable."""
    delta = days_until(value)
    if delta is None:
        return ""
    if delta < 0:
        return f"overdue by {abs(delta)} day{'s' if abs(delta) != 1 else ''}"
    if delta == 0:
        return "due today"
    if delta == 1:
        return "due tomorrow"
    return f"in {delta} days"


def is_upcoming(value, within_days: int = 14) -> bool:
    delta = days_until(value)
    return delta is not None and 0 <= delta <= within_days


def is_overdue(value) -> bool:
    delta = days_until(value)
    return delta is not None and delta < 0


# ----------------------------------------------------------------------
# Badges
# ----------------------------------------------------------------------
def _esc(text) -> str:
    return html.escape(str(text if text is not None else ""))


def priority_badge(priority) -> str:
    text = (str(priority or "Medium")).strip().title()
    css = {"High": "high", "Medium": "medium", "Low": "low"}.get(text, "medium")
    return f'<span class="badge badge-{css}">{_esc(text)}</span>'


def status_badge(status) -> str:
    raw = str(status or "Pending").strip()
    key = raw.lower().replace(" ", "").replace("-", "").replace("_", "")
    mapping = {
        "pending": ("pending", "○"),
        "todo": ("pending", "○"),
        "inprogress": ("progress", "◐"),
        "completed": ("completed", "●"),
        "done": ("completed", "●"),
    }
    css, icon = mapping.get(key, ("pending", "○"))
    return f'<span class="badge badge-{css}">{icon} {_esc(raw)}</span>'


def risk_chip(delta: int | None) -> str:
    if delta is None:
        return ""
    if delta < 0:
        return f'<span class="badge badge-high">Overdue</span>'
    if delta <= 3:
        return f'<span class="badge badge-high">Due soon</span>'
    if delta <= 7:
        return f'<span class="badge badge-medium">This week</span>'
    return f'<span class="badge badge-low">Upcoming</span>'


# ----------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------
def task_stats(tasks: list[dict]) -> dict:
    total = len(tasks)
    pending = sum(1 for t in tasks if str(t.get("status", "")).strip() == "Pending")
    progress = sum(1 for t in tasks if str(t.get("status", "")).strip() == "In Progress")
    completed = sum(1 for t in tasks if str(t.get("status", "")).strip() == "Completed")
    return {
        "total": total,
        "pending": pending,
        "in_progress": progress,
        "completed": completed,
        "open": pending + progress,
    }


def upcoming_deadlines(tasks: list[dict], within_days: int = 21) -> list[dict]:
    """Open tasks with a parseable deadline inside the window, soonest first."""
    out = []
    for task in tasks:
        if str(task.get("status", "")).strip() == "Completed":
            continue
        delta = days_until(task.get("deadline"))
        if delta is None or delta > within_days:
            continue
        enriched = dict(task)
        enriched["_delta"] = delta
        enriched["_label"] = deadline_label(task.get("deadline"))
        out.append(enriched)
    return sorted(out, key=lambda t: t["_delta"])


# ----------------------------------------------------------------------
# Context building for Q&A
# ----------------------------------------------------------------------
def bundle_to_context(bundle: dict, max_transcript_chars: int = 7000) -> str:
    """Render one meeting bundle as a compact, LLM-friendly text block."""
    meeting = bundle.get("meeting") or {}
    lines = [
        f"### MEETING: {meeting.get('title', 'Untitled')}",
        f"Date: {meeting.get('date') or 'unknown'}",
        f"Participants: {meeting.get('participants') or 'not recorded'}",
        f"Executive summary: {meeting.get('summary') or 'n/a'}",
    ]

    key_points = meeting.get("key_points") or []
    if key_points:
        lines.append("Key discussion points:")
        lines.extend(f"  - {p}" for p in key_points)

    if bundle.get("decisions"):
        lines.append("Decisions made:")
        lines.extend(f"  - {d}" for d in bundle["decisions"])

    if bundle.get("tasks"):
        lines.append("Action items:")
        for t in bundle["tasks"]:
            lines.append(
                f"  - {t.get('task')} | assignee: {t.get('assignee')} | "
                f"deadline: {t.get('deadline')} | priority: {t.get('priority')} | "
                f"status: {t.get('status')}"
            )

    if bundle.get("risks"):
        lines.append("Risks and blockers:")
        lines.extend(f"  - {r}" for r in bundle["risks"])

    if bundle.get("questions"):
        lines.append("Unresolved questions:")
        lines.extend(f"  - {q}" for q in bundle["questions"])

    transcript = (meeting.get("transcript") or "").strip()
    if transcript:
        snippet = transcript[:max_transcript_chars]
        if len(transcript) > max_transcript_chars:
            snippet += "\n[...transcript truncated...]"
        lines.append("Transcript:")
        lines.append(snippet)

    return "\n".join(lines)


def build_context(bundles: list[dict], max_total_chars: int = 26000) -> str:
    """Concatenate multiple meeting bundles, respecting a total budget."""
    blocks = []
    used = 0
    for bundle in bundles:
        block = bundle_to_context(bundle)
        if used + len(block) > max_total_chars:
            remaining = max_total_chars - used
            if remaining < 500:
                break
            block = block[:remaining] + "\n[...truncated...]"
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def truncate(text: str, limit: int = 120) -> str:
    text = str(text or "")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"