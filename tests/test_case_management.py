
import sqlite3

import pytest

from src.case_management import (
    create_case,
    get_case,
    get_audit_history,
    update_case,
)


@pytest.fixture
def test_db(tmp_path):
    """Create an isolated database for case-management tests."""
    db_path = tmp_path / "case_test.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE claims (
                claim_id TEXT PRIMARY KEY
            )
        """)
        conn.execute(
            "INSERT INTO claims (claim_id) VALUES (?)",
            ("TEST-CLAIM-001",),
        )

    return db_path


@pytest.fixture
def case_id(test_db):
    """Create a case for tests that need an existing investigation."""
    return create_case(
        claim_id="TEST-CLAIM-001",
        reason="Test suspicious shared contact",
        actor="test-analyst",
        assigned_to="test-reviewer",
        db_path=test_db,
    )


def test_create_case_and_audit(test_db, case_id):
    case = get_case(case_id, db_path=test_db)

    assert case["claim_id"] == "TEST-CLAIM-001"
    assert case["status"] == "Open"
    assert case["reviewer_decision"] == "Pending"
    assert case["assigned_to"] == "test-reviewer"

    history = get_audit_history(case_id, db_path=test_db)
    assert len(history) == 1
    assert history[0]["action"] == "CASE_CREATED"
    assert history[0]["actor"] == "test-analyst"


def test_cannot_create_case_for_missing_claim(test_db):
    with pytest.raises(ValueError, match="Claim does not exist"):
        create_case(
            "MISSING-CLAIM",
            "Test missing claim",
            "test-analyst",
            db_path=test_db,
        )


def test_valid_lifecycle_and_audit_history(test_db, case_id):
    update_case(
        case_id,
        actor="test-reviewer",
        reason="Begin investigation",
        status="Under Review",
        db_path=test_db,
    )

    update_case(
        case_id,
        actor="test-reviewer",
        reason="Evidence reviewed",
        reviewer_decision="No Fraud Found",
        db_path=test_db,
    )

    update_case(
        case_id,
        actor="test-reviewer",
        reason="Review completed",
        status="Closed",
        db_path=test_db,
    )

    case = get_case(case_id, db_path=test_db)
    assert case["status"] == "Closed"
    assert case["reviewer_decision"] == "No Fraud Found"

    history = get_audit_history(case_id, db_path=test_db)
    assert len(history) == 4
    assert history[0]["action"] == "CASE_CREATED"
    assert all(event["actor"] == "test-reviewer"
               for event in history[1:])


def test_cannot_skip_required_status_transition(test_db, case_id):
    with pytest.raises(ValueError, match="Transition not allowed"):
        update_case(
            case_id,
            actor="test-reviewer",
            reason="Invalid direct closure",
            status="Closed",
            db_path=test_db,
        )

    assert get_case(case_id, db_path=test_db)["status"] == "Open"
    assert len(get_audit_history(case_id, db_path=test_db)) == 1


def test_cannot_close_pending_case(test_db, case_id):
    update_case(
        case_id,
        actor="test-reviewer",
        reason="Begin review",
        status="Under Review",
        db_path=test_db,
    )

    with pytest.raises(
        ValueError, match="reviewer decision before closing"
    ):
        update_case(
            case_id,
            actor="test-reviewer",
            reason="Attempt closure without decision",
            status="Closed",
            db_path=test_db,
        )

    assert get_case(case_id, db_path=test_db)["status"] == "Under Review"


def test_closed_case_cannot_be_changed(test_db, case_id):
    update_case(
        case_id,
        actor="test-reviewer",
        reason="Begin review",
        status="Under Review",
        db_path=test_db,
    )
    update_case(
        case_id,
        actor="test-reviewer",
        reason="Review completed",
        reviewer_decision="Insufficient Evidence",
        db_path=test_db,
    )
    update_case(
        case_id,
        actor="test-reviewer",
        reason="Close review",
        status="Closed",
        db_path=test_db,
    )

    with pytest.raises(ValueError, match="closed case cannot be changed"):
        update_case(
            case_id,
            actor="test-reviewer",
            reason="Attempt to reopen",
            status="Under Review",
            db_path=test_db,
        )
