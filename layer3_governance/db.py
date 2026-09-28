"""
Layer 3 - Governance & Logging (central threat-intelligence log).

Every decision the system makes - both prompt screening (Layer 1) and image
screening (Layer 2) - is recorded in this SQLite database. This builds the
evidentiary trail the seminar calls for under the Nigeria Data Protection Act
(2023) and the Cybercrimes (Amendment) Act (2024), and it feeds the analyst
review dashboard.

Pure standard-library (sqlite3) - no external dependencies.
"""

import os
import json
import sqlite3
from datetime import datetime

# database.db lives at the project root (one level up from this package).
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "database.db",
)


def get_connection():
    """Open a connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the events table if it does not yet exist."""
    conn = get_connection()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     TEXT    NOT NULL,
            event_type    TEXT    NOT NULL,   -- 'prompt' or 'image'
            input_summary TEXT,               -- prompt text or image filename
            verdict       TEXT    NOT NULL,   -- allowed / blocked / clean / flagged
            risk_score    REAL,               -- 0.0 - 1.0
            severity      TEXT,               -- low / medium / high / critical
            details       TEXT,               -- JSON: reasons, signals, model info
            reviewed      INTEGER DEFAULT 0,  -- 0 = pending, 1 = reviewed
            analyst_note  TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def log_event(event_type, input_summary, verdict, risk_score, severity, details=None):
    """Record one decision and return its new event id."""
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO events
            (timestamp, event_type, input_summary, verdict, risk_score,
             severity, details, reviewed)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            event_type,
            input_summary,
            verdict,
            float(risk_score),
            severity,
            json.dumps(details or {}),
        ),
    )
    conn.commit()
    event_id = cur.lastrowid
    conn.close()
    return event_id


def get_events(limit=100, only_flagged=False, only_pending=False):
    """Return recent events, newest first, with optional filters."""
    conn = get_connection()
    query = "SELECT * FROM events"
    clauses = []
    if only_flagged:
        clauses.append("verdict IN ('blocked', 'flagged')")
    if only_pending:
        clauses.append("reviewed = 0")
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC LIMIT ?"
    rows = conn.execute(query, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_event(event_id):
    """Return a single event as a dict, or None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_review(event_id, analyst_note, mark_reviewed=True):
    """Attach an analyst note and (optionally) mark the case reviewed."""
    conn = get_connection()
    cur = conn.execute(
        "UPDATE events SET analyst_note = ?, reviewed = ? WHERE id = ?",
        (analyst_note, 1 if mark_reviewed else 0, event_id),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise ValueError(f"Event {event_id} not found.")


def get_stats():
    """Summary counters for the dashboard header."""
    conn = get_connection()
    one = lambda sql: conn.execute(sql).fetchone()[0]
    stats = {
        "total": one("SELECT COUNT(*) FROM events"),
        "blocked": one("SELECT COUNT(*) FROM events WHERE verdict = 'blocked'"),
        "flagged": one("SELECT COUNT(*) FROM events WHERE verdict = 'flagged'"),
        "pending_review": one(
            "SELECT COUNT(*) FROM events "
            "WHERE reviewed = 0 AND verdict IN ('blocked', 'flagged')"
        ),
        "critical": one("SELECT COUNT(*) FROM events WHERE severity = 'critical'"),
    }
    conn.close()
    return stats


if __name__ == "__main__":
    # Allow `py layer3_governance/db.py` to initialise the database directly.
    init_db()
    print(f"Database ready at: {DB_PATH}")
