"""Measured-pool candidate-ranking Task for Superconductor."""

from __future__ import annotations

import math
from collections.abc import Hashable, Sequence
from numbers import Real
from pathlib import Path

from sci_modeling_bench.objective import Candidate
from sci_modeling_bench.task import CandidatePoolRankingTask
from sci_modeling_bench.suites.design_bench.superconductor.dataset import (
    DEFAULT_SUPERCONDUCTOR_REPO_ID,
    ELEMENT_SYMBOLS,
    SUPERCONDUCTOR_CONFIG_NAME,
    SuperconductorDataset,
    composition_id,
)
from sci_modeling_bench.suites.design_bench.superconductor.objective import (
    SuperconductorMeasuredObjective,
)
from sci_modeling_bench.suites.design_bench.superconductor.protocol import (
    SuperconductorAgentInput,
    SuperconductorMeasuredPoolProtocol,
)


class SuperconductorCandidatePoolRankingTask(
    CandidatePoolRankingTask[SuperconductorAgentInput]
):
    """Select and rank measured high-Tc composition groups from a finite pool."""

    task_id = "design-bench/superconductor-candidate-pool-ranking-v2"
    default_primary_metric = "global_ndcg"

    def __init__(
        self,
        dataset: SuperconductorDataset,
        *,
        protocol: SuperconductorMeasuredPoolProtocol | None = None,
        objective: SuperconductorMeasuredObjective | None = None,
        submission_size: int = 32,
        summary_size: int | None = None,
        primary_metric: str | None = None,
    ) -> None:
        selected_protocol = protocol or SuperconductorMeasuredPoolProtocol()
        selected_objective = objective or SuperconductorMeasuredObjective(dataset)
        candidate_pool = selected_protocol.candidate_pool(
            dataset, split=selected_objective.split
        )
        self._pool_ids_by_composition = {
            tuple(composition): candidate_id
            for candidate_id, composition in zip(
                candidate_pool["composition_id"],
                candidate_pool["composition"],
                strict=True,
            )
        }
        super().__init__(
            dataset,
            selected_protocol,
            selected_objective,
            candidate_pool=(
                {"composition": composition}
                for composition in candidate_pool["composition"]
            ),
            score_field="critical_temp_k",
            reference_scores=candidate_pool["critical_temp_k"],
            reference_scope="evaluation_pool",
            submission_size=submission_size,
            summary_size=summary_size,
            primary_metric=primary_metric,
        )

    def _candidate_identity(self, candidate: Candidate) -> Hashable:
        return tuple(candidate["composition"])

    def _candidate_for_dataset_validation(self, candidate: Candidate) -> Candidate:
        composition = candidate.get("composition")
        if not _valid_composition(composition):
            return {"composition_id": None}
        return {"composition_id": composition_id(composition)}

    def _candidate_for_objective(self, candidate: Candidate) -> Candidate:
        candidate_id = self._pool_ids_by_composition[tuple(candidate["composition"])]
        return {"composition_id": candidate_id}

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_SUPERCONDUCTOR_REPO_ID,
        config_name: str | None = SUPERCONDUCTOR_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
        submission_size: int = 32,
        summary_size: int | None = None,
        primary_metric: str | None = None,
    ) -> SuperconductorCandidatePoolRankingTask:
        dataset = SuperconductorDataset.from_hub(
            repo_id=repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
            cache=cache,
            cache_dir=cache_dir,
        )
        return cls(
            dataset,
            submission_size=submission_size,
            summary_size=summary_size,
            primary_metric=primary_metric,
        )


def _valid_composition(value: object) -> bool:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        return False
    if len(value) != len(ELEMENT_SYMBOLS):
        return False
    if not all(
        not isinstance(item, bool)
        and isinstance(item, Real)
        and math.isfinite(item)
        and item >= 0
        for item in value
    ):
        return False
    return math.isclose(math.fsum(value), 1.0, abs_tol=1e-6)
