"""Shared routing objective and classical solvers.

Every algorithm in this module consumes the same immutable edge objective.  That
is the basis for a meaningful algorithm comparison: different implementations
may have different runtimes, but an optimal solver must report the same minimum
objective value.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
import tracemalloc
from typing import Callable

import networkx as nx


FUEL_PRICE_INR_PER_LITRE = 96.0


@dataclass(frozen=True, init=False)
class CostWeights:
    distance: float
    time: float
    fuel: float
    congestion: float
    risk: float

    def __init__(
        self,
        distance: float = 0.20,
        time: float = 0.45,
        fuel: float = 0.15,
        congestion: float = 0.15,
        risk: float = 0.05,
    ) -> None:
        values = (distance, time, fuel, congestion, risk)
        if any(value < 0 or not math.isfinite(value) for value in values):
            raise ValueError("cost weights must be finite and non-negative")
        total = sum(values)
        if total <= 0:
            raise ValueError("at least one cost weight must be greater than zero")
        for name, value in zip(
            ("distance", "time", "fuel", "congestion", "risk"), values
        ):
            object.__setattr__(self, name, value / total)


@dataclass(frozen=True)
class PathMetrics:
    distance_km: float
    time_min: float
    fuel_l: float
    fuel_cost_inr: float
    congestion_exposure: float
    risk_exposure: float
    objective_value: float


@dataclass(frozen=True)
class AlgorithmResult:
    algorithm: str
    feasible: bool
    path: list[str]
    metrics: PathMetrics | None
    objective_value: float
    execution_time_ms: float
    memory_peak_kb: float
    error: str | None = None


def edge_objective(data: dict, weights: CostWeights) -> float:
    """Return a dimensionless, non-negative cost for one directed edge."""
    distance = float(data.get("distance_km", data.get("distance", 0.0)))
    duration = float(data.get("time_min", data.get("time", 0.0)))
    fuel = float(data.get("fuel_l", 0.0))
    congestion = float(data.get("congestion", 0.0))
    risk = float(data.get("risk", 0.0))
    if min(distance, duration, fuel, congestion, risk) < 0:
        raise ValueError("edge metrics must be non-negative")
    return (
        weights.distance * distance / 20.0
        + weights.time * duration / 30.0
        + weights.fuel * fuel / 2.0
        + weights.congestion * congestion
        + weights.risk * risk
    )


def evaluate_path(
    graph: nx.DiGraph, path: list[str], weights: CostWeights
) -> PathMetrics:
    if not path:
        raise ValueError("path cannot be empty")
    edges = [graph[path[index]][path[index + 1]] for index in range(len(path) - 1)]
    distance = sum(float(edge.get("distance_km", edge.get("distance", 0))) for edge in edges)
    duration = sum(float(edge.get("time_min", edge.get("time", 0))) for edge in edges)
    fuel = sum(float(edge.get("fuel_l", 0)) for edge in edges)
    congestion = sum(float(edge.get("congestion", 0)) for edge in edges)
    risk = sum(float(edge.get("risk", 0)) for edge in edges)
    objective = sum(edge_objective(edge, weights) for edge in edges)
    return PathMetrics(
        distance_km=round(distance, 4),
        time_min=round(duration, 4),
        fuel_l=round(fuel, 5),
        fuel_cost_inr=round(fuel * FUEL_PRICE_INR_PER_LITRE, 2),
        congestion_exposure=round(congestion, 4),
        risk_exposure=round(risk, 4),
        objective_value=objective,
    )


def _run_solver(
    name: str,
    graph: nx.DiGraph,
    source: str,
    destination: str,
    weights: CostWeights,
    solver: Callable[[Callable[[str, str, dict], float]], list[str]],
) -> AlgorithmResult:
    weight = lambda _u, _v, data: edge_objective(data, weights)
    tracemalloc.start()
    started = time.perf_counter()
    try:
        path = solver(weight)
        metrics = evaluate_path(graph, path, weights)
        feasible = True
        error = None
        objective = metrics.objective_value
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        path = []
        metrics = None
        feasible = False
        error = "no_route"
        objective = math.inf
    elapsed = (time.perf_counter() - started) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return AlgorithmResult(
        algorithm=name,
        feasible=feasible,
        path=path,
        metrics=metrics,
        objective_value=objective,
        execution_time_ms=round(elapsed, 4),
        memory_peak_kb=round(peak / 1024, 3),
        error=error,
    )


def solve_all_classical(
    graph: nx.DiGraph,
    source: str,
    destination: str,
    weights: CostWeights,
) -> dict[str, AlgorithmResult]:
    """Run all classical solvers against one graph and one edge objective."""

    def dijkstra(weight: Callable[[str, str, dict], float]) -> list[str]:
        return nx.dijkstra_path(graph, source, destination, weight=weight)

    def astar(weight: Callable[[str, str, dict], float]) -> list[str]:
        # Zero is always admissible.  A stronger lower bound is used by the city
        # graph service after it verifies its distance/cost calibration.
        return nx.astar_path(
            graph,
            source,
            destination,
            heuristic=lambda _u, _v: 0.0,
            weight=weight,
        )

    def bellman_ford(weight: Callable[[str, str, dict], float]) -> list[str]:
        return nx.bellman_ford_path(graph, source, destination, weight=weight)

    return {
        "dijkstra": _run_solver("Dijkstra", graph, source, destination, weights, dijkstra),
        "astar": _run_solver("A*", graph, source, destination, weights, astar),
        "bellman_ford": _run_solver(
            "Bellman-Ford", graph, source, destination, weights, bellman_ford
        ),
    }
