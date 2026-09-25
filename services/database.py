"""
MeetMind AI - SQLite persistence layer.
Simple, synchronous, zero-ORM.
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "meetings.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meetings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    date          TEXT,
    participants  TEXT,
    transcript    TEXT,
    summary       TEXT,
    key_points    TEXT,
    created_at    TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id  INTEGER NOT NULL,
    task        TEXT,
    assignee    TEXT,
    deadline    TEXT,
    priority    TEXT,
    status      TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id  INTEGER NOT NULL,
    decision    TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS risks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id  INTEGER NOT NULL,
    risk        TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS questions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id  INTEGER NOT NULL,
    question    TEXT,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
);
"""


class DatabaseError(Exception):
    """Raised for any friendly-wrapped database failure."""


# ----------------------------------------------------------------------
# Low level helpers
# ----------------------------------------------------------------------
def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _query(sql: str, params: tuple = ()) -> list[dict]:
    try:
        conn = get_conn()
        try:
            cur = conn.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Database read failed: {exc}") from exc


def _execute(sql: str, params: tuple = ()) -> int:
    try:
        conn = get_conn()
        try:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Database write failed: {exc}") from exc


def init_db() -> None:
    try:
        conn = get_conn()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        raise DatabaseError(f"Could not initialise database: {exc}") from exc


# ----------------------------------------------------------------------
# Meetings
# ----------------------------------------------------------------------
def create_meeting(title, date, participants, transcript, summary, key_points) -> int:
    return _execute(
        """INSERT INTO meetings (title, date, participants, transcript, summary, key_points, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            title.strip(),
            (date or "").strip(),
            (participants or "").strip(),
            transcript or "",
            summary or "",
            json.dumps(key_points or []),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def save_extraction(meeting_id: int, data: dict) -> None:
    """Persist the structured extraction produced by the LLM."""
    for item in data.get("action_items", []):
        _execute(
            """INSERT INTO tasks (meeting_id, task, assignee, deadline, priority, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                meeting_id,
                item.get("task", ""),
                item.get("assignee", "Unassigned"),
                item.get("deadline", "No deadline"),
                item.get("priority", "Medium"),
                item.get("status", "Pending"),
            ),
        )

    for d in data.get("decisions", []):
        _execute("INSERT INTO decisions (meeting_id, decision) VALUES (?, ?)", (meeting_id, d))

    for r in data.get("risks", []):
        _execute("INSERT INTO risks (meeting_id, risk) VALUES (?, ?)", (meeting_id, r))

    for q in data.get("unresolved_questions", []):
        _execute("INSERT INTO questions (meeting_id, question) VALUES (?, ?)", (meeting_id, q))


def get_meetings() -> list[dict]:
    return _query(
        """
        SELECT m.*,
            (SELECT COUNT(*) FROM tasks     t WHERE t.meeting_id = m.id) AS task_count,
            (SELECT COUNT(*) FROM decisions d WHERE d.meeting_id = m.id) AS decision_count,
            (SELECT COUNT(*) FROM risks     r WHERE r.meeting_id = m.id) AS risk_count,
            (SELECT COUNT(*) FROM questions q WHERE q.meeting_id = m.id) AS question_count
        FROM meetings m
        ORDER BY COALESCE(date(m.date), '0000-00-00') DESC, m.id DESC
        """
    )


def get_meeting(meeting_id: int) -> dict | None:
    rows = _query("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
    if not rows:
        return None
    row = rows[0]
    try:
        row["key_points"] = json.loads(row.get("key_points") or "[]")
    except (json.JSONDecodeError, TypeError):
        row["key_points"] = []
    return row


def delete_meeting(meeting_id: int) -> None:
    _execute("DELETE FROM tasks     WHERE meeting_id = ?", (meeting_id,))
    _execute("DELETE FROM decisions WHERE meeting_id = ?", (meeting_id,))
    _execute("DELETE FROM risks     WHERE meeting_id = ?", (meeting_id,))
    _execute("DELETE FROM questions WHERE meeting_id = ?", (meeting_id,))
    _execute("DELETE FROM meetings  WHERE id = ?", (meeting_id,))


def count_meetings() -> int:
    rows = _query("SELECT COUNT(*) AS c FROM meetings")
    return rows[0]["c"] if rows else 0


# ----------------------------------------------------------------------
# Tasks
# ----------------------------------------------------------------------
def get_all_tasks() -> list[dict]:
    return _query(
        """
        SELECT t.*, m.title AS meeting_title, m.date AS meeting_date
        FROM tasks t
        LEFT JOIN meetings m ON m.id = t.meeting_id
        ORDER BY t.id DESC
        """
    )


def get_tasks_for_meeting(meeting_id: int) -> list[dict]:
    return _query("SELECT * FROM tasks WHERE meeting_id = ? ORDER BY id", (meeting_id,))


def update_task_status(task_id: int, status: str) -> None:
    _execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))


# ----------------------------------------------------------------------
# Decisions / Risks / Questions
# ----------------------------------------------------------------------
def get_decisions(meeting_id: int | None = None) -> list[dict]:
    if meeting_id is None:
        return _query("SELECT * FROM decisions ORDER BY id")
    return _query("SELECT * FROM decisions WHERE meeting_id = ? ORDER BY id", (meeting_id,))


def get_risks(meeting_id: int | None = None) -> list[dict]:
    if meeting_id is None:
        return _query("SELECT * FROM risks ORDER BY id")
    return _query("SELECT * FROM risks WHERE meeting_id = ? ORDER BY id", (meeting_id,))


def get_questions(meeting_id: int | None = None) -> list[dict]:
    if meeting_id is None:
        return _query("SELECT * FROM questions ORDER BY id")
    return _query("SELECT * FROM questions WHERE meeting_id = ? ORDER BY id", (meeting_id,))


# ----------------------------------------------------------------------
# Bundles (used by the Q&A context builder)
# ----------------------------------------------------------------------
def get_meeting_bundle(meeting_id: int) -> dict | None:
    meeting = get_meeting(meeting_id)
    if meeting is None:
        return None
    return {
        "meeting": meeting,
        "tasks": get_tasks_for_meeting(meeting_id),
        "decisions": [d["decision"] for d in get_decisions(meeting_id)],
        "risks": [r["risk"] for r in get_risks(meeting_id)],
        "questions": [q["question"] for q in get_questions(meeting_id)],
    }


def get_all_bundles() -> list[dict]:
    return [get_meeting_bundle(m["id"]) for m in get_meetings()]


# ----------------------------------------------------------------------
# Demo data
# ----------------------------------------------------------------------
def seed_sample_data() -> int:
    """Insert the demo meetings, skipping any whose title already exists.

    Returns the count of newly inserted meetings.
    """
    from sample_data.seed import SEED_MEETINGS

    existing = {row["title"] for row in _query("SELECT title FROM meetings")}

    inserted = 0
    for entry in SEED_MEETINGS:
        if entry["title"] in existing:
            continue

        transcript_path = BASE_DIR / "sample_data" / entry["file"]
        try:
            transcript = transcript_path.read_text(encoding="utf-8")
        except OSError:
            transcript = entry.get("transcript", "")

        mid = create_meeting(
            title=entry["title"],
            date=entry["date"],
            participants=entry["participants"],
            transcript=transcript,
            summary=entry["summary"],
            key_points=entry["key_points"],
        )
        save_extraction(mid, entry)
        inserted += 1

    return inserted


# ----------------------------------------------------------------------
# Global search (used by the Search page)
# ----------------------------------------------------------------------
def global_search(query: str) -> dict:
    """Search meetings, tasks, decisions, risks, and questions for a substring.

    Returns a dict of lists keyed by category. Empty string returns empty lists.
    """
    q = (query or "").strip()
    if not q:
        return {"meetings": [], "tasks": [], "decisions": [], "risks": [], "questions": []}

    like = f"%{q}%"

    return {
        "meetings": _query(
            """
            SELECT id, title, date, participants, summary
            FROM meetings
            WHERE title LIKE ? OR summary LIKE ? OR participants LIKE ? OR transcript LIKE ?
            ORDER BY COALESCE(date(date), '0000-00-00') DESC, id DESC
            """,
            (like, like, like, like),
        ),
        "tasks": _query(
            """
            SELECT t.id, t.task, t.assignee, t.status, t.priority, t.deadline,
                   t.meeting_id, m.title AS meeting_title, m.date AS meeting_date
            FROM tasks t
            LEFT JOIN meetings m ON m.id = t.meeting_id
            WHERE t.task LIKE ? OR t.assignee LIKE ?
            ORDER BY t.id DESC
            """,
            (like, like),
        ),
        "decisions": _query(
            """
            SELECT d.id, d.decision, d.meeting_id,
                   m.title AS meeting_title, m.date AS meeting_date
            FROM decisions d
            LEFT JOIN meetings m ON m.id = d.meeting_id
            WHERE d.decision LIKE ?
            ORDER BY COALESCE(date(m.date), '0000-00-00') DESC, d.id DESC
            """,
            (like,),
        ),
        "risks": _query(
            """
            SELECT r.id, r.risk, r.meeting_id,
                   m.title AS meeting_title, m.date AS meeting_date
            FROM risks r
            LEFT JOIN meetings m ON m.id = r.meeting_id
            WHERE r.risk LIKE ?
            ORDER BY COALESCE(date(m.date), '0000-00-00') DESC, r.id DESC
            """,
            (like,),
        ),
        "questions": _query(
            """
            SELECT q.id, q.question, q.meeting_id,
                   m.title AS meeting_title, m.date AS meeting_date
            FROM questions q
            LEFT JOIN meetings m ON m.id = q.meeting_id
            WHERE q.question LIKE ?
            ORDER BY COALESCE(date(m.date), '0000-00-00') DESC, q.id DESC
            """,
            (like,),
        ),
    }


def get_decisions_with_meetings() -> list[dict]:
    """All decisions with the meeting they came from. Used by the Decision Log page."""
    return _query(
        """
        SELECT d.id, d.decision, d.meeting_id,
               m.title AS meeting_title, m.date AS meeting_date
        FROM decisions d
        LEFT JOIN meetings m ON m.id = d.meeting_id
        ORDER BY COALESCE(date(m.date), '0000-00-00') DESC, d.id DESC
        """
    )