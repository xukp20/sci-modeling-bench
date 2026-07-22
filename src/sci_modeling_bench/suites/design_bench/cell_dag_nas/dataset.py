"""Canonical NASBench-101 Dataset and integrity validation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from numbers import Real
from pathlib import Path
from typing import Any

from sci_modeling_bench.dataset import (
    Dataset,
    DatasetValidator,
    HubDatasetSource,
    ValidationReport,
    Violation,
)
from sci_modeling_bench.suites.design_bench.cell_dag_nas._graph import (
    ArchitectureEncodingError,
    decode_architecture,
)

DEFAULT_CELL_DAG_NAS_REPO_ID = "sci-modeling-bench/design-bench"
CELL_DAG_NAS_CONFIG_NAME = "cell_dag_nas"
CELL_DAG_NAS_DEFAULT_SPLIT = "architectures"
DEFAULT_CELL_DAG_NAS_SOURCE = HubDatasetSource(
    repo_id=DEFAULT_CELL_DAG_NAS_REPO_ID,
    config_name=CELL_DAG_NAS_CONFIG_NAME,
)

EXPECTED_CANONICAL_GRAPHS = 423_624
EXPECTED_ALIAS_ROWS = 1_293_208
EXPECTED_REPEAT_COUNT = 3
GLOBAL_BEST_MEAN_TEST_ACCURACY = 0.943175752957662

_DATASET_ID = "design-bench/cell-dag-nas"
_EXPECTED_COLUMNS = (
    "architecture",
    "test_accuracies",
    "mean_test_accuracy",
    "canonical_hash",
    "aliases",
    "train_accuracies",
    "validation_accuracies",
    "training_times",
)


class CellDAGNASDataset(Dataset):
    """Canonical NASBench-101 architectures with an overridable Hub source."""

    @classmethod
    def from_hub(
        cls,
        repo_id: str = DEFAULT_CELL_DAG_NAS_REPO_ID,
        config_name: str | None = CELL_DAG_NAS_CONFIG_NAME,
        revision: str | None = None,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> CellDAGNASDataset:
        return super().from_hub(
            repo_id,
            config_name=config_name,
            revision=revision,
            token=token,
            validator=validator or CellDAGNASValidator(),
            cache=cache,
            cache_dir=cache_dir,
        )

    @classmethod
    def from_source(
        cls,
        source: HubDatasetSource = DEFAULT_CELL_DAG_NAS_SOURCE,
        *,
        token: str | None = None,
        validator: DatasetValidator | None = None,
        cache: bool = True,
        cache_dir: str | Path | None = None,
    ) -> CellDAGNASDataset:
        return super().from_source(
            source,
            token=token,
            validator=validator or CellDAGNASValidator(),
            cache=cache,
            cache_dir=cache_dir,
        )


class CellDAGNASValidator(DatasetValidator):
    """Validate graph candidates and canonical NASBench-101 observations."""

    def validate_inputs(
        self,
        inputs: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ValidationReport:
        architecture = inputs.get("architecture")
        if architecture is None:
            return ValidationReport()
        try:
            decode_architecture(architecture)
        except ArchitectureEncodingError as exc:
            return ValidationReport(
                violations=(
                    Violation(
                        code=exc.code,
                        field="architecture",
                        message=str(exc),
                    ),
                )
            )
        return ValidationReport()

    def validate_observation(
        self,
        observation: Mapping[str, Any],
    ) -> ValidationReport:
        violations: list[Violation] = []
        try:
            representative = decode_architecture(observation["architecture"])
        except (KeyError, ArchitectureEncodingError) as exc:
            return ValidationReport(
                violations=(
                    Violation(
                        code="invalid_canonical_architecture",
                        field="architecture",
                        message=str(exc),
                    ),
                )
            )
        expected_hash = observation.get("canonical_hash")
        if representative.canonical_hash != expected_hash:
            violations.append(
                Violation(
                    code="canonical_hash_mismatch",
                    field="canonical_hash",
                    message="representative architecture does not match canonical_hash",
                )
            )

        aliases = observation.get("aliases", ())
        if not aliases:
            violations.append(
                Violation(
                    code="missing_architecture_alias",
                    field="aliases",
                    message="every canonical graph must retain at least one alias",
                )
            )
        elif tuple(observation["architecture"]) != min(tuple(alias) for alias in aliases):
            violations.append(
                Violation(
                    code="noncanonical_representative",
                    field="architecture",
                    message="architecture must be the lexicographically smallest alias",
                )
            )
        for alias in aliases:
            try:
                alias_hash = decode_architecture(alias).canonical_hash
            except ArchitectureEncodingError as exc:
                violations.append(
                    Violation(
                        code="invalid_architecture_alias",
                        field="aliases",
                        message=str(exc),
                    )
                )
                continue
            if alias_hash != expected_hash:
                violations.append(
                    Violation(
                        code="alias_hash_mismatch",
                        field="aliases",
                        message="alias does not map to the row canonical_hash",
                    )
                )

        repeat_fields = (
            "train_accuracies",
            "validation_accuracies",
            "test_accuracies",
            "training_times",
        )
        for field in repeat_fields:
            values = observation.get(field, ())
            if len(values) != EXPECTED_REPEAT_COUNT:
                violations.append(
                    Violation(
                        code="invalid_repeat_count",
                        field=field,
                        message=f"{field} must contain exactly three values",
                    )
                )
        tests = observation.get("test_accuracies", ())
        mean = observation.get("mean_test_accuracy")
        if (
            len(tests) == EXPECTED_REPEAT_COUNT
            and isinstance(mean, Real)
            and all(isinstance(value, Real) for value in tests)
            and not math.isclose(
                float(mean),
                sum(float(value) for value in tests) / EXPECTED_REPEAT_COUNT,
                rel_tol=0.0,
                abs_tol=5e-8,
            )
        ):
            violations.append(
                Violation(
                    code="mean_test_accuracy_mismatch",
                    field="mean_test_accuracy",
                    message="mean_test_accuracy must equal the three-repeat mean",
                )
            )
        return ValidationReport(violations=tuple(violations))

    def validate_dataset(self, data: Any) -> ValidationReport:
        violations: list[Violation] = []
        columns = tuple(getattr(data, "column_names", ()))
        if columns and columns != _EXPECTED_COLUMNS:
            violations.append(
                Violation(
                    code="cell_dag_nas_columns",
                    message=f"canonical columns must be {_EXPECTED_COLUMNS}, got {columns}",
                )
            )
        if len(data) != EXPECTED_CANONICAL_GRAPHS:
            violations.append(
                Violation(
                    code="incomplete_canonical_graph_space",
                    message=(
                        f"expected {EXPECTED_CANONICAL_GRAPHS} canonical graphs, "
                        f"got {len(data)}"
                    ),
                )
            )
        table = getattr(getattr(data, "data", None), "table", None)
        if table is not None:
            table = table.combine_chunks()
            hashes = table["canonical_hash"].to_pylist()
            alias_lists = table["aliases"].chunk(0)
            offsets = alias_lists.offsets.to_numpy()
            alias_count = int(offsets[-1] - offsets[0])
        else:
            hashes = data["canonical_hash"]
            alias_count = sum(len(aliases) for aliases in data["aliases"])
        if len(set(hashes)) != len(hashes):
            violations.append(
                Violation(
                    code="duplicate_canonical_hash",
                    field="canonical_hash",
                    message="canonical_hash must be unique",
                )
            )
        if alias_count != EXPECTED_ALIAS_ROWS:
            violations.append(
                Violation(
                    code="alias_count_mismatch",
                    field="aliases",
                    message=f"expected {EXPECTED_ALIAS_ROWS} aliases, got {alias_count}",
                )
            )
        return ValidationReport(violations=tuple(violations))
