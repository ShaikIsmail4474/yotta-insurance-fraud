
import pandas as pd
import pytest
import networkx as nx

from src.network_analysis import (
    find_connection_paths,
    find_connected_entities,
    load_relationship_graph,
    summarize_connection_path,
)


def test_finds_indirect_connection():
    graph = nx.Graph()
    graph.add_edge(
        "CLT-A", "CLT-B",
        edge_type="SHARES_CONTACT",
        edge_id="E1",
        effective_date="2026-01-01",
        strength="review",
    )
    graph.add_edge(
        "CLT-B", "PRV-X",
        edge_type="CLAIM_USES_PROVIDER",
        edge_id="E2",
        effective_date="2026-01-01",
        strength="context",
    )
    graph.add_edge(
        "PRV-X", "CLT-C",
        edge_type="SHARES_ADDRESS",
        edge_id="E3",
        effective_date="2026-01-01",
        strength="weak",
    )

    paths = find_connection_paths(
        graph, "CLT-A", "CLT-C", max_hops=3
    )

    assert len(paths) == 1
    assert paths[0]["hops"] == 3
    assert paths[0]["nodes"] == ["CLT-A", "CLT-B", "PRV-X", "CLT-C"]
    assert len(paths[0]["relationships"]) == 3


def test_returns_no_path_for_missing_entity():
    graph = nx.Graph()
    graph.add_edge(
        "CLT-A", "CLT-B",
        edge_type="SHARES_CONTACT",
        edge_id="E1",
        effective_date="2026-01-01",
        strength="review",
    )

    assert find_connection_paths(graph, "CLT-A", "UNKNOWN") == []


def test_respects_max_hops():
    graph = nx.path_graph(["A", "B", "C", "D"])
    paths = find_connection_paths(graph, "A", "D", max_hops=2)
    assert paths == []


def test_shared_address_is_described_as_weak_evidence():
    graph = nx.Graph()
    graph.add_edge(
        "CLT-A", "CLT-B",
        edge_type="SHARES_ADDRESS",
        edge_id="E1",
        effective_date="2026-01-01",
        strength="weak",
    )

    path = find_connection_paths(graph, "CLT-A", "CLT-B")[0]
    explanation = summarize_connection_path(path)

    assert "SHARES_ADDRESS" in explanation
    assert "not proof of fraud" in explanation
    assert "1 shared-address edge(s)" in explanation


def test_loader_does_not_use_ground_truth_as_detection_input(tmp_path):
    edges_file = tmp_path / "edges.csv"
    pd.DataFrame([
        {
            "edge_id": "E1",
            "source_id": "CLT-A",
            "target_id": "CLT-B",
            "edge_type": "SHARES_CONTACT",
            "effective_date": "2026-01-01",
            "is_planted_suspicious": True,
        },
    ]).to_csv(edges_file, index=False)

    graph = load_relationship_graph(edges_file)

    assert graph.has_edge("CLT-A", "CLT-B")
    assert "is_planted_suspicious" not in graph["CLT-A"]["CLT-B"]


def test_connected_entities_finds_reachable_nodes():
    graph = nx.Graph()
    graph.add_edge(
        "CLT-A", "CLT-B",
        edge_type="SHARES_CONTACT",
        edge_id="E1",
        effective_date="2026-01-01",
        strength="review",
    )
    graph.add_edge(
        "CLT-B", "CLT-C",
        edge_type="SHARES_ADDRESS",
        edge_id="E2",
        effective_date="2026-01-01",
        strength="weak",
    )

    results = find_connected_entities(graph, "CLT-A", max_hops=2)
    found = {item["entity_id"]: item["hops"] for item in results}

    assert found["CLT-B"] == 1
    assert found["CLT-C"] == 2


def test_rejects_invalid_hop_limits():
    graph = nx.Graph()

    with pytest.raises(ValueError):
        find_connection_paths(graph, "A", "B", max_hops=0)

    with pytest.raises(ValueError):
        find_connected_entities(graph, "A", max_hops=0)

def test_real_dataset_has_indirect_claimant_path():
    from src.network_analysis import load_relationship_graph

    graph = load_relationship_graph()

    paths = find_connection_paths(
        graph,
        "CLT-000001",
        "CLT-000003",
        max_hops=4,
    )

    assert paths, "Expected a connection between the two claimants."
    assert paths[0]["hops"] > 1
    assert paths[0]["nodes"][0] == "CLT-000001"
    assert paths[0]["nodes"][-1] == "CLT-000003"
    assert all(
        "edge_type" in relationship
        for relationship in paths[0]["relationships"]
    )
