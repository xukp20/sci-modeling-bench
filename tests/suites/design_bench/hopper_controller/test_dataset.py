from __future__ import annotations

from sci_modeling_bench.suites.design_bench.hopper_controller import (
    EXPECTED_ROLLOUT_COUNT,
)


def test_dataset_validates_policy_identity_and_rollout_summaries(
    tiny_hopper_controller_dataset,
) -> None:
    row = tiny_hopper_controller_dataset.load()[0]

    report = tiny_hopper_controller_dataset.validate_observation(row)

    assert report.valid
    assert len(row["raw_returns"]) == EXPECTED_ROLLOUT_COUNT
    assert len(row["episode_lengths"]) == EXPECTED_ROLLOUT_COUNT


def test_dataset_rejects_summary_not_recomputed_from_raw_returns(
    tiny_hopper_controller_dataset,
) -> None:
    row = dict(tiny_hopper_controller_dataset.load()[0])
    row["mean_return"] += 1.0

    report = tiny_hopper_controller_dataset.validate_observation(row)

    assert not report.valid
    assert "mean_return_mismatch" in {
        violation.code for violation in report.violations
    }


def test_dataset_rejects_non_finite_submitted_policy(
    tiny_hopper_controller_dataset,
) -> None:
    weights = list(tiny_hopper_controller_dataset.load()[0]["policy_weights"])
    weights[0] = float("nan")

    report = tiny_hopper_controller_dataset.validate_inputs(
        {"policy_weights": weights}
    )

    assert not report.valid
    assert report.violations[-1].code == "invalid_policy_weights"
