from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest

from sci_modeling_bench.dataset.dataset import Dataset
from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.exceptions import ObjectiveOutputError
from sci_modeling_bench.objective import Candidate, Objective, ObjectiveOutput


class ScoreObjective(Objective):
    objective_id = "test/score-v1"

    @property
    def output_fields(self) -> tuple[str, ...]:
        return ("score",)

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        return (
            {"score": float(len(candidate["sequence"]))} for candidate in candidates
        )


class MissingOutputObjective(ScoreObjective):
    objective_id = "test/missing-output-v1"

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        return ({"wrong": 1.0} for _ in candidates)


class DerivedOutputObjective(ScoreObjective):
    objective_id = "test/derived-output-v1"

    @property
    def output_fields(self) -> tuple[str, ...]:
        return ("derived_score",)

    def _evaluate_batch(
        self,
        candidates: tuple[Candidate, ...],
    ) -> Iterable[ObjectiveOutput]:
        return (
            {"derived_score": float(len(candidate["sequence"]))}
            for candidate in candidates
        )


def make_dataset(fake_repository: Any) -> Dataset:
    manifest = DatasetManifest.from_json(
        fake_repository.read_text("manifests/tfbind8.json")
    )
    return Dataset(manifest, fake_repository, config_name="tfbind8")


def test_objective_returns_stable_ordered_outputs(
    fake_repository,
) -> None:
    objective = ScoreObjective(make_dataset(fake_repository))

    assert objective.evaluate_batch(
        [{"sequence": "AACCGGTT"}, {"sequence": "TTGGCCAA"}]
    ) == ({"score": 8.0}, {"score": 8.0})


def test_objective_rejects_undeclared_output_fields(fake_repository) -> None:
    objective = MissingOutputObjective(make_dataset(fake_repository))

    with pytest.raises(ObjectiveOutputError, match="expected"):
        objective.evaluate({"sequence": "AACCGGTT"})


def test_objective_can_return_a_derived_non_dataset_field(fake_repository) -> None:
    objective = DerivedOutputObjective(make_dataset(fake_repository))

    assert objective.evaluate({"sequence": "AACCGGTT"}) == {"derived_score": 8.0}
