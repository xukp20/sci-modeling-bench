"""Frozen measured-return Objective for Hopper controller policies."""

from __future__ import annotations

from collections.abc import Iterable

from sci_modeling_bench.exceptions import ObjectiveError, ObjectiveLookupError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput
from sci_modeling_bench.suites.design_bench.hopper_controller.dataset import (
    HOPPER_CONTROLLER_DEFAULT_SPLIT,
    HopperControllerDataset,
)
from sci_modeling_bench.suites.design_bench.hopper_controller.simulator import (
    policy_identity,
)

_DATASET_ID = "design-bench/hopper-controller"


class HopperControllerMeasuredObjective(Objective):
    """Return the frozen 500-rollout arithmetic mean for a source policy."""

    objective_id = "design-bench/hopper-controller-mean-return-v1"

    def __init__(
        self,
        dataset: HopperControllerDataset,
        *,
        split: str = HOPPER_CONTROLLER_DEFAULT_SPLIT,
    ) -> None:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ObjectiveError(
                f"HopperControllerMeasuredObjective requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        dataset.split(split)
        self._split = split
        self._lookup: dict[str, float] | None = None
        super().__init__(dataset)

    @property
    def output_fields(self) -> tuple[str, ...]:
        return ("mean_return",)

    @property
    def split(self) -> str:
        return self._split

    def contains_identity(self, identity: str) -> bool:
        return identity in self._get_lookup()

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        lookup = self._get_lookup()
        for candidate in candidates:
            identity = policy_identity(candidate["policy_weights"])
            try:
                value = lookup[identity]
            except KeyError as exc:
                raise ObjectiveLookupError(
                    f"policy {identity!r} is absent from split {self.split!r}"
                ) from exc
            yield {"mean_return": value}

    def _get_lookup(self) -> dict[str, float]:
        if self._lookup is not None:
            return self._lookup
        policies = self.dataset.load(self.split)
        lookup = {
            str(identity): float(value)
            for identity, value in zip(
                policies["policy_identity"],
                policies["mean_return"],
                strict=True,
            )
        }
        if len(lookup) != len(policies):
            raise ObjectiveError("Hopper policy identities must be unique")
        self._lookup = lookup
        return lookup
