"""Candidate-route QUBO construction and transparent sample decoding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class CandidateQubo:
    costs: tuple[float, ...]
    penalty: float

    def energy(self, state: Sequence[int]) -> float:
        if len(state) != len(self.costs) or any(bit not in (0, 1) for bit in state):
            raise ValueError("state must be a binary vector matching candidate count")
        selected = sum(state)
        return sum(cost * bit for cost, bit in zip(self.costs, state)) + self.penalty * (
            selected - 1
        ) ** 2

    @property
    def linear(self) -> tuple[float, ...]:
        # A(sum x - 1)^2 contributes -A*x_i to each linear coefficient.
        return tuple(cost - self.penalty for cost in self.costs)

    @property
    def quadratic(self) -> dict[tuple[int, int], float]:
        return {
            (left, right): 2 * self.penalty
            for left in range(len(self.costs))
            for right in range(left + 1, len(self.costs))
        }


@dataclass(frozen=True)
class DecodedSample:
    feasible: bool
    candidate_index: int | None
    bitstring: str | None
    sample_count: int
    feasible_probability: float


def build_candidate_qubo(costs: Sequence[float], penalty: float = 2.0) -> CandidateQubo:
    if not costs:
        raise ValueError("at least one candidate cost is required")
    if any(cost < 0 for cost in costs):
        raise ValueError("candidate costs must be non-negative")
    high = max(costs)
    low = min(costs)
    normalized = tuple(0.0 if high == low else (cost - low) / (high - low) for cost in costs)
    if penalty <= max(normalized, default=0):
        raise ValueError("penalty must exceed every normalized candidate cost")
    return CandidateQubo(costs=normalized, penalty=float(penalty))


def decode_samples(costs: Sequence[float], counts: Mapping[str, int]) -> DecodedSample:
    total = sum(max(0, count) for count in counts.values())
    feasible: list[tuple[float, int, int, str]] = []
    feasible_count = 0
    for bitstring, count in counts.items():
        if count <= 0 or len(bitstring) != len(costs):
            continue
        # Qiskit prints classical bits most-significant first; x_0 is rightmost.
        selected = [index for index, bit in enumerate(reversed(bitstring)) if bit == "1"]
        if len(selected) == 1:
            index = selected[0]
            feasible_count += count
            feasible.append((float(costs[index]), index, -count, bitstring))
    if not feasible:
        return DecodedSample(False, None, None, 0, 0.0)
    _, index, negative_count, bitstring = min(feasible)
    return DecodedSample(
        feasible=True,
        candidate_index=index,
        bitstring=bitstring,
        sample_count=-negative_count,
        feasible_probability=feasible_count / total if total else 0.0,
    )
