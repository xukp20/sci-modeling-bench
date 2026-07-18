from __future__ import annotations

from sci_modeling_bench.suites.design_bench.hopper_controller import (
    HopperControllerCandidatePoolRankingTask,
    HopperControllerLowerScoreProtocol,
    policy_identity,
)
from sci_modeling_bench.task import CandidatePoolRankingTask


def _task(dataset, **kwargs):
    return HopperControllerCandidatePoolRankingTask(
        dataset,
        protocol=HopperControllerLowerScoreProtocol(visible_fraction=0.5),
        submission_size=3,
        **kwargs,
    )


def test_task_scores_selection_and_submitted_order(
    tiny_hopper_controller_dataset,
) -> None:
    task = _task(tiny_hopper_controller_dataset)
    pool = task.protocol.candidate_pool(tiny_hopper_controller_dataset)
    by_score = {
        float(row["mean_return"]): {"policy_weights": row["policy_weights"]}
        for row in pool
    }

    evaluation = task.evaluate([by_score[8.0], by_score[10.0], by_score[9.0]])

    assert isinstance(task, CandidatePoolRankingTask)
    assert evaluation.primary_metric == "global_ndcg"
    assert evaluation.metrics["best_score"] == 10.0
    assert evaluation.metrics["rank_1_score"] == 8.0
    assert evaluation.metrics["batch_mean"] == 9.0
    assert evaluation.reference_scope == "evaluation_pool"


def test_task_rejects_policy_outside_candidate_pool(
    tiny_hopper_controller_dataset,
) -> None:
    task = _task(tiny_hopper_controller_dataset)
    visible = task.build_input().observations[0]
    candidates = list(task.build_input().candidates)

    evaluation = task.evaluate(
        [{"policy_weights": visible["policy_weights"]}, *candidates[:2]]
    )

    assert not evaluation.evaluation_eligible
    assert evaluation.candidates[0].validation.violations[0].code == (
        "candidate_outside_evaluation_pool"
    )


def test_task_rejects_duplicate_policy_and_accepts_ignored_suffix(
    tiny_hopper_controller_dataset,
) -> None:
    task = _task(tiny_hopper_controller_dataset)
    candidates = list(task.build_input().candidates)

    duplicate = task.evaluate([candidates[0], candidates[0], candidates[1]])
    valid = task.evaluate(candidates[:4])

    assert duplicate.metrics == {}
    assert duplicate.candidates[1].validation.violations[0].code == (
        "duplicate_candidate"
    )
    assert valid.evaluation_eligible
    assert valid.evaluated_candidates == 3
    assert valid.ignored_candidates == 1


def test_task_identity_uses_canonical_policy_bytes(
    tiny_hopper_controller_dataset,
) -> None:
    task = _task(tiny_hopper_controller_dataset)
    candidate = task.build_input().candidates[0]

    assert task._candidate_identity(candidate) == policy_identity(
        candidate["policy_weights"]
    )
