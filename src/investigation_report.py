
"""Create an investigator-friendly report from fraud-risk scores."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "generated"
OUTPUT_DIR = ROOT / "outputs"

RISK_FILE = OUTPUT_DIR / "claim_risk_scores.csv"
CLAIMS_FILE = DATA_DIR / "claims.csv"
CLAIMANTS_FILE = DATA_DIR / "claimants.csv"
PROVIDERS_FILE = DATA_DIR / "providers.csv"
POLICIES_FILE = DATA_DIR / "policies.csv"
INVOICES_FILE = DATA_DIR / "invoices.csv"
PAYMENTS_FILE = DATA_DIR / "payments.csv"
EDGES_FILE = DATA_DIR / "relationship_edges.csv"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load operational data and risk scores, never ground truth.
    scores = pd.read_csv(RISK_FILE)
    claims = pd.read_csv(CLAIMS_FILE)
    claimants = pd.read_csv(CLAIMANTS_FILE)
    providers = pd.read_csv(PROVIDERS_FILE)
    policies = pd.read_csv(POLICIES_FILE)
    invoices = pd.read_csv(INVOICES_FILE)
    payments = pd.read_csv(PAYMENTS_FILE)
    edges = pd.read_csv(EDGES_FILE)

    # Attach useful claim details.
    report = scores.merge(
        claims[
            [
                "claim_id",
                "policy_id",
                "incident_id",
                "claim_date",
                "claimed_amount",
                "approved_amount",
                "status",
            ]
        ],
        on="claim_id",
        how="left",
        validate="one_to_one",
    )

    report = report.merge(
        claimants[["claimant_id", "full_name", "phone", "address_id"]],
        on="claimant_id",
        how="left",
        validate="many_to_one",
    )

    report = report.merge(
        providers[["provider_id", "provider_name", "provider_type"]],
        on="provider_id",
        how="left",
        validate="many_to_one",
    )

    # Count related records using source data.
    invoices_per_claim = invoices.groupby("claim_id").size()
    payments_per_claim = payments.groupby("claim_id").size()

    report["invoice_count"] = (
        report["claim_id"].map(invoices_per_claim).fillna(0).astype(int)
    )
    report["payment_count"] = (
        report["claim_id"].map(payments_per_claim).fillna(0).astype(int)
    )

    # Count claimants sharing each phone number.
    phone_counts = claimants.groupby("phone")["claimant_id"].nunique()
    report["claimants_sharing_phone"] = (
        report["phone"].map(phone_counts).fillna(0).astype(int)
    )

    # Count graph edges for the claimant and provider.
    claimant_edge_counts = edges[
        edges["edge_type"].astype(str).str.contains(
            "SHARED_CONTACT", case=False, na=False
        )
    ].groupby("source_id").size()

    provider_claim_counts = claims.groupby("provider_id")["claim_id"].nunique()

    report["shared_contact_edges"] = (
        report["claimant_id"].map(claimant_edge_counts).fillna(0).astype(int)
    )
    report["claims_for_provider"] = (
        report["provider_id"].map(provider_claim_counts).fillna(0).astype(int)
    )

    # Explain the score using existing evidence and observable details.
    def make_investigation_note(row):
        reasons = []

        if row["risk_level"] == "HIGH":
            reasons.append("High risk under the current scoring rules")

        if row["claimants_sharing_phone"] >= 3:
            reasons.append(
                f"Phone shared by {row['claimants_sharing_phone']} claimants"
            )

        if row["claims_for_provider"] >= 10:
            reasons.append(
                f"Provider has {row['claims_for_provider']} claims"
            )

        if row["shared_contact_edges"] > 0:
            reasons.append(
                f"{row['shared_contact_edges']} shared-contact edge(s) found"
            )

        if not reasons:
            reasons.append("No high-risk rule triggered in the current baseline")

        return "; ".join(reasons)

    report["investigation_note"] = report.apply(
        make_investigation_note, axis=1
    )

    # Create a prioritized work queue.
    report["priority"] = report["risk_level"].map(
        {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
    ).fillna(4).astype(int)

    report = report.sort_values(
        ["priority", "risk_score", "claim_id"],
        ascending=[True, False, True],
    )

    columns = [
        "claim_id",
        "claimant_id",
        "full_name",
        "provider_id",
        "provider_name",
        "policy_id",
        "incident_id",
        "claim_date",
        "claimed_amount",
        "approved_amount",
        "status",
        "risk_score",
        "risk_level",
        "priority",
        "investigation_note",
        "evidence",
        "claimants_sharing_phone",
        "claims_for_provider",
        "shared_contact_edges",
        "invoice_count",
        "payment_count",
    ]

    report[columns].to_csv(
        OUTPUT_DIR / "investigation_report.csv", index=False
    )

    high_risk = report[report["risk_level"] == "HIGH"]
    summary = {
        "claims_in_report": int(len(report)),
        "high_risk_claims": int((report["risk_level"] == "HIGH").sum()),
        "medium_risk_claims": int((report["risk_level"] == "MEDIUM").sum()),
        "low_risk_claims": int((report["risk_level"] == "LOW").sum()),
        "high_risk_claims_with_invoice": int(
            (high_risk["invoice_count"] > 0).sum()
        ),
        "high_risk_claims_with_payment": int(
            (high_risk["payment_count"] > 0).sum()
        ),
        "note": (
            "Risk indicators prioritize manual review. "
            "They do not establish that fraud occurred. "
            "Ground-truth labels were not loaded."
        ),
    }

    (OUTPUT_DIR / "investigation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print("Investigation report created.")
    print(json.dumps(summary, indent=2))
    print(f"\nCSV report: {OUTPUT_DIR / 'investigation_report.csv'}")
    print(f"Summary: {OUTPUT_DIR / 'investigation_summary.json'}")

    print("\nHighest-priority claims:")
    print(
        report[
            [
                "claim_id",
                "claimant_id",
                "provider_id",
                "risk_score",
                "risk_level",
                "investigation_note",
            ]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()
