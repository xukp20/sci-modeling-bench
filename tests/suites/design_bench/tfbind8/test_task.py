from __future__ import annotations

from sci_modeling_bench.suites.design_bench import (
    CandidateValidationReport,
    CandidateViolation,
    TFBind8BlackBoxOptimizationTask,
)
from sci_modeling_bench.task import SubmissionValidationReport


def test_default_task_builds_protocol_input_and_scores_top_candidate(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(tiny_tfbind8_dataset)
    submission = [
        {"sequence": "AAAAAAAA"} for _ in range(127)
    ] + [{"sequence": "TTTTTTTT"}]

    agent_input = task.build_input()
    evaluation = task.evaluate(submission)

    assert len(agent_input) == 2
    assert agent_input.column_names == ["sequence", "normalized_e_score"]
    assert evaluation.submission_valid
    assert evaluation.all_candidates_valid
    assert evaluation.score == 1.0
    assert evaluation.metrics == {"top_1_normalized_e_score": 1.0}
    assert evaluation.best_candidate_index == 127
    assert evaluation.best_objective_output == {
        "e_score": 0.5,
        "normalized_e_score": 1.0,
    }
    assert len(evaluation.candidates) == 128
    assert evaluation.candidates[0].score == 0.0
    assert evaluation.candidates[127].score == 1.0


def test_task_keeps_submission_and_candidate_validation_separate(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(tiny_tfbind8_dataset)
    submission = (
        [{"sequence": "TTTTTTTT"}]
        + [{"sequence": "AAAAAAAA"} for _ in range(125)]
        + [{"sequence": "AACCGGTX"}, {"sequence": "ACGT"}]
    )

    evaluation = task.evaluate(submission)

    assert isinstance(
        evaluation.submission_validation,
        SubmissionValidationReport,
    )
    assert evaluation.submission_validation.valid
    assert evaluation.valid_candidates == 126
    assert evaluation.invalid_candidates == 2
    assert evaluation.score == 1.0
    assert not evaluation.all_candidates_valid

    alphabet_failure = evaluation.candidates[126]
    assert isinstance(alphabet_failure.validation, CandidateValidationReport)
    assert isinstance(
        alphabet_failure.validation.violations[0],
        CandidateViolation,
    )
    assert not alphabet_failure.valid
    assert alphabet_failure.score is None
    assert alphabet_failure.objective_output is None
    assert alphabet_failure.validation.violations[0].code == (
        "invalid_alphabet_symbol"
    )
    assert evaluation.candidates[127].validation.violations[0].code == (
        "below_minimum_length"
    )


def test_all_invalid_candidates_receive_floor_aggregate_without_fake_outputs(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(tiny_tfbind8_dataset)

    evaluation = task.evaluate(
        [{"sequence": "XXXXXXXX"} for _ in range(128)]
    )

    assert evaluation.submission_valid
    assert evaluation.valid_candidates == 0
    assert evaluation.invalid_candidates == 128
    assert evaluation.score == 0.0
    assert evaluation.best_candidate_index is None
    assert evaluation.best_objective_output is None
    assert all(item.score is None for item in evaluation.candidates)
    assert all(item.objective_output is None for item in evaluation.candidates)


def test_wrong_candidate_count_is_a_submission_level_failure(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(tiny_tfbind8_dataset)

    evaluation = task.evaluate(
        [{"sequence": "AAAAAAAA"} for _ in range(127)]
    )

    assert not evaluation.submission_valid
    assert evaluation.submission_validation.violations[0].code == (
        "candidate_count_mismatch"
    )
    assert evaluation.expected_candidates == 128
    assert evaluation.submitted_candidates == 127
    assert evaluation.score == 0.0
    assert evaluation.candidates == ()


def test_non_iterable_candidate_submission_is_rejected(
    tiny_tfbind8_dataset,
) -> None:
    task = TFBind8BlackBoxOptimizationTask(tiny_tfbind8_dataset)

    evaluation = task.evaluate({"sequence": "AAAAAAAA"})

    assert not evaluation.submission_valid
    assert evaluation.submission_validation.violations[0].code == (
        "invalid_submission_type"
    )
    assert evaluation.submitted_candidates == 0
    assert evaluation.score == 0.0
