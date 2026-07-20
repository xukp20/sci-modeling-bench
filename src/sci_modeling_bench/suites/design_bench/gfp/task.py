"""Measured-pool candidate-ranking Task for Sarkisyan GFP."""

from __future__ import annotations

from collections.abc import Hashable

from sci_modeling_bench.objective import Candidate
from sci_modeling_bench.task import CandidatePoolRankingTask
from sci_modeling_bench.suites.design_bench.gfp.dataset import (
    DEFAULT_GFP_REPO_ID,
    GFP_CONFIG_NAME,
    GFPDataset,
)
from sci_modeling_bench.suites.design_bench.gfp.objective import (
    GFPMeasuredObjective,
)
from sci_modeling_bench.suites.design_bench.gfp.protocol import (
    GFPAgentInput,
    GFPLowerToHigherMeasuredPoolProtocol,
)


class GFPCandidatePoolRankingTask(CandidatePoolRankingTask[GFPAgentInput]):
    """Select and rank measured upper-tail GFP protein candidates."""

    task_id = "design-bench/gfp-candidate-pool-ranking-v2"
    default_summary_size = 16
    default_primary_metric = "normalized_enrichment"

    def __init__(
        self,
        dataset: GFPDataset,
        *,
        protocol: GFPLowerToHigherMeasuredPoolProtocol | None = None,
        objective: GFPMeasuredObjective | None = None,
        submission_size: int = 128,
        summary_size: int | None = None,
        primary_metric: str | None = None,
    ) -> None:
        selected_protocol = protocol or GFPLowerToHigherMeasuredPoolProtocol()
        selected_objective = objective or GFPMeasuredObjective(dataset)
        candidate_pool = selected_protocol.candidate_pool(
            dataset,
            split=selected_objective.split,
        )
        super().__init__(
            dataset,
            selected_protocol,
            selected_objective,
            candidate_pool=(
                {"sequence": sequence} for sequence in candidate_pool["sequence"]
            ),
            score_field="median_log10_brightness",
            reference_scores=candidate_pool["median_log10_brightness"],
            reference_scope="evaluation_pool",
            submission_size=submission_size,
            summary_size=summary_size,
            primary_metric=primary_metric,
        )
    def _candidate_identity(self, candidate: Candidate) -> Hashable:
        return str(candidate["sequence"])

    def _candidate_for_dataset_validation(self, candidate: Candidate) -> Candidate:
        return {"sequence": candidate.get("sequence")}

    def _candidate_for_objective(self, candidate: Candidate) -> Candidate:
        return {"sequence": candidate["sequence"]}

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_GFP_REPO_ID,
        config_name: str | None = GFP_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        submission_size: int = 128,
        summary_size: int | None = None,
        primary_metric: str | None = None,
    ) -> GFPCandidatePoolRankingTask:
        dataset = GFPDataset.from_hub(
            repo_id=repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
        )
        return cls(
            dataset,
            submission_size=submission_size,
            summary_size=summary_size,
            primary_metric=primary_metric,
        )
