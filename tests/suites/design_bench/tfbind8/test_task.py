from __future__ import annotations

import pytest

from sci_modeling_bench.exceptions import TaskError
from sci_modeling_bench.task import (
    BlackBoxOptimizationEvaluation,
    BlackBoxOptimizationTask,
    CandidatePoolRankingTask,
)
from sci_modeling_bench.suites.design_bench import (
    CandidateValidationReport,
    CandidateViolation,
    TFBind8BlackBoxOptimizationTask,
)
from sci_modeling_bench.suites.design_bench.tfbind8 import (
    TFBind8DesignBenchProtocol,
    TFBind8ExactObjective,
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

    evaluation = task.evaluate([{"sequence": "AACCGGTT"}, {"sequence": "TTTTTTTT"}])

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
    evaluation = task.evaluate([{"sequence": "XXXXXXXX"} for _ in range(3)])

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
    evaluation = task.evaluate([{"sequence": "AAAAAAAA"}, {"sequence": "AAAAAAAC"}])

    assert not evaluation.submission_valid
    assert evaluation.submission_validation.violations[0].code == (
        "candidate_count_mismatch"
    )
    assert evaluation.expected_candidates == 3
    assert evaluation.submitted_candidates == 2
    assert evaluation.score is None
    assert evaluation.candidates == ()


def test_overlong_bbo_submission_is_also_a_count_failure(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(
        tiny_tfbind8_dataset,
        submission_size=3,
    )

    evaluation = task.evaluate(
        [
            {"sequence": "AAAAAAAA"},
            {"sequence": "AAAAAAAC"},
            {"sequence": "AACCGGTT"},
            {"sequence": "TTTTTTTT"},
        ]
    )

    assert not evaluation.submission_valid
    assert evaluation.submitted_candidates == 4
    assert evaluation.submission_validation.violations[0].code == (
        "candidate_count_mismatch"
    )


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


class _TinyTFBind8RankingTask(CandidatePoolRankingTask):
    task_id = "test/tfbind8-candidate-pool-ranking"


def _ranking_task(dataset) -> _TinyTFBind8RankingTask:
    data = dataset.load()
    pool = tuple({"sequence": sequence} for sequence in data["sequence"])
    return _TinyTFBind8RankingTask(
        dataset,
        TFBind8DesignBenchProtocol(),
        TFBind8ExactObjective(dataset),
        candidate_pool=pool,
        score_field="normalized_e_score",
        reference_scores=data["normalized_e_score"],
        submission_size=3,
    )


def test_pool_ranking_scores_only_the_required_prefix(
    tiny_tfbind8_dataset,
) -> None:
    task = _ranking_task(tiny_tfbind8_dataset)
    evaluation = task.evaluate(
        [
            {"sequence": "AAAAAAAA"},
            {"sequence": "TTTTTTTT"},
            {"sequence": "AACCGGTT"},
            {"sequence": "XXXXXXXX"},
        ]
    )

    assert evaluation.submission_valid
    assert evaluation.evaluation_eligible
    assert evaluation.candidate_pool_size == 4
    assert evaluation.submitted_candidates == 4
    assert evaluation.evaluated_candidates == 3
    assert evaluation.ignored_candidates == 1
    assert len(evaluation.candidates) == 3


def test_pool_ranking_rejects_a_short_submission(
    tiny_tfbind8_dataset,
) -> None:
    evaluation = _ranking_task(tiny_tfbind8_dataset).evaluate(
        [{"sequence": "AAAAAAAA"}, {"sequence": "TTTTTTTT"}]
    )

    assert not evaluation.submission_valid
    assert evaluation.submission_validation.violations[0].code == (
        "insufficient_candidate_count"
    )
    assert evaluation.evaluated_candidates == 0


def test_pool_ranking_rejects_out_of_pool_candidates_in_the_prefix(
    tiny_tfbind8_dataset,
) -> None:
    evaluation = _ranking_task(tiny_tfbind8_dataset).evaluate(
        [
            {"sequence": "AAAAAAAG"},
            {"sequence": "TTTTTTTT"},
            {"sequence": "AACCGGTT"},
        ]
    )

    assert not evaluation.evaluation_eligible
    assert evaluation.candidates[0].validation.violations[0].code == (
        "candidate_outside_evaluation_pool"
    )


class _TinyMinimizationTask(BlackBoxOptimizationTask):
    task_id = "test/tfbind8-minimization"


def test_common_metrics_support_minimization_and_keep_the_report_schema(
    tiny_tfbind8_dataset,
) -> None:
    data = tiny_tfbind8_dataset.load()
    task = _TinyMinimizationTask(
        tiny_tfbind8_dataset,
        TFBind8DesignBenchProtocol(),
        TFBind8ExactObjective(tiny_tfbind8_dataset),
        score_field="normalized_e_score",
        reference_scores=data["normalized_e_score"],
        reference_scope="full_domain",
        submission_size=3,
        objective_direction="minimize",
    )

    evaluation = task.evaluate(
        [
            {"sequence": "AACCGGTT"},
            {"sequence": "AAAAAAAC"},
            {"sequence": "AAAAAAAA"},
        ]
    )

    assert isinstance(evaluation, BlackBoxOptimizationEvaluation)
    assert evaluation.metrics["best_score"] == 0.0
    assert evaluation.best_candidate_index == 2
    assert evaluation.metric_directions["best_score"] == "minimize"
    assert evaluation.metric_directions["best_regret"] == "minimize"
    assert {
        "task_id",
        "submission_validation",
        "metrics",
        "metric_directions",
        "primary_metric",
        "metric_direction",
        "expected_candidates",
        "submitted_candidates",
        "valid_candidates",
        "invalid_candidates",
        "score_field",
        "aggregation",
        "summary_size",
        "reference_scope",
        "reference_size",
        "best_candidate_index",
        "best_objective_output",
        "candidates",
        "submission_valid",
        "score",
        "all_candidates_valid",
        "evaluation_eligible",
    } == set(evaluation.model_dump())
