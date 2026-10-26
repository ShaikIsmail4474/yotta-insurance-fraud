# Insurance Fraud Detection — Data Model

## 1. Purpose

This project generates synthetic insurance records, validates relationships and financial data, assigns explainable fraud-risk scores, and produces investigation reports for manual review.

The current implementation contains eight operational datasets and one separate ground-truth dataset.

## 2. Implemented Entities

| Entity | Primary key | Purpose |
|---|---|---|
| Claimant | `claimant_id` | Person or account holder submitting claims |
| Provider | `provider_id` | Organization or person providing services |
| Policy | `policy_id` | Insurance coverage and validity dates |
| Incident | `incident_id` | Event associated with a claim |
| Claim | `claim_id` | Claim amount, status, claimant, policy, incident, and provider |
| Invoice | `invoice_id` | Provider charges associated with a claim |
| Payment | `payment_id` | Payment transaction associated with a claim and invoice |
| RelationshipEdge | `edge_id` | Recorded relationship between two entity IDs |
| Ground truth | Claim or edge reference, depending on label type | Separate synthetic labels used for evaluation |

`FraudIndicator` and `Investigation` are conceptual entities in the original design but are not currently generated as separate datasets or stored as dedicated database tables. The risk scores and investigation report are generated as output files.

## 3. Dataset Relationships

- A claimant can be associated with multiple claims.
- Each generated policy references a claimant.
- A claim references a claimant, policy, incident, and provider.
- Each generated invoice references a claim and provider.
- The current database schema enforces one invoice per claim.
- A payment references a claim and invoice.
- RelationshipEdge records links between source and target IDs. The edge type identifies the relationship.
- Ground-truth labels are exported separately from the operational datasets.

### Current Implementation Limitation

The data model documentation describes broader relationships than the current database supports. For example, multiple invoices per claim are not allowed by the current `UNIQUE` constraint on `invoices.claim_id`.

The relationship-edge table also uses generic source and target IDs rather than dedicated foreign keys to each entity table. Consequently, the validator checks IDs against the combined entity ID set and applies relationship-type rules.

## 4. RelationshipEdge Fields

The implemented relationship-edge dataset contains:

- `edge_id`
- `source_id`
- `target_id`
- `edge_type`
- `effective_date`
- `is_planted_suspicious`

The `is_planted_suspicious` field describes synthetic planted edges. It must not be used as an input feature by the fraud-risk detector.

## 5. Validation Rules

The current validation implementation checks primary-key uniqueness, relationship-edge integrity, supported relationship types, and selected claim, invoice, and payment constraints.

The broader design also calls for:

- Date and policy-period validation.
- Allowed lifecycle statuses.
- Financial reconciliation between claims, invoices, approvals, and payments.
- Explicit handling of intentionally invalid negative-test records.
- Protection against treating a shared address alone as proof of fraud.

Only checks implemented in the validation code should be described as automatically enforced.

## 6. Negative Test Scenarios

The test suite includes five intended negative scenarios:

1. A claim references a nonexistent policy.
2. A payment exceeds the approved amount.
3. An invoice identifier is duplicated across different claimants.
4. A planted relationship is missing from the recorded relationship edges.
5. A benign shared address must not be treated as sufficient proof of fraud.

These tests verify selected failure cases and design expectations. They do not establish that every possible invalid state is detected.

## 7. Ground Truth and Evaluation

The generator writes ground-truth labels separately from operational data. The fraud-risk scoring process uses operational records rather than ground-truth labels.

The evaluation process compares the generated risk scores with the separate claim-level labels and calculates confusion-matrix counts, precision, recall, and F1 score.

The current synthetic dataset contains deliberately planted patterns that align with the baseline detection rules. Therefore, the resulting metrics must not be interpreted as evidence of equivalent performance on real insurance data.

## 8. Reproducibility

The generator uses a fixed random seed and deterministic identifiers. The reproducibility script compares row counts and checksums across generated datasets.

The current run with seed `42` passed the reproducibility check for all nine datasets.

## 9. Known Gaps and Future Work

- Add dedicated FraudIndicator and Investigation records if required by the final system design.
- Implement reviewer assignment, investigation status transitions, outcomes, and audit history.
- Review whether invoice and payment cardinalities should be expanded.
- Improve explicit lifecycle and financial reconciliation validation.
- Extend relationship analysis to support traceable multi-hop investigations.
- Continue testing false positives, false negatives, and benign shared relationships.
