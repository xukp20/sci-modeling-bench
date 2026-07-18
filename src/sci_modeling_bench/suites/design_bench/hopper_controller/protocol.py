"""Lower-score observation and candidate-pool Protocol for Hopper policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from datasets import Dataset as HFDataset

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import (
    AgentInputBundle,
    AgentInputContext,
    AgentInputField,
    Protocol,
    agent_input_field,
    agent_input_manifest,
    agent_table_view,
)
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
    ) -> AgentInputBundle[HopperControllerAgentInput]:
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
        data = HopperControllerAgentInput(
            observations=observations,
            candidates=candidates,
        )
        selected_split = split or HOPPER_CONTROLLER_DEFAULT_SPLIT
        return AgentInputBundle(
            data=data,
            manifest=agent_input_manifest(
                dataset,
                protocol_id=self.protocol_id,
                split=selected_split,
                views=(
                    agent_table_view(
                        dataset,
                        data.observations,
                        name="observations",
                        role="observations",
                        description=(
                            "Lower-score Hopper policies with every frozen stochastic "
                            "rollout outcome exposed."
                        ),
                        overrides=_observation_view_fields(data.observations),
                    ),
                    agent_table_view(
                        dataset,
                        data.candidates,
                        name="candidates",
                        role="candidates",
                        description=(
                            "Label-hidden Hopper policy parameter vectors available for ranking."
                        ),
                    ),
                ),
                context=_policy_context(data),
            ),
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


def _observation_view_fields(data: HFDataset) -> dict[str, AgentInputField]:
    return {
        "raw_returns": agent_input_field(
            data,
            "raw_returns",
            role="target",
            description="Frozen episodic return from each stochastic policy rollout.",
            source_field="raw_returns",
        ),
        "episode_lengths": agent_input_field(
            data,
            "episode_lengths",
            role="context",
            description="Episode length paired with each frozen rollout return.",
            unit="environment steps",
            source_field="episode_lengths",
        ),
        "terminated": agent_input_field(
            data,
            "terminated",
            role="context",
            description="Whether each frozen rollout ended by environment termination.",
            source_field="terminated",
        ),
        "truncated": agent_input_field(
            data,
            "truncated",
            role="context",
            description="Whether each frozen rollout ended at the time limit.",
            source_field="truncated",
        ),
    }


def _policy_context(data: HopperControllerAgentInput) -> tuple[AgentInputContext, ...]:
    return (
        AgentInputContext(
            name="policy_layers",
            description="Policy-network layer widths from observation to action.",
            value=list(data.policy_layers),
        ),
        AgentInputContext(
            name="parameter_order",
            description="Flattened parameter-block order used by policy_weights.",
            value=list(data.parameter_order),
        ),
        AgentInputContext(
            name="hidden_activation",
            description="Activation function used by both hidden policy layers.",
            value=data.hidden_activation,
        ),
        AgentInputContext(
            name="action_distribution",
            description="Distribution used to sample continuous actions.",
            value=data.action_distribution,
        ),
        AgentInputContext(
            name="action_clip",
            description="Inclusive lower and upper clipping bounds for sampled actions.",
            value=list(data.action_clip),
        ),
        AgentInputContext(
            name="environment_id",
            description="Frozen Gymnasium environment identity used for rollouts.",
            value=data.environment_id,
        ),
        AgentInputContext(
            name="rollout_count",
            description="Number of frozen stochastic rollouts per policy.",
            value=data.rollout_count,
        ),
        AgentInputContext(
            name="target_aggregation",
            description="Aggregation defining the trusted policy score.",
            value=data.target_aggregation,
        ),
    )
