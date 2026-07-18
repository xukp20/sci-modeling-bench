"""Lower-score observation and candidate-pool Protocol for Hopper policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import Protocol
from sci_modeling_bench.suites.design_bench.hopper_controller.dataset import (
    EXPECTED_ROLLOUT_COUNT,
    HOPPER_CONTROLLER_DEFAULT_SPLIT,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.simulator import (
    ACTION_SIZE,
    ENVIRONMENT_ID,
    HIDDEN_SIZE,
    OBSERVATION_SIZE,
)

_DATASET_ID = "design-bench/hopper-controller"
_PARAMETER_ORDER = ("W1", "b1", "W2", "b2", "W3", "b3", "logstd")


@dataclass(frozen=True)
class HopperControllerAgentInput:
    """Raw lower-score rollouts and label-hidden policy candidates."""

    observations: HFDataset
    candidates: HFDataset
    policy_layers: tuple[int, ...] = (
        OBSERVATION_SIZE,
        HIDDEN_SIZE,
        HIDDEN_SIZE,
        ACTION_SIZE,
    )
    parameter_order: tuple[str, ...] = _PARAMETER_ORDER
    hidden_activation: str = "tanh"
    action_distribution: str = "Gaussian with learned logstd"
    action_clip: tuple[float, float] = (-1.0, 1.0)
    environment_id: str = ENVIRONMENT_ID
    rollout_count: int = EXPECTED_ROLLOUT_COUNT
    target_aggregation: str = "arithmetic mean episodic return"


@dataclass(frozen=True)
class HopperControllerLowerScoreProtocol(Protocol[HopperControllerAgentInput]):
    """Expose the lower 60% policies and hide labels for the upper 40%."""

    protocol_id: ClassVar[str] = "design-bench/hopper-controller-lower-score-v1"
    visible_fraction: float = 0.60

    def __post_init__(self) -> None:
        if not 0.0 < self.visible_fraction < 1.0:
            raise ProtocolError("visible_fraction must be in the interval (0, 1)")

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> HopperControllerAgentInput:
        policies = self._load_policies(dataset, split)
        visible_indices, candidate_indices, _ = self.partition(policies)
        identities = policies["policy_identity"]
        visible_indices.sort(key=lambda index: identities[index])
        candidate_indices.sort(key=lambda index: identities[index])
        observations = policies.select(visible_indices).select_columns(
            [
                "policy_weights",
                "raw_returns",
                "episode_lengths",
                "terminated",
                "truncated",
            ]
        )
        candidates = policies.select(candidate_indices).select_columns(
            ["policy_weights"]
        )
        return HopperControllerAgentInput(
            observations=observations,
            candidates=candidates,
        )

    def candidate_pool(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> HFDataset:
        """Return the trusted labeled upper-score evaluation pool."""

        policies = self._load_policies(dataset, split)
        _, candidate_indices, _ = self.partition(policies)
        identities = policies["policy_identity"]
        candidate_indices.sort(key=lambda index: identities[index])
        return policies.select(candidate_indices)

    def partition(
        self,
        policies: HFDataset,
    ) -> tuple[list[int], list[int], float]:
        means = np.asarray(policies["mean_return"], dtype=np.float64)
        if means.ndim != 1 or means.size == 0 or not np.all(np.isfinite(means)):
            raise ProtocolError("mean_return must be a non-empty finite scalar column")
        identities = policies["policy_identity"]
        if len(set(identities)) != len(identities):
            raise ProtocolError("policy_identity must be unique")
        visible_count = int(np.floor(len(policies) * self.visible_fraction))
        if visible_count == 0 or visible_count == len(policies):
            raise ProtocolError("visible_fraction produced an empty partition")
        order = sorted(
            range(len(policies)),
            key=lambda index: (float(means[index]), identities[index]),
        )
        visible = order[:visible_count]
        candidates = order[visible_count:]
        return visible, candidates, float(means[order[visible_count - 1]])

    def _load_policies(self, dataset: Dataset, split: str | None) -> HFDataset:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ProtocolError(
                f"HopperControllerLowerScoreProtocol requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        selected_split = split or HOPPER_CONTROLLER_DEFAULT_SPLIT
        try:
            policies = dataset.load(selected_split)
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc
        required = {
            "policy_identity",
            "policy_weights",
            "raw_returns",
            "episode_lengths",
            "terminated",
            "truncated",
            "mean_return",
        }
        missing = sorted(required - set(policies.column_names))
        if missing:
            raise ProtocolError(f"Hopper Controller split is missing columns: {missing}")
        return policies
