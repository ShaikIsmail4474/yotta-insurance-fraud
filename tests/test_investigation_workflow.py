
import pytest

from src.investigation_workflow import (
    build_network_evidence,
    open_network_investigation,
)
from src.case_management import get_case, get_audit_history


def test_network_evidence_contains_explanation():
    evidence = build_network_evidence("CLM-2026-000001")

    assert evidence["claim_id"] == "CLM-2026-000001"
    assert evidence["max_hops"] == 3
    assert evidence["connected_entity_count"] >= 1
    assert "investigative leads, not proof of fraud" in evidence["summary"]


def test_network_evidence_rejects_invalid_hop_limit():
    with pytest.raises(ValueError, match="max_hops"):
        build_network_evidence("CLM-2026-000001", max_hops=0)


def test_network_evidence_rejects_unknown_claim():
    with pytest.raises(ValueError, match="not found"):
        build_network_evidence("CLM-DOES-NOT-EXIST")


def test_open_network_investigation_creates_audited_case(tmp_path):
    from src.build_database import DB_PATH
    import shutil

    test_db = tmp_path / "insurance_fraud_test.db"
    shutil.copy2(DB_PATH, test_db)

    result = open_network_investigation(
        claim_id="CLM-2026-000001",
        actor="test_reviewer",
        assigned_to="analyst_1",
        db_path=test_db,
    )

    assert result["status"] == "Open"
    assert result["reviewer_decision"] == "Pending"
    assert result["evidence"]["claim_id"] == "CLM-2026-000001"

    case = get_case(result["case_id"], db_path=test_db)
    assert case["status"] == "Open"
    assert case["reviewer_decision"] == "Pending"
    assert "Network review for claim" in case["reason"]

    history = get_audit_history(result["case_id"], db_path=test_db)
    assert len(history) == 1
    assert history[0]["action"] == "CASE_CREATED"
