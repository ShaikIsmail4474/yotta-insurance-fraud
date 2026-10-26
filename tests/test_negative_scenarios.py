
"""Tests for five negative scenarios in the insurance fraud challenge."""

from copy import deepcopy
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generator import GeneratorConfig, generate_master_records
from validate_data import validate_records


@pytest.fixture(scope="module")
def valid_records():
    return generate_master_records(GeneratorConfig(seed=42))


def test_claim_with_nonexistent_policy_is_rejected(valid_records):
    records = deepcopy(valid_records)
    claim = records["claims"][0]
    claim["policy_id"] = "POL-DOES-NOT-EXIST"

    errors = validate_records(records)

    assert any(
        claim["claim_id"] in error and "policy does not exist" in error
        for error in errors
    ), f"Expected missing-policy error. Got: {errors}"


def test_payment_above_approved_amount_is_rejected(valid_records):
    records = deepcopy(valid_records)
    payment = records["payments"][0]

    claim_by_id = {
        claim["claim_id"]: claim
        for claim in records["claims"]
    }
    claim = claim_by_id[payment["claim_id"]]

    # Use the actual field name: payment_amount.
    payment["payment_amount"] = claim["approved_amount"] + 1000

    errors = validate_records(records)

    assert any(
        payment["payment_id"] in error
        and "payment exceeds approved amount" in error
        for error in errors
    ), f"Expected excessive-payment error. Got: {errors}"


def test_duplicate_invoice_across_claimants_is_rejected(valid_records):
    records = deepcopy(valid_records)

    first_invoice = records["invoices"][0]
    first_claim = next(
        claim for claim in records["claims"]
        if claim["claim_id"] == first_invoice["claim_id"]
    )

    second_invoice = next(
        invoice for invoice in records["invoices"][1:]
        if next(
            claim for claim in records["claims"]
            if claim["claim_id"] == invoice["claim_id"]
        )["claimant_id"] != first_claim["claimant_id"]
    )

    # Reuse an existing invoice ID for a different claimant's claim.
    second_invoice["invoice_id"] = first_invoice["invoice_id"]

    errors = validate_records(records)

    assert any(
        "duplicate primary key in invoices" in error.lower()
        for error in errors
    ), f"Expected duplicate invoice ID error. Got: {errors}"


def test_missing_planted_relationship_edge_is_detectable(valid_records):
    records = deepcopy(valid_records)

    planted_edges = [
        edge for edge in records["relationship_edges"]
        if edge["edge_type"] == "SHARES_CONTACT"
        and edge.get("is_planted_suspicious") is True
    ]
    assert planted_edges, "Expected planted suspicious contact edges."

    removed_edge = planted_edges[0]

    # Ground truth must retain the label even when the graph edge is missing.
    edge_truth = [
        label for label in records["ground_truth"]
        if label["record_id"] == removed_edge["edge_id"]
        and label["is_planted_suspicious"] is True
    ]
    assert edge_truth, (
        "Expected a ground-truth label for the planted relationship edge. "
        "Check how relationship-edge labels are represented by the generator."
    )

    records["relationship_edges"].remove(removed_edge)

    remaining_edge_ids = {
        edge["edge_id"] for edge in records["relationship_edges"]
    }

    assert removed_edge["edge_id"] not in remaining_edge_ids
    assert any(
        label["record_id"] == removed_edge["edge_id"]
        and label["is_planted_suspicious"] is True
        for label in records["ground_truth"]
    ), "Ground truth should still identify the missing planted relationship."


def test_shared_address_alone_is_not_proof_of_fraud(valid_records):
    records = deepcopy(valid_records)

    # Ground truth labels claims and planted edges, not claimant IDs.
    suspicious_claim_ids = {
        label["record_id"]
        for label in records["ground_truth"]
        if label["record_id"].startswith("CLM-")
        and label["is_planted_suspicious"] is True
    }

    claims_by_claimant = {}
    for claim in records["claims"]:
        claims_by_claimant.setdefault(
            claim["claimant_id"], []
        ).append(claim)

    suspicious_claimants = {
        claim["claimant_id"]
        for claim in records["claims"]
        if claim["claim_id"] in suspicious_claim_ids
    }

    claimants_by_address = {}
    for claimant in records["claimants"]:
        claimants_by_address.setdefault(
            claimant["address_id"], []
        ).append(claimant["claimant_id"])

    # Find a shared address used by at least two claimants who are not
    # part of the planted suspicious-claim pattern.
    benign_pair = None
    for claimant_ids in claimants_by_address.values():
        benign_ids = [
            claimant_id for claimant_id in claimant_ids
            if claimant_id not in suspicious_claimants
        ]
        if len(benign_ids) >= 2:
            benign_pair = benign_ids[:2]
            break

    assert benign_pair is not None, (
        "Expected at least two non-suspicious claimants sharing an address."
    )

    for claimant_id in benign_pair:
        for claim in claims_by_claimant.get(claimant_id, []):
            assert claim["claim_id"] not in suspicious_claim_ids, (
                "A shared address alone must not make a claim suspicious."
            )
