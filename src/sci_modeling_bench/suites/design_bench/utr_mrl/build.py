"""Build the canonical replicate-mean eGFP UTR MRL release."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable
from importlib import resources
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from datasets import Dataset as HFDataset
from datasets import Features, Value
from huggingface_hub import DatasetCard
from huggingface_hub.repocard_data import DatasetCardData

from sci_modeling_bench.suites.design_bench.utr_mrl._sequence import (
    UTR_LENGTH,
    sequence_annotations,
)
from sci_modeling_bench.suites.design_bench.utr_mrl.dataset import (
    EXPECTED_UTR_MRL_ROWS,
    UTR_MRL_CONFIG_NAME,
    UTR_MRL_DEFAULT_SPLIT,
)

SOURCE_REPO_ID = "morrislab/mrl-sample"
SOURCE_REVISION = "ef67f7cf8a999bb1c412ad6551aa7d9f901cbb95"
SOURCE_FILENAME = "mrl-sample-egfp.parquet"
SOURCE_URL = (
    "https://huggingface.co/datasets/morrislab/mrl-sample/blob/"
    f"{SOURCE_REVISION}/{SOURCE_FILENAME}"
)
SOURCE_SIZE = 37_117_316
SOURCE_SHA256 = "c007cf66cfcea0807e90baf92ac24b6078102729ad050100bde00f7f0ab4c9b3"
SOURCE_COLUMNS = (
    "sequence",
    "cds",
    "splice",
    "target_mrl_egfp_m1pseudo",
    "target_mrl_egfp_pseudo",
    "target_mrl_egfp_unmod",
    "u_start",
    "u_oof_start",
    "kozak_quality",
)
SOURCE_TARGET = "target_mrl_egfp_unmod"
PRIMER_SEQUENCE = "GGGACATCGTAGAGAGTCGTACTTA"
CONSTRUCT_LENGTH = 855
EGFP_SUFFIX_LENGTH = 780
EGFP_SUFFIX_SHA256 = "b78735cd31b316ea2de07646db65a6c07e051fc0e1cefc8c2b8d668ef680e6f1"

DATASET_REPO_ID = "sci-modeling-bench/design-bench"
DATASET_ID = "design-bench/utr-mrl-egfp-unmodified"
DATASET_VERSION = "1.0.0"
MRNABENCH_COMMIT = "74f96b8e6ae9f41cc3cccff089d826a62d5604b8"

KNOWLEDGE_RESOURCES = {
    "rna_sequence_structure_and_base_pairing": {
        "title": "RNA Sequence, Structure, and Base Pairing",
        "description": (
            "RNA polarity, nucleotide alphabet, canonical and wobble pairing, "
            "secondary structure, folding energetics, and structural ensembles."
        ),
        "source_path": "shared/rna-sequence-structure-and-base-pairing.md",
        "path": "knowledge/shared/rna-sequence-structure-and-base-pairing.md",
        "media_type": "text/markdown",
    },
    "eukaryotic_mrna_and_translation_initiation": {
        "title": "Eukaryotic mRNA and Translation Initiation",
        "description": (
            "mRNA organization, cap-dependent initiation, pre-initiation "
            "complex recruitment, scanning, start recognition, and exceptions."
        ),
        "source_path": "shared/eukaryotic-mrna-and-translation-initiation.md",
        "path": (
            "knowledge/shared/eukaryotic-mrna-and-translation-initiation.md"
        ),
        "media_type": "text/markdown",
    },
    "five_prime_utr_regulatory_elements": {
        "title": "Five-Prime UTR Regulatory Elements",
        "description": (
            "Sequence and structural elements in eukaryotic 5' UTRs and their "
            "context-dependent effects on translation."
        ),
        "source_path": "shared/five-prime-utr-regulatory-elements.md",
        "path": "knowledge/shared/five-prime-utr-regulatory-elements.md",
        "media_type": "text/markdown",
    },
    "kozak_context_and_start_codon_recognition": {
        "title": "Kozak Context and Start-Codon Recognition",
        "description": (
            "Start-site coordinate conventions, vertebrate AUG context, "
            "leaky scanning, non-AUG initiation, and organism dependence."
        ),
        "source_path": "shared/kozak-context-and-start-codon-recognition.md",
        "path": "knowledge/shared/kozak-context-and-start-codon-recognition.md",
        "media_type": "text/markdown",
    },
    "upstream_start_codons_and_upstream_open_reading_frames": {
        "title": "Upstream Start Codons and Upstream Open Reading Frames",
        "description": (
            "uAUG and uORF definitions, reading frames, leaky scanning, "
            "reinitiation, overlap, and conditional translational regulation."
        ),
        "source_path": (
            "shared/upstream-start-codons-and-upstream-open-reading-frames.md"
        ),
        "path": (
            "knowledge/shared/"
            "upstream-start-codons-and-upstream-open-reading-frames.md"
        ),
        "media_type": "text/markdown",
    },
    "polysome_profiling_and_mean_ribosome_load": {
        "title": "Polysome Profiling and Mean Ribosome Load",
        "description": (
            "Polysome fractionation, sequencing-based abundance measurement, "
            "weighted mean ribosome load, normalization, and interpretation."
        ),
        "source_path": "shared/polysome-profiling-and-mean-ribosome-load.md",
        "path": "knowledge/shared/polysome-profiling-and-mean-ribosome-load.md",
        "media_type": "text/markdown",
    },
    "massively_parallel_translation_reporter_assays": {
        "title": "Massively Parallel Translation Reporter Assays",
        "description": (
            "Pooled reporter libraries for measuring how cis-regulatory "
            "sequences affect translation, including controls and limitations."
        ),
        "source_path": "shared/massively-parallel-translation-reporter-assays.md",
        "path": (
            "knowledge/shared/massively-parallel-translation-reporter-assays.md"
        ),
        "media_type": "text/markdown",
    },
}


def build_utr_mrl_release(
    source_parquet: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Build an upload-ready UTR MRL config and return provenance."""

    source = Path(source_parquet)
    destination = Path(output_dir)
    _verify_source(source)
    rows, statistics = canonicalize_source(source)

    data_path = (
        destination
        / "data"
        / UTR_MRL_CONFIG_NAME
        / f"{UTR_MRL_DEFAULT_SPLIT}.parquet"
    )
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data = HFDataset.from_dict(rows, features=_features())
    data.to_parquet(data_path)

    provenance = _provenance(source, data_path, statistics)
    provenance["knowledge"] = _write_knowledge_resources(destination)
    _write_release_metadata(destination, provenance)
    return provenance


def canonicalize_source(
    source_parquet: str | Path,
) -> tuple[dict[str, list[Any]], dict[str, Any]]:
    """Extract the variable UTR and verify every source annotation."""

    source = Path(source_parquet)
    parquet = pq.ParquetFile(source)
    actual_columns = tuple(parquet.schema_arrow.names)
    if actual_columns != SOURCE_COLUMNS:
        raise ValueError(
            f"unexpected source columns: expected {SOURCE_COLUMNS}, got {actual_columns}"
        )
    selected = [
        "sequence",
        SOURCE_TARGET,
        "u_start",
        "u_oof_start",
        "kozak_quality",
    ]
    table = parquet.read(columns=selected)
    if table.num_rows != EXPECTED_UTR_MRL_ROWS:
        raise ValueError(
            f"expected {EXPECTED_UTR_MRL_ROWS} source rows, got {table.num_rows}"
        )
    for name in selected:
        if table[name].null_count:
            raise ValueError(f"source column {name!r} contains null values")

    constructs = table["sequence"].to_pylist()
    source_targets = np.asarray(table[SOURCE_TARGET].to_numpy(), dtype=np.float64)
    source_uaug = np.asarray(table["u_start"].to_numpy(), dtype=np.int8)
    source_oof = np.asarray(table["u_oof_start"].to_numpy(), dtype=np.int8)
    source_kozak = table["kozak_quality"].to_pylist()
    if not np.all(np.isfinite(source_targets)):
        raise ValueError("source MRL target contains non-finite values")
    if np.any(source_targets < 0.0) or np.any(source_targets > 13.0):
        raise ValueError("source MRL target is outside [0, 13]")

    utrs: list[str] = []
    annotations: list[tuple[bool, bool, str]] = []
    suffix: str | None = None
    for index, construct in enumerate(constructs):
        if len(construct) != CONSTRUCT_LENGTH:
            raise ValueError(f"source construct {index} has length {len(construct)}")
        if not construct.startswith(PRIMER_SEQUENCE):
            raise ValueError(f"source construct {index} has an unexpected primer")
        current_suffix = construct[len(PRIMER_SEQUENCE) + UTR_LENGTH :]
        if len(current_suffix) != EGFP_SUFFIX_LENGTH:
            raise ValueError(f"source construct {index} has an unexpected suffix length")
        if suffix is None:
            suffix = current_suffix
            if _sha256_text(suffix) != EGFP_SUFFIX_SHA256:
                raise ValueError("source eGFP suffix checksum mismatch")
        elif current_suffix != suffix:
            raise ValueError(f"source construct {index} has a different eGFP suffix")
        utr = construct[len(PRIMER_SEQUENCE) : len(PRIMER_SEQUENCE) + UTR_LENGTH]
        annotation = sequence_annotations(utr)
        if int(annotation[0]) != int(source_uaug[index]):
            raise ValueError(f"u_start annotation mismatch at source row {index}")
        if int(annotation[1]) != int(source_oof[index]):
            raise ValueError(f"u_oof_start annotation mismatch at source row {index}")
        if annotation[2] != source_kozak[index]:
            raise ValueError(f"kozak_quality annotation mismatch at source row {index}")
        utrs.append(utr)
        annotations.append(annotation)

    if len(set(utrs)) != len(utrs):
        raise ValueError("source eGFP UTR sequences must be unique")
    order = sorted(range(len(utrs)), key=utrs.__getitem__)
    rows = {
        "sequence": [utrs[index] for index in order],
        "mean_ribosome_load": [float(source_targets[index]) for index in order],
        "has_uaug": [annotations[index][0] for index in order],
        "has_out_of_frame_uaug": [annotations[index][1] for index in order],
        "kozak_quality": [annotations[index][2] for index in order],
    }

    targets = np.asarray(rows["mean_ribosome_load"], dtype=np.float64)
    uaug = np.asarray(rows["has_uaug"], dtype=np.bool_)
    oof = np.asarray(rows["has_out_of_frame_uaug"], dtype=np.bool_)
    kozak = np.asarray(rows["kozak_quality"], dtype=object)
    visible = ((~uaug) & np.isin(kozak, ["strong", "weak"])) | (
        uaug & (kozak == "strong")
    )
    candidates = uaug & (kozak == "weak")
    combination_counts = {
        "no_uaug_strong": int(np.count_nonzero((~uaug) & (kozak == "strong"))),
        "no_uaug_weak": int(np.count_nonzero((~uaug) & (kozak == "weak"))),
        "uaug_strong": int(np.count_nonzero(uaug & (kozak == "strong"))),
        "uaug_weak": int(np.count_nonzero(candidates)),
        "mixed": int(np.count_nonzero(kozak == "mixed")),
    }
    statistics = {
        "rows": len(utrs),
        "unique_sequences": len(set(utrs)),
        "target_minimum": float(targets.min()),
        "target_mean": float(targets.mean()),
        "target_standard_deviation": float(targets.std()),
        "target_maximum": float(targets.max()),
        "has_uaug": int(np.count_nonzero(uaug)),
        "has_out_of_frame_uaug": int(np.count_nonzero(oof)),
        "kozak_counts": {
            quality: int(np.count_nonzero(kozak == quality))
            for quality in ("mixed", "strong", "weak")
        },
        "compositional_partition": {
            "visible_observations": int(np.count_nonzero(visible)),
            "candidate_pool": int(np.count_nonzero(candidates)),
            "combination_counts": combination_counts,
        },
    }
    return rows, statistics


def _features() -> Features:
    return Features(
        {
            "sequence": Value("string"),
            "mean_ribosome_load": Value("float64"),
            "has_uaug": Value("bool"),
            "has_out_of_frame_uaug": Value("bool"),
            "kozak_quality": Value("string"),
        }
    )


def _provenance(
    source: Path,
    data_path: Path,
    statistics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "config": UTR_MRL_CONFIG_NAME,
        "split": UTR_MRL_DEFAULT_SPLIT,
        "source_artifact": {
            "repo_id": SOURCE_REPO_ID,
            "revision": SOURCE_REVISION,
            "filename": SOURCE_FILENAME,
            "url": SOURCE_URL,
            "size_bytes": source.stat().st_size,
            "sha256": _sha256(source),
        },
        "construct": {
            "length": CONSTRUCT_LENGTH,
            "primer_sequence": PRIMER_SEQUENCE,
            "variable_region_start": len(PRIMER_SEQUENCE),
            "variable_region_length": UTR_LENGTH,
            "egfp_suffix_length": EGFP_SUFFIX_LENGTH,
            "egfp_suffix_sha256": EGFP_SUFFIX_SHA256,
        },
        "transformation": {
            "mrnabench_commit": MRNABENCH_COMMIT,
            "steps": [
                "verify the pinned mRNABench eGFP Parquet artifact",
                "verify fixed primer, variable-region, and eGFP construct boundaries",
                "extract the 50-nucleotide variable UTR",
                "retain the unmodified-RNA two-replicate mean MRL without normalization",
                "recompute and verify uAUG, out-of-frame-uAUG, and Kozak annotations",
                "reject duplicate UTR sequences",
                "sort canonical rows lexicographically by sequence",
            ],
        },
        "statistics": statistics,
        "artifact": {
            "path": (
                f"data/{UTR_MRL_CONFIG_NAME}/"
                f"{UTR_MRL_DEFAULT_SPLIT}.parquet"
            ),
            "size_bytes": data_path.stat().st_size,
            "sha256": _sha256(data_path),
        },
    }


def _write_release_metadata(destination: Path, provenance: dict[str, Any]) -> None:
    manifest_dir = destination / "manifests"
    provenance_dir = destination / "provenance" / UTR_MRL_CONFIG_NAME
    manifest_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir.mkdir(parents=True, exist_ok=True)

    collection_path = destination / "scimodelingbench.json"
    if collection_path.exists():
        collection = json.loads(collection_path.read_text(encoding="utf-8"))
    else:
        collection = {
            "schema_version": 1,
            "default_config": UTR_MRL_CONFIG_NAME,
            "configs": {},
        }
    collection["configs"][UTR_MRL_CONFIG_NAME] = {
        "manifest": f"manifests/{UTR_MRL_CONFIG_NAME}.json"
    }

    manifest = {
        "schema_version": 1,
        "dataset_id": DATASET_ID,
        "version": DATASET_VERSION,
        "default_split": UTR_MRL_DEFAULT_SPLIT,
        "description": (
            "Replicate-mean MRL measurements for synthetic 50-nt UTRs in "
            "a fixed eGFP, unmodified-RNA, HEK293T context."
        ),
        "license": "unknown",
        "source": [
            {
                "name": "mRNABench mrl-sample eGFP redistribution",
                "url": SOURCE_URL,
                "revision": SOURCE_REVISION,
                "checksum": f"sha256:{SOURCE_SHA256}",
            },
            {
                "name": "GEO GSE114002",
                "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE114002",
                "version": "GSE114002",
            },
        ],
        "citation": [
            {
                "text": (
                    "Sample et al. (2019), Human 5' UTR design and variant "
                    "effect prediction from a massively parallel translation assay."
                ),
                "url": "https://doi.org/10.1038/s41587-019-0164-5",
            },
            {
                "text": (
                    "mRNABench: A curated benchmark for mature mRNA property "
                    "and function prediction."
                ),
                "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12265608/",
            },
        ],
        "inputs": [
            {
                "name": "sequence",
                "description": (
                    "The 5'-to-3' DNA-alphabet representation of the "
                    "50-nucleotide variable segment at the 3' end of the "
                    "reporter 5' leader. It is preceded by a fixed "
                    "25-nucleotide leader segment and followed immediately by "
                    "the fixed eGFP main start codon ATG; T represents U in "
                    "the transcribed RNA."
                ),
                "constraints": [
                    {"kind": "alphabet", "symbols": ["A", "C", "G", "T"]},
                    {"kind": "length", "minimum": 50, "maximum": 50},
                ],
            }
        ],
        "targets": [
            {
                "name": "mean_ribosome_load",
                "description": (
                    "Mean ribosome load averaged across two unmodified-RNA replicates."
                ),
                "unit": "ribosomes per transcript",
                "constraints": [
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0.0, "maximum": 13.0},
                ],
            }
        ],
        "context": [
            {
                "name": "has_uaug",
                "description": "Whether the variable UTR contains an upstream ATG.",
                "required": False,
            },
            {
                "name": "has_out_of_frame_uaug",
                "description": (
                    "Whether any upstream ATG is out of frame with the fixed main CDS."
                ),
                "required": False,
            },
            {
                "name": "kozak_quality",
                "description": (
                    "Simplified strong, weak, or mixed main-start context class."
                ),
                "required": False,
                "constraints": [
                    {
                        "kind": "allowed_values",
                        "values": ["strong", "weak", "mixed"],
                    }
                ],
            },
        ],
        "splits": [
            {
                "name": UTR_MRL_DEFAULT_SPLIT,
                "description": (
                    "All canonical eGFP unmodified-RNA replicate-mean measurements."
                ),
                "num_rows": EXPECTED_UTR_MRL_ROWS,
                "attributes": {
                    "reporter": "eGFP",
                    "rna_chemistry": "unmodified",
                    "cell_line": "HEK293T",
                    "variable_region_length": UTR_LENGTH,
                    "fixed_upstream_leader_length": len(PRIMER_SEQUENCE),
                    "main_start_junction": "<50-nt variable sequence>ATG",
                    "target_aggregation": "mean_of_two_replicates",
                },
            }
        ],
        "knowledge": {
            key: {
                field: value
                for field, value in specification.items()
                if field != "source_path"
            }
            for key, specification in KNOWLEDGE_RESOURCES.items()
        },
    }
    _write_json(collection_path, collection)
    _write_json(manifest_dir / f"{UTR_MRL_CONFIG_NAME}.json", manifest)
    _write_json(
        provenance_dir / f"{UTR_MRL_DEFAULT_SPLIT}.json",
        provenance,
    )
    _update_dataset_card(destination / "README.md", provenance)


def _update_dataset_card(path: Path, provenance: dict[str, Any]) -> None:
    if path.exists():
        card = DatasetCard.load(path)
    else:
        card = DatasetCard(
            "---\nlicense: other\nconfigs: []\n---\n\n"
            "# SciModelingBench Design-Bench Data\n\n"
            "Canonical observations used by the Design-Bench suite.\n"
        )
    metadata = card.data.to_dict()
    configs = [
        config
        for config in metadata.get("configs", [])
        if config.get("config_name") != UTR_MRL_CONFIG_NAME
    ]
    configs.append(
        {
            "config_name": UTR_MRL_CONFIG_NAME,
            "data_files": [
                {
                    "split": UTR_MRL_DEFAULT_SPLIT,
                    "path": provenance["artifact"]["path"],
                }
            ],
        }
    )
    metadata["configs"] = configs
    metadata["license"] = "other"
    card.data = DatasetCardData(**metadata)

    marker = "## UTR MRL"
    section = f"""
## UTR MRL

The `{UTR_MRL_CONFIG_NAME}` config contains {EXPECTED_UTR_MRL_ROWS:,}
replicate-mean MRL measurements for synthetic 50-nt UTRs in the eGFP,
unmodified-RNA condition. It retains deterministic uAUG and simplified Kozak
annotations for validation and compositional splitting; the benchmark
Protocol does not expose those annotations as model features.

See `provenance/{UTR_MRL_CONFIG_NAME}/{UTR_MRL_DEFAULT_SPLIT}.json`. The
upstream redistribution does not declare a specific data license, so the
config manifest records `license: unknown`.
"""
    if marker not in card.text:
        license_marker = "\n## License"
        if license_marker in card.text:
            before, after = card.text.split(license_marker, 1)
            card.text = before.rstrip() + "\n" + section + license_marker + after
        else:
            card.text = card.text.rstrip() + "\n" + section
    card.save(path)


def _write_knowledge_resources(destination: Path) -> list[dict[str, Any]]:
    source_root = resources.files("sci_modeling_bench").joinpath(
        "resources", "knowledge"
    )
    artifacts: list[dict[str, Any]] = []
    for key, specification in KNOWLEDGE_RESOURCES.items():
        content = source_root.joinpath(specification["source_path"]).read_bytes()
        output_path = destination / specification["path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(content)
        artifacts.append(
            {
                "key": key,
                "path": specification["path"],
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return artifacts


def _verify_source(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != SOURCE_SIZE:
        raise ValueError("mRNABench source Parquet size mismatch")
    if _sha256(path) != SOURCE_SHA256:
        raise ValueError("mRNABench source Parquet checksum mismatch")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _write_json(path: Path, content: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(content, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the replicate-mean eGFP UTR MRL HF config."
    )
    parser.add_argument("--source-parquet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    provenance = build_utr_mrl_release(args.source_parquet, args.output_dir)
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
