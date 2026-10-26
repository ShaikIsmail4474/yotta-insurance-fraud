
"""Baseline fraud-risk scoring for synthetic insurance claims."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "generated"
OUTPUT_DIR = ROOT / "outputs"


def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / f"{name}.csv")


def build_risk_scores() -> pd.DataFrame:
    claimants = load_csv("claimants")
    claims = load_csv("claims")
    edges = load_csv("relationship_edges")

    # Count claimants sharing each phone number.
    phone_counts = claimants.groupby("phone")["claimant_id"].nunique()
    phone_counts = phone_counts.to_dict()

    # Count distinct claimants using each provider.
    provider_counts = (
        claims.groupby("provider_id")["claimant_id"].nunique().to_dict()
    )

    # Count shared-contact relationships per claimant.
    contact_edges = edges[edges["edge_type"] == "SHARES_CONTACT"]
    contact_counts = {}

    for _, edge in contact_edges.iterrows():
        for claimant_id in (edge["source_id"], edge["target_id"]):
            contact_counts[claimant_id] = (
                contact_counts.get(claimant_id, 0) + 1
            )

    claimant_phone = claimants.set_index("claimant_id")["phone"].to_dict()

    results = []

    for _, claim in claims.iterrows():
        claimant_id = claim["claimant_id"]
        provider_id = claim["provider_id"]
        phone = claimant_phone.get(claimant_id, "")

        shared_phone_count = phone_counts.get(phone, 0)
        provider_claimant_count = provider_counts.get(provider_id, 0)
        contact_edge_count = contact_counts.get(claimant_id, 0)

        # Transparent baseline score: 0 to 100.
        score = 0
        reasons = []

        if shared_phone_count >= 3:
            score += 40
            reasons.append(
                f"Phone shared by {shared_phone_count} claimants"
            )

        if provider_claimant_count >= 10:
            score += 30
            reasons.append(
                f"Provider serves {provider_claimant_count} claimants"
            )

        if contact_edge_count >= 1:
            score += 30
            reasons.append(
                f"{contact_edge_count} shared-contact edge(s)"
            )

        score = min(score, 100)

        results.append({
            "claim_id": claim["claim_id"],
            "claimant_id": claimant_id,
            "provider_id": provider_id,
            "risk_score": score,
            "risk_level": (
                "HIGH" if score >= 70
                else "MEDIUM" if score >= 40
                else "LOW"
            ),
            "evidence": "; ".join(reasons) if reasons else "No baseline signals",
        })

    return pd.DataFrame(results)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scores = build_risk_scores()
    scores = scores.sort_values(
        ["risk_score", "claim_id"],
        ascending=[False, True],
    )

    output_path = OUTPUT_DIR / "claim_risk_scores.csv"
    scores.to_csv(output_path, index=False)

    summary = {
        "claims_scored": int(len(scores)),
        "high_risk": int((scores["risk_level"] == "HIGH").sum()),
        "medium_risk": int((scores["risk_level"] == "MEDIUM").sum()),
        "low_risk": int((scores["risk_level"] == "LOW").sum()),
        "scoring_method": "Transparent rule-based baseline",
    }

    with (OUTPUT_DIR / "risk_summary.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=2)

    print("Fraud-risk scoring complete")
    print(json.dumps(summary, indent=2))
    print("\nTop 10 claims:")
    print(scores.head(10).to_string(index=False))
    print(f"\nSaved scores to: {output_path}")


if __name__ == "__main__":
    main()
