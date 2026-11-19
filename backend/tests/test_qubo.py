import itertools

import pytest

from quantum.qubo import build_candidate_qubo, decode_samples


def test_qubo_global_minimum_is_one_hot_lowest_cost_candidate() -> None:
    qubo = build_candidate_qubo([0.8, 0.2, 0.5], penalty=2.0)
    states = list(itertools.product([0, 1], repeat=3))
    best = min(states, key=qubo.energy)

    assert best == (0, 1, 0)
    assert qubo.energy((0, 0, 0)) > qubo.energy(best)
    assert qubo.energy((1, 1, 0)) > qubo.energy(best)


def test_penalty_is_validated_against_normalized_not_raw_route_costs() -> None:
    qubo = build_candidate_qubo([3.4, 7.2, 11.9], penalty=2.0)

    assert qubo.costs == pytest.approx((0.0, 3.8 / 8.5, 1.0))
    assert qubo.penalty == 2.0


def test_equal_cost_tie_is_decoded_deterministically() -> None:
    decoded = decode_samples(
        costs=[0.4, 0.4],
        counts={"01": 25, "10": 25},
    )

    assert decoded.feasible
    assert decoded.candidate_index == 0
    assert decoded.feasible_probability == pytest.approx(1.0)


def test_no_feasible_measurement_is_reported_without_fake_quantum_result() -> None:
    decoded = decode_samples(costs=[0.1, 0.2], counts={"00": 60, "11": 40})

    assert not decoded.feasible
    assert decoded.candidate_index is None
    assert decoded.feasible_probability == 0
