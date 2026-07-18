"""Minimal Protocol contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sci_modeling_bench.dataset.dataset import Dataset
from sci_modeling_bench.protocol.agent_input import AgentInputBundle

ProtocolDataT = TypeVar("ProtocolDataT")
# Backward-compatible name for callers that imported the former output type.
ProtocolOutputT = ProtocolDataT


class Protocol(ABC, Generic[ProtocolDataT]):
    """Build one typed Agent input from a complete Dataset."""

    protocol_id: str

    @abstractmethod
    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> AgentInputBundle[ProtocolDataT]:
        """Construct the Agent-visible input without mutating the Dataset."""
