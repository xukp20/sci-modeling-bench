"""Design-Bench-compatible offline black-box optimization Tasks."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from numbers import Real
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from sci_modeling_bench.dataset import Dataset, ValidationReport
from sci_modeling_bench.exceptions import TaskError
from sci_modeling_bench.objective import Candidate, Objective
from sci_modeling_bench.protocol import Protocol
from sci_modeling_bench.task import (
    ObjectiveBackedTask,
    SubmissionEvaluation,
    SubmissionValidationReport,
    SubmissionViolation,
)

AgentInputT = TypeVar("AgentInputT")


class CandidateViolation(BaseModel):
    """One Dataset-contract finding for a submitted candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    field: str | None = None
    severity: Literal["error", "warning"] = "error"


class CandidateValidationReport(BaseModel):
    """Validation result for one candidate, independent of submission shape."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    violations: tuple[CandidateViolation, ...] = ()

    @computed_field
    @property
    def valid(self) -> bool:
        """Whether the candidate has no error-severity violations."""

        return not any(item.severity == "error" for item in self.violations)

    @classmethod
    def from_dataset_report(
        cls,
        report: ValidationReport,
    ) -> CandidateValidationReport:
        """Translate Dataset findings at the candidate/Task boundary."""

        return cls(
            violations=tuple(
                CandidateViolation(
                    code=item.code,
                    message=item.message,
                    field=item.field,
                    severity=item.severity,
                )
                for item in report.violations
            )
        )


class CandidateEvaluation(BaseModel):
    """Validation and Objective output for one submitted candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(ge=0)
    validation: CandidateValidationReport
    score: float | None = None
    objective_output: dict[str, Any] | None = None

    @computed_field
    @property
    def valid(self) -> bool:
        return self.validation.valid

    @model_validator(mode="after")
    def validate_evaluation_state(self) -> CandidateEvaluation:
        if self.valid and (self.score is None or self.objective_output is None):
            raise ValueError(
                "valid candidates require a score and Objective output"
            )
        if not self.valid and (
            self.score is not None or self.objective_output is not None
        ):
            raise ValueError(
                "invalid candidates cannot have a score or Objective output"
            )
        return self


class BlackBoxOptimizationEvaluation(SubmissionEvaluation):
    """Structured evaluation of a fixed-size candidate submission."""

    expected_candidates: int = Field(ge=1)
    submitted_candidates: int = Field(ge=0)
    valid_candidates: int = Field(ge=0)
    invalid_candidates: int = Field(ge=0)
    score_field: str = Field(min_length=1)
    aggregation: Literal["max"] = "max"
    best_candidate_index: int | None = Field(default=None, ge=0)
    best_objective_output: dict[str, Any] | None = None
    candidates: tuple[CandidateEvaluation, ...] = ()

    @computed_field
    @property
    def all_candidates_valid(self) -> bool:
        return self.submission_valid and self.invalid_candidates == 0


class DesignBenchBlackBoxOptimizationTask(
    ObjectiveBackedTask[
        AgentInputT,
        Iterable[Candidate],
        BlackBoxOptimizationEvaluation,
    ],
    Generic[AgentInputT],
):
    """Evaluate 128 candidates by their maximum normalized Objective score."""

    expected_candidates = 128
    invalid_submission_score = 0.0

    def __init__(
        self,
        dataset: Dataset,
        protocol: Protocol[AgentInputT],
        objective: Objective,
        *,
        score_field: str,
    ) -> None:
        if not score_field.strip():
            raise TaskError("score_field must be a non-empty string")
        if score_field not in objective.output_fields:
            raise TaskError(
                f"score field {score_field!r} is not returned by the Objective"
            )
        self._score_field = score_field
        super().__init__(dataset, protocol, objective)

    @property
    def score_field(self) -> str:
        return self._score_field

    @property
    def primary_metric(self) -> str:
        return f"top_1_{self.score_field}"

    def evaluate(
        self,
        submission: Iterable[Candidate],
    ) -> BlackBoxOptimizationEvaluation:
        candidate_batch, submission_report = self._validate_submission(submission)
        if not submission_report.valid:
            return self._invalid_submission_evaluation(
                submission_report,
                submitted_candidates=len(candidate_batch),
            )

        validation_reports = tuple(
            CandidateValidationReport.from_dataset_report(
                self.dataset.validate_inputs(candidate)
            )
            for candidate in candidate_batch
        )
        valid_pairs = tuple(
            (index, candidate)
            for index, (candidate, report) in enumerate(
                zip(candidate_batch, validation_reports, strict=True)
            )
            if report.valid
        )
        outputs = (
            self.objective.evaluate_batch(
                candidate for _, candidate in valid_pairs
            )
            if valid_pairs
            else ()
        )

        evaluated: dict[int, tuple[float, dict[str, Any]]] = {}
        for (index, _), output in zip(valid_pairs, outputs, strict=True):
            value = output[self.score_field]
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TaskError(
                    f"Objective score field {self.score_field!r} must be numeric"
                )
            score = float(value)
            if not math.isfinite(score):
                raise TaskError(
                    f"Objective score field {self.score_field!r} must be finite"
                )
            evaluated[index] = (score, dict(output))

        candidate_evaluations = tuple(
            CandidateEvaluation(
                index=index,
                validation=report,
                score=evaluated[index][0] if index in evaluated else None,
                objective_output=(
                    evaluated[index][1] if index in evaluated else None
                ),
            )
            for index, report in enumerate(validation_reports)
        )
        valid_evaluations = tuple(
            item for item in candidate_evaluations if item.valid
        )
        best = (
            max(valid_evaluations, key=lambda item: item.score)
            if valid_evaluations
            else None
        )
        score = best.score if best is not None else self.invalid_submission_score

        return BlackBoxOptimizationEvaluation(
            task_id=self.task_id,
            submission_validation=submission_report,
            metrics={self.primary_metric: score},
            primary_metric=self.primary_metric,
            metric_direction="maximize",
            expected_candidates=self.expected_candidates,
            submitted_candidates=len(candidate_batch),
            valid_candidates=len(valid_evaluations),
            invalid_candidates=len(candidate_batch) - len(valid_evaluations),
            score_field=self.score_field,
            best_candidate_index=best.index if best is not None else None,
            best_objective_output=(
                best.objective_output if best is not None else None
            ),
            candidates=candidate_evaluations,
        )

    def _validate_submission(
        self,
        submission: Iterable[Candidate],
    ) -> tuple[tuple[Any, ...], SubmissionValidationReport]:
        if isinstance(submission, (str, bytes, bytearray, Mapping)):
            return (), SubmissionValidationReport(
                violations=(
                    SubmissionViolation(
                        code="invalid_submission_type",
                        message="submission must be an iterable of candidates",
                    ),
                )
            )
        try:
            candidate_batch = tuple(submission)
        except TypeError:
            return (), SubmissionValidationReport(
                violations=(
                    SubmissionViolation(
                        code="invalid_submission_type",
                        message="submission must be an iterable of candidates",
                    ),
                )
            )

        if len(candidate_batch) != self.expected_candidates:
            return candidate_batch, SubmissionValidationReport(
                violations=(
                    SubmissionViolation(
                        code="candidate_count_mismatch",
                        message=(
                            f"expected {self.expected_candidates} candidates, "
                            f"got {len(candidate_batch)}"
                        ),
                    ),
                )
            )
        return candidate_batch, SubmissionValidationReport()

    def _invalid_submission_evaluation(
        self,
        report: SubmissionValidationReport,
        *,
        submitted_candidates: int,
    ) -> BlackBoxOptimizationEvaluation:
        return BlackBoxOptimizationEvaluation(
            task_id=self.task_id,
            submission_validation=report,
            metrics={self.primary_metric: self.invalid_submission_score},
            primary_metric=self.primary_metric,
            metric_direction="maximize",
            expected_candidates=self.expected_candidates,
            submitted_candidates=submitted_candidates,
            valid_candidates=0,
            invalid_candidates=0,
            score_field=self.score_field,
            best_candidate_index=None,
            best_objective_output=None,
            candidates=(),
        )
