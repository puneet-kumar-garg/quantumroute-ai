import math

import networkx as nx
import pytest

from services.routing import CostWeights, evaluate_path, solve_all_classical


def demo_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_node("A", lat=30.70, lng=76.70)
    graph.add_node("B", lat=30.71, lng=76.71)
    graph.add_node("C", lat=30.72, lng=76.72)
    graph.add_node("D", lat=30.73, lng=76.73)
    graph.add_edge("A", "B", distance_km=2.0, time_min=4.0, fuel_l=0.15, congestion=0.2, risk=0.1)
    graph.add_edge("B", "D", distance_km=2.0, time_min=4.0, fuel_l=0.15, congestion=0.2, risk=0.1)
    graph.add_edge("A", "C", distance_km=3.0, time_min=3.0, fuel_l=0.30, congestion=0.6, risk=0.2)
    graph.add_edge("C", "D", distance_km=3.0, time_min=3.0, fuel_l=0.30, congestion=0.6, risk=0.2)
    return graph


def test_cost_weights_are_normalized_and_reject_all_zero() -> None:
    weights = CostWeights(distance=2, time=1, fuel=1, congestion=0, risk=0)
    assert weights.distance == pytest.approx(0.5)
    assert weights.time == pytest.approx(0.25)
    assert weights.fuel == pytest.approx(0.25)

    with pytest.raises(ValueError, match="at least one"):
        CostWeights(distance=0, time=0, fuel=0, congestion=0, risk=0)


def test_all_classical_algorithms_use_the_same_objective() -> None:
    graph = demo_graph()
    weights = CostWeights(distance=0.2, time=0.6, fuel=0.1, congestion=0.1, risk=0)

    results = solve_all_classical(graph, "A", "D", weights)

    assert set(results) == {"dijkstra", "astar", "bellman_ford"}
    assert all(result.feasible for result in results.values())
    objective_values = [result.objective_value for result in results.values()]
    assert max(objective_values) - min(objective_values) < 1e-9
    assert all(result.path == ["A", "B", "D"] for result in results.values())


def test_disconnected_route_is_explicitly_infeasible() -> None:
    graph = demo_graph()
    graph.add_node("X", lat=30.8, lng=76.8)

    results = solve_all_classical(graph, "A", "X", CostWeights())

    assert all(not result.feasible for result in results.values())
    assert all(result.path == [] for result in results.values())
    assert all(math.isinf(result.objective_value) for result in results.values())


def test_path_metrics_are_calculated_once_from_edges() -> None:
    metrics = evaluate_path(demo_graph(), ["A", "B", "D"], CostWeights())

    assert metrics.distance_km == pytest.approx(4.0)
    assert metrics.time_min == pytest.approx(8.0)
    assert metrics.fuel_l == pytest.approx(0.30)
    assert metrics.fuel_cost_inr > 0
