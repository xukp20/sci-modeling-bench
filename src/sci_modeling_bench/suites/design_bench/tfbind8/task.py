"""Default Design-Bench black-box optimization Task for TFBind8."""

from __future__ import annotations

from datasets import Dataset as HFDataset

from sci_modeling_bench.task import BlackBoxOptimizationTask
from sci_modeling_bench.suites.design_bench.tfbind8.dataset import (
    DEFAULT_TFBIND8_REPO_ID,
    TFBIND8_CONFIG_NAME,
    TFBind8Dataset,
)
from sci_modeling_bench.suites.design_bench.tfbind8.objective import (
    TFBind8ExactObjective,
)
from sci_modeling_bench.suites.design_bench.tfbind8.protocol import (
    TFBind8DesignBenchProtocol,
)


class TFBind8BlackBoxOptimizationTask(
    BlackBoxOptimizationTask[HFDataset]
):
    """Expose offline TFBind8 data and evaluate an ordered candidate batch."""

    task_id = "design-bench/tfbind8-black-box-optimization-v2"
    default_primary_metric = "best_k_mean"

    def __init__(
        self,
        dataset: TFBind8Dataset,
        *,
        protocol: TFBind8DesignBenchProtocol | None = None,
        objective: TFBind8ExactObjective | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> None:
        selected_objective = objective or TFBind8ExactObjective(dataset)
        observations = dataset.load(selected_objective.split)
        super().__init__(
            dataset,
            protocol or TFBind8DesignBenchProtocol(),
            selected_objective,
            score_field="normalized_e_score",
            reference_scores=observations["normalized_e_score"],
            reference_scope="full_domain",
            submission_size=submission_size,
            primary_metric=primary_metric,
        )

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_TFBIND8_REPO_ID,
        config_name: str | None = TFBIND8_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        submission_size: int = 128,
        primary_metric: str | None = None,
    ) -> TFBind8BlackBoxOptimizationTask:
        """Construct the default Task from a Hugging Face Dataset revision."""

        dataset = TFBind8Dataset.from_hub(
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
