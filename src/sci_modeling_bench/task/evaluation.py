"""Task-level submission validation and evaluation results."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class SubmissionViolation(BaseModel):
    """One finding about the structure of an entire submission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    severity: Literal["error", "warning"] = "error"


class SubmissionValidationReport(BaseModel):
    """Validation result for a complete Task submission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    violations: tuple[SubmissionViolation, ...] = ()

    @computed_field
    @property
    def valid(self) -> bool:
        """Whether the submission has no error-severity violations."""

        return not any(item.severity == "error" for item in self.violations)


class SubmissionEvaluation(BaseModel):
    """Common metric and validation envelope returned by every Task."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    task_id: str = Field(min_length=1)
    submission_validation: SubmissionValidationReport
    metrics: dict[str, float]
    metric_directions: dict[str, Literal["maximize", "minimize"]] = Field(
        default_factory=dict
    )
    primary_metric: str = Field(min_length=1)
    metric_direction: Literal["maximize", "minimize"]

    @computed_field
    @property
    def submission_valid(self) -> bool:
        """Whether the top-level submission contract was satisfied."""

        return self.submission_validation.valid

    @computed_field
    @property
    def score(self) -> float | None:
        """Return the primary metric value when one was produced."""

        return self.metrics.get(self.primary_metric)
