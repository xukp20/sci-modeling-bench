"""Candidate-pool ranking Task for stochastic Hopper controllers."""

from __future__ import annotations

from collections.abc import Hashable

from sci_modeling_bench.objective import Candidate
from sci_modeling_bench.task import CandidatePoolRankingTask
from sci_modeling_bench.suites.design_bench.hopper_controller.dataset import (
    DEFAULT_HOPPER_CONTROLLER_REPO_ID,
    DEFAULT_HOPPER_CONTROLLER_REVISION,
    HOPPER_CONTROLLER_CONFIG_NAME,
    HopperControllerDataset,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.objective import (
    HopperControllerMeasuredObjective,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.protocol import (
    HopperControllerAgentInput,
    HopperControllerLowerScoreProtocol,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.simulator import (
    policy_identity,
)


class HopperControllerCandidatePoolRankingTask(
    CandidatePoolRankingTask[HopperControllerAgentInput]
):
    """Select and rank high-return policies from the frozen candidate pool."""

    task_id = "design-bench/hopper-controller-candidate-pool-ranking-v1"
    default_primary_metric = "global_ndcg"

    def __init__(
        self,
        dataset: HopperControllerDataset,
        *,
        protocol: HopperControllerLowerScoreProtocol | None = None,
        objective: HopperControllerMeasuredObjective | None = None,
        submission_size: int = 32,
        primary_metric: str | None = None,
    ) -> None:
        selected_protocol = protocol or HopperControllerLowerScoreProtocol()
        selected_objective = objective or HopperControllerMeasuredObjective(dataset)
        candidate_pool = selected_protocol.candidate_pool(
            dataset, split=selected_objective.split
        )
        super().__init__(
            dataset,
            selected_protocol,
            selected_objective,
            candidate_pool=(
                {"policy_weights": weights}
                for weights in candidate_pool["policy_weights"]
            ),
            score_field="mean_return",
            reference_scores=candidate_pool["mean_return"],
            reference_scope="evaluation_pool",
            submission_size=submission_size,
            primary_metric=primary_metric,
        )

    def _candidate_identity(self, candidate: Candidate) -> Hashable:
        return policy_identity(candidate["policy_weights"])

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_HOPPER_CONTROLLER_REPO_ID,
        config_name: str | None = HOPPER_CONTROLLER_CONFIG_NAME,
        revision: str | None = DEFAULT_HOPPER_CONTROLLER_REVISION,
        *,
        token: str | None = None,
        submission_size: int = 32,
        primary_metric: str | None = None,
    ) -> HopperControllerCandidatePoolRankingTask:
        dataset = HopperControllerDataset.from_hub(
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
