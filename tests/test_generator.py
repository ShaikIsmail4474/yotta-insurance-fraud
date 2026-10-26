
"""Automated tests for the synthetic insurance data generator."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generator import GeneratorConfig, generate_master_records
from validate_data import validate_records


@pytest.fixture(scope="module")
def records():
    return generate_master_records(GeneratorConfig(seed=42))


def test_expected_record_counts(records):
    assert len(records["claimants"]) == 2000
    assert len(records["providers"]) == 500
    assert len(records["policies"]) == 2000
    assert len(records["incidents"]) == 3000
    assert len(records["claims"]) == 5000
    assert len(records["invoices"]) == 5000
    assert len(records["relationship_edges"]) == 8000


def test_primary_keys_are_unique(records):
    key_fields = {
        "claimants": "claimant_id",
        "providers": "provider_id",
        "policies": "policy_id",
        "incidents": "incident_id",
        "claims": "claim_id",
        "invoices": "invoice_id",
        "payments": "payment_id",
        "relationship_edges": "edge_id",
    }

    for entity, key in key_fields.items():
        values = [row[key] for row in records[entity]]
        assert len(values) == len(set(values)), entity


def test_relationship_edges_are_unique(records):
    edge_keys = {
        (row["source_id"], row["target_id"], row["edge_type"])
        for row in records["relationship_edges"]
    }
    assert len(edge_keys) == 8000


def test_claim_amounts_are_valid(records):
    for claim in records["claims"]:
        assert claim["claimed_amount"] > 0
        assert 0 <= claim["approved_amount"] <= claim["claimed_amount"]


def test_invoice_amount_matches_claim(records):
    claims_by_id = {
        row["claim_id"]: row for row in records["claims"]
    }

    for invoice in records["invoices"]:
        claim = claims_by_id[invoice["claim_id"]]
        assert invoice["invoice_amount"] == claim["claimed_amount"]
        assert invoice["provider_id"] == claim["provider_id"]


def test_ground_truth_is_separate(records):
    assert "ground_truth" in records
    assert len(records["ground_truth"]) >= len(records["claims"])

    for label in records["ground_truth"]:
        assert "record_id" in label
        assert "is_planted_suspicious" in label
        assert "reason" in label


def test_generator_passes_validator(records):
    errors = validate_records(records)
    assert errors == [], "\n".join(errors)
