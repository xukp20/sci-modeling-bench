"""Minimal Protocol contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sci_modeling_bench.dataset.dataset import Dataset

ProtocolOutputT = TypeVar("ProtocolOutputT")


class Protocol(ABC, Generic[ProtocolOutputT]):
    """Build one typed Agent input from a complete Dataset."""

    protocol_id: str

    @abstractmethod
    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> ProtocolOutputT:
        """Construct the Agent-visible input without mutating the Dataset."""
