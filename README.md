# Insurance Fraud Detection and Investigation

## Overview

A reproducible synthetic insurance-claims investigation system that identifies potentially suspicious claims, explains risk indicators, and helps investigators prioritize cases for manual review.

The workflow connects claimants, policies, incidents, claims, providers, invoices, payments, and relationship edges. It validates data integrity, generates explainable risk scores, evaluates detection against separately stored synthetic ground truth, and creates investigator-friendly reports.

**Important:** A risk score is an investigation signal, not proof of fraud. The current detector is a transparent rule-based baseline and has not been validated on real-world insurance data.

## Features

- Generate deterministic synthetic insurance data using a configurable random seed.
- Create 5,000 claims and supporting claimant, policy, incident, provider, invoice, payment, and relationship records.
- Validate primary keys, foreign-key references, relationship edges, and financial constraints.
- Export generated records to CSV and JSON.
- Build and validate a SQLite database.
- Assign explainable claim risk scores using observable patterns such as shared phone numbers, provider activity, and recorded relationships.
- Keep synthetic ground-truth labels separate from fraud-risk scoring inputs.
- Evaluate predictions using precision, recall, F1 score, and confusion-matrix counts.
- Generate a prioritized investigation report with evidence explanations.
- Test invalid references, excessive payments, duplicate invoices, missing relationship edges, and benign shared-address scenarios.
- Check reproducibility by comparing generated outputs from repeated runs with the same seed.

## Technology Stack

- Python 3.10+
- Pandas
- NetworkX
- SQLite
- Pytest
- CSV and JSON

## Project Structure

```text
yotta-insurance-fraud/
├── data/
│   ├── generated/              # Generated CSV and JSON data
│   └── insurance_fraud.db      # Built SQLite database
├── docs/
│   ├── data_dictionary.md
│   ├── data_model.md
│   └── schema.sql
├── outputs/
│   ├── claim_risk_scores.csv
│   ├── risk_summary.json
│   ├── evaluation_summary.json
│   ├── investigation_report.csv
│   └── investigation_summary.json
├── prompts/                    # AI prompt history for the challenge
├── src/
│   ├── generator.py
│   ├── validate_data.py
│   ├── export_data.py
│   ├── check_reproducibility.py
│   ├── build_database.py
│   ├── check_database.py
│   ├── detect_fraud.py
│   ├── evaluate_model.py
│   └── investigation_report.py
├── tests/
│   ├── test_generator.py
│   └── test_negative_scenarios.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10 or newer
- Git
- A terminal such as Git Bash
- A virtual environment is recommended

## Setup

Clone the repository and enter the project directory:

```bash
git clone <YOUR_PUBLIC_REPOSITORY_URL>
cd yotta-insurance-fraud
```

Create and activate a virtual environment.

**Windows Git Bash:**

```bash
python -m venv .venv
source .venv/Scripts/activate
```

**Linux or macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Workflow

Run these commands from the repository root, in the following order.

### 1. Generate synthetic records

```bash
python src/generator.py
```

The generator uses a fixed seed by default so the synthetic records can be reproduced.

### 2. Validate generated records

```bash
python src/validate_data.py
```

### 3. Export CSV and JSON files

```bash
python src/export_data.py
```

### 4. Verify reproducibility

```bash
python src/check_reproducibility.py
```

### 5. Build the SQLite database

```bash
python src/build_database.py
```

### 6. Validate the database

```bash
python src/check_database.py
```

This checks SQLite integrity and foreign-key violations.

### 7. Calculate fraud-risk scores

```bash
python src/detect_fraud.py
```

Outputs include:

- `outputs/claim_risk_scores.csv`
- `outputs/risk_summary.json`

### 8. Evaluate detection results

```bash
python src/evaluate_model.py
```

The evaluation compares predicted risk labels with claim-level synthetic ground truth. Ground truth is used for evaluation only, not for calculating risk scores.

Output:

- `outputs/evaluation_summary.json`

### 9. Create the investigation report

```bash
python src/investigation_report.py
```

Outputs include:

- `outputs/investigation_report.csv`
- `outputs/investigation_summary.json`

### 10. Run automated tests

```bash
pytest -q
```

The current development environment has passed 33 automated tests. Run `python -m pytest -q` again after making changes and before submission.

## Current Synthetic Dataset

The current generated dataset contains:

| Entity | Records |
|---|---:|
| Claimants | 2,000 |
| Providers | 500 |
| Policies | 2,000 |
| Incidents | 3,000 |
| Claims | 5,000 |
| Invoices | 5,000 |
| Payments | 1,987 |
| Relationship edges | 8,000 |

The generated ground-truth file is stored separately from the operational entity data.

Counts may change if the generator configuration or random seed changes.

## Detection Approach

The initial detector uses transparent rules to assign claim risk scores. Current signals include:

- Phone numbers shared across multiple claimants.
- Providers associated with many claimants.
- Recorded shared-contact relationship edges.

The investigation report combines the scores with claim, claimant, provider, invoice, and payment details to help an analyst prioritize review.

Shared contact details, high provider volume, and graph connections can have legitimate explanations. These indicators must be reviewed in context; none alone proves fraud.

## Evaluation and Limitations

The current synthetic test run reported:

- Claims evaluated: 5,000
- True positives: 25
- False positives: 0
- False negatives: 0
- True negatives: 4,975
- Precision: 1.00
- Recall: 1.00
- F1 score: 1.00

These results reflect the planted patterns in the synthetic dataset and the behavior of the current rule-based detector. They **must not be interpreted as 100% accuracy on real insurance fraud**. The synthetic patterns and detection rules are not independent evidence of real-world performance.

Further work should test broader suspicious patterns, improve false-positive analysis, validate lifecycle and financial reconciliation rules, and evaluate performance on more diverse data.

## Data and Privacy

This project is designed around synthetic records. Do not commit real personal information, API keys, credentials, private application data, or other sensitive records.

The ground-truth labels are intended for evaluation and should not be used as detector input features.

## Reproducibility

The generator uses a configurable random seed and deterministic identifiers. The reproducibility script compares generated outputs from repeated runs using the same seed.

For meaningful comparisons, keep the seed, generator configuration, dependencies, and code version fixed.

## AI Prompt History

The `prompts/` directory should contain a reasonable record of prompts used with AI tools during development, as required by the challenge. Include the tool used and enough context to identify the purpose of each prompt. Disclose any unavailable history rather than claiming a complete export if one is not available.

## Future Improvements

- Expand graph-based investigation to trace multi-hop connections among claimants, providers, incidents, invoices, and payments.
- Add stronger lifecycle and payment-reconciliation validation.
- Improve handling of benign shared addresses and household relationships.
- Add investigation status, reviewer decisions, and an audit trail.
- Measure performance across more diverse synthetic scenarios and document false-positive and false-negative cases.
- Add a user interface or API if time permits.

## Disclaimer

This project is an educational synthetic-data prototype. Its outputs support investigation prioritization and do not establish that an individual or provider has committed fraud.
