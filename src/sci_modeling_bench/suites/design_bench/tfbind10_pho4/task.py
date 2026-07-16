"""Count-grounded black-box optimization Task for Pho4 TFBind10."""

from __future__ import annotations

from sci_modeling_bench.objective import Candidate
from sci_modeling_bench.suites.design_bench.black_box_optimization import (
    CandidateValidationReport,
    CandidateViolation,
    DesignBenchBlackBoxOptimizationTask,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.dataset import (
    DEFAULT_TFBIND10_PHO4_REPO_ID,
    TFBIND10_PHO4_CONFIG_NAME,
    TFBind10Pho4Dataset,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.objective import (
    TFBind10Pho4PosteriorObjective,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.protocol import (
    TFBind10Pho4AgentInput,
    TFBind10Pho4LowerHalfProtocol,
)


class TFBind10Pho4BlackBoxOptimizationTask(
    DesignBenchBlackBoxOptimizationTask[TFBind10Pho4AgentInput]
):
    """Select a high-affinity batch from the label-hidden upper-half pool."""

    task_id = "design-bench/tfbind10-pho4-black-box-optimization-v1"
    default_primary_metric = "normalized_enrichment"

    def __init__(
        self,
        dataset: TFBind10Pho4Dataset,
        *,
        protocol: TFBind10Pho4LowerHalfProtocol | None = None,
        objective: TFBind10Pho4PosteriorObjective | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> None:
        selected_objective = objective or TFBind10Pho4PosteriorObjective(dataset)
        selected_protocol = protocol or TFBind10Pho4LowerHalfProtocol()
        candidate_pool = selected_protocol.candidate_pool(
            dataset,
            split=selected_objective.split,
            score_table=selected_objective.score_table(),
        )
        self._candidate_pool_ids = frozenset(candidate_pool["sequence"])
        super().__init__(
            dataset,
            selected_protocol,
            selected_objective,
            score_field="affinity_score",
            reference_scores=candidate_pool["affinity_score"],
            reference_scope="evaluation_pool",
            submission_size=submission_size,
            primary_metric=primary_metric,
        )

    def _validate_candidate(
        self,
        candidate: Candidate,
        report: CandidateValidationReport,
    ) -> CandidateValidationReport:
        if report.valid and candidate["sequence"] not in self._candidate_pool_ids:
            return report.with_violation(
                CandidateViolation(
                    code="candidate_outside_evaluation_pool",
                    field="sequence",
                    message="sequence is not in the label-hidden upper-half pool",
                )
            )
        return report

    def _candidate_identity(self, candidate: Candidate) -> str:
        return str(candidate["sequence"])

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_TFBIND10_PHO4_REPO_ID,
        config_name: str | None = TFBIND10_PHO4_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> TFBind10Pho4BlackBoxOptimizationTask:
        dataset = TFBind10Pho4Dataset.from_hub(
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
