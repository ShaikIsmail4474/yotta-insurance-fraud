# Source Manifest and Data Provenance

## 1. Purpose

This project uses reproducible synthetic insurance data to demonstrate insurance-claim risk detection, relationship-network analysis, and investigation case management. The generated data is intended for software development and evaluation, not for making real insurance decisions.

## 2. Data Sources

| Dataset | Source | Purpose |
|---|---|---|
| `claimants.csv` | Synthetic generator | Represents claimant records |
| `policies.csv` | Synthetic generator | Represents insurance policies |
| `providers.csv` | Synthetic generator | Represents service providers |
| `incidents.csv` | Synthetic generator | Represents reported incidents |
| `claims.csv` | Synthetic generator | Represents insurance claims and their lifecycle fields |
| `invoices.csv` | Synthetic generator | Represents invoices associated with claims |
| `payments.csv` | Synthetic generator | Represents payments against claims and invoices |
| `relationship_edges.csv` | Synthetic generator | Represents relationships between entities |
| `ground_truth.csv` | Synthetic generator | Stores planted evaluation labels, separate from operational detection inputs |

All datasets are generated for this project. No production insurance records or real customer personal data are intentionally used.

## 3. Reproducibility

The generator uses a fixed random seed of `42` for the baseline dataset.

Run the repository's documented generator command from the project root to recreate the data. Use the exact command documented in `README.md` and `src/generator.py`.

After generation, run the project's validation and reproducibility checks. The resulting counts and checksums should be recorded in the validation summary.

## 4. Detection and Evaluation Separation

Operational detection and investigation reporting must not use `ground_truth.csv` to calculate claim risk scores or decide which cases to investigate.

Ground-truth labels are reserved for evaluating detection results after scoring. Any planted relationship marker, including `is_planted_suspicious`, must not be treated as an operational fraud signal.

## 5. Limitations

- The data is synthetic and cannot establish real-world fraud-detection accuracy.
- Planted patterns may be easier to detect than real fraud.
- Shared addresses, contacts, providers, and other relationships can have legitimate explanations.
- Risk scores and network connections are investigative leads, not proof of fraud.
- Results depend on the generator, rules, seed, and evaluation labels used.

## 6. Data Handling

Generated datasets and derived reports should be treated as project artifacts. Do not add secrets, credentials, real policyholder data, or other sensitive production information to the public repository.