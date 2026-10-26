
"""Generate reproducible synthetic insurance records."""

from dataclasses import dataclass
from datetime import date
import random


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int = 42
    claim_count: int = 5_000
    claimant_count: int = 2_000
    provider_count: int = 500
    incident_count: int = 3_000
    relationship_edge_count: int = 8_000


def make_id(prefix: str, number: int, width: int = 6) -> str:
    return f"{prefix}{number:0{width}d}"


def generate_master_records(config: GeneratorConfig) -> dict:
    rng = random.Random(config.seed)

    # 1. Claimants
    claimants = []
    for n in range(1, config.claimant_count + 1):
        claimants.append({
            "claimant_id": make_id("CLT-", n),
            "full_name": f"Claimant {n:06d}",
            "email": f"claimant{n:06d}@example.test",
            "phone": f"900{n:07d}",
            "address_id": make_id("ADDR-", rng.randint(1, 1800)),
        })

    # 2. Providers
    providers = []
    for n in range(1, config.provider_count + 1):
        providers.append({
            "provider_id": make_id("PRV-", n),
            "provider_name": f"Provider {n:06d}",
            "provider_type": rng.choice([
                "HOSPITAL", "CLINIC", "REPAIR_SHOP", "PHARMACY"
            ]),
            "tax_id": f"SYNTH-TAX-{n:06d}",
            "address_id": make_id("ADDR-", rng.randint(1, 1200)),
        })

    # 3. Policies: one policy per claimant
    policies = []
    for n in range(1, config.claimant_count + 1):
        start_year = rng.choice([2024, 2025, 2026])
        policies.append({
            "policy_id": make_id("POL-", n),
            "claimant_id": make_id("CLT-", n),
            "policy_type": rng.choice(["HEALTH", "AUTO", "PROPERTY"]),
            "start_date": f"{start_year}-01-01",
            "end_date": f"{start_year + 1}-12-31",
            "coverage_limit": round(rng.uniform(5000, 100000), 2),
            "status": "ACTIVE",
        })

    # 4. Incidents
    incidents = []
    for n in range(1, config.incident_count + 1):
        year = rng.choice([2024, 2025, 2026])
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)

        incidents.append({
            "incident_id": f"INC-{year}-{n:06d}",
            "incident_date": f"{year}-{month:02d}-{day:02d}",
            "incident_type": rng.choice([
                "ILLNESS", "ACCIDENT", "PROPERTY_DAMAGE", "THEFT"
            ]),
            "location": f"Synthetic Location {rng.randint(1, 300):03d}",
            "description": f"Synthetic incident report {n:06d}",
        })

    incidents_by_year = {}
    for incident in incidents:
        year = date.fromisoformat(incident["incident_date"]).year
        incidents_by_year.setdefault(year, []).append(incident)

    # 5. Claims
    claims = []
    for n in range(1, config.claim_count + 1):
        claimant_number = rng.randint(1, config.claimant_count)
        policy = policies[claimant_number - 1]

        start = date.fromisoformat(policy["start_date"])
        end = date.fromisoformat(policy["end_date"])

        eligible_incidents = [
            incident
            for year in range(start.year, end.year + 1)
            for incident in incidents_by_year.get(year, [])
            if start <= date.fromisoformat(
                incident["incident_date"]
            ) <= end
        ]

        if not eligible_incidents:
            raise ValueError(
                f"No eligible incident found for {policy['policy_id']}"
            )

        incident = rng.choice(eligible_incidents)
        claimed_amount = round(rng.uniform(500, 25000), 2)
        approved_amount = round(
            min(claimed_amount, policy["coverage_limit"])
            * rng.uniform(0.50, 1.00),
            2,
        )

        claims.append({
            "claim_id": f"CLM-2026-{n:06d}",
            "claimant_id": policy["claimant_id"],
            "policy_id": policy["policy_id"],
            "incident_id": incident["incident_id"],
            "provider_id": rng.choice(providers)["provider_id"],
            "claim_date": incident["incident_date"],
            "claimed_amount": claimed_amount,
            "approved_amount": approved_amount,
            "status": rng.choice([
                "SUBMITTED", "UNDER_REVIEW", "APPROVED",
                "REJECTED", "PAID"
            ]),
        })

    # 6. Plant a controlled synthetic suspicious pattern.
    # Ten claimants share a contact number and their claims use one provider.
    suspicious_claimant_ids = {
        make_id("CLT-", n) for n in range(1, 11)
    }
    suspicious_provider_id = providers[0]["provider_id"]

    for claimant in claimants:
        if claimant["claimant_id"] in suspicious_claimant_ids:
            claimant["phone"] = "900SUSPICIOUS"

    suspicious_claims = []
    for claim in claims:
        if claim["claimant_id"] in suspicious_claimant_ids:
            claim["provider_id"] = suspicious_provider_id
            suspicious_claims.append(claim)

    # 7. Invoices: one per claim, with consistent provider IDs.
    invoice_counter_by_provider = {}
    invoices = []

    for claim in claims:
        provider_id = claim["provider_id"]
        invoice_counter_by_provider[provider_id] = (
            invoice_counter_by_provider.get(provider_id, 0) + 1
        )

        invoices.append({
            "invoice_id": (
                f"INV-{provider_id}-"
                f"{invoice_counter_by_provider[provider_id]:06d}"
            ),
            "claim_id": claim["claim_id"],
            "provider_id": provider_id,
            "invoice_amount": claim["claimed_amount"],
            "invoice_date": claim["claim_date"],
            "status": (
                "REJECTED" if claim["status"] == "REJECTED"
                else "SUBMITTED"
            ),
        })

    # 8. Payments: approved or paid claims only.
    payments = []
    invoice_by_claim = {
        invoice["claim_id"]: invoice for invoice in invoices
    }

    for claim in claims:
        if claim["status"] not in ("APPROVED", "PAID"):
            continue

        invoice = invoice_by_claim[claim["claim_id"]]
        payment_amount = round(
            claim["approved_amount"] * rng.uniform(0.50, 1.00), 2
        )

        payments.append({
            "payment_id": f"PAY-2026-{len(payments) + 1:06d}",
            "claim_id": claim["claim_id"],
            "invoice_id": invoice["invoice_id"],
            "payment_amount": payment_amount,
            "payment_date": claim["claim_date"],
            "status": (
                "COMPLETED" if claim["status"] == "PAID"
                else "PENDING"
            ),
        })

    # 9. Build relationship edges within the configured edge limit.
    # Preserve all claim-provider and claimant-policy relationships.
    required_edges = set()

    for claim in claims:
        required_edges.add((
            claim["claim_id"],
            claim["provider_id"],
            "CLAIM_USES_PROVIDER",
        ))

    for policy in policies:
        required_edges.add((
            policy["claimant_id"],
            policy["policy_id"],
            "CLAIMANT_HAS_POLICY",
        ))

    # Preserve the planted shared-contact network.
    suspicious_ids_sorted = sorted(suspicious_claimant_ids)
    for i in range(len(suspicious_ids_sorted) - 1):
        required_edges.add((
            suspicious_ids_sorted[i],
            suspicious_ids_sorted[i + 1],
            "SHARES_CONTACT",
        ))

    if len(required_edges) > config.relationship_edge_count:
        raise ValueError(
            "Required provider, policy, and suspicious-contact edges "
            "exceed relationship_edge_count."
        )

    # Build optional incident and address relationships separately.
    incident_edges = {
        (
            claim["claim_id"],
            claim["incident_id"],
            "CLAIM_LINKED_TO_INCIDENT",
        )
        for claim in claims
    }

    address_edges = set()
    claimants_by_address = {}
    for claimant in claimants:
        claimants_by_address.setdefault(
            claimant["address_id"], []
        ).append(claimant)

    for group in claimants_by_address.values():
        for i in range(len(group) - 1):
            address_edges.add((
                group[i]["claimant_id"],
                group[i + 1]["claimant_id"],
                "SHARES_ADDRESS",
            ))

    # Keep suspicious claims' incident links first, where available.
    suspicious_claim_ids = {
        claim["claim_id"] for claim in suspicious_claims
    }
    preferred_incident_edges = sorted(
        edge for edge in incident_edges
        if edge[0] in suspicious_claim_ids
    )
    other_incident_edges = sorted(
        incident_edges - set(preferred_incident_edges)
    )
    rng.shuffle(other_incident_edges)

    selected_edges = list(sorted(required_edges))
    remaining_slots = config.relationship_edge_count - len(selected_edges)

    # Add some genuine shared-address links so address sharing is not
    # automatically treated as suspicious.
    optional_address_edges = sorted(address_edges)
    rng.shuffle(optional_address_edges)

    address_count = min(500, remaining_slots, len(optional_address_edges))
    selected_edges.extend(optional_address_edges[:address_count])
    remaining_slots -= address_count

    # Fill the rest with claim-incident relationships.
    incident_pool = preferred_incident_edges + other_incident_edges
    incident_count = min(remaining_slots, len(incident_pool))
    selected_edges.extend(incident_pool[:incident_count])
    remaining_slots -= incident_count

    # If a custom configuration still needs more edges, add other unique
    # valid candidates. Default configuration should not need this section.
    extra_candidates = sorted(
        (incident_edges | address_edges) - set(selected_edges)
    )
    rng.shuffle(extra_candidates)

    if remaining_slots > 0:
        selected_edges.extend(extra_candidates[:remaining_slots])
        remaining_slots = config.relationship_edge_count - len(selected_edges)

    if remaining_slots != 0:
        raise ValueError(
            f"Could not create {config.relationship_edge_count} unique edges."
        )

    relationship_edges = []
    for n, (source_id, target_id, edge_type) in enumerate(
        selected_edges, start=1
    ):
        planted = (
            edge_type == "SHARES_CONTACT"
            and source_id in suspicious_claimant_ids
            and target_id in suspicious_claimant_ids
        )

        relationship_edges.append({
            "edge_id": f"EDGE-{n:06d}",
            "source_id": source_id,
            "target_id": target_id,
            "edge_type": edge_type,
            "effective_date": "2026-01-01",
            "is_planted_suspicious": planted,
        })

    edge_keys = {
        (edge["source_id"], edge["target_id"], edge["edge_type"])
        for edge in relationship_edges
    }

    assert len(relationship_edges) == config.relationship_edge_count
    assert len(edge_keys) == len(relationship_edges)

    # 10. Keep ground-truth labels separate from model input records.
    ground_truth = []

    for claim in claims:
        planted = claim["claimant_id"] in suspicious_claimant_ids
        ground_truth.append({
            "record_type": "CLAIM",
            "record_id": claim["claim_id"],
            "is_planted_suspicious": planted,
            "reason": (
                "PLANTED_SHARED_CONTACT_PROVIDER_PATTERN"
                if planted else "SYNTHETIC_BASELINE"
            ),
        })

    for edge in relationship_edges:
        if edge["is_planted_suspicious"]:
            ground_truth.append({
                "record_type": "RELATIONSHIP_EDGE",
                "record_id": edge["edge_id"],
                "is_planted_suspicious": True,
                "reason": "PLANTED_SHARED_CONTACT_PATTERN",
            })

    return {
        "claimants": claimants,
        "providers": providers,
        "policies": policies,
        "incidents": incidents,
        "claims": claims,
        "invoices": invoices,
        "payments": payments,
        "relationship_edges": relationship_edges,
        "ground_truth": ground_truth,
    }


def main() -> None:
    records = generate_master_records(GeneratorConfig())

    print("Synthetic record generation successful")
    for entity, rows in records.items():
        print(f"{entity.capitalize()} generated: {len(rows)}")

    print("\nSample claim:", records["claims"][0])
    print("Sample invoice:", records["invoices"][0])
    print("Sample relationship edge:", records["relationship_edges"][0])

    print(
        "Unique relationship edges:",
        len({
            (edge["source_id"], edge["target_id"], edge["edge_type"])
            for edge in records["relationship_edges"]
        }),
    )

    print(
        "Planted suspicious claims:",
        sum(
            row["is_planted_suspicious"]
            for row in records["ground_truth"]
            if row["record_type"] == "CLAIM"
        ),
    )
    print("Ground-truth labels:", len(records["ground_truth"]))


if __name__ == "__main__":
    main()
