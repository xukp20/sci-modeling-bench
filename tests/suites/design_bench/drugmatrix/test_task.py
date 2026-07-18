from __future__ import annotations

import pytest

from sci_modeling_bench.exceptions import TaskError
from sci_modeling_bench.suites.design_bench.drugmatrix import (
    DrugMatrixCandidatePoolRankingTask,
    DrugMatrixEndpointObjective,
)


def test_task_scores_ordered_condition_ids(tiny_drugmatrix_dataset) -> None:
    task = DrugMatrixCandidatePoolRankingTask(
        tiny_drugmatrix_dataset,
        endpoint="sodium",
        submission_size=3,
    )
    pool = task.protocol.candidate_pool(tiny_drugmatrix_dataset)
    score_field = "sodium_control_deviation"
    ranked = sorted(pool, key=lambda row: row[score_field], reverse=True)

    evaluation = task.evaluate(
        [{"condition_id": row["condition_id"]} for row in ranked[:3]]
    )

    assert task.task_id == (
        "design-bench/drugmatrix-sodium-candidate-pool-ranking-v1"
    )
    assert evaluation.evaluation_eligible
    assert evaluation.primary_metric == "global_ndcg"
    assert evaluation.score == 1.0
    assert evaluation.reference_scope == "evaluation_pool"
    assert evaluation.best_objective_output is not None
    assert set(evaluation.best_objective_output) == {
        "raw_response",
        "control_deviation",
    }


def test_task_rejects_unknown_and_duplicate_conditions(
    tiny_drugmatrix_dataset,
) -> None:
    task = DrugMatrixCandidatePoolRankingTask(
        tiny_drugmatrix_dataset,
        endpoint="mchc",
        submission_size=3,
    )
    candidates = list(task.build_input().data.candidates)

    outside = task.evaluate(
        [
            {"condition_id": "unknown"},
            {"condition_id": candidates[0]["condition_id"]},
            {"condition_id": candidates[1]["condition_id"]},
        ]
    )
    duplicate = task.evaluate(
        [
            {"condition_id": candidates[0]["condition_id"]},
            {"condition_id": candidates[0]["condition_id"]},
            {"condition_id": candidates[1]["condition_id"]},
        ]
    )

    assert not outside.evaluation_eligible
    assert outside.candidates[0].validation.violations[0].code == (
        "candidate_outside_evaluation_pool"
    )
    assert not duplicate.evaluation_eligible
    assert duplicate.candidates[1].validation.violations[0].code == (
        "duplicate_candidate"
    )

    malformed = task.evaluate(
        [
            {},
            {"condition_id": candidates[0]["condition_id"]},
            {"condition_id": candidates[1]["condition_id"]},
        ]
    )
    assert malformed.candidates[0].validation.violations[0].code == (
        "invalid_condition_id"
    )


def test_task_rejects_endpoint_mismatched_objective(
    tiny_drugmatrix_dataset,
) -> None:
    objective = DrugMatrixEndpointObjective(
        tiny_drugmatrix_dataset,
        endpoint="mch",
    )
    with pytest.raises(TaskError, match="endpoint must match"):
        DrugMatrixCandidatePoolRankingTask(
            tiny_drugmatrix_dataset,
            endpoint="mchc",
            objective=objective,
            submission_size=3,
        )
