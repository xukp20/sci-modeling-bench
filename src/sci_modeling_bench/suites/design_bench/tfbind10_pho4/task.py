"""Count-grounded black-box optimization Task for Pho4 TFBind10."""

from __future__ import annotations

from datasets import Dataset as HFDataset

from sci_modeling_bench.objective import Candidate
from sci_modeling_bench.task import BlackBoxOptimizationTask
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.dataset import (
    DEFAULT_TFBIND10_PHO4_REPO_ID,
    TFBIND10_PHO4_CONFIG_NAME,
    TFBind10Pho4Dataset,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.objective import (
    TFBind10Pho4PosteriorObjective,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.protocol import (
    TFBind10Pho4LowerHalfProtocol,
)


class TFBind10Pho4BlackBoxOptimizationTask(
    BlackBoxOptimizationTask[HFDataset]
):
    """Evaluate a high-affinity batch over the complete DNA 10-mer domain."""

    task_id = "design-bench/tfbind10-pho4-black-box-optimization-v2"
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
        landscape = selected_objective.landscape
        self._landscape = landscape
        self._tfbind10_protocol = selected_protocol
        super().__init__(
            dataset,
            selected_protocol,
            selected_objective,
            score_field="affinity_score",
            reference_scores=landscape.scores[landscape.observed],
            reference_scope="full_domain",
            submission_size=submission_size,
            primary_metric=primary_metric,
        )

    def _candidate_identity(self, candidate: Candidate) -> str:
        return str(candidate["sequence"])

    def build_input(self) -> HFDataset:
        """Build the visible rows without recomputing the Objective landscape."""

        return self._tfbind10_protocol.build_input(
            self.dataset,
            split=self.objective.split,
            landscape=self._landscape,
        )

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
