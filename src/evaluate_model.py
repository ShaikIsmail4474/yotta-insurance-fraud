
"""Evaluate fraud-risk scores against separate ground-truth labels."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "generated"
OUTPUT_DIR = ROOT / "outputs"


def main() -> None:
    scores = pd.read_csv(OUTPUT_DIR / "claim_risk_scores.csv")
    ground_truth = pd.read_csv(DATA_DIR / "ground_truth.csv")

    # Evaluate claim labels only; relationship-edge labels are separate.
    claim_truth = ground_truth[
        ground_truth["record_id"].astype(str).str.startswith("CLM-")
    ].copy()

    claim_truth = claim_truth.rename(
        columns={"record_id": "claim_id"}
    )

    evaluation = scores.merge(
        claim_truth[["claim_id", "is_planted_suspicious"]],
        on="claim_id",
        how="left",
        validate="one_to_one",
    )

    if evaluation["is_planted_suspicious"].isna().any():
        raise ValueError("Some scored claims have no ground-truth label.")

    actual = (
        evaluation["is_planted_suspicious"].astype(bool)
    )
    predicted = evaluation["risk_level"].eq("HIGH")

    true_positive = int((predicted & actual).sum())
    false_positive = int((predicted & ~actual).sum())
    false_negative = int((~predicted & actual).sum())
    true_negative = int((~predicted & ~actual).sum())

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    summary = {
        "claims_evaluated": int(len(evaluation)),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "note": (
            "Evaluation only. Ground truth is not used by the "
            "fraud-risk scoring process."
        ),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "evaluation_summary.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    print("Fraud detection evaluation complete")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved evaluation to: {output_path}")


if __name__ == "__main__":
    main()
