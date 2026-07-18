"""Minimal Task contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import TaskError
from sci_modeling_bench.objective import Objective
from sci_modeling_bench.protocol import AgentInputBundle, Protocol
from sci_modeling_bench.task.evaluation import SubmissionEvaluation

AgentInputT = TypeVar("AgentInputT")
SubmissionT = TypeVar("SubmissionT")
EvaluationT = TypeVar("EvaluationT", bound=SubmissionEvaluation)


class Task(ABC, Generic[AgentInputT, SubmissionT, EvaluationT]):
    """Bind trusted data and an Agent-visible Protocol to evaluation semantics."""

    task_id: str

    def __init__(self, dataset: Dataset, protocol: Protocol[AgentInputT]) -> None:
        if not getattr(self, "task_id", "").strip():
            raise TaskError("task_id must be a non-empty string")
        self._dataset = dataset
        self._protocol = protocol

    @property
    def dataset(self) -> Dataset:
        return self._dataset

    @property
    def protocol(self) -> Protocol[AgentInputT]:
        return self._protocol

    def build_input(self) -> AgentInputBundle[AgentInputT]:
        """Build the information exposed to the Agent."""

        bundle = self.protocol.build_input(self.dataset)
        return AgentInputBundle(
            data=bundle.data,
            manifest=bundle.manifest.for_task(self.task_id),
        )

    @abstractmethod
    def evaluate(self, submission: SubmissionT) -> EvaluationT:
        """Evaluate one complete submission using trusted Task state."""


class ObjectiveBackedTask(Task[AgentInputT, SubmissionT, EvaluationT], ABC):
    """Task specialization for evaluations that require an Objective."""

    def __init__(
        self,
        dataset: Dataset,
        protocol: Protocol[AgentInputT],
        objective: Objective,
    ) -> None:
        if objective.dataset is not dataset:
            raise TaskError("Objective must be bound to the Task Dataset instance")
        self._objective = objective
        super().__init__(dataset, protocol)

    @property
    def objective(self) -> Objective:
        return self._objective
