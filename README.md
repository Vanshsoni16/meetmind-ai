# 🧠 MeetMind AI
### Turn every meeting into clear actions.

An AI Meeting Assistant Agent that converts unstructured meeting transcripts into
structured summaries, decisions, action items, owners, deadlines, risks and open questions —
and lets you ask questions about any meeting in natural language.

---

## 1. Problem

Meetings produce decisions, tasks and deadlines that are buried inside long, unstructured
notes. Participants forget what was agreed, who owns what, and when things are due.
Manually reviewing transcripts is slow and error-prone.

## 2. Solution

MeetMind AI ingests a meeting transcript or raw notes, sends it to an LLM with a strict
extraction prompt, and stores the result in a structured database. It then gives the team a
dashboard, a task tracker with live status updates, deadline monitoring, analytics, and a
chat interface that answers questions using **only** the stored meeting records.

## 3. Features

| Capability | Where |
|---|---|
| Create meetings from text or `.txt` upload | ➕ New Meeting |
| LLM extraction of summary, key points, decisions, actions, risks, questions | ➕ New Meeting |
| Structured storage of unlimited meetings | SQLite |
| Dashboard with live stats and recent meetings | 🏠 Dashboard |
| Full meeting detail view with badges and tables | 📋 Meetings |
| Cross-meeting task tracker with filters and inline editing | ✅ Tasks |
| Upcoming deadline monitoring | Dashboard + Tasks |
| Ask-the-Meeting chat (single meeting or all meetings) | 💬 Ask Meeting |
| Analytics: meetings over time, tasks by status/priority/assignee | 📊 Analytics |
| One-click demo workspace | 🏠 Dashboard → Load demo data |



