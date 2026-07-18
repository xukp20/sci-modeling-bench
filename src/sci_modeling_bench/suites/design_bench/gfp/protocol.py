"""Lower-to-higher measured-pool Protocol for Sarkisyan GFP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Value

from sci_modeling_bench.dataset import Dataset
from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.protocol import Protocol
from sci_modeling_bench.suites.design_bench.gfp.dataset import GFP_DEFAULT_SPLIT

_DATASET_ID = "design-bench/gfp"


@dataclass(frozen=True)
class GFPAgentInput:
    """Visible source observations and label-hidden measured proteins."""

    protein_observations: HFDataset
    nucleotide_observations: HFDataset
    barcode_observations: HFDataset
    candidates: HFDataset
    reference_sequence: str


@dataclass(frozen=True)
class GFPLowerToHigherMeasuredPoolProtocol(Protocol[GFPAgentInput]):
    """Expose lower-brightness measurements and withhold the upper tail."""

    protocol_id: ClassVar[str] = "design-bench/gfp-lower-to-higher-measured-pool-v1"

    visible_max_percentile: float = 80.0

    def __post_init__(self) -> None:
        if not 0.0 < self.visible_max_percentile < 100.0:
            raise ProtocolError("visible_max_percentile must be between 0 and 100")

    def build_input(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> GFPAgentInput:
        proteins = self._load_proteins(dataset, split)
        visible_indices, candidate_indices, _ = self.partition(proteins)
        visible = proteins.select(visible_indices)
        reference_indices = np.flatnonzero(
            np.asarray(proteins["mutation_count"], dtype=np.int16) == 0
        )
        if reference_indices.size != 1:
            raise ProtocolError("GFP data must contain exactly one reference protein")
        return GFPAgentInput(
            protein_observations=visible.select_columns(
                [
                    "protein_id",
                    "sequence",
                    "aa_mutations",
                    "mutation_count",
                    "unique_barcodes",
                    "median_log10_brightness",
                    "brightness_std",
                ]
            ),
            nucleotide_observations=_expand_nucleotide_observations(visible),
            barcode_observations=_expand_barcode_observations(visible),
            candidates=proteins.select(candidate_indices).select_columns(
                ["protein_id", "sequence", "aa_mutations", "mutation_count"]
            ),
            reference_sequence=str(proteins[int(reference_indices[0])]["sequence"]),
        )

    def candidate_pool(
        self,
        dataset: Dataset,
        *,
        split: str | None = None,
    ) -> HFDataset:
        """Return the trusted labeled pool used to construct the Task."""

        proteins = self._load_proteins(dataset, split)
        _, candidate_indices, _ = self.partition(proteins)
        return proteins.select(candidate_indices).select_columns(
            [
                "protein_id",
                "sequence",
                "aa_mutations",
                "mutation_count",
                "median_log10_brightness",
            ]
        )

    def partition(
        self,
        proteins: HFDataset,
    ) -> tuple[list[int], list[int], float]:
        values = np.asarray(proteins["median_log10_brightness"], dtype=np.float64)
        if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
            raise ProtocolError(
                "median_log10_brightness must be a non-empty finite scalar column"
            )
        cutoff = float(
            np.percentile(values, self.visible_max_percentile, method="linear")
        )
        visible = np.flatnonzero(values <= cutoff).tolist()
        candidates = np.flatnonzero(values > cutoff).tolist()
        if not visible or not candidates:
            raise ProtocolError("GFP percentile partition produced an empty side")
        return visible, candidates, cutoff

    def _load_proteins(
        self,
        dataset: Dataset,
        split: str | None,
    ) -> HFDataset:
        if dataset.metadata.dataset_id != _DATASET_ID:
            raise ProtocolError(
                f"GFPLowerToHigherMeasuredPoolProtocol requires dataset_id "
                f"{_DATASET_ID!r}, got {dataset.metadata.dataset_id!r}"
            )
        selected_split = split or GFP_DEFAULT_SPLIT
        try:
            proteins = dataset.load(selected_split)
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc
        required = {
            "protein_id",
            "sequence",
            "aa_mutations",
            "mutation_count",
            "unique_barcodes",
            "median_log10_brightness",
            "brightness_std",
            "nucleotide_mutations",
            "nucleotide_mutation_counts",
            "nucleotide_unique_barcodes",
            "nucleotide_median_log10_brightness",
            "nucleotide_brightness_std",
            "source_barcode_ids",
            "barcode_nucleotide_mutations",
            "barcode_nucleotide_mutation_counts",
            "barcode_log10_brightness",
            "barcode_min_coverage",
            "barcode_mean_coverage",
        }
        missing = sorted(required - set(proteins.column_names))
        if missing:
            raise ProtocolError(f"GFP split is missing columns: {missing}")
        return proteins


def _expand_nucleotide_observations(proteins: HFDataset) -> HFDataset:
    columns: dict[str, list[object]] = {
        "protein_id": [],
        "nucleotide_mutations": [],
        "nucleotide_mutation_count": [],
        "unique_barcodes": [],
        "median_log10_brightness": [],
        "brightness_std": [],
    }
    for row in proteins:
        for mutation, count, barcodes, brightness, std in zip(
            row["nucleotide_mutations"],
            row["nucleotide_mutation_counts"],
            row["nucleotide_unique_barcodes"],
            row["nucleotide_median_log10_brightness"],
            row["nucleotide_brightness_std"],
            strict=True,
        ):
            columns["protein_id"].append(row["protein_id"])
            columns["nucleotide_mutations"].append(mutation)
            columns["nucleotide_mutation_count"].append(count)
            columns["unique_barcodes"].append(barcodes)
            columns["median_log10_brightness"].append(brightness)
            columns["brightness_std"].append(std)
    return HFDataset.from_dict(
        columns,
        features=Features(
            {
                "protein_id": Value("string"),
                "nucleotide_mutations": Value("string"),
                "nucleotide_mutation_count": Value("int16"),
                "unique_barcodes": Value("int32"),
                "median_log10_brightness": Value("float64"),
                "brightness_std": Value("float64"),
            }
        ),
    )


def _expand_barcode_observations(proteins: HFDataset) -> HFDataset:
    columns: dict[str, list[object]] = {
        "protein_id": [],
        "nucleotide_mutations": [],
        "nucleotide_mutation_count": [],
        "log10_brightness": [],
        "min_coverage": [],
        "mean_coverage": [],
    }
    for row in proteins:
        for mutation, count, brightness, min_coverage, mean_coverage in zip(
            row["barcode_nucleotide_mutations"],
            row["barcode_nucleotide_mutation_counts"],
            row["barcode_log10_brightness"],
            row["barcode_min_coverage"],
            row["barcode_mean_coverage"],
            strict=True,
        ):
            columns["protein_id"].append(row["protein_id"])
            columns["nucleotide_mutations"].append(mutation)
            columns["nucleotide_mutation_count"].append(count)
            columns["log10_brightness"].append(brightness)
            columns["min_coverage"].append(min_coverage)
            columns["mean_coverage"].append(mean_coverage)
    return HFDataset.from_dict(
        columns,
        features=Features(
            {
                "protein_id": Value("string"),
                "nucleotide_mutations": Value("string"),
                "nucleotide_mutation_count": Value("int16"),
                "log10_brightness": Value("float64"),
                "min_coverage": Value("int32"),
                "mean_coverage": Value("float64"),
            }
        ),
    )
