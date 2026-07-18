"""Measured-pool compositional ranking Task for UTR MRL."""

from __future__ import annotations

from collections.abc import Hashable

from sci_modeling_bench.objective import Candidate
from sci_modeling_bench.task import CandidatePoolRankingTask
from sci_modeling_bench.suites.design_bench.utr_mrl.dataset import (
    DEFAULT_UTR_MRL_REPO_ID,
    UTR_MRL_CONFIG_NAME,
    UTRMRLDataset,
)
from sci_modeling_bench.suites.design_bench.utr_mrl.objective import (
    UTRMRLMeasuredObjective,
)
from sci_modeling_bench.suites.design_bench.utr_mrl.protocol import (
    UTRMRLAgentInput,
    UTRMRLCompositionalProtocol,
)


class UTRMRLCompositionalRankingTask(
    CandidatePoolRankingTask[UTRMRLAgentInput]
):
    """Select and prioritize the held-out measured biological combination."""

    task_id = "design-bench/utr-mrl-egfp-unmodified-compositional-ranking-v1"
    default_primary_metric = "global_ndcg"

    def __init__(
        self,
        dataset: UTRMRLDataset,
        *,
        protocol: UTRMRLCompositionalProtocol | None = None,
        objective: UTRMRLMeasuredObjective | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> None:
        selected_protocol = protocol or UTRMRLCompositionalProtocol()
        selected_objective = objective or UTRMRLMeasuredObjective(dataset)
        candidate_pool = selected_protocol.candidate_pool(
            dataset,
            split=selected_objective.split,
        )
        super().__init__(
            dataset,
            selected_protocol,
            selected_objective,
            candidate_pool=(
                {"sequence": sequence}
                for sequence in candidate_pool["sequence"]
            ),
            score_field="mean_ribosome_load",
            reference_scores=candidate_pool["mean_ribosome_load"],
            reference_scope="evaluation_pool",
            submission_size=submission_size,
            primary_metric=primary_metric,
        )

    def _candidate_identity(self, candidate: Candidate) -> Hashable:
        return str(candidate["sequence"])

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_UTR_MRL_REPO_ID,
        config_name: str | None = UTR_MRL_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> UTRMRLCompositionalRankingTask:
        dataset = UTRMRLDataset.from_hub(
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
