
import pandas as pd

from src.investigation_report import count_shared_contact_edges


def test_shared_contact_edges_count_both_endpoints():
    edges = pd.DataFrame(
        [
            {
                "source_id": "CLT-000001",
                "target_id": "CLT-000002",
                "edge_type": "SHARES_CONTACT",
            },
            {
                "source_id": "CLT-000003",
                "target_id": "CLT-000001",
                "edge_type": "SHARES_CONTACT",
            },
            {
                "source_id": "CLT-000001",
                "target_id": "CLT-000004",
                "edge_type": "SHARES_ADDRESS",
            },
        ]
    )

    counts = count_shared_contact_edges(edges)

    assert counts["CLT-000001"] == 2
    assert counts["CLT-000002"] == 1
    assert counts["CLT-000003"] == 1
    assert "CLT-000004" not in counts.index


def test_shared_contact_edges_handles_empty_input():
    edges = pd.DataFrame(
        columns=["source_id", "target_id", "edge_type"]
    )

    counts = count_shared_contact_edges(edges)

    assert counts.empty
