"""Hopper Controller Dataset and candidate-pool ranking Task."""

from sci_modeling_bench.suites.design_bench.hopper_controller.dataset import (
    DEFAULT_HOPPER_CONTROLLER_REPO_ID,
    DEFAULT_HOPPER_CONTROLLER_REVISION,
    DEFAULT_HOPPER_CONTROLLER_SOURCE,
    EXPECTED_POLICY_COUNT,
    EXPECTED_ROLLOUT_COUNT,
    HOPPER_CONTROLLER_CONFIG_NAME,
    HOPPER_CONTROLLER_DEFAULT_SPLIT,
    HopperControllerDataset,
    HopperControllerValidator,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.objective import (
    HopperControllerMeasuredObjective,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.protocol import (
    HopperControllerAgentInput,
    HopperControllerLowerScoreProtocol,
)

from sci_modeling_bench.suites.design_bench.hopper_controller.simulator import (
    POLICY_SIZE,
    canonical_policy,
    policy_identity,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.task import (
    HopperControllerCandidatePoolRankingTask,
)

__all__ = [
    "DEFAULT_HOPPER_CONTROLLER_REPO_ID",
    "DEFAULT_HOPPER_CONTROLLER_REVISION",
    "DEFAULT_HOPPER_CONTROLLER_SOURCE",
    "EXPECTED_POLICY_COUNT",
    "EXPECTED_ROLLOUT_COUNT",
    "HOPPER_CONTROLLER_CONFIG_NAME",
    "HOPPER_CONTROLLER_DEFAULT_SPLIT",
    "HopperControllerAgentInput",
    "HopperControllerCandidatePoolRankingTask",
    "HopperControllerDataset",
    "HopperControllerLowerScoreProtocol",
    "HopperControllerMeasuredObjective",
    "HopperControllerValidator",
    "POLICY_SIZE",
    "canonical_policy",
    "policy_identity",
]
