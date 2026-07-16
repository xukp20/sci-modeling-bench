"""Shared candidate evaluation for Design-Bench-style optimization Tasks."""

from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Mapping, Sequence
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
MetricDirection = Literal["maximize", "minimize"]
ReferenceScope = Literal["full_domain", "evaluation_pool", "best_known"]

COMMON_METRICS = (
    "best_score",
    "rank_1_score",
    "best_k_mean",
    "prefix_k_mean",
    "batch_mean",
    "best_regret",
    "best_k_mean_regret",
    "batch_mean_regret",
    "normalized_enrichment",
    "global_ndcg",
    "reranking_ndcg",
)


class CandidateViolation(BaseModel):
    """One Dataset- or Task-contract finding for a submitted candidate."""

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

    def with_violation(self, violation: CandidateViolation) -> CandidateValidationReport:
        """Return a report with one additional immutable finding."""

        return self.model_copy(
            update={"violations": self.violations + (violation,)}
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
    """Structured evaluation of one ordered candidate submission."""

    expected_candidates: int = Field(ge=1)
    submitted_candidates: int = Field(ge=0)
    valid_candidates: int = Field(ge=0)
    invalid_candidates: int = Field(ge=0)
    score_field: str = Field(min_length=1)
    aggregation: Literal["max", "candidate_metrics"] = "max"
    summary_size: int = Field(default=1, ge=1)
    reference_scope: ReferenceScope | None = None
    reference_size: int | None = Field(default=None, ge=1)
    best_candidate_index: int | None = Field(default=None, ge=0)
    best_objective_output: dict[str, Any] | None = None
    candidates: tuple[CandidateEvaluation, ...] = ()

    @computed_field
    @property
    def all_candidates_valid(self) -> bool:
        return self.submission_valid and self.invalid_candidates == 0

    @computed_field
    @property
    def evaluation_eligible(self) -> bool:
        """Whether the submission produced comparable aggregate metrics."""

        return self.all_candidates_valid and bool(self.metrics)


class DesignBenchBlackBoxOptimizationTask(
    ObjectiveBackedTask[
        AgentInputT,
        Iterable[Candidate],
        BlackBoxOptimizationEvaluation,
    ],
    Generic[AgentInputT],
):
    """Evaluate an ordered, fixed-size batch against a trusted reference."""

    default_submission_size = 128
    default_primary_metric = "best_k_mean"

    def __init__(
        self,
        dataset: Dataset,
        protocol: Protocol[AgentInputT],
        objective: Objective,
        *,
        score_field: str,
        reference_scores: Iterable[Real],
        reference_scope: ReferenceScope,
        submission_size: int = default_submission_size,
        primary_metric: str | None = None,
        objective_direction: MetricDirection = "maximize",
    ) -> None:
        if not score_field.strip():
            raise TaskError("score_field must be a non-empty string")
        if score_field not in objective.output_fields:
            raise TaskError(
                f"score field {score_field!r} is not returned by the Objective"
            )
        if (
            isinstance(submission_size, bool)
            or not isinstance(submission_size, int)
            or submission_size < 1
        ):
            raise TaskError("submission_size must be a positive integer")
        selected_primary = primary_metric or self.default_primary_metric
        if selected_primary not in COMMON_METRICS:
            raise TaskError(
                f"primary_metric must be one of {COMMON_METRICS}, "
                f"got {selected_primary!r}"
            )

        reference = tuple(_finite_score(value, "reference score") for value in reference_scores)
        if len(reference) < submission_size:
            raise TaskError(
                f"reference contains {len(reference)} scores but submission_size "
                f"is {submission_size}"
            )
        reference_utilities = tuple(
            _utility(value, objective_direction) for value in reference
        )
        if min(reference_utilities) == max(reference_utilities):
            raise TaskError("reference scores must have non-zero utility range")
        ideal_batch_mean = _mean(
            sorted(reference_utilities, reverse=True)[:submission_size]
        )
        reference_mean = _mean(reference_utilities)
        if ideal_batch_mean == reference_mean:
            raise TaskError(
                "reference cannot normalize batch enrichment at this submission_size"
            )

        self._score_field = score_field
        self._submission_size = submission_size
        self._summary_size = min(5, submission_size)
        self._primary_metric = selected_primary
        self._objective_direction = objective_direction
        self._reference_scope = reference_scope
        self._reference_scores = reference
        self._reference_utilities = reference_utilities
        super().__init__(dataset, protocol, objective)

    @property
    def score_field(self) -> str:
        return self._score_field

    @property
    def submission_size(self) -> int:
        return self._submission_size

    @property
    def expected_candidates(self) -> int:
        """Required candidate count for one submission."""

        return self.submission_size

    @property
    def summary_size(self) -> int:
        return self._summary_size

    @property
    def primary_metric(self) -> str:
        return self._primary_metric

    @property
    def objective_direction(self) -> MetricDirection:
        return self._objective_direction

    @property
    def reference_scope(self) -> ReferenceScope:
        return self._reference_scope

    @property
    def metric_directions(self) -> dict[str, MetricDirection]:
        raw = {
            "best_score": self.objective_direction,
            "rank_1_score": self.objective_direction,
            "best_k_mean": self.objective_direction,
            "prefix_k_mean": self.objective_direction,
            "batch_mean": self.objective_direction,
        }
        return {
            **raw,
            "best_regret": "minimize",
            "best_k_mean_regret": "minimize",
            "batch_mean_regret": "minimize",
            "normalized_enrichment": "maximize",
            "global_ndcg": "maximize",
            "reranking_ndcg": "maximize",
        }

    def evaluate(
        self,
        submission: Iterable[Candidate],
    ) -> BlackBoxOptimizationEvaluation:
        candidate_batch, submission_report = self._validate_submission(submission)
        if not submission_report.valid:
            return self._build_evaluation(
                submission_report,
                submitted_candidates=len(candidate_batch),
            )

        reports = [
            self._validate_candidate(
                candidate,
                CandidateValidationReport.from_dataset_report(
                    self.dataset.validate_inputs(candidate)
                ),
            )
            for candidate in candidate_batch
        ]
        self._mark_duplicates(candidate_batch, reports)

        valid_pairs = tuple(
            (index, candidate)
            for index, (candidate, report) in enumerate(
                zip(candidate_batch, reports, strict=True)
            )
            if report.valid
        )
        outputs = (
            self.objective.evaluate_batch(candidate for _, candidate in valid_pairs)
            if valid_pairs
            else ()
        )

        evaluated: dict[int, tuple[float, dict[str, Any]]] = {}
        for (index, _), output in zip(valid_pairs, outputs, strict=True):
            score = _finite_score(
                output[self.score_field],
                f"Objective score field {self.score_field!r}",
            )
            evaluated[index] = (score, dict(output))

        candidates = tuple(
            CandidateEvaluation(
                index=index,
                validation=report,
                score=evaluated[index][0] if index in evaluated else None,
                objective_output=evaluated[index][1] if index in evaluated else None,
            )
            for index, report in enumerate(reports)
        )
        valid = tuple(item for item in candidates if item.valid)
        best = self._best_candidate(valid)
        metrics = (
            self._calculate_metrics(tuple(item.score for item in valid))
            if len(valid) == self.submission_size
            else {}
        )
        return self._build_evaluation(
            submission_report,
            submitted_candidates=len(candidate_batch),
            candidates=candidates,
            metrics=metrics,
            best=best,
        )

    def _validate_candidate(
        self,
        candidate: Candidate,
        report: CandidateValidationReport,
    ) -> CandidateValidationReport:
        """Add Task-specific candidate findings after Dataset validation."""

        return report

    def _candidate_identity(self, candidate: Candidate) -> Hashable:
        """Return the identity used to reject repeated submitted candidates."""

        return _freeze(candidate)

    def _mark_duplicates(
        self,
        candidates: Sequence[Candidate],
        reports: list[CandidateValidationReport],
    ) -> None:
        seen: dict[Hashable, int] = {}
        for index, (candidate, report) in enumerate(
            zip(candidates, reports, strict=True)
        ):
            if not report.valid:
                continue
            identity = self._candidate_identity(candidate)
            if identity in seen:
                reports[index] = report.with_violation(
                    CandidateViolation(
                        code="duplicate_candidate",
                        message=(
                            "candidate duplicates the canonical identity at index "
                            f"{seen[identity]}"
                        ),
                    )
                )
            else:
                seen[identity] = index

    def _best_candidate(
        self,
        candidates: tuple[CandidateEvaluation, ...],
    ) -> CandidateEvaluation | None:
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda item: _utility(item.score, self.objective_direction),
        )

    def _calculate_metrics(self, scores: tuple[float, ...]) -> dict[str, float]:
        utilities = tuple(
            _utility(score, self.objective_direction) for score in scores
        )
        best_indices = sorted(
            range(len(scores)),
            key=utilities.__getitem__,
            reverse=True,
        )
        best_index = best_indices[0]
        best_k_indices = best_indices[: self.summary_size]
        reference_descending = sorted(self._reference_utilities, reverse=True)

        reference_best = reference_descending[0]
        reference_best_k_mean = _mean(
            reference_descending[: self.summary_size]
        )
        reference_batch_mean = _mean(
            reference_descending[: self.submission_size]
        )
        reference_mean = _mean(self._reference_utilities)
        submitted_mean_utility = _mean(utilities)

        minimum = min(self._reference_utilities)
        maximum = max(self._reference_utilities)
        span = maximum - minimum
        gains = tuple((utility - minimum) / span for utility in utilities)
        reference_gains = tuple(
            (utility - minimum) / span for utility in reference_descending
        )
        global_ideal_dcg = _dcg(reference_gains[: self.submission_size])
        reranking_ideal_dcg = _dcg(sorted(gains, reverse=True))
        actual_dcg = _dcg(gains)

        return {
            "best_score": scores[best_index],
            "rank_1_score": scores[0],
            "best_k_mean": _mean(tuple(scores[index] for index in best_k_indices)),
            "prefix_k_mean": _mean(scores[: self.summary_size]),
            "batch_mean": _mean(scores),
            "best_regret": max(0.0, reference_best - max(utilities)),
            "best_k_mean_regret": max(
                0.0,
                reference_best_k_mean
                - _mean(tuple(utilities[index] for index in best_k_indices)),
            ),
            "batch_mean_regret": max(
                0.0, reference_batch_mean - submitted_mean_utility
            ),
            "normalized_enrichment": (
                (submitted_mean_utility - reference_mean)
                / (reference_batch_mean - reference_mean)
            ),
            "global_ndcg": actual_dcg / global_ideal_dcg,
            "reranking_ndcg": (
                actual_dcg / reranking_ideal_dcg
                if reranking_ideal_dcg > 0.0
                else 0.0
            ),
        }

    def _validate_submission(
        self,
        submission: Iterable[Candidate],
    ) -> tuple[tuple[Any, ...], SubmissionValidationReport]:
        if isinstance(submission, (str, bytes, bytearray, Mapping)):
            return (), _invalid_submission_type()
        try:
            candidate_batch = tuple(submission)
        except TypeError:
            return (), _invalid_submission_type()

        if len(candidate_batch) != self.submission_size:
            return candidate_batch, SubmissionValidationReport(
                violations=(
                    SubmissionViolation(
                        code="candidate_count_mismatch",
                        message=(
                            f"expected {self.submission_size} candidates, "
                            f"got {len(candidate_batch)}"
                        ),
                    ),
                )
            )
        return candidate_batch, SubmissionValidationReport()

    def _build_evaluation(
        self,
        report: SubmissionValidationReport,
        *,
        submitted_candidates: int,
        candidates: tuple[CandidateEvaluation, ...] = (),
        metrics: dict[str, float] | None = None,
        best: CandidateEvaluation | None = None,
    ) -> BlackBoxOptimizationEvaluation:
        produced_metrics = metrics or {}
        valid_count = sum(item.valid for item in candidates)
        return BlackBoxOptimizationEvaluation(
            task_id=self.task_id,
            submission_validation=report,
            metrics=produced_metrics,
            metric_directions=self.metric_directions,
            primary_metric=self.primary_metric,
            metric_direction=self.metric_directions[self.primary_metric],
            expected_candidates=self.submission_size,
            submitted_candidates=submitted_candidates,
            valid_candidates=valid_count,
            invalid_candidates=len(candidates) - valid_count,
            score_field=self.score_field,
            aggregation="candidate_metrics",
            summary_size=self.summary_size,
            reference_scope=self.reference_scope,
            reference_size=len(self._reference_scores),
            best_candidate_index=best.index if best is not None else None,
            best_objective_output=(
                best.objective_output if best is not None else None
            ),
            candidates=candidates,
        )


def _invalid_submission_type() -> SubmissionValidationReport:
    return SubmissionValidationReport(
        violations=(
            SubmissionViolation(
                code="invalid_submission_type",
                message="submission must be an iterable of candidates",
            ),
        )
    )


def _finite_score(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TaskError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise TaskError(f"{label} must be finite")
    return result


def _utility(score: float | None, direction: MetricDirection) -> float:
    if score is None:
        raise TaskError("cannot calculate utility for a missing score")
    return score if direction == "maximize" else -score


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise TaskError("cannot calculate the mean of an empty score sequence")
    return math.fsum(values) / len(values)


def _dcg(gains: Sequence[float]) -> float:
    return math.fsum(
        gain / math.log2(index + 2)
        for index, gain in enumerate(gains)
    )


def _freeze(value: Any) -> Hashable:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, (str, bytes, int, float, bool, type(None))):
        return value
    if isinstance(value, Sequence):
        return tuple(_freeze(item) for item in value)
    to_list = getattr(value, "tolist", None)
    if callable(to_list):
        return _freeze(to_list())
    if isinstance(value, Hashable):
        return value
    raise TaskError(f"candidate value of type {type(value).__name__} has no stable identity")
