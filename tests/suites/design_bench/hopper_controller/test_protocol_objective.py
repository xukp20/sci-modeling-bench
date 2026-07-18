from __future__ import annotations

import pytest

from sci_modeling_bench.suites.design_bench.hopper_controller import (
    EXPECTED_ROLLOUT_COUNT,
    HopperControllerLowerScoreProtocol,
    HopperControllerMeasuredObjective,
)


def test_protocol_exposes_all_visible_rollouts_and_hides_candidate_labels(
    tiny_hopper_controller_dataset,
) -> None:
    protocol = HopperControllerLowerScoreProtocol(visible_fraction=0.5)

    agent_input = protocol.build_input(tiny_hopper_controller_dataset).data
    pool = protocol.candidate_pool(tiny_hopper_controller_dataset)

    assert len(agent_input.observations) == 5
    assert len(agent_input.observations["raw_returns"][0]) == EXPECTED_ROLLOUT_COUNT
    assert agent_input.observations.column_names == [
        "policy_weights",
        "raw_returns",
        "episode_lengths",
        "terminated",
        "truncated",
    ]
    assert len(agent_input.candidates) == 5
    assert agent_input.candidates.column_names == ["policy_weights"]
    assert sorted(pool["mean_return"]) == pytest.approx([6.0, 7.0, 8.0, 9.0, 10.0])


def test_objective_returns_frozen_rollout_mean(
    tiny_hopper_controller_dataset,
) -> None:
    row = tiny_hopper_controller_dataset.load()[7]
    objective = HopperControllerMeasuredObjective(tiny_hopper_controller_dataset)

    assert objective.evaluate({"policy_weights": row["policy_weights"]}) == {
        "mean_return": pytest.approx(8.0)
    }
