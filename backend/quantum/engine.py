"""QAOA execution for bounded candidate-route selection.

The quantum problem has one binary variable per already-feasible route.  QAOA
therefore compares feasible alternatives; it does not replace graph traversal
and it cannot improve on an exact classical minimum included in the set.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import time
from typing import Sequence

import networkx as nx

from quantum.qubo import build_candidate_qubo, decode_samples
from services.routing import CostWeights, edge_objective, evaluate_path


class QuantumStatus(str, Enum):
    COMPLETED = "completed"
    NOT_REQUIRED = "not_required"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True)
class QuantumSelectionResult:
    status: QuantumStatus
    selected_index: int | None
    backend: str | None
    execution_time_ms: float
    shots: int | None
    layers: int
    optimizer_evaluations: int | None
    circuit_depth: int | None
    num_qubits: int
    feasible_probability: float | None
    counts: dict[str, int]
    objective_value: float | None
    error: str | None = None


def generate_candidates(
    graph: nx.DiGraph,
    source: str,
    destination: str,
    weights: CostWeights,
    limit: int = 8,
) -> list[list[str]]:
    if limit < 1 or limit > 8:
        raise ValueError("candidate limit must be between 1 and 8")
    weight = lambda _u, _v, data: edge_objective(data, weights)
    try:
        generator = nx.shortest_simple_paths(graph, source, destination, weight=weight)
        candidates: list[list[str]] = []
        seen: set[tuple[str, ...]] = set()
        for path in generator:
            key = tuple(path)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(path)
            if len(candidates) == limit:
                break
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []
    return sorted(
        candidates,
        key=lambda path: (evaluate_path(graph, path, weights).objective_value, tuple(path)),
    )


def _quasi_to_counts(distribution: object, qubits: int, shots: int) -> dict[str, int]:
    binary = distribution.binary_probabilities(num_bits=qubits)
    counts = {bits: int(round(probability * shots)) for bits, probability in binary.items()}
    difference = shots - sum(counts.values())
    if counts and difference:
        most_likely = max(counts, key=counts.get)
        counts[most_likely] += difference
    return {bits: count for bits, count in counts.items() if count > 0}


def solve_candidate_selection(
    costs: Sequence[float],
    *,
    layers: int = 2,
    shots: int = 1_024,
    maxiter: int = 80,
    seed: int = 42,
) -> QuantumSelectionResult:
    if not costs:
        return QuantumSelectionResult(
            status=QuantumStatus.FAILED,
            selected_index=None,
            backend=None,
            execution_time_ms=0,
            shots=None,
            layers=layers,
            optimizer_evaluations=None,
            circuit_depth=None,
            num_qubits=0,
            feasible_probability=None,
            counts={},
            objective_value=None,
            error="no_candidates",
        )
    if len(costs) == 1:
        return QuantumSelectionResult(
            status=QuantumStatus.NOT_REQUIRED,
            selected_index=0,
            backend=None,
            execution_time_ms=0,
            shots=None,
            layers=layers,
            optimizer_evaluations=0,
            circuit_depth=None,
            num_qubits=1,
            feasible_probability=1.0,
            counts={},
            objective_value=float(costs[0]),
        )
    if len(costs) > 8:
        raise ValueError("QAOA candidate selection supports at most 8 routes")
    if not 1 <= layers <= 5:
        raise ValueError("layers must be between 1 and 5")
    if shots < 32:
        raise ValueError("shots must be at least 32")

    started = time.perf_counter()
    try:
        from qiskit import transpile
        from qiskit.circuit.library import QAOAAnsatz
        from qiskit_aer import AerSimulator
        from qiskit_aer.primitives import Sampler as AerSampler
        from qiskit_algorithms import QAOA
        from qiskit_algorithms.optimizers import COBYLA
        from qiskit_optimization import QuadraticProgram
        from qiskit_optimization.algorithms import MinimumEigenOptimizer
    except ImportError as exc:
        return QuantumSelectionResult(
            status=QuantumStatus.UNAVAILABLE,
            selected_index=None,
            backend=None,
            execution_time_ms=round((time.perf_counter() - started) * 1000, 3),
            shots=None,
            layers=layers,
            optimizer_evaluations=None,
            circuit_depth=None,
            num_qubits=len(costs),
            feasible_probability=None,
            counts={},
            objective_value=None,
            error=f"qiskit_unavailable: {exc}",
        )

    try:
        qubo = build_candidate_qubo(costs, penalty=2.0)
        program = QuadraticProgram("candidate_route_selection")
        for index in range(len(costs)):
            program.binary_var(f"route_{index}")
        linear = {f"route_{index}": value for index, value in enumerate(qubo.linear)}
        quadratic = {
            (f"route_{left}", f"route_{right}"): value
            for (left, right), value in qubo.quadratic.items()
        }
        program.minimize(constant=qubo.penalty, linear=linear, quadratic=quadratic)

        sampler = AerSampler(
            run_options={"shots": shots, "seed": seed},
            transpile_options={"seed_transpiler": seed},
        )
        qaoa = QAOA(
            sampler=sampler,
            optimizer=COBYLA(maxiter=maxiter),
            reps=layers,
            initial_point=[0.5] * (layers * 2),
        )
        optimization = MinimumEigenOptimizer(qaoa).solve(program)
        raw = optimization.min_eigen_solver_result
        distribution = raw.eigenstate
        counts = _quasi_to_counts(distribution, len(costs), shots)
        decoded = decode_samples(costs, counts)

        operator, _offset = program.to_ising()
        ansatz = QAOAAnsatz(operator, reps=layers)
        compiled = transpile(ansatz.decompose(reps=2), AerSimulator(), seed_transpiler=seed)
        selected = decoded.candidate_index
        if selected is None:
            status = QuantumStatus.FAILED
            error = "no_feasible_measurement"
            objective_value = None
        else:
            status = QuantumStatus.COMPLETED
            error = None
            objective_value = float(costs[selected])
        return QuantumSelectionResult(
            status=status,
            selected_index=selected,
            backend="qiskit_aer_simulator",
            execution_time_ms=round((time.perf_counter() - started) * 1000, 3),
            shots=shots,
            layers=layers,
            optimizer_evaluations=getattr(raw, "cost_function_evals", None),
            circuit_depth=compiled.depth(),
            num_qubits=len(costs),
            feasible_probability=decoded.feasible_probability,
            counts=counts,
            objective_value=objective_value,
            error=error,
        )
    except Exception as exc:  # Qiskit supplies heterogeneous execution errors.
        return QuantumSelectionResult(
            status=QuantumStatus.FAILED,
            selected_index=None,
            backend="qiskit_aer_simulator",
            execution_time_ms=round((time.perf_counter() - started) * 1000, 3),
            shots=shots,
            layers=layers,
            optimizer_evaluations=None,
            circuit_depth=None,
            num_qubits=len(costs),
            feasible_probability=None,
            counts={},
            objective_value=None,
            error=f"{type(exc).__name__}: {exc}",
        )
