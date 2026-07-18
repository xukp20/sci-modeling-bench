from __future__ import annotations

import json
from typing import Any

import pytest
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value

from sci_modeling_bench.dataset.manifest import DatasetManifest
from sci_modeling_bench.suites.design_bench.gfp import GFPDataset, GFPValidator, protein_id
from sci_modeling_bench.suites.design_bench.gfp._sequence import (
    apply_amino_acid_mutations,
)

REFERENCE = (
    "SKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTLSY"
    "GVQCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLVNRIELKGIDFKE"
    "DGNILGHKLEYNYNSHNVYIMADKQKNGIKVNFKIRHNIEDGSVQLADHYQQNTPIGDGPVLLPDN"
    "HYLSTQSALSKDPNEKRDHMVLLEFVTAAGITHGMDELYK"
)


class TinyGFPRepository:
    repo_id = "local/gfp"
    resolved_revision = "tiny-gfp-fixture"

    def __init__(self) -> None:
        mutations = ["", "SS0A", "SS0C", "SS0D", "SS0E", "SS0F", "SS0G", "SS0H", "SS0I", "SS0K"]
        rows = []
        for index, notation in enumerate(mutations):
            sequence = apply_amino_acid_mutations(REFERENCE, notation)
            nucleotide_mutation = "" if index == 0 else f"SA{index}G"
            row = {
                "protein_id": protein_id(sequence),
                "sequence": sequence,
                "aa_mutations": notation,
                "mutation_count": 0 if not notation else 1,
                "unique_barcodes": 1,
                "median_log10_brightness": float(index + 1),
                "brightness_std": None,
                "nucleotide_mutations": [nucleotide_mutation],
                "nucleotide_mutation_counts": [0 if index == 0 else 1],
                "nucleotide_unique_barcodes": [1],
                "nucleotide_median_log10_brightness": [float(index + 1)],
                "nucleotide_brightness_std": [None],
                "source_barcode_ids": [format(index, "020b").translate(str.maketrans("01", "AC"))],
                "barcode_nucleotide_mutations": [nucleotide_mutation],
                "barcode_nucleotide_mutation_counts": [0 if index == 0 else 1],
                "barcode_log10_brightness": [float(index + 1)],
                "barcode_min_coverage": [100 + index],
                "barcode_mean_coverage": [150.0 + index],
            }
            rows.append(row)
        rows.sort(key=lambda row: row["protein_id"])
        self.data = HFDataset.from_list(rows, features=_features())

    def read_text(self, path: str) -> str:
        raise FileNotFoundError(path)

    def load(self, config_name: str, split: str, *, streaming: bool) -> Any:
        return self.data


@pytest.fixture
def tiny_gfp_dataset() -> GFPDataset:
    context = [
        {"name": name, "description": name, "required": False}
        for name in _features()
        if name not in {"sequence", "median_log10_brightness"}
    ]
    manifest = DatasetManifest.from_json(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": "design-bench/gfp",
                "version": "test",
                "default_split": "protein_genotypes",
                "description": "Tiny GFP fixture.",
                "license": "test-only",
                "inputs": [
                    {
                        "name": "sequence",
                        "description": "Protein sequence.",
                        "constraints": [
                            {
                                "kind": "alphabet",
                                "symbols": list("ACDEFGHIKLMNPQRSTVWY"),
                            },
                            {"kind": "length", "minimum": 237, "maximum": 237},
                        ],
                    }
                ],
                "targets": [
                    {
                        "name": "median_log10_brightness",
                        "description": "Measured brightness.",
                        "constraints": [{"kind": "finite"}],
                    }
                ],
                "context": context,
                "splits": [
                    {
                        "name": "protein_genotypes",
                        "description": "Tiny proteins.",
                        "num_rows": 10,
                    }
                ],
            }
        )
    )
    return GFPDataset(
        manifest,
        TinyGFPRepository(),
        config_name="gfp",
        validator=GFPValidator(expected_rows=10),
    )


def _features() -> Features:
    return Features(
        {
            "protein_id": Value("string"),
            "sequence": Value("string"),
            "aa_mutations": Value("string"),
            "mutation_count": Value("int16"),
            "unique_barcodes": Value("int32"),
            "median_log10_brightness": Value("float64"),
            "brightness_std": Value("float64"),
            "nucleotide_mutations": Sequence(Value("string")),
            "nucleotide_mutation_counts": Sequence(Value("int16")),
            "nucleotide_unique_barcodes": Sequence(Value("int32")),
            "nucleotide_median_log10_brightness": Sequence(Value("float64")),
            "nucleotide_brightness_std": Sequence(Value("float64")),
            "source_barcode_ids": Sequence(Value("string")),
            "barcode_nucleotide_mutations": Sequence(Value("string")),
            "barcode_nucleotide_mutation_counts": Sequence(Value("int16")),
            "barcode_log10_brightness": Sequence(Value("float64")),
            "barcode_min_coverage": Sequence(Value("int32")),
            "barcode_mean_coverage": Sequence(Value("float64")),
        }
    )
