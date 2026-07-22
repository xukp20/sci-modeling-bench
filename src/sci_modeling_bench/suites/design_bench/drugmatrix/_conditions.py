"""Private condition grouping and measured-pool construction for DrugMatrix."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Value

from sci_modeling_bench.cache import PreparedArtifact, artifact_identity
from sci_modeling_bench.exceptions import ProtocolError

ENDPOINTS = (
    "mchc",
    "mch",
    "creatinine",
    "sodium",
    "chloride",
    "phosphorus",
)

_REQUIRED_COLUMNS = {
    "animal_id",
    "study_id",
    "casrn",
    "canonical_smiles",
    "dose",
    "duration_days",
    "vehicle",
    "treatment",
    "sex",
    "route",
    *ENDPOINTS,
}
_CANDIDATE_COLUMNS = (
    "condition_id",
    "casrn",
    "canonical_smiles",
    "dose",
    "duration_days",
    "vehicle",
    "sex",
    "route",
    "study_id",
)
_ARTIFACT_ID = "drugmatrix-measured-pool"
_ARTIFACT_PRODUCER_VERSION = 1


@dataclass(frozen=True)
class MeasuredPool:
    """Internal labeled pool and raw treatment rows withheld by the Protocol."""

    table: HFDataset
    treatment_row_indices: frozenset[int]


def build_measured_pool(observations: HFDataset) -> MeasuredPool:
    """Build the deterministic five-day maximum-dose exact-control pool."""

    missing = sorted(_REQUIRED_COLUMNS - set(observations.column_names))
    if missing:
        raise ProtocolError(f"DrugMatrix observations are missing columns: {missing}")

    chemical_groups: dict[tuple[Any, ...], list[int]] = {}
    control_groups: dict[tuple[Any, ...], list[int]] = {}
    maximum_dose: dict[str, float] = {}

    for index, row in enumerate(observations):
        treatment = row["treatment"]
        if treatment == "Chemical":
            casrn = row["casrn"]
            dose = row["dose"]
            if not isinstance(casrn, str) or not casrn or not _finite(dose):
                continue
            numeric_dose = float(dose)
            maximum_dose[casrn] = max(maximum_dose.get(casrn, -math.inf), numeric_dose)
            chemical_groups.setdefault(_condition_key(row), []).append(index)
        elif treatment in {"Vehicle Control", "Untreated Control"}:
            control_groups.setdefault(_control_key(row), []).append(index)

    rows: list[dict[str, Any]] = []
    withheld: set[int] = set()
    for key, row_indices in chemical_groups.items():
        representative = observations[row_indices[0]]
        casrn = str(representative["casrn"])
        dose = float(representative["dose"])
        duration = float(representative["duration_days"])
        smiles = representative["canonical_smiles"]
        if (
            duration != 5.0
            or dose != maximum_dose[casrn]
            or not isinstance(smiles, str)
            or not smiles
        ):
            continue

        control_indices = control_groups.get(_control_key(representative))
        if not control_indices:
            continue
        treatment_scores = _endpoint_means(observations, row_indices)
        control_scores = _endpoint_means(observations, control_indices)
        if treatment_scores is None or control_scores is None:
            continue
        if any(
            treatment_scores[name] <= 0.0 or control_scores[name] <= 0.0
            for name in ENDPOINTS
        ):
            continue

        output: dict[str, Any] = {
            "condition_id": condition_id(key),
            "casrn": casrn,
            "canonical_smiles": smiles,
            "dose": dose,
            "duration_days": duration,
            "vehicle": representative["vehicle"],
            "sex": representative["sex"],
            "route": representative["route"],
            "study_id": representative["study_id"],
        }
        for endpoint in ENDPOINTS:
            raw_response = treatment_scores[endpoint]
            control_response = control_scores[endpoint]
            output[f"{endpoint}_raw_response"] = raw_response
            output[f"{endpoint}_control_deviation"] = abs(
                math.log(raw_response / control_response)
            )
        rows.append(output)
        withheld.update(row_indices)

    rows.sort(key=lambda row: row["condition_id"])
    if not rows:
        raise ProtocolError("DrugMatrix measured-pool construction produced no candidates")
    identities = [str(row["condition_id"]) for row in rows]
    if len(set(identities)) != len(identities):
        raise ProtocolError("DrugMatrix condition IDs must be unique")
    return MeasuredPool(
        table=HFDataset.from_list(rows, features=_pool_features()),
        treatment_row_indices=frozenset(withheld),
    )


def prepare_measured_pool(
    dataset: Any,
    *,
    split: str,
    observations: HFDataset | None = None,
) -> PreparedArtifact[MeasuredPool]:
    """Load or build the shared measured-condition pool for all endpoints."""

    identity = artifact_identity(
        dataset,
        artifact_id=_ARTIFACT_ID,
        producer_version=_ARTIFACT_PRODUCER_VERSION,
        split=split,
    )
    return dataset.artifact_cache.get_or_build(
        identity,
        load=lambda directory: _load_measured_pool(
            directory,
            expected_rows=dataset.split(split).num_rows,
        ),
        build=lambda: build_measured_pool(
            dataset.load(split) if observations is None else observations
        ),
        write=_write_measured_pool,
    )


def _write_measured_pool(directory: Path, pool: MeasuredPool) -> None:
    pool.table.to_parquet(str(directory / "measured_pool.parquet"))
    np.save(
        directory / "treatment_row_indices.npy",
        np.asarray(sorted(pool.treatment_row_indices), dtype=np.int64),
        allow_pickle=False,
    )


def _load_measured_pool(
    directory: Path, *, expected_rows: int | None
) -> MeasuredPool:
    table = HFDataset.from_parquet(str(directory / "measured_pool.parquet"))
    indices = np.load(
        directory / "treatment_row_indices.npy",
        allow_pickle=False,
        mmap_mode="r",
    )
    if indices.ndim != 1 or indices.dtype != np.int64:
        raise ValueError("cached DrugMatrix treatment indices are invalid")
    if len(indices) and (int(indices[0]) < 0 or np.any(indices[1:] <= indices[:-1])):
        raise ValueError("cached DrugMatrix treatment indices must be sorted and unique")
    if expected_rows is not None and len(indices) and int(indices[-1]) >= expected_rows:
        raise ValueError("cached DrugMatrix treatment index is outside the split")
    required = {"condition_id", "canonical_smiles"}
    required.update(
        f"{endpoint}_{suffix}"
        for endpoint in ENDPOINTS
        for suffix in ("raw_response", "control_deviation")
    )
    missing = sorted(required - set(table.column_names))
    if missing:
        raise ValueError(f"cached DrugMatrix measured pool is missing {missing}")
    identities = list(table["condition_id"])
    if not identities or len(set(identities)) != len(identities):
        raise ValueError("cached DrugMatrix condition IDs must be non-empty and unique")
    return MeasuredPool(
        table=table,
        treatment_row_indices=frozenset(int(index) for index in indices),
    )


def candidate_view(pool: MeasuredPool) -> HFDataset:
    """Return the label-hidden candidate table exposed by the Protocol."""

    return pool.table.select_columns(list(_CANDIDATE_COLUMNS))


def condition_id(key: tuple[Any, ...]) -> str:
    """Return a stable ID for one complete treatment condition key."""

    encoded = json.dumps(
        [_identity_value(value) for value in key],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"dm-{hashlib.sha256(encoded).hexdigest()[:24]}"


def _condition_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["study_id"],
        row["casrn"],
        row["canonical_smiles"],
        float(row["dose"]),
        float(row["duration_days"]),
        row["vehicle"],
        row["sex"],
        row["route"],
    )


def _control_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["study_id"],
        float(row["duration_days"]),
        _normalized_text(row["vehicle"]),
        _normalized_text(row["sex"]),
        _normalized_text(row["route"]),
    )


def _endpoint_means(
    observations: HFDataset,
    row_indices: list[int],
) -> dict[str, float] | None:
    result: dict[str, float] = {}
    for endpoint in ENDPOINTS:
        values = [
            float(value)
            for index in row_indices
            if _finite(value := observations[index][endpoint])
        ]
        if not values:
            return None
        result[endpoint] = math.fsum(values) / len(values)
    return result


def _pool_features() -> Features:
    fields: dict[str, Any] = {
        "condition_id": Value("string"),
        "casrn": Value("string"),
        "canonical_smiles": Value("string"),
        "dose": Value("float64"),
        "duration_days": Value("float64"),
        "vehicle": Value("string"),
        "sex": Value("string"),
        "route": Value("string"),
        "study_id": Value("string"),
    }
    for endpoint in ENDPOINTS:
        fields[f"{endpoint}_raw_response"] = Value("float64")
        fields[f"{endpoint}_control_deviation"] = Value("float64")
    return Features(fields)


def _identity_value(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".17g")
    return value


def _normalized_text(value: Any) -> str:
    return "" if value is None else str(value).strip().casefold()


def _finite(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )
