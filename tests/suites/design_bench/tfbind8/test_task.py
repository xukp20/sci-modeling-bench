from __future__ import annotations

import pytest

from sci_modeling_bench.exceptions import TaskError
from sci_modeling_bench.suites.design_bench import (
    CandidateValidationReport,
    CandidateViolation,
    TFBind8BlackBoxOptimizationTask,
)
from sci_modeling_bench.task import SubmissionValidationReport


def test_task_returns_the_common_ordered_candidate_metrics(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(
        tiny_tfbind8_dataset,
        submission_size=3,
    )
    submission = [
        {"sequence": "AAAAAAAA"},
        {"sequence": "TTTTTTTT"},
        {"sequence": "AACCGGTT"},
    ]

    agent_input = task.build_input()
    evaluation = task.evaluate(submission)

    assert len(agent_input) == 2
    assert evaluation.submission_valid
    assert evaluation.all_candidates_valid
    assert evaluation.evaluation_eligible
    assert evaluation.primary_metric == "best_k_mean"
    assert evaluation.score == pytest.approx((0.0 + 1.0 + 0.75) / 3)
    assert set(evaluation.metrics) == set(task.metric_directions)
    assert evaluation.metrics["best_score"] == 1.0
    assert evaluation.metrics["rank_1_score"] == 0.0
    assert evaluation.metrics["prefix_k_mean"] == evaluation.metrics["best_k_mean"]
    assert evaluation.metrics["best_regret"] == 0.0
    assert evaluation.metrics["best_k_mean_regret"] == pytest.approx(1.0 / 12.0)
    assert 0.0 < evaluation.metrics["global_ndcg"] < 1.0
    assert 0.0 < evaluation.metrics["reranking_ndcg"] < 1.0
    assert evaluation.best_candidate_index == 1
    assert evaluation.reference_scope == "full_domain"
    assert evaluation.reference_size == 4
    assert evaluation.summary_size == 3


def test_task_primary_metric_and_submission_size_are_configurable(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(
        tiny_tfbind8_dataset,
        submission_size=2,
        primary_metric="rank_1_score",
    )

    evaluation = task.evaluate(
        [{"sequence": "AACCGGTT"}, {"sequence": "TTTTTTTT"}]
    )

    assert evaluation.expected_candidates == 2
    assert evaluation.primary_metric == "rank_1_score"
    assert evaluation.metric_direction == "maximize"
    assert evaluation.score == 0.75


@pytest.mark.parametrize("submission_size", [True, 0, 1.5])
def test_submission_size_must_be_a_positive_integer(
    tiny_tfbind8_dataset,
    submission_size,
) -> None:
    with pytest.raises(TaskError, match="positive integer"):
        TFBind8BlackBoxOptimizationTask(
            tiny_tfbind8_dataset,
            submission_size=submission_size,
        )


def test_duplicate_candidates_are_ineligible_for_batch_metrics(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(
        tiny_tfbind8_dataset,
        submission_size=3,
    )
    evaluation = task.evaluate(
        [
            {"sequence": "TTTTTTTT"},
            {"sequence": "AAAAAAAA"},
            {"sequence": "AAAAAAAA"},
        ]
    )

    assert evaluation.submission_valid
    assert evaluation.valid_candidates == 2
    assert evaluation.invalid_candidates == 1
    assert not evaluation.evaluation_eligible
    assert evaluation.metrics == {}
    assert evaluation.score is None
    assert evaluation.candidates[2].validation.violations[0].code == (
        "duplicate_candidate"
    )


def test_task_keeps_submission_and_candidate_validation_separate(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(
        tiny_tfbind8_dataset,
        submission_size=3,
    )
    evaluation = task.evaluate(
        [
            {"sequence": "TTTTTTTT"},
            {"sequence": "AACCGGTX"},
            {"sequence": "ACGT"},
        ]
    )

    assert isinstance(evaluation.submission_validation, SubmissionValidationReport)
    assert evaluation.submission_validation.valid
    assert evaluation.valid_candidates == 1
    assert evaluation.invalid_candidates == 2
    assert evaluation.score is None

    alphabet_failure = evaluation.candidates[1]
    assert isinstance(alphabet_failure.validation, CandidateValidationReport)
    assert isinstance(alphabet_failure.validation.violations[0], CandidateViolation)
    assert alphabet_failure.validation.violations[0].code == "invalid_alphabet_symbol"
    assert evaluation.candidates[2].validation.violations[0].code == (
        "below_minimum_length"
    )


def test_all_invalid_candidates_return_diagnostics_without_fake_outputs(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(
        tiny_tfbind8_dataset,
        submission_size=3,
    )
    evaluation = task.evaluate(
        [{"sequence": "XXXXXXXX"} for _ in range(3)]
    )

    assert evaluation.submission_valid
    assert evaluation.valid_candidates == 0
    assert evaluation.invalid_candidates == 3
    assert evaluation.score is None
    assert evaluation.best_candidate_index is None
    assert all(item.objective_output is None for item in evaluation.candidates)


def test_wrong_candidate_count_is_a_submission_level_failure(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(
        tiny_tfbind8_dataset,
        submission_size=3,
    )
    evaluation = task.evaluate(
        [{"sequence": "AAAAAAAA"}, {"sequence": "AAAAAAAC"}]
    )

    assert not evaluation.submission_valid
    assert evaluation.submission_validation.violations[0].code == (
        "candidate_count_mismatch"
    )
    assert evaluation.expected_candidates == 3
    assert evaluation.submitted_candidates == 2
    assert evaluation.score is None
    assert evaluation.candidates == ()


def test_non_iterable_candidate_submission_is_rejected(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(
        tiny_tfbind8_dataset,
        submission_size=3,
    )
    evaluation = task.evaluate({"sequence": "AAAAAAAA"})

    assert not evaluation.submission_valid
    assert evaluation.submission_validation.violations[0].code == (
        "invalid_submission_type"
    )
    assert evaluation.submitted_candidates == 0
    assert evaluation.score is None
