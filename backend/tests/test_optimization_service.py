import networkx as nx

from services.optimization import OptimizationSettings, optimize_graph
from services.routing import CostWeights


def test_recommendation_uses_verified_lowest_objective_independent_of_qaoa() -> None:
    graph = nx.DiGraph()
    graph.add_node("A", lat=30.7, lng=76.7)
    graph.add_node("B", lat=30.71, lng=76.71)
    graph.add_node("C", lat=30.72, lng=76.72)
    graph.add_edge("A", "B", distance_km=1, time_min=2, fuel_l=.05, congestion=.1, risk=.1)
    graph.add_edge("B", "C", distance_km=1, time_min=2, fuel_l=.05, congestion=.1, risk=.1)
    graph.add_edge("A", "C", distance_km=4, time_min=5, fuel_l=.25, congestion=.3, risk=.1)

    result = optimize_graph(
        graph,
        "A",
        "C",
        CostWeights(distance=1, time=0, fuel=0, congestion=0, risk=0),
        OptimizationSettings(candidate_limit=3, layers=1, shots=64, maxiter=4, seed=2),
    )

    assert result.recommended_path == ["A", "B", "C"]
    assert result.recommendation_reason.startswith("Lowest verified")
    assert result.network_provenance == "curated_scenario_graph"
    assert result.classical["dijkstra"].objective_value == result.recommended_objective
    assert result.quantum.status.value in {"completed", "not_required", "failed"}
    assert [alternative.rank for alternative in result.alternatives] == [1, 2]
    assert result.alternatives[0].path == result.recommended_path
    assert result.search_report["optimal_route_guarantee"] == "exact_non_negative_shortest_path"
    assert result.search_report["alternative_search"] == "loopless_k_shortest_paths"
    assert result.search_report["exhaustive_path_enumeration"] is False
