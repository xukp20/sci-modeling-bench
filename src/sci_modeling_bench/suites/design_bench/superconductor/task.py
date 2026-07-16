"""Measured-pool black-box optimization Task for Superconductor."""

from __future__ import annotations

from sci_modeling_bench.objective import Candidate
from sci_modeling_bench.suites.design_bench.black_box_optimization import (
    CandidateValidationReport,
    CandidateViolation,
    DesignBenchBlackBoxOptimizationTask,
)
from sci_modeling_bench.suites.design_bench.superconductor.dataset import (
    DEFAULT_SUPERCONDUCTOR_REPO_ID,
    SUPERCONDUCTOR_CONFIG_NAME,
    SuperconductorDataset,
)
from sci_modeling_bench.suites.design_bench.superconductor.objective import (
    SuperconductorMeasuredObjective,
)
from sci_modeling_bench.suites.design_bench.superconductor.protocol import (
    SuperconductorAgentInput,
    SuperconductorMeasuredPoolProtocol,
)


class SuperconductorBlackBoxOptimizationTask(
    DesignBenchBlackBoxOptimizationTask[SuperconductorAgentInput]
):
    """Select and rank measured high-Tc composition groups."""

    task_id = "design-bench/superconductor-measured-pool-optimization-v1"
    default_primary_metric = "global_ndcg"

    def __init__(
        self,
        dataset: SuperconductorDataset,
        *,
        protocol: SuperconductorMeasuredPoolProtocol | None = None,
        objective: SuperconductorMeasuredObjective | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> None:
        selected_protocol = protocol or SuperconductorMeasuredPoolProtocol()
        selected_objective = objective or SuperconductorMeasuredObjective(dataset)
        candidate_pool = selected_protocol.candidate_pool(
            dataset, split=selected_objective.split
        )
        self._candidate_pool_ids = frozenset(candidate_pool["composition_id"])
        super().__init__(
            dataset,
            selected_protocol,
            selected_objective,
            score_field="critical_temp_k",
            reference_scores=candidate_pool["critical_temp_k"],
            reference_scope="evaluation_pool",
            submission_size=submission_size,
            primary_metric=primary_metric,
        )

    def _validate_candidate(
        self,
        candidate: Candidate,
        report: CandidateValidationReport,
    ) -> CandidateValidationReport:
        if report.valid and candidate["composition_id"] not in self._candidate_pool_ids:
            return report.with_violation(
                CandidateViolation(
                    code="candidate_outside_evaluation_pool",
                    field="composition_id",
                    message="composition_id is not in the label-hidden candidate pool",
                )
            )
        return report

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_SUPERCONDUCTOR_REPO_ID,
        config_name: str | None = SUPERCONDUCTOR_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> SuperconductorBlackBoxOptimizationTask:
        dataset = SuperconductorDataset.from_hub(
            repo_id=repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
        )
        return cls(
            dataset,
            submission_size=submission_size,
            primary_metric=primary_metric,
        )
