
"""Connect network-analysis evidence to investigation case management."""

from pathlib import Path

from src.case_management import create_case
from src.network_analysis import find_connected_entities, load_relationship_graph

DEFAULT_DB = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "insurance_fraud.db"
)


def build_network_evidence(
    claim_id,
    max_hops=3,
    edges_path=None,
    claims_path=None,
):
    """Build an explainable network summary for a claim."""
    if not isinstance(claim_id, str) or not claim_id.strip():
        raise ValueError("claim_id is required.")

    if not isinstance(max_hops, int) or isinstance(max_hops, bool) or max_hops < 1:
        raise ValueError("max_hops must be an integer of at least 1.")

    graph_kwargs = {}
    if edges_path is not None:
        graph_kwargs["edges_path"] = edges_path
    if claims_path is not None:
        graph_kwargs["claims_path"] = claims_path

    graph = load_relationship_graph(**graph_kwargs)

    if claim_id not in graph:
        raise ValueError(
            f"Claim {claim_id} was not found in the relationship graph."
        )

    connections = find_connected_entities(
        graph,
        claim_id,
        max_hops=max_hops,
    )

    relationship_types = sorted({
        relationship["edge_type"]
        for item in connections
        for relationship in item["relationships"]
    })

    weak_address_edges = sum(
        relationship["edge_type"] == "SHARES_ADDRESS"
        for item in connections
        for relationship in item["relationships"]
    )

    review_contact_edges = sum(
        relationship["edge_type"] == "SHARES_CONTACT"
        for item in connections
        for relationship in item["relationships"]
    )

    lines = [
        f"Network review for claim {claim_id}.",
        f"Search depth: up to {max_hops} hops.",
        f"Reachable entities returned: {len(connections)}.",
        "Relationship types encountered: "
        + (", ".join(relationship_types) if relationship_types else "none"),
        f"Shared-address edges in returned paths: {weak_address_edges}.",
        f"Shared-contact edges in returned paths: {review_contact_edges}.",
        "These connections are investigative leads, not proof of fraud.",
    ]

    return {
        "claim_id": claim_id,
        "max_hops": max_hops,
        "connected_entity_count": len(connections),
        "relationship_types": relationship_types,
        "shared_address_edge_count": weak_address_edges,
        "shared_contact_edge_count": review_contact_edges,
        "connections": connections,
        "summary": "\n".join(lines),
    }


def open_network_investigation(
    claim_id,
    actor,
    assigned_to=None,
    max_hops=3,
    db_path=DEFAULT_DB,
    edges_path=None,
    claims_path=None,
):
    """Create an Open case containing a network-evidence summary."""
    evidence = build_network_evidence(
        claim_id=claim_id,
        max_hops=max_hops,
        edges_path=edges_path,
        claims_path=claims_path,
    )

    case_id = create_case(
        claim_id=claim_id,
        reason=evidence["summary"],
        actor=actor,
        assigned_to=assigned_to,
        db_path=db_path,
    )

    return {
        "case_id": case_id,
        "claim_id": claim_id,
        "status": "Open",
        "reviewer_decision": "Pending",
        "evidence": evidence,
    }
