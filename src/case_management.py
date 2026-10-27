
"""Investigation case lifecycle and audit trail using SQLite."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "insurance_fraud.db"
)

STATUSES = {"Open", "Under Review", "Escalated", "Closed"}

DECISIONS = {
    "Pending",
    "Fraud Suspected",
    "No Fraud Found",
    "Insufficient Evidence",
}

ALLOWED_TRANSITIONS = {
    "Open": {"Under Review", "Escalated"},
    "Under Review": {"Open", "Escalated", "Closed"},
    "Escalated": {"Under Review", "Closed"},
    "Closed": set(),
}


def connect(db_path=DB_PATH):
    """Create a SQLite connection with foreign-key checks enabled."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection_scope(db_path=DB_PATH):
    """Commit successful transactions, roll back failures, and close."""
    conn = connect(db_path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def initialize_case_tables(db_path=DB_PATH):
    """Create investigation and audit tables and supporting indexes."""
    with connection_scope(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS investigation_cases (
                case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open'
                    CHECK(status IN (
                        'Open', 'Under Review', 'Escalated', 'Closed'
                    )),
                reviewer_decision TEXT NOT NULL DEFAULT 'Pending'
                    CHECK(reviewer_decision IN (
                        'Pending', 'Fraud Suspected', 'No Fraud Found',
                        'Insufficient Evidence'
                    )),
                assigned_to TEXT,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
            );

            CREATE TABLE IF NOT EXISTS investigation_audit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                old_values TEXT,
                new_values TEXT,
                reason TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                FOREIGN KEY (case_id)
                    REFERENCES investigation_cases(case_id)
            );

            CREATE INDEX IF NOT EXISTS idx_cases_status
                ON investigation_cases(status);

            CREATE INDEX IF NOT EXISTS idx_cases_claim
                ON investigation_cases(claim_id);

            CREATE INDEX IF NOT EXISTS idx_audit_case_time
                ON investigation_audit(case_id, occurred_at);
        """)


def _now():
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _record_audit(
    conn, case_id, actor, action, old_values, new_values, reason
):
    """Append an audit event within the current transaction."""
    conn.execute(
        """
        INSERT INTO investigation_audit (
            case_id, actor, action, old_values, new_values,
            reason, occurred_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            actor,
            action,
            json.dumps(old_values, sort_keys=True)
            if old_values is not None else None,
            json.dumps(new_values, sort_keys=True)
            if new_values is not None else None,
            reason,
            _now(),
        ),
    )


def create_case(
    claim_id, reason, actor, assigned_to=None, db_path=DB_PATH
):
    """Create an Open investigation case for an existing claim."""
    if not all(
        isinstance(value, str) and value.strip()
        for value in (claim_id, reason, actor)
    ):
        raise ValueError("claim_id, reason, and actor are required.")

    if assigned_to is not None and (
        not isinstance(assigned_to, str) or not assigned_to.strip()
    ):
        raise ValueError("assigned_to must be non-empty or None.")

    initialize_case_tables(db_path)

    with connection_scope(db_path) as conn:
        claim = conn.execute(
            "SELECT claim_id FROM claims WHERE claim_id = ?",
            (claim_id,),
        ).fetchone()

        if claim is None:
            raise ValueError(f"Claim does not exist: {claim_id}")

        now = _now()
        cursor = conn.execute(
            """
            INSERT INTO investigation_cases (
                claim_id, status, reviewer_decision, assigned_to,
                reason, created_at, updated_at
            ) VALUES (?, 'Open', 'Pending', ?, ?, ?, ?)
            """,
            (claim_id, assigned_to, reason, now, now),
        )
        case_id = cursor.lastrowid

        _record_audit(
            conn,
            case_id,
            actor,
            "CASE_CREATED",
            None,
            {
                "claim_id": claim_id,
                "status": "Open",
                "reviewer_decision": "Pending",
                "assigned_to": assigned_to,
                "reason": reason,
            },
            reason,
        )

        return case_id


def get_case(case_id, db_path=DB_PATH):
    """Return a case dictionary, or None if it does not exist."""
    initialize_case_tables(db_path)

    with connection_scope(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM investigation_cases WHERE case_id = ?",
            (case_id,),
        ).fetchone()

        return dict(row) if row else None


def update_case(
    case_id,
    actor,
    reason,
    *,
    status=None,
    reviewer_decision=None,
    assigned_to=None,
    update_assignment=False,
    db_path=DB_PATH,
):
    """Update a case, enforce lifecycle rules, and record an audit event."""
    if not all(
        isinstance(value, str) and value.strip()
        for value in (actor, reason)
    ):
        raise ValueError("actor and reason are required.")

    if (
        status is None
        and reviewer_decision is None
        and not update_assignment
    ):
        raise ValueError("Provide at least one field to update.")

    if status is not None and status not in STATUSES:
        raise ValueError(f"Invalid status: {status}")

    if (
        reviewer_decision is not None
        and reviewer_decision not in DECISIONS
    ):
        raise ValueError(
            f"Invalid reviewer decision: {reviewer_decision}"
        )

    if update_assignment and assigned_to is not None and (
        not isinstance(assigned_to, str) or not assigned_to.strip()
    ):
        raise ValueError("assigned_to must be non-empty or None.")

    initialize_case_tables(db_path)

    with connection_scope(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM investigation_cases WHERE case_id = ?",
            (case_id,),
        ).fetchone()

        if row is None:
            raise ValueError(f"Case does not exist: {case_id}")

        old = dict(row)

        if old["status"] == "Closed":
            raise ValueError("A closed case cannot be changed.")

        new = {}

        if status is not None:
            if status != old["status"] and (
                status not in ALLOWED_TRANSITIONS[old["status"]]
            ):
                raise ValueError(
                    f"Transition not allowed: "
                    f"{old['status']} -> {status}"
                )
            new["status"] = status

        if reviewer_decision is not None:
            new["reviewer_decision"] = reviewer_decision

        if update_assignment:
            new["assigned_to"] = assigned_to

        if not new or all(
            old[key] == value for key, value in new.items()
        ):
            raise ValueError("No actual change to save.")

        final_status = new.get("status", old["status"])
        final_decision = new.get(
            "reviewer_decision", old["reviewer_decision"]
        )

        if final_status == "Closed" and final_decision == "Pending":
            raise ValueError(
                "Record a reviewer decision before closing the case."
            )

        changed_old = {
            key: old[key]
            for key, value in new.items()
            if old[key] != value
        }
        changed_new = {
            key: value
            for key, value in new.items()
            if old[key] != value
        }

        if not changed_new:
            raise ValueError("No actual change to save.")

        changed_new["updated_at"] = _now()
        fields = list(changed_new)
        assignments = ", ".join(
            f"{field} = ?" for field in fields
        )

        conn.execute(
            f"UPDATE investigation_cases SET {assignments} "
            "WHERE case_id = ?",
            [changed_new[field] for field in fields] + [case_id],
        )

        _record_audit(
            conn,
            case_id,
            actor,
            "CASE_UPDATED",
            changed_old,
            changed_new,
            reason,
        )


def get_audit_history(case_id, db_path=DB_PATH):
    """Return audit events for a case in insertion order."""
    initialize_case_tables(db_path)

    with connection_scope(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM investigation_audit
            WHERE case_id = ?
            ORDER BY audit_id
            """,
            (case_id,),
        ).fetchall()

        return [dict(row) for row in rows]
