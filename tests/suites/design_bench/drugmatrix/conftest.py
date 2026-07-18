"""DrugMatrix test fixtures."""

from __future__ import annotations

import json
import os
from typing import Any

import pytest
from datasets import Dataset as HFDataset
from datasets import Features, Value

from sci_modeling_bench.dataset import DatasetValidator
from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.drugmatrix import DrugMatrixDataset
from sci_modeling_bench.suites.design_bench.drugmatrix._conditions import ENDPOINTS

PUBLISHED_REVISION = "013a4d698f61db49a6c26f986e5f3bab143aa4fe"


class TinyDrugMatrixRepository:
    repo_id = "local/drugmatrix"
    resolved_revision = "tiny-drugmatrix-fixture"

    def __init__(self) -> None:
        rows: list[dict[str, Any]] = []
        for study_index in range(4):
            study_id = f"study-{study_index}"
            rows.append(
                _row(
                    animal_id=f"control-{study_index}",
                    study_id=study_id,
                    treatment="Vehicle Control",
                    value=10.0,
                )
            )
            rows.append(
                _row(
                    animal_id=f"history-{study_index}",
                    study_id=study_id,
                    casrn=f"100-00-{study_index}",
                    canonical_smiles="C" * (study_index + 1),
                    dose=1.0,
                    duration_days=3.0,
                    treatment="Chemical",
                    value=10.0 + study_index,
                )
            )
            rows.append(
                _row(
                    animal_id=f"candidate-{study_index}",
                    study_id=study_id,
                    casrn=f"100-00-{study_index}",
                    canonical_smiles="C" * (study_index + 1),
                    dose=10.0,
                    duration_days=5.0,
                    treatment="Chemical",
                    value=11.0 + 2.0 * study_index,
                )
            )
        self.data = HFDataset.from_list(rows, features=_features())

    def read_text(self, path: str) -> str:
        raise FileNotFoundError(path)

    def load(self, config_name: str, split: str, *, streaming: bool) -> Any:
        return self.data


def _row(
    *,
    animal_id: str,
    study_id: str,
    treatment: str,
    value: float,
    casrn: str | None = None,
    canonical_smiles: str | None = None,
    dose: float | None = None,
    duration_days: float = 5.0,
) -> dict[str, Any]:
    return {
        "animal_id": animal_id,
        "study_id": study_id,
        "casrn": casrn,
        "canonical_smiles": canonical_smiles,
        "dose": dose,
        "duration_days": duration_days,
        "vehicle": "water",
        "treatment": treatment,
        "sex": "Male",
        "route": "Oral Gavage",
        **{endpoint: value + offset for offset, endpoint in enumerate(ENDPOINTS)},
    }


def _features() -> Features:
    return Features(
        {
            "animal_id": Value("string"),
            "study_id": Value("string"),
            "casrn": Value("string"),
            "canonical_smiles": Value("string"),
            "dose": Value("float64"),
            "duration_days": Value("float64"),
            "vehicle": Value("string"),
            "treatment": Value("string"),
            "sex": Value("string"),
            "route": Value("string"),
            **{endpoint: Value("float64") for endpoint in ENDPOINTS},
        }
    )


@pytest.fixture
def tiny_drugmatrix_dataset() -> DrugMatrixDataset:
    manifest = DatasetManifest.from_json(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": "design-bench/drugmatrix-clinical-pathology",
                "version": "test",
                "default_split": "observations",
                "description": "Tiny DrugMatrix fixture.",
                "license": "test-only",
                "inputs": [
                    {
                        "name": "canonical_smiles",
                        "description": "Canonical molecule SMILES.",
                        "required": False,
                    }
                ],
                "targets": [
                    {
                        "name": endpoint,
                        "description": f"Measured {endpoint}.",
                        "required": False,
                        "constraints": [{"kind": "finite"}],
                    }
                    for endpoint in ENDPOINTS
                ],
                "context": [],
                "splits": [
                    {
                        "name": "observations",
                        "description": "Tiny individual-animal observations.",
                        "num_rows": 12,
                    }
                ],
            }
        )
    )
    return DrugMatrixDataset(
        manifest,
        TinyDrugMatrixRepository(),
        config_name="drugmatrix_clinical_pathology",
        validator=DatasetValidator(),
    )


@pytest.fixture(scope="session")
def published_drugmatrix_dataset() -> DrugMatrixDataset:
    if os.environ.get("SMB_RUN_HUB_INTEGRATION") != "1":
        pytest.skip("SMB_RUN_HUB_INTEGRATION is not enabled")
    return DrugMatrixDataset.from_hub(revision=PUBLISHED_REVISION)
