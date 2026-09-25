"""
MeetMind AI — Turn every meeting into clear actions.
Streamlit single-file front end.
Run with:  streamlit run app.py
"""
from __future__ import annotations

import re
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MeetMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

from services import ai_service, database as db
from utils import helpers

# ----------------------------------------------------------------------
# Bootstrap
# ----------------------------------------------------------------------
try:
    db.init_db()
except db.DatabaseError as exc:
    st.error(f"⚠️ {exc}")
    st.stop()

NAV_ITEMS = [
    "🏠 Dashboard",
    "➕ New Meeting",
    "📋 Meetings",
    "✅ Tasks",
    "🧭 Decisions",
    "💬 Ask Meeting",
    "🔍 Search",
    "📊 Analytics",
]

for key, value in {
    "nav": NAV_ITEMS[0],
    "pending_nav": None,
    "view_meeting": None,
    "flash": None,
    "chat": {},
    "transcript_input": "",
    "global_search_input": "",
    "pending_search": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go(page: str, meeting_id: int | None = None) -> None:
    """Queue a navigation change (applied on next run, before sidebar)."""
    st.session_state.pending_nav = page
    if meeting_id is not None:
        st.session_state.view_meeting = meeting_id
    st.rerun()


def flash(kind: str, message: str) -> None:
    st.session_state.flash = (kind, message)


# Apply any queued navigation BEFORE the sidebar radio is built
if st.session_state.pending_nav is not None:
    st.session_state.nav = st.session_state.pending_nav
    st.session_state.pending_nav = None


# ----------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
.stApp { background: #f5f6fb; }
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1250px; }

/* ---------------- Sidebar ---------------- */
section[data-testid="stSidebar"] { background: #0b1220; border-right: 1px solid #1e293b; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label { color: #cbd5e1; }
section[data-testid="stSidebar"] hr { border-color: #1e293b; }

.brand { font-size: 1.3rem; font-weight: 800; letter-spacing: .5px; color: #ffffff !important; }
.brand span { color: #818cf8 !important; }
.brand-tag { font-size: .74rem; color: #64748b !important; line-height: 1.35; margin: .15rem 0 1.1rem 0; }

section[data-testid="stSidebar"] div[role="radiogroup"] > label {
  display: flex; align-items: center; width: 100%;
  padding: .55rem .7rem; border-radius: 10px; margin-bottom: 3px;
  cursor: pointer; transition: background .15s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: #152036; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: linear-gradient(90deg, #4f46e5, #7c3aed);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
  color: #ffffff !important; font-weight: 600;
}
section[data-testid="stSidebar"] div[role="radiogroup"] p { font-size: .93rem; margin: 0; }

.status-pill { display: inline-block; font-size: .74rem; padding: .3rem .6rem;
  border-radius: 8px; margin-top: .4rem; font-weight: 600; }
.status-ok { background: #052e21; color: #34d399 !important; }
.status-warn { background: #3b2413; color: #fbbf24 !important; }

/* ---------------- Typography ---------------- */
.page-title { font-size: 2rem; font-weight: 800; color: #0f172a; margin: 0; letter-spacing: -.5px; }
.page-sub { color: #64748b; font-size: .95rem; margin-top: .2rem; margin-bottom: 1.4rem; }
.section-title { font-size: 1.05rem; font-weight: 700; color: #0f172a;
  margin: 1.6rem 0 .7rem 0; letter-spacing: -.2px; }

/* ---------------- Stat cards ---------------- */
.stat-card {
  background: #ffffff; border: 1px solid #e6e9f0; border-radius: 14px;
  padding: 1rem 1.1rem; height: 100%;
  box-shadow: 0 1px 2px rgba(15,23,42,.04);
}
.stat-card .stat-label { font-size: .74rem; font-weight: 600; letter-spacing: .6px;
  text-transform: uppercase; color: #94a3b8; }
.stat-card .stat-value { font-size: 1.85rem; font-weight: 800; color: #0f172a;
  line-height: 1.2; margin-top: .2rem; }
.stat-card .stat-sub { font-size: .76rem; color: #94a3b8; margin-top: .15rem; }
.stat-card.accent-indigo { border-left: 4px solid #4f46e5; }
.stat-card.accent-amber  { border-left: 4px solid #f59e0b; }
.stat-card.accent-green  { border-left: 4px solid #10b981; }
.stat-card.accent-rose   { border-left: 4px solid #f43f5e; }
.stat-card.accent-sky    { border-left: 4px solid #0ea5e9; }

/* ---------------- Meeting cards ---------------- */
.mcard {
  background: #ffffff; border: 1px solid #e6e9f0; border-radius: 14px;
  padding: 1rem 1.15rem; box-shadow: 0 1px 2px rgba(15,23,42,.04);
}
.mcard-top { display: flex; justify-content: space-between; align-items: baseline; gap: .5rem; }
.mcard-title { font-weight: 700; font-size: 1rem; color: #0f172a; }
.mcard-date { font-size: .78rem; color: #94a3b8; white-space: nowrap; }
.mcard-stats { margin-top: .6rem; display: flex; flex-wrap: wrap; gap: .35rem; }
.chip {
  background: #f1f5f9; color: #475569; font-size: .74rem; font-weight: 600;
  padding: .22rem .55rem; border-radius: 7px; display: inline-block;
}

/* ---------------- Panels ---------------- */
.panel {
  background: #ffffff; border: 1px solid #e6e9f0; border-radius: 14px;
  padding: 1.1rem 1.25rem; margin-bottom: .9rem;
  box-shadow: 0 1px 2px rgba(15,23,42,.04);
}
.panel-title { font-size: .8rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .7px; color: #4f46e5; margin-bottom: .55rem; }
.panel p { color: #334155; font-size: .92rem; line-height: 1.6; margin: 0; }
.panel ul { margin: .2rem 0 0 1.1rem; padding: 0; }
.panel li { color: #334155; font-size: .92rem; line-height: 1.65; margin-bottom: .25rem; }

/* ---------------- Badges ---------------- */
.badge {
  display: inline-block; padding: .16rem .5rem; border-radius: 6px;
  font-size: .72rem; font-weight: 700; letter-spacing: .2px; white-space: nowrap;
}
.badge-high      { background: #fee2e2; color: #b91c1c; }
.badge-medium    { background: #fef3c7; color: #b45309; }
.badge-low       { background: #dcfce7; color: #15803d; }
.badge-pending   { background: #f1f5f9; color: #475569; }
.badge-progress  { background: #dbeafe; color: #1d4ed8; }
.badge-completed { background: #dcfce7; color: #15803d; }

/* ---------------- HTML tables ---------------- */
table.mm-table { width: 100%; border-collapse: collapse; font-size: .87rem; }
table.mm-table thead th {
  text-align: left; font-size: .72rem; text-transform: uppercase; letter-spacing: .6px;
  color: #94a3b8; font-weight: 700; padding: .55rem .6rem; border-bottom: 1px solid #e6e9f0;
}
table.mm-table tbody td {
  padding: .62rem .6rem; border-bottom: 1px solid #f1f5f9; color: #334155; vertical-align: top;
}
table.mm-table tbody tr:hover { background: #fafbff; }
td.t-task { font-weight: 600; color: #0f172a; }

/* ---------------- Buttons ---------------- */
.stButton > button {
  border-radius: 9px; font-weight: 600; font-size: .88rem;
  border: 1px solid #e2e8f0; transition: all .15s ease;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(90deg, #4f46e5, #7c3aed);
  border: none; color: #fff;
}
.stButton > button[kind="primary"]:hover { opacity: .92; }

/* ---------------- Misc ---------------- */
.empty-state {
  text-align: center; padding: 2.6rem 1rem; background: #ffffff;
  border: 1px dashed #d8dee9; border-radius: 14px; color: #64748b;
}
.empty-state .es-title { font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: .3rem; }
.participant-chip {
  display: inline-block; background: #eef2ff; color: #4338ca; font-size: .78rem;
  font-weight: 600; padding: .25rem .6rem; border-radius: 20px; margin: 0 .3rem .3rem 0;
}
.meta-line { color: #64748b; font-size: .87rem; margin-bottom: .6rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Reusable UI components
# ----------------------------------------------------------------------
def stat_card(label: str, value, sub: str = "", accent: str = "indigo") -> str:
    return (
        f'<div class="stat-card accent-{accent}">'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-sub">{sub}</div>'
        f"</div>"
    )


def meeting_card(m: dict) -> str:
    return (
        '<div class="mcard">'
        '<div class="mcard-top">'
        f'<span class="mcard-title">{helpers.truncate(m.get("title"), 70)}</span>'
        f'<span class="mcard-date">{helpers.pretty_date(m.get("date"))}</span>'
        "</div>"
        '<div class="mcard-stats">'
        f'<span class="chip">✅ {m.get("task_count", 0)} tasks</span>'
        f'<span class="chip">🧭 {m.get("decision_count", 0)} decisions</span>'
        f'<span class="chip">⚠️ {m.get("risk_count", 0)} risks</span>'
        f'<span class="chip">❓ {m.get("question_count", 0)} open questions</span>'
        "</div></div>"
    )


def panel(title: str, body_html: str) -> str:
    return f'<div class="panel"><div class="panel-title">{title}</div>{body_html}</div>'


def bullets(items: list[str]) -> str:
    if not items:
        return '<p style="color:#94a3b8;">Nothing recorded.</p>'
    return "<ul>" + "".join(f"<li>{helpers._esc(i)}</li>" for i in items) + "</ul>"


def tasks_table_html(tasks: list[dict], show_meeting: bool = False) -> str:
    if not tasks:
        return '<p style="color:#94a3b8;">No action items recorded.</p>'

    head = "<th>Task</th>"
    if show_meeting:
        head += "<th>Meeting</th>"
    head += "<th>Assignee</th><th>Deadline</th><th>Priority</th><th>Status</th>"

    rows = []
    for t in tasks:
        label = helpers.deadline_label(t.get("deadline"))
        deadline_cell = helpers._esc(t.get("deadline") or "No deadline")
        if label:
            deadline_cell += f'<br><span style="font-size:.72rem;color:#94a3b8;">{label}</span>'

        row = f'<td class="t-task">{helpers._esc(t.get("task"))}</td>'
        if show_meeting:
            row += f'<td>{helpers._esc(helpers.truncate(t.get("meeting_title"), 34))}</td>'
        row += (
            f'<td>{helpers._esc(t.get("assignee") or "Unassigned")}</td>'
            f"<td>{deadline_cell}</td>"
            f'<td>{helpers.priority_badge(t.get("priority"))}</td>'
            f'<td>{helpers.status_badge(t.get("status"))}</td>'
        )
        rows.append(f"<tr>{row}</tr>")

    return (
        '<table class="mm-table"><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def known_participants() -> list[str]:
    """Collect every participant name seen across all meetings."""
    names: set[str] = set()
    try:
        for m in db.get_meetings():
            raw = m.get("participants") or ""
            for name in raw.split(","):
                name = name.strip()
                if name:
                    names.add(name)
    except Exception:
        pass
    return sorted(names)


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract selectable text from a PDF file. Returns '' if the PDF has no text layer.

    Raises RuntimeError if pypdf isn't installed.
    """
    from io import BytesIO

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF support requires the pypdf library. "
            "Run:  pip install pypdf>=4.0.0"
        ) from exc

    reader = PdfReader(BytesIO(file_bytes))
    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            pages.append(text)
    return "\n\n".join(pages).strip()


def build_meeting_markdown(bundle: dict) -> str:
    """Render a meeting bundle as a standalone Markdown document."""
    m = bundle["meeting"]
    lines: list[str] = [
        f"# {m.get('title', 'Untitled Meeting')}",
        "",
        f"**Date:** {helpers.pretty_date(m.get('date'))}  ",
        f"**Participants:** {m.get('participants') or 'Not recorded'}",
        "",
        "## Executive Summary",
        "",
        m.get("summary") or "—",
        "",
    ]

    key_points = m.get("key_points") or []
    if key_points:
        lines.append("## Key Discussion Points")
        lines.append("")
        for kp in key_points:
            lines.append(f"- {kp}")
        lines.append("")

    if bundle.get("decisions"):
        lines.append("## Decisions")
        lines.append("")
        for d in bundle["decisions"]:
            lines.append(f"- {d}")
        lines.append("")

    if bundle.get("tasks"):
        lines.append("## Action Items")
        lines.append("")
        lines.append("| Task | Assignee | Deadline | Priority | Status |")
        lines.append("|---|---|---|---|---|")
        for t in bundle["tasks"]:
            lines.append(
                f"| {t.get('task', '')} "
                f"| {t.get('assignee') or 'Unassigned'} "
                f"| {t.get('deadline') or 'No deadline'} "
                f"| {t.get('priority') or 'Medium'} "
                f"| {t.get('status') or 'Pending'} |"
            )
        lines.append("")

    if bundle.get("risks"):
        lines.append("## Risks & Blockers")
        lines.append("")
        for r in bundle["risks"]:
            lines.append(f"- {r}")
        lines.append("")

    if bundle.get("questions"):
        lines.append("## Unresolved Questions")
        lines.append("")
        for q in bundle["questions"]:
            lines.append(f"- {q}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by MeetMind AI — turn every meeting into clear actions.*")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand">🧠 MEETMIND <span>AI</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-tag">Turn every meeting into clear actions.</div>',
        unsafe_allow_html=True,
    )
    st.radio("Navigation", NAV_ITEMS, key="nav", label_visibility="collapsed")

    st.markdown("---")
    if ai_service.is_configured():
        st.markdown('<div class="status-pill status-ok">● AI connected</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="status-pill status-warn">● LLM_API_KEY not set</div>',
            unsafe_allow_html=True,
        )
        st.caption("Add your key to `.env` to enable analysis and Q&A.")

    st.markdown("---")
    st.caption("💡 Tip: use **🔍 Search** to find anything across meetings.")
    st.caption("MeetMind AI · PS-09 · Hackathon build")


# Flash messages from the previous run
if st.session_state.flash:
    kind, message = st.session_state.flash
    (st.success if kind == "success" else st.error)(message)
    st.session_state.flash = None


# ----------------------------------------------------------------------
# PAGE: Dashboard
# ----------------------------------------------------------------------
def page_dashboard() -> None:
    meetings = db.get_meetings()
    tasks = db.get_all_tasks()
    stats = helpers.task_stats(tasks)
    decisions = db.get_decisions()
    upcoming = helpers.upcoming_deadlines(tasks, within_days=14)

    head_l, head_r = st.columns([3, 1])
    with head_l:
        st.markdown('<div class="page-title">MeetMind AI</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="page-sub">Turn every meeting into clear actions.</div>',
            unsafe_allow_html=True,
        )
    with head_r:
        st.write("")
        if st.button("＋  New Meeting", type="primary", width="stretch"):
            go("➕ New Meeting")

    # ---- Demo guide ----
    with st.expander("🎬 Demo guide — 2-minute walkthrough", expanded=False):
        st.markdown(
            """
**MeetMind AI in 7 steps:**

1. **Load demo data** (only if you haven't yet) — 5 realistic meetings, zero API calls.
2. **➕ New Meeting** — paste a transcript or upload a .txt, .md, or .pdf → **Analyze Meeting**. Watch the LLM extract summary, decisions, action items, risks, and open questions.
3. **✅ Tasks** — filter, sort, and click **✅ Done** on any open item. It flips to Completed instantly.
4. **🧭 Decisions** — every decision across every meeting, on one page, with CSV export.
5. **💬 Ask Meeting** — ask *"What decisions were made?"* or *"What tasks are assigned to Rahul?"*. Answers come only from your records.
6. **🔀 Compare two meetings** — pick Kickoff vs Final Review → generate a "what changed" diff.
7. **🔍 Search** — one box across every meeting, task, decision, risk, and question.

**Closing line:**
> MeetMind AI transforms unstructured meeting conversations into structured decisions, responsibilities, and actionable follow-ups.
            """
        )

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_card("Meetings", len(meetings), "in your workspace", "indigo"), unsafe_allow_html=True)
    c2.markdown(stat_card("Open Tasks", stats["open"], f'{stats["total"]} total tasks', "amber"), unsafe_allow_html=True)
    c3.markdown(stat_card("Decisions", len(decisions), "captured across meetings", "sky"), unsafe_allow_html=True)
    c4.markdown(stat_card("Upcoming", len(upcoming), "deadlines in 14 days", "rose"), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Recent Meetings</div>', unsafe_allow_html=True)

    if not meetings:
        st.markdown(
            '<div class="empty-state">'
            '<div class="es-title">No meetings yet</div>'
            "Create your first meeting, or load the built-in demo workspace to explore MeetMind AI immediately."
            "</div>",
            unsafe_allow_html=True,
        )
        st.write("")
        col_a, col_b, _ = st.columns([1, 1, 2])
        with col_a:
            if st.button("＋ Create a meeting", type="primary", width="stretch"):
                go("➕ New Meeting")
        with col_b:
            if st.button("⚡ Load demo data", width="stretch"):
                try:
                    count = db.seed_sample_data()
                    flash("success", f"Loaded {count} demo meetings. Explore the dashboard!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not load demo data: {exc}")
        return

    for m in meetings[:6]:
        col_card, col_btn = st.columns([5, 1])
        with col_card:
            st.markdown(meeting_card(m), unsafe_allow_html=True)
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Open →", key=f"open_{m['id']}", width="stretch"):
                go("📋 Meetings", m["id"])
        st.write("")

    if upcoming:
        st.markdown('<div class="section-title">Upcoming Deadlines</div>', unsafe_allow_html=True)
        rows = []
        for t in upcoming[:6]:
            rows.append(
                {
                    "Task": helpers.truncate(t.get("task"), 60),
                    "Owner": t.get("assignee") or "Unassigned",
                    "Deadline": helpers.pretty_date(t.get("deadline")),
                    "When": t.get("_label", ""),
                    "Priority": t.get("priority") or "Medium",
                }
            )
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    # ---- Weekly activity ----
    if len(meetings) >= 2:
        st.markdown('<div class="section-title">Meetings Per Week</div>', unsafe_allow_html=True)
        try:
            rows_wk = []
            for m in meetings:
                d = helpers.parse_deadline(m.get("date"))
                if d:
                    iso = d.isocalendar()
                    label = f"W{iso.week:02d} {iso.year}"
                    rows_wk.append({"Week": label, "Count": 1})

            if rows_wk:
                wk = (
                    pd.DataFrame(rows_wk)
                    .groupby("Week", sort=True)
                    .size()
                    .reset_index(name="Meetings")
                )
                st.bar_chart(wk.set_index("Week"), height=220, color="#4f46e5")
            else:
                st.caption("No dated meetings yet.")
        except Exception:
            st.caption("Could not compute weekly activity.")


# ----------------------------------------------------------------------
# PAGE: New Meeting
# ----------------------------------------------------------------------
def page_new_meeting() -> None:
    st.markdown('<div class="page-title">New Meeting</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Paste a transcript or upload a .txt, .md, or .pdf file — MeetMind AI extracts the rest.</div>',
        unsafe_allow_html=True,
    )

    if not ai_service.is_configured():
        st.warning(
            "⚠️ No LLM API key configured. Add `LLM_API_KEY` to your `.env` file, "
            "then restart the app to enable analysis."
        )

    col_left, col_right = st.columns([3, 2])

    with col_left:
        title = st.text_input("Meeting title", placeholder="e.g. Project Nimbus – Sprint Review")
        meeting_date = st.date_input("Meeting date", value=date.today())

        existing = known_participants()
        selected_participants = st.multiselect(
            "Participants (pick from previous meetings)",
            options=existing,
            default=[],
            help="Choose any returning participants",
        )
        extra_participants = st.text_input(
            "Add new participants",
            placeholder="Comma-separated, e.g. Priya Nair, Karan Shah",
            help="New names not in the list above",
        )

        all_names: list[str] = list(selected_participants)
        for raw in extra_participants.split(","):
            raw = raw.strip()
            if raw and raw not in all_names:
                all_names.append(raw)
        participants = ", ".join(all_names)

    with col_right:
        st.markdown("**Upload transcript**")
        uploaded = st.file_uploader(
            "Upload a transcript",
            type=["txt", "md", "pdf"],
            help="Supports .txt, .md, and .pdf files",
        )
        if uploaded is not None:
            if st.button("📥 Load file into notes", width="stretch"):
                try:
                    name_lower = (uploaded.name or "").lower()
                    raw_bytes = uploaded.read()

                    if name_lower.endswith(".pdf"):
                        content = extract_pdf_text(raw_bytes)
                        if not content:
                            st.error(
                                "This PDF doesn't contain selectable text — it's "
                                "likely a scanned document. Please paste the "
                                "transcript manually or upload a text version."
                            )
                        else:
                            st.session_state.transcript_input = content
                            st.success(
                                f"Extracted {len(content):,} characters from the PDF."
                            )
                            st.rerun()
                    else:
                        content = raw_bytes.decode("utf-8", errors="ignore")
                        st.session_state.transcript_input = content
                        st.rerun()

                except RuntimeError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Could not read that file: {exc}")

        st.caption(
            "Supports **.txt**, **.md**, and **.pdf**. "
            "PDFs must contain selectable text (not scanned images)."
        )

    transcript = st.text_area(
        "Transcript / Notes",
        key="transcript_input",
        height=300,
        placeholder="Paste the full meeting transcript or your rough notes here…",
    )

    word_count = len(transcript.split()) if transcript else 0
    st.caption(f"{word_count} words · {len(transcript)} characters")

    analyze = st.button("⚡  Analyze Meeting", type="primary", width="content")

    if not analyze:
        return

    if not title.strip():
        st.error("Please enter a meeting title.")
        return
    if not transcript.strip():
        st.error("Please paste a transcript or upload a file first.")
        return
    if len(transcript.strip()) < 40:
        st.error("The transcript is too short to analyse. Add at least a few sentences.")
        return
    if not ai_service.is_configured():
        st.error("No LLM API key configured. Add LLM_API_KEY to your .env file and restart.")
        return

    with st.spinner("Analyzing meeting… this usually takes 5–15 seconds."):
        try:
            data = ai_service.extract_meeting_data(transcript)
        except ai_service.AIServiceError as exc:
            st.error(f"Analysis failed: {exc}")
            return
        except Exception as exc:
            st.error(f"Unexpected error during analysis: {exc}")
            return

        try:
            meeting_id = db.create_meeting(
                title=title,
                date=meeting_date.isoformat(),
                participants=participants,
                transcript=transcript,
                summary=data["summary"],
                key_points=data["key_points"],
            )
            db.save_extraction(meeting_id, data)
        except db.DatabaseError as exc:
            st.error(f"Could not save the meeting: {exc}")
            return

    flash(
        "success",
        f"✅ “{title}” analysed — {len(data['action_items'])} tasks, "
        f"{len(data['decisions'])} decisions, {len(data['risks'])} risks extracted.",
    )
    st.session_state.transcript_input = ""
    go("📋 Meetings", meeting_id)


# ----------------------------------------------------------------------
# PAGE: Meetings (list + detail)
# ----------------------------------------------------------------------
def render_meeting_detail(meeting_id: int) -> None:
    bundle = db.get_meeting_bundle(meeting_id)
    if not bundle:
        st.error("That meeting could not be found.")
        return

    m = bundle["meeting"]
    tasks = bundle["tasks"]

    st.markdown(f'<div class="page-title">{helpers._esc(m["title"])}</div>', unsafe_allow_html=True)
    meta = f'📅 {helpers.pretty_date(m.get("date"))}'
    st.markdown(f'<div class="meta-line">{meta}</div>', unsafe_allow_html=True)

    if m.get("participants"):
        chips = "".join(
            f'<span class="participant-chip">{helpers._esc(p.strip())}</span>'
            for p in m["participants"].split(",")
            if p.strip()
        )
        st.markdown(chips, unsafe_allow_html=True)

    # ---- Export to Markdown ----
    md_content = build_meeting_markdown(bundle)
    safe_name = re.sub(r"[^\w\-]+", "_", m.get("title") or "meeting")[:60] or "meeting"
    _, col_export = st.columns([4, 1])
    with col_export:
        st.download_button(
            "⬇️  Export .md",
            data=md_content,
            file_name=f"{safe_name}.md",
            mime="text/markdown",
            width="stretch",
            help="Download this meeting as a Markdown file",
        )

    st.write("")
    stats = helpers.task_stats(tasks)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_card("Tasks", stats["total"], f'{stats["open"]} open', "indigo"), unsafe_allow_html=True)
    c2.markdown(stat_card("Decisions", len(bundle["decisions"]), "recorded", "sky"), unsafe_allow_html=True)
    c3.markdown(stat_card("Risks", len(bundle["risks"]), "flagged", "rose"), unsafe_allow_html=True)
    c4.markdown(stat_card("Open Questions", len(bundle["questions"]), "unresolved", "amber"), unsafe_allow_html=True)

    st.write("")
    st.markdown(panel("Executive Summary", f'<p>{helpers._esc(m.get("summary"))}</p>'), unsafe_allow_html=True)
    st.markdown(panel("Key Discussion Points", bullets(m.get("key_points") or [])), unsafe_allow_html=True)
    st.markdown(panel("Decisions", bullets(bundle["decisions"])), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Action Items</div>', unsafe_allow_html=True)
    st.markdown(tasks_table_html(tasks), unsafe_allow_html=True)

    if tasks:
        with st.expander("✏️ Update a task status"):
            labels = {t["id"]: f'{helpers.truncate(t["task"], 70)}' for t in tasks}
            col_a, col_b, col_c = st.columns([3, 2, 1])
            with col_a:
                task_id = st.selectbox(
                    "Task", options=list(labels.keys()),
                    format_func=lambda i: labels[i], key=f"upd_task_{meeting_id}",
                )
            with col_b:
                new_status = st.selectbox(
                    "New status", ["Pending", "In Progress", "Completed"],
                    key=f"upd_status_{meeting_id}",
                )
            with col_c:
                st.write("")
                st.write("")
                if st.button("Update", key=f"upd_btn_{meeting_id}", width="stretch"):
                    try:
                        db.update_task_status(int(task_id), new_status)
                        flash("success", "Task status updated.")
                        st.rerun()
                    except db.DatabaseError as exc:
                        st.error(str(exc))

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(panel("Risks & Blockers", bullets(bundle["risks"])), unsafe_allow_html=True)
    with col_r:
        st.markdown(panel("Unresolved Questions", bullets(bundle["questions"])), unsafe_allow_html=True)

    with st.expander("📄 Original transcript"):
        st.text(m.get("transcript") or "No transcript stored.")

    st.write("")
    b1, b2, _ = st.columns([1, 1, 3])
    with b1:
        if st.button("💬 Ask about this meeting", width="stretch"):
            st.session_state["ask_scope"] = meeting_id
            go("💬 Ask Meeting")
    with b2:
        if st.button("🗑 Delete meeting", width="stretch"):
            try:
                db.delete_meeting(meeting_id)
                st.session_state.view_meeting = None
                flash("success", "Meeting deleted.")
                st.rerun()
            except db.DatabaseError as exc:
                st.error(str(exc))


def page_meetings() -> None:
    meetings = db.get_meetings()
    st.markdown('<div class="page-title">Meetings</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Browse every meeting in your workspace.</div>',
        unsafe_allow_html=True,
    )

    if meetings:
        search_query = st.text_input(
            "🔍 Search meetings",
            placeholder="Filter by title, participant, or date…",
            label_visibility="collapsed",
        ).strip().lower()

        if search_query:
            before = len(meetings)
            meetings = [
                m
                for m in meetings
                if search_query in (m.get("title") or "").lower()
                or search_query in (m.get("participants") or "").lower()
                or search_query in (m.get("date") or "").lower()
                or search_query in (m.get("summary") or "").lower()
            ]
            st.caption(f"Showing {len(meetings)} of {before} meetings")

    if not meetings:
        st.markdown(
            '<div class="empty-state"><div class="es-title">No meetings yet</div>'
            "Create a meeting or load the demo workspace from the Dashboard.</div>",
            unsafe_allow_html=True,
        )
        return

    ids = [m["id"] for m in meetings]
    if st.session_state.view_meeting not in ids:
        st.session_state.view_meeting = ids[0]

    labels = {
        m["id"]: f'{m["title"]}  ·  {helpers.pretty_date(m.get("date"))}' for m in meetings
    }
    selected = st.selectbox(
        "Select a meeting",
        options=ids,
        index=ids.index(st.session_state.view_meeting),
        format_func=lambda i: labels[i],
    )
    st.session_state.view_meeting = selected

    st.markdown("---")
    render_meeting_detail(selected)


# ----------------------------------------------------------------------
# PAGE: Tasks
# ----------------------------------------------------------------------
def page_tasks() -> None:
    st.markdown('<div class="page-title">Tasks</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Every action item across every meeting, in one place.</div>',
        unsafe_allow_html=True,
    )

    # ---- One-shot toast from a previous action ----
    toast_msg = st.session_state.pop("_toast_msg", None)
    if toast_msg:
        try:
            st.toast(toast_msg, icon="✅")
        except Exception:
            st.success(toast_msg)

    all_tasks = db.get_all_tasks()

    if not all_tasks:
        st.markdown(
            '<div class="empty-state"><div class="es-title">No tasks yet</div>'
            "Analyse a meeting to generate action items.</div>",
            unsafe_allow_html=True,
        )
        return

    stats = helpers.task_stats(all_tasks)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_card("Total Tasks", stats["total"], "across all meetings", "indigo"), unsafe_allow_html=True)
    c2.markdown(stat_card("Pending", stats["pending"], "not started", "amber"), unsafe_allow_html=True)
    c3.markdown(stat_card("In Progress", stats["in_progress"], "being worked on", "sky"), unsafe_allow_html=True)
    c4.markdown(stat_card("Completed", stats["completed"], "done", "green"), unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="section-title">Filters</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        status_filter = st.multiselect(
            "Status", ["Pending", "In Progress", "Completed"], default=[]
        )
    with f2:
        assignees = sorted({(t.get("assignee") or "Unassigned") for t in all_tasks})
        assignee_filter = st.multiselect("Assignee", assignees, default=[])
    with f3:
        priority_filter = st.multiselect("Priority", ["High", "Medium", "Low"], default=[])

    filtered = all_tasks
    if status_filter:
        filtered = [t for t in filtered if (t.get("status") or "Pending") in status_filter]
    if assignee_filter:
        filtered = [t for t in filtered if (t.get("assignee") or "Unassigned") in assignee_filter]
    if priority_filter:
        filtered = [t for t in filtered if (t.get("priority") or "Medium") in priority_filter]

    # ---- Sort controls ----
    sort_col, dir_col, _spacer = st.columns([2, 1, 3])
    with sort_col:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest first", "Deadline (soonest)", "Priority (High→Low)", "Status", "Assignee"],
            index=0,
            key="tasks_sort_by",
        )
    with dir_col:
        sort_desc = st.checkbox("Descending", value=False, key="tasks_sort_desc")

    PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}
    STATUS_RANK = {"Pending": 0, "In Progress": 1, "Completed": 2}

    from datetime import date as _date

    def _deadline_key(t):
        d = helpers.parse_deadline(t.get("deadline"))
        return d or _date.max

    if sort_by == "Newest first":
        filtered = sorted(filtered, key=lambda t: t.get("id", 0), reverse=not sort_desc)
    elif sort_by == "Deadline (soonest)":
        filtered = sorted(filtered, key=_deadline_key, reverse=sort_desc)
    elif sort_by == "Priority (High→Low)":
        filtered = sorted(
            filtered,
            key=lambda t: PRIORITY_RANK.get(t.get("priority") or "Medium", 1),
            reverse=sort_desc,
        )
    elif sort_by == "Status":
        filtered = sorted(
            filtered,
            key=lambda t: STATUS_RANK.get(t.get("status") or "Pending", 0),
            reverse=sort_desc,
        )
    elif sort_by == "Assignee":
        filtered = sorted(
            filtered,
            key=lambda t: (t.get("assignee") or "Unassigned").lower(),
            reverse=sort_desc,
        )

    # ---- Quick complete: one-click finish for open tasks ----
    open_tasks = [t for t in filtered if (t.get("status") or "Pending") != "Completed"]
    if open_tasks:
        with st.expander(f"⚡ Quick complete — {len(open_tasks)} open task(s)", expanded=False):
            for task in open_tasks[:25]:
                col_info, col_btn = st.columns([6, 1])
                with col_info:
                    st.markdown(
                        f"**{helpers.truncate(task.get('task'), 72)}**  \n"
                        f"<small style='color:#64748b;'>"
                        f"{helpers._esc(task.get('assignee') or 'Unassigned')} · "
                        f"{helpers._esc(task.get('deadline') or 'No deadline')} · "
                        f"{helpers._esc(task.get('priority') or 'Medium')}"
                        f"</small>",
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    if st.button(
                        "✅ Done",
                        key=f"quick_done_{task['id']}",
                        width="stretch",
                        help="Mark as Completed",
                    ):
                        try:
                            db.update_task_status(int(task["id"]), "Completed")
                            st.session_state["_toast_msg"] = (
                                f"Completed: {helpers.truncate(task.get('task'), 60)}"
                            )
                            st.rerun()
                        except db.DatabaseError as exc:
                            st.error(str(exc))

    st.markdown('<div class="section-title">All Action Items</div>', unsafe_allow_html=True)
    st.caption("Edit the Status column directly — changes save automatically.")

    if not filtered:
        st.info("No tasks match the current filters.")
    else:
        df = pd.DataFrame(
            [
                {
                    "id": t["id"],
                    "Task": t.get("task") or "",
                    "Meeting": t.get("meeting_title") or "—",
                    "Assignee": t.get("assignee") or "Unassigned",
                    "Deadline": t.get("deadline") or "No deadline",
                    "Priority": t.get("priority") or "Medium",
                    "Status": t.get("status") or "Pending",
                }
                for t in filtered
            ]
        )

        editor_key = f"tasks_editor_{len(df)}_{'-'.join(status_filter)}_{'-'.join(assignee_filter)}_{'-'.join(priority_filter)}_{sort_by}_{sort_desc}"

        edited = st.data_editor(
            df,
            hide_index=True,
            width="stretch",
            key=editor_key,
            disabled=["Task", "Meeting", "Assignee", "Deadline", "Priority"],
            column_config={
                "id": None,
                "Task": st.column_config.TextColumn("Task", width="large"),
                "Meeting": st.column_config.TextColumn("Meeting", width="medium"),
                "Assignee": st.column_config.TextColumn("Assignee", width="small"),
                "Deadline": st.column_config.TextColumn("Deadline", width="small"),
                "Priority": st.column_config.SelectboxColumn(
                    "Priority", options=["High", "Medium", "Low"], width="small"
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Pending", "In Progress", "Completed"],
                    required=True,
                    width="small",
                ),
            },
        )

        changed = False
        try:
            for idx in df.index:
                if edited.at[idx, "Status"] != df.at[idx, "Status"]:
                    db.update_task_status(int(df.at[idx, "id"]), str(edited.at[idx, "Status"]))
                    changed = True
        except (KeyError, db.DatabaseError) as exc:
            st.error(f"Could not update task status: {exc}")

        if changed:
            flash("success", "Task status updated.")
            st.rerun()

    upcoming = helpers.upcoming_deadlines(all_tasks, within_days=21)
    st.markdown('<div class="section-title">Upcoming Deadlines</div>', unsafe_allow_html=True)
    if not upcoming:
        st.caption("No upcoming deadlines in the next 21 days.")
    else:
        for t in upcoming[:10]:
            st.markdown(
                f'<div class="panel" style="padding:.7rem 1rem;margin-bottom:.5rem;">'
                f'<strong style="color:#0f172a;">{helpers._esc(helpers.truncate(t.get("task"), 80))}</strong>'
                f'<span style="color:#94a3b8;font-size:.82rem;"> · {helpers._esc(t.get("meeting_title") or "")}</span>'
                f'<br><span style="font-size:.8rem;color:#64748b;">'
                f'{helpers._esc(t.get("assignee") or "Unassigned")} · '
                f'{helpers.pretty_date(t.get("deadline"))} · {helpers._esc(t.get("_label", ""))}</span> '
                f'{helpers.priority_badge(t.get("priority"))} {helpers.status_badge(t.get("status"))}'
                f"</div>",
                unsafe_allow_html=True,
            )


# ----------------------------------------------------------------------
# PAGE: Decision Log
# ----------------------------------------------------------------------
def page_decisions() -> None:
    st.markdown('<div class="page-title">Decision Log</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Every decision across every meeting, in one place.</div>',
        unsafe_allow_html=True,
    )

    decisions = db.get_decisions_with_meetings()
    if not decisions:
        st.markdown(
            '<div class="empty-state"><div class="es-title">No decisions recorded yet</div>'
            "Load the demo workspace or analyse a meeting to populate the log.</div>",
            unsafe_allow_html=True,
        )
        return

    meetings = db.get_meetings()
    meeting_ids = [m["id"] for m in meetings]
    labels = {
        m["id"]: f'{m["title"]}  ·  {helpers.pretty_date(m.get("date"))}'
        for m in meetings
    }

    # ---- Stat row ----
    unique_meetings = len({d["meeting_id"] for d in decisions})
    avg = round(len(decisions) / unique_meetings, 1) if unique_meetings else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(
        stat_card("Total Decisions", len(decisions), "across your workspace", "sky"),
        unsafe_allow_html=True,
    )
    c2.markdown(
        stat_card(
            "Meetings with Decisions",
            unique_meetings,
            f"of {len(meetings)} total",
            "indigo",
        ),
        unsafe_allow_html=True,
    )
    c3.markdown(
        stat_card("Average per Meeting", avg, "decisions per meeting", "amber"),
        unsafe_allow_html=True,
    )

    st.write("")

    # ---- Filters + Export ----
    filter_col, export_col, _spacer = st.columns([2, 1, 3])
    with filter_col:
        selected_meetings = st.multiselect(
            "Filter by meeting",
            options=meeting_ids,
            format_func=lambda i: labels[i],
            default=[],
            key="decisions_filter",
        )

    filtered = decisions
    if selected_meetings:
        filtered = [d for d in filtered if d["meeting_id"] in selected_meetings]

    # ---- CSV export ----
    csv_lines = ["Meeting,Date,Decision"]
    for d in filtered:
        meeting = (d.get("meeting_title") or "").replace(",", ";").replace('"', "'")
        d_date = d.get("meeting_date") or ""
        decision = (d.get("decision") or "").replace(",", ";").replace('"', "'")
        csv_lines.append(f'"{meeting}","{d_date}","{decision}"')
    csv_data = "\n".join(csv_lines)

    with export_col:
        st.write("")
        st.write("")
        st.download_button(
            "⬇️  Export CSV",
            data=csv_data,
            file_name="meetmind_decisions.csv",
            mime="text/csv",
            width="stretch",
            help="Download the filtered decisions as CSV",
        )

    if not filtered:
        st.info("No decisions match the current filter.")
        return

    st.markdown(
        f'<div class="section-title">Showing {len(filtered)} decision(s)</div>',
        unsafe_allow_html=True,
    )

    # ---- Timeline-style cards ----
    for d in filtered:
        st.markdown(
            f'<div class="panel" style="padding:.9rem 1.2rem;margin-bottom:.55rem;">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:.75rem;">'
            f'<div style="color:#0f172a;font-size:.95rem;font-weight:600;line-height:1.5;">'
            f'🧭 {helpers._esc(d.get("decision"))}'
            f'</div>'
            f'<div style="color:#94a3b8;font-size:.78rem;white-space:nowrap;">'
            f'{helpers.pretty_date(d.get("meeting_date"))}'
            f'</div>'
            f'</div>'
            f'<div style="color:#64748b;font-size:.8rem;margin-top:.35rem;">'
            f'from <strong>{helpers._esc(d.get("meeting_title") or "—")}</strong>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------
# PAGE: Ask Meeting
# ----------------------------------------------------------------------
def page_ask() -> None:
    st.markdown('<div class="page-title">Ask the Meeting</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Ask anything — answers come only from your meeting records.</div>',
        unsafe_allow_html=True,
    )

    meetings = db.get_meetings()
    if not meetings:
        st.markdown(
            '<div class="empty-state"><div class="es-title">No meetings to query</div>'
            "Create a meeting first, then come back and ask questions.</div>",
            unsafe_allow_html=True,
        )
        return

    scope_options = ["🌐 All meetings"] + [
        f'{m["title"]}  ·  {helpers.pretty_date(m.get("date"))}' for m in meetings
    ]
    preset = st.session_state.pop("ask_scope", None)
    default_index = 0
    if preset is not None:
        for i, m in enumerate(meetings, start=1):
            if m["id"] == preset:
                default_index = i
                break

    scope = st.selectbox("Scope", scope_options, index=default_index)

    if scope == "🌐 All meetings":
        bundles = db.get_all_bundles()
        scope_key = "__all__"
    else:
        idx = scope_options.index(scope) - 1
        bundle = db.get_meeting_bundle(meetings[idx]["id"])
        bundles = [bundle] if bundle else []
        scope_key = str(meetings[idx]["id"])

    context = helpers.build_context(bundles)

    if not ai_service.is_configured():
        st.warning(
            "⚠️ No LLM API key configured. Add `LLM_API_KEY` to your `.env` file to enable Q&A."
        )

    st.caption(f"Context: {len(bundles)} meeting(s) · {len(context):,} characters")

    # ---- Compare two meetings ----
    if len(meetings) >= 2:
        with st.expander("🔀 Compare two meetings — what changed?", expanded=False):
            st.caption(
                "Pick any two meetings. The AI will summarize what changed between them, "
                "using only the content of those two meetings."
            )
            meeting_labels = {
                m["id"]: f'{m["title"]}  ·  {helpers.pretty_date(m.get("date"))}'
                for m in meetings
            }
            ids_sorted = list(meeting_labels.keys())
            cc1, cc2 = st.columns(2)
            with cc1:
                older_id = st.selectbox(
                    "Earlier meeting",
                    options=ids_sorted,
                    index=len(ids_sorted) - 1,
                    format_func=lambda i: meeting_labels[i],
                    key="cmp_older",
                )
            with cc2:
                newer_id = st.selectbox(
                    "Later meeting",
                    options=ids_sorted,
                    index=0,
                    format_func=lambda i: meeting_labels[i],
                    key="cmp_newer",
                )

            if st.button("🔀 Generate comparison", type="primary", key="cmp_btn"):
                if older_id == newer_id:
                    st.warning("Please pick two different meetings.")
                elif not ai_service.is_configured():
                    st.error("No LLM API key configured.")
                else:
                    older = db.get_meeting_bundle(older_id)
                    newer = db.get_meeting_bundle(newer_id)
                    cmp_context = helpers.build_context(
                        [older, newer], max_total_chars=20000
                    )
                    cmp_question = (
                        "Compare these two meetings. Describe what changed between them: "
                        "new decisions, changed decisions, tasks that were completed, "
                        "tasks that were added, new risks, and questions that were resolved "
                        "or remain open. Structure your answer with clear headings."
                    )
                    with st.spinner("Comparing meetings…"):
                        try:
                            cmp_answer = ai_service.answer_question(cmp_context, cmp_question)
                        except ai_service.AIServiceError as exc:
                            st.error(str(exc))
                        except Exception as exc:
                            st.error(f"Unexpected error: {exc}")
                        else:
                            st.markdown('<div class="section-title">Comparison Result</div>',
                                        unsafe_allow_html=True)
                            st.markdown(cmp_answer)
                            st.session_state["_last_comparison"] = cmp_answer

    col_a, col_b = st.columns([1, 5])
    with col_a:
        if st.button("🧹 Clear chat", width="stretch"):
            st.session_state.chat[scope_key] = []
            st.rerun()

    if scope_key not in st.session_state.chat:
        st.session_state.chat[scope_key] = []

    history = st.session_state.chat[scope_key]

    suggestions = [
        "What decisions were made?",
        "What tasks are assigned to Rahul?",
        "What is the deadline for the payment integration?",
        "What risks were identified?",
        "What is still unresolved?",
    ]
    if not history:
        st.markdown('<div class="section-title">Try asking</div>', unsafe_allow_html=True)
        cols = st.columns(len(suggestions))
        for col, suggestion in zip(cols, suggestions):
            with col:
                if st.button(helpers.truncate(suggestion, 26), key=f"sug_{scope_key}_{suggestion}",
                             width="stretch"):
                    history.append({"role": "user", "content": suggestion})
                    st.session_state.chat[scope_key] = history
                    st.rerun()

    for message in history:
        with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🧠"):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask a question about the selected meeting(s)…")

    if prompt:
        history.append({"role": "user", "content": prompt})
        st.session_state.chat[scope_key] = history

        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Searching meeting records…"):
                try:
                    answer = ai_service.answer_question(context, prompt, history[:-1])
                except ai_service.AIServiceError as exc:
                    answer = f"⚠️ {exc}"
                except Exception as exc:
                    answer = f"⚠️ Unexpected error: {exc}"
            st.markdown(answer)

        history.append({"role": "assistant", "content": answer})
        st.session_state.chat[scope_key] = history


# ----------------------------------------------------------------------
# PAGE: Global Search
# ----------------------------------------------------------------------
def page_search() -> None:
    st.markdown('<div class="page-title">Search</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">One search box across every meeting, task, decision, risk, and question.</div>',
        unsafe_allow_html=True,
    )

    # Apply any queued suggestion click BEFORE the search input is created.
    if st.session_state.pending_search is not None:
        st.session_state.global_search_input = st.session_state.pending_search
        st.session_state.pending_search = None

    total = db.count_meetings()
    if total == 0:
        st.markdown(
            '<div class="empty-state"><div class="es-title">Nothing to search yet</div>'
            "Load the demo workspace from the Dashboard, or create a meeting first.</div>",
            unsafe_allow_html=True,
        )
        return

    query = st.text_input(
        "🔍 Search everything",
        placeholder="Try: Razorpay, refund, deployment, Rahul, 20 April…",
        label_visibility="collapsed",
        key="global_search_input",
    ).strip()

    if not query:
        st.caption(f"Searching across {total} meeting(s).")
        st.markdown('<div class="section-title">Try one of these</div>', unsafe_allow_html=True)
        suggestions = ["Razorpay", "refund", "deployment", "Dean", "Rahul", "UPI"]
        cols = st.columns(len(suggestions))
        for col, s in zip(cols, suggestions):
            with col:
                if st.button(s, key=f"search_sug_{s}", width="stretch"):
                    st.session_state.pending_search = s
                    st.rerun()
        return

    results = db.global_search(query)

    counts = {k: len(v) for k, v in results.items()}
    total_hits = sum(counts.values())

    if total_hits == 0:
        st.info(f'No matches for **"{query}"**. Try a shorter or different keyword.')
        return

    st.caption(
        f"**{total_hits}** result(s) for **\"{query}\"** — "
        f"{counts['meetings']} meetings · {counts['tasks']} tasks · "
        f"{counts['decisions']} decisions · {counts['risks']} risks · "
        f"{counts['questions']} questions"
    )

    # ---- Meetings ----
    if results["meetings"]:
        st.markdown('<div class="section-title">📋 Meetings</div>', unsafe_allow_html=True)
        for m in results["meetings"]:
            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(
                    f'<div class="mcard">'
                    f'<div class="mcard-top">'
                    f'<span class="mcard-title">{helpers._esc(m.get("title"))}</span>'
                    f'<span class="mcard-date">{helpers.pretty_date(m.get("date"))}</span>'
                    f'</div>'
                    f'<div style="margin-top:.4rem;color:#64748b;font-size:.85rem;">'
                    f'{helpers._esc(helpers.truncate(m.get("summary"), 160))}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
            with col_btn:
                st.write("")
                st.write("")
                if st.button("Open →", key=f"search_open_meeting_{m['id']}", width="stretch"):
                    st.session_state.view_meeting = m["id"]
                    go("📋 Meetings", m["id"])
            st.write("")

    # ---- Tasks ----
    if results["tasks"]:
        st.markdown('<div class="section-title">✅ Tasks</div>', unsafe_allow_html=True)
        rows = []
        for t in results["tasks"]:
            rows.append(
                f'<tr>'
                f'<td class="t-task">{helpers._esc(helpers.truncate(t.get("task"), 80))}</td>'
                f'<td>{helpers._esc(t.get("assignee") or "Unassigned")}</td>'
                f'<td>{helpers._esc(t.get("meeting_title") or "—")}</td>'
                f'<td>{helpers._esc(t.get("deadline") or "No deadline")}</td>'
                f'<td>{helpers.priority_badge(t.get("priority"))}</td>'
                f'<td>{helpers.status_badge(t.get("status"))}</td>'
                f'</tr>'
            )
        st.markdown(
            '<table class="mm-table"><thead><tr>'
            '<th>Task</th><th>Assignee</th><th>Meeting</th><th>Deadline</th><th>Priority</th><th>Status</th>'
            '</tr></thead><tbody>'
            + "".join(rows)
            + '</tbody></table>',
            unsafe_allow_html=True,
        )

    # ---- Decisions ----
    if results["decisions"]:
        st.markdown('<div class="section-title">🧭 Decisions</div>', unsafe_allow_html=True)
        for d in results["decisions"]:
            st.markdown(
                f'<div class="panel" style="padding:.7rem 1rem;margin-bottom:.5rem;">'
                f'<div style="color:#0f172a;font-size:.92rem;">'
                f'🧭 {helpers._esc(d.get("decision"))}'
                f'</div>'
                f'<div style="color:#94a3b8;font-size:.78rem;margin-top:.25rem;">'
                f'{helpers._esc(d.get("meeting_title") or "—")} · '
                f'{helpers.pretty_date(d.get("meeting_date"))}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    # ---- Risks ----
    if results["risks"]:
        st.markdown('<div class="section-title">⚠️ Risks & Blockers</div>', unsafe_allow_html=True)
        for r in results["risks"]:
            st.markdown(
                f'<div class="panel" style="padding:.7rem 1rem;margin-bottom:.5rem;">'
                f'<div style="color:#0f172a;font-size:.92rem;">'
                f'⚠️ {helpers._esc(r.get("risk"))}'
                f'</div>'
                f'<div style="color:#94a3b8;font-size:.78rem;margin-top:.25rem;">'
                f'{helpers._esc(r.get("meeting_title") or "—")} · '
                f'{helpers.pretty_date(r.get("meeting_date"))}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    # ---- Questions ----
    if results["questions"]:
        st.markdown('<div class="section-title">❓ Unresolved Questions</div>', unsafe_allow_html=True)
        for q in results["questions"]:
            st.markdown(
                f'<div class="panel" style="padding:.7rem 1rem;margin-bottom:.5rem;">'
                f'<div style="color:#0f172a;font-size:.92rem;">'
                f'❓ {helpers._esc(q.get("question"))}'
                f'</div>'
                f'<div style="color:#94a3b8;font-size:.78rem;margin-top:.25rem;">'
                f'{helpers._esc(q.get("meeting_title") or "—")} · '
                f'{helpers.pretty_date(q.get("meeting_date"))}'
                f'</div></div>',
                unsafe_allow_html=True,
            )


# ----------------------------------------------------------------------
# PAGE: Analytics
# ----------------------------------------------------------------------
def page_analytics() -> None:
    st.markdown('<div class="page-title">Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">A quick read on how your team is executing.</div>',
        unsafe_allow_html=True,
    )

    meetings = db.get_meetings()
    tasks = db.get_all_tasks()
    decisions = db.get_decisions()
    questions = db.get_questions()

    if not meetings:
        st.markdown(
            '<div class="empty-state"><div class="es-title">Nothing to analyse yet</div>'
            "Add a meeting or load the demo workspace from the Dashboard.</div>",
            unsafe_allow_html=True,
        )
        return

    stats = helpers.task_stats(tasks)
    completion = round((stats["completed"] / stats["total"]) * 100) if stats["total"] else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_card("Meetings", len(meetings), "total", "indigo"), unsafe_allow_html=True)
    c2.markdown(stat_card("Decisions", len(decisions), "captured", "sky"), unsafe_allow_html=True)
    c3.markdown(stat_card("Open Questions", len(questions), "unresolved", "amber"), unsafe_allow_html=True)
    c4.markdown(stat_card("Completion", f"{completion}%", f'{stats["completed"]}/{stats["total"]} tasks', "green"), unsafe_allow_html=True)

    st.write("")

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">Meetings Over Time</div>', unsafe_allow_html=True)
        mdf = pd.DataFrame([{"Date": m.get("date") or "unknown"} for m in meetings])
        mdf = mdf[mdf["Date"] != "unknown"]
        if mdf.empty:
            st.caption("No dated meetings yet.")
        else:
            grouped = mdf.groupby("Date").size().reset_index(name="Meetings")
            st.bar_chart(grouped.set_index("Date"), height=260, color="#4f46e5")

    with col_r:
        st.markdown('<div class="section-title">Tasks by Status</div>', unsafe_allow_html=True)
        sdf = pd.DataFrame(
            {
                "Status": ["Pending", "In Progress", "Completed"],
                "Count": [stats["pending"], stats["in_progress"], stats["completed"]],
            }
        )
        st.bar_chart(sdf.set_index("Status"), height=260, color="#7c3aed")

    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.markdown('<div class="section-title">Tasks by Priority</div>', unsafe_allow_html=True)
        pcounts = {"High": 0, "Medium": 0, "Low": 0}
        for t in tasks:
            pcounts[(t.get("priority") or "Medium")] = pcounts.get(t.get("priority") or "Medium", 0) + 1
        pdf = pd.DataFrame({"Priority": list(pcounts.keys()), "Count": list(pcounts.values())})
        st.bar_chart(pdf.set_index("Priority"), height=260, color="#f59e0b")

    with col_r2:
        st.markdown('<div class="section-title">Tasks by Assignee</div>', unsafe_allow_html=True)
        if not tasks:
            st.caption("No tasks yet.")
        else:
            adf = (
                pd.DataFrame([{"Assignee": t.get("assignee") or "Unassigned"} for t in tasks])
                .groupby("Assignee")
                .size()
                .reset_index(name="Tasks")
                .sort_values("Tasks", ascending=False)
            )
            st.bar_chart(adf.set_index("Assignee"), height=260, color="#0ea5e9")

    st.markdown('<div class="section-title">Meetings Summary</div>', unsafe_allow_html=True)
    summary_df = pd.DataFrame(
        [
            {
                "Meeting": m["title"],
                "Date": helpers.pretty_date(m.get("date")),
                "Tasks": m.get("task_count", 0),
                "Decisions": m.get("decision_count", 0),
                "Risks": m.get("risk_count", 0),
                "Open Questions": m.get("question_count", 0),
            }
            for m in meetings
        ]
    )
    st.dataframe(summary_df, hide_index=True, width="stretch")


# ----------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------
PAGES = {
    "🏠 Dashboard": page_dashboard,
    "➕ New Meeting": page_new_meeting,
    "📋 Meetings": page_meetings,
    "✅ Tasks": page_tasks,
    "🧭 Decisions": page_decisions,
    "💬 Ask Meeting": page_ask,
    "🔍 Search": page_search,
    "📊 Analytics": page_analytics,
}

current = st.session_state.nav
if current not in PAGES:
    current = NAV_ITEMS[0]

try:
    PAGES[current]()
except db.DatabaseError as exc:
    st.error(f"⚠️ Database error: {exc}")
except Exception as exc:
    st.error(f"⚠️ Something went wrong: {exc}")
    with st.expander("Technical details"):
        import traceback

        st.code(traceback.format_exc())