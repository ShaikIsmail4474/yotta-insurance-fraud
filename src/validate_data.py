
"""Validate generated synthetic insurance records."""

from generator import GeneratorConfig, generate_master_records


def validate_records(records: dict) -> list[str]:
    errors = []

    # 1. Check primary-key uniqueness
    primary_keys = {
        "claimants": "claimant_id",
        "providers": "provider_id",
        "policies": "policy_id",
        "incidents": "incident_id",
        "claims": "claim_id",
        "invoices": "invoice_id",
        "payments": "payment_id",
    }

    for entity, key in primary_keys.items():
        values = [row[key] for row in records[entity]]
        if len(values) != len(set(values)):
            errors.append(f"Duplicate primary key in {entity}")

    # 2. Build lookup sets and dictionaries
    claimant_ids = {
        row["claimant_id"] for row in records["claimants"]
    }
    provider_ids = {
        row["provider_id"] for row in records["providers"]
    }
    policy_by_id = {
        row["policy_id"]: row for row in records["policies"]
    }
    incident_by_id = {
        row["incident_id"]: row for row in records["incidents"]
    }
    claim_by_id = {
        row["claim_id"]: row for row in records["claims"]
    }
    invoice_by_id = {
        row["invoice_id"]: row for row in records["invoices"]
    }

    # 3. Validate claims
    for claim in records["claims"]:
        claim_id = claim["claim_id"]

        if claim["claimant_id"] not in claimant_ids:
            errors.append(f"{claim_id}: claimant does not exist")

        policy = policy_by_id.get(claim["policy_id"])
        if policy is None:
            errors.append(f"{claim_id}: policy does not exist")
            continue

        if policy["claimant_id"] != claim["claimant_id"]:
            errors.append(f"{claim_id}: policyholder mismatch")

        incident = incident_by_id.get(claim["incident_id"])
        if incident is None:
            errors.append(f"{claim_id}: incident does not exist")
        elif not (
            policy["start_date"]
            <= incident["incident_date"]
            <= policy["end_date"]
        ):
            errors.append(f"{claim_id}: incident outside policy dates")

        if claim["provider_id"] not in provider_ids:
            errors.append(f"{claim_id}: provider does not exist")

        if claim["claimed_amount"] <= 0:
            errors.append(f"{claim_id}: claimed amount must be positive")

        if not (
            0 <= claim["approved_amount"] <= claim["claimed_amount"]
        ):
            errors.append(f"{claim_id}: invalid approved amount")

    # 4. Validate invoices
    invoice_claim_ids = set()

    for invoice in records["invoices"]:
        invoice_id = invoice["invoice_id"]
        claim = claim_by_id.get(invoice["claim_id"])

        if claim is None:
            errors.append(f"{invoice_id}: claim does not exist")
            continue

        if invoice["provider_id"] not in provider_ids:
            errors.append(f"{invoice_id}: provider does not exist")

        if invoice["provider_id"] != claim["provider_id"]:
            errors.append(f"{invoice_id}: provider does not match claim")

        if invoice["invoice_amount"] <= 0:
            errors.append(f"{invoice_id}: invoice amount must be positive")

        if invoice["invoice_amount"] != claim["claimed_amount"]:
            errors.append(f"{invoice_id}: invoice amount mismatch")

        if invoice["claim_id"] in invoice_claim_ids:
            errors.append(f"{invoice_id}: duplicate invoice for claim")

        invoice_claim_ids.add(invoice["claim_id"])

    # 5. Validate payments
    for payment in records["payments"]:
        payment_id = payment["payment_id"]
        claim = claim_by_id.get(payment["claim_id"])
        invoice = invoice_by_id.get(payment["invoice_id"])

        if claim is None:
            errors.append(f"{payment_id}: claim does not exist")
            continue

        if invoice is None:
            errors.append(f"{payment_id}: invoice does not exist")
            continue

        if invoice["claim_id"] != payment["claim_id"]:
            errors.append(f"{payment_id}: invoice belongs to another claim")

        if payment["payment_amount"] <= 0:
            errors.append(f"{payment_id}: payment must be positive")

        if payment["payment_amount"] > claim["approved_amount"]:
            errors.append(f"{payment_id}: payment exceeds approved amount")

        if claim["status"] not in ("APPROVED", "PAID"):
            errors.append(f"{payment_id}: payment for unapproved claim")


    # 6. Validate relationship edges
    edges = records["relationship_edges"]

    edge_ids = [edge["edge_id"] for edge in edges]
    if len(edge_ids) != len(set(edge_ids)):
        errors.append("Duplicate primary key in relationship_edges")

    allowed_edge_types = {
        "SHARES_ADDRESS",
        "SHARES_CONTACT",
        "CLAIM_USES_PROVIDER",
        "CLAIM_LINKED_TO_INCIDENT",
        "CLAIMANT_HAS_POLICY",
    }

    all_ids = (
        claimant_ids
        | provider_ids
        | set(policy_by_id.keys())
        | set(incident_by_id.keys())
        | set(claim_by_id.keys())
        | set(invoice_by_id.keys())
        | {row["payment_id"] for row in records["payments"]}
    )

    seen_edges = set()

    for edge in edges:
        edge_id = edge["edge_id"]
        source_id = edge["source_id"]
        target_id = edge["target_id"]
        edge_type = edge["edge_type"]

        if edge_type not in allowed_edge_types:
            errors.append(f"{edge_id}: invalid relationship type")

        if source_id not in all_ids:
            errors.append(f"{edge_id}: source entity does not exist")

        if target_id not in all_ids:
            errors.append(f"{edge_id}: target entity does not exist")

        edge_key = (source_id, target_id, edge_type)
        if edge_key in seen_edges:
            errors.append(f"{edge_id}: duplicate relationship edge")
        seen_edges.add(edge_key)

        # Check that the source and target entity types match the edge type.
        if edge_type in ("SHARES_ADDRESS", "SHARES_CONTACT"):
            if source_id not in claimant_ids or target_id not in claimant_ids:
                errors.append(f"{edge_id}: claimant relationship has invalid endpoints")

        elif edge_type == "CLAIM_USES_PROVIDER":
            if source_id not in claim_by_id or target_id not in provider_ids:
                errors.append(f"{edge_id}: invalid claim-provider relationship")

        elif edge_type == "CLAIM_LINKED_TO_INCIDENT":
            if source_id not in claim_by_id or target_id not in incident_by_id:
                errors.append(f"{edge_id}: invalid claim-incident relationship")

        elif edge_type == "CLAIMANT_HAS_POLICY":
            if source_id not in claimant_ids or target_id not in policy_by_id:
                errors.append(f"{edge_id}: invalid claimant-policy relationship")


    return errors




def main() -> None:
    records = generate_master_records(GeneratorConfig())
    errors = validate_records(records)

    if errors:
        print(f"Validation failed: {len(errors)} issue(s)")
        for error in errors[:20]:
            print("-", error)
    else:
        print("Validation passed: no issues found")

    print("\nValidated record counts:")
    for entity, rows in records.items():
        print(f"{entity.capitalize()}: {len(rows)}")


if __name__ == "__main__":
    main()
