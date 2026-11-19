import networkx as nx

from quantum.engine import QuantumStatus, generate_candidates, solve_candidate_selection
from services.routing import CostWeights, evaluate_path


def graph_with_alternatives() -> nx.DiGraph:
    graph = nx.DiGraph()
    for index, name in enumerate("ABCDE"):
        graph.add_node(name, lat=30.70 + index * 0.01, lng=76.70 + index * 0.01)
    for start, end, distance in [
        ("A", "B", 1.0), ("B", "E", 1.0),
        ("A", "C", 1.2), ("C", "E", 1.2),
        ("A", "D", 1.4), ("D", "E", 1.4),
    ]:
        graph.add_edge(
            start,
            end,
            distance_km=distance,
            time_min=distance * 2,
            fuel_l=distance * 0.06,
            congestion=0.1,
            risk=0.05,
        )
    return graph


def test_candidate_generation_is_deterministic_and_includes_exact_optimum() -> None:
    graph = graph_with_alternatives()
    weights = CostWeights(distance=1, time=0, fuel=0, congestion=0, risk=0)

    first = generate_candidates(graph, "A", "E", weights, limit=3)
    second = generate_candidates(graph, "A", "E", weights, limit=3)

    assert first == second
    assert first[0] == ["A", "B", "E"]
    assert len({tuple(path) for path in first}) == 3


def test_single_candidate_skips_quantum_execution() -> None:
    graph = nx.DiGraph()
    graph.add_edge("A", "B", distance_km=1, time_min=2, fuel_l=0.1, congestion=0, risk=0)
    weights = CostWeights()
    candidates = [["A", "B"]]
    costs = [evaluate_path(graph, candidates[0], weights).objective_value]

    result = solve_candidate_selection(costs, layers=1, shots=64, maxiter=3, seed=9)

    assert result.status is QuantumStatus.NOT_REQUIRED
    assert result.selected_index == 0
    assert result.backend is None


def test_aer_qaoa_reports_measured_execution_provenance() -> None:
    result = solve_candidate_selection(
        [0.1, 0.6, 0.9], layers=1, shots=128, maxiter=8, seed=11
    )

    assert result.status is QuantumStatus.COMPLETED
    assert result.backend == "qiskit_aer_simulator"
    assert result.selected_index in {0, 1, 2}
    assert result.shots == 128
    assert result.circuit_depth is not None and result.circuit_depth > 0
    assert result.execution_time_ms > 0
    assert result.counts
