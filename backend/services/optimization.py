"""Orchestration for one reproducible hybrid optimization run."""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from quantum.engine import (
    QuantumSelectionResult,
    generate_candidates,
    solve_candidate_selection,
)
from services.routing import (
    AlgorithmResult,
    CostWeights,
    PathMetrics,
    evaluate_path,
    solve_all_classical,
)


@dataclass(frozen=True)
class OptimizationSettings:
    candidate_limit: int = 8
    layers: int = 2
    shots: int = 1_024
    maxiter: int = 80
    seed: int = 42


@dataclass(frozen=True)
class RouteAlternative:
    rank: int
    path: list[str]
    metrics: PathMetrics
    objective_delta: float


@dataclass(frozen=True)
class OptimizationOutcome:
    classical: dict[str, AlgorithmResult]
    candidates: list[list[str]]
    candidate_costs: list[float]
    alternatives: list[RouteAlternative]
    search_report: dict[str, object]
    quantum: QuantumSelectionResult
    recommended_path: list[str]
    recommended_objective: float
    recommendation_reason: str
    network_provenance: str


def optimize_graph(
    graph: nx.DiGraph,
    source: str,
    destination: str,
    weights: CostWeights,
    settings: OptimizationSettings | None = None,
) -> OptimizationOutcome:
    settings = settings or OptimizationSettings()
    classical = solve_all_classical(graph, source, destination, weights)
    exact = classical["dijkstra"]
    if not exact.feasible:
        quantum = solve_candidate_selection([], layers=settings.layers)
        return OptimizationOutcome(
            classical=classical,
            candidates=[],
            candidate_costs=[],
            alternatives=[],
            search_report={
                "optimal_route_guarantee": "exact_non_negative_shortest_path",
                "alternative_search": "loopless_k_shortest_paths",
                "exhaustive_path_enumeration": False,
                "alternatives_evaluated": 0,
                "alternative_limit": settings.candidate_limit,
                "reachable_nodes": 0,
                "graph_nodes": graph.number_of_nodes(),
                "graph_edges": graph.number_of_edges(),
            },
            quantum=quantum,
            recommended_path=[],
            recommended_objective=float("inf"),
            recommendation_reason="No feasible route satisfies the active constraints.",
            network_provenance="curated_scenario_graph",
        )
    candidates = generate_candidates(
        graph, source, destination, weights, limit=settings.candidate_limit
    )
    costs = [evaluate_path(graph, path, weights).objective_value for path in candidates]
    alternatives = [
        RouteAlternative(
            rank=index + 1,
            path=path,
            metrics=evaluate_path(graph, path, weights),
            objective_delta=max(0.0, costs[index] - exact.objective_value),
        )
        for index, path in enumerate(candidates)
    ]
    quantum = solve_candidate_selection(
        costs,
        layers=settings.layers,
        shots=settings.shots,
        maxiter=settings.maxiter,
        seed=settings.seed,
    )
    return OptimizationOutcome(
        classical=classical,
        candidates=candidates,
        candidate_costs=costs,
        alternatives=alternatives,
        search_report={
            "optimal_route_guarantee": "exact_non_negative_shortest_path",
            "alternative_search": "loopless_k_shortest_paths",
            "exhaustive_path_enumeration": False,
            "alternatives_evaluated": len(alternatives),
            "alternative_limit": settings.candidate_limit,
            "reachable_nodes": len(nx.descendants(graph, source)) + 1,
            "graph_nodes": graph.number_of_nodes(),
            "graph_edges": graph.number_of_edges(),
            "note": (
                "Dijkstra, A*, and Bellman-Ford search the complete reachable graph for the exact optimum. "
                "The displayed/QAOA alternatives are the first loopless K-shortest paths, not every simple path."
            ),
        },
        quantum=quantum,
        recommended_path=exact.path,
        recommended_objective=exact.objective_value,
        recommendation_reason=(
            "Lowest verified weighted objective across the complete reachable graph; "
            "QAOA is reported separately as an experimental selector."
        ),
        network_provenance="curated_scenario_graph",
    )
