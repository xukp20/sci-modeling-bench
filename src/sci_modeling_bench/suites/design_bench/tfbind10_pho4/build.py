"""Build the raw-replicate Pho4 BET-seq release from the Figshare archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import tarfile
from collections.abc import Iterable
from importlib import resources
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from sci_modeling_bench.suites.design_bench.tfbind10_pho4._sequence import (
    FIXED_EBOX_CORE,
    FLANK_LENGTH_PER_SIDE,
    FULL_SITE_TEMPLATE,
    SEQUENCE_COUNT,
    sequence_indices,
)
from sci_modeling_bench.suites.design_bench.tfbind10_pho4.dataset import (
    EXPECTED_BOUND_DEPTHS,
    EXPECTED_FINITE_DDG,
    EXPECTED_INPUT_DEPTHS,
    EXPECTED_NEGATIVE_INFINITY_DDG,
    EXPECTED_OBSERVATION_ROWS,
    EXPECTED_POSITIVE_INFINITY_DDG,
    EXPECTED_ROWS_BY_REPLICATE,
    TFBIND10_PHO4_CONFIG_NAME,
    TFBIND10_PHO4_DEFAULT_SPLIT,
    THERMAL_ENERGY_KCAL_PER_MOL,
)

SOURCE_ARCHIVE_NAME = "BET-seq_processed_data.tar.gz"
SOURCE_ARCHIVE_URL = "https://ndownloader.figshare.com/files/10071876"
SOURCE_ARCHIVE_PAGE = (
    "https://figshare.com/articles/dataset/BET-seq_Processed_Data/5728467"
)
SOURCE_ARCHIVE_VERSION = "v1"
SOURCE_ARCHIVE_SIZE = 861_436_605
SOURCE_ARCHIVE_MD5 = "f32aba52f72b5087788717333010369b"
SOURCE_ARCHIVE_SHA256 = (
    "3f6bc76273b00f5e1fb074b8e181077907eb265f12f443546f6da7db8c90f91e"
)
SOURCE_MEMBER = "data/Manuscript_Data/counts.txt.gz"
SOURCE_MEMBER_SIZE = 150_364_492
SOURCE_MEMBER_SHA256 = (
    "f88b8b7a1bd7d4cd69eca64f982bd6a27b46a325d26677b2f2f9e04c1b818a57"
)
SOURCE_TEXT_SIZE = 736_892_398
SOURCE_TEXT_SHA256 = "61394cbeaa820377cc6c72837424facacddfa4865383cd22a16897be1934d8f3"
SOURCE_TOTAL_ROWS = 7_265_823

BETSEQ_COMMIT = "d73e583dc2c0d73539b804f41775d8cb3d42e633"
BETSEQ_REPOSITORY = "https://github.com/FordyceLab/BET-seq"
DESIGN_BENCH_COMMIT = "e52939588421b5433f6f2e9b359cf013c542bd89"
DESIGN_BENCH_PROCESSOR = (
    "https://github.com/brandontrabucco/design-bench/blob/"
    f"{DESIGN_BENCH_COMMIT}/process/process_raw_tf_bind_10.py"
)

DATASET_REPO_ID = "sci-modeling-bench/design-bench"
DATASET_VERSION = "1.0.0"

KNOWLEDGE_RESOURCES = {
    "dna_structure_and_base_pairing": {
        "title": "DNA Structure and Base Pairing",
        "description": (
            "DNA strand direction, complementarity, canonical base pairing, "
            "grooves, and sequence-dependent duplex structure."
        ),
        "source_path": "shared/dna-structure-and-base-pairing.md",
        "path": "knowledge/shared/dna-structure-and-base-pairing.md",
        "media_type": "text/markdown",
    },
    "transcription_factor_dna_binding": {
        "title": "Transcription Factor–DNA Binding",
        "description": (
            "Physical modes of DNA recognition and the distinctions among "
            "affinity, specificity, occupancy, and regulatory activity."
        ),
        "source_path": "shared/transcription-factor-dna-binding.md",
        "path": "knowledge/shared/transcription-factor-dna-binding.md",
        "media_type": "text/markdown",
    },
    "binding_sites_motifs_and_sequence_context": {
        "title": "Binding Sites, Motifs, and Sequence Context",
        "description": (
            "Binding sites, consensus sequences, PFM/PWM representations, "
            "strand orientation, and nucleotide dependencies."
        ),
        "source_path": "shared/binding-sites-motifs-and-sequence-context.md",
        "path": "knowledge/shared/binding-sites-motifs-and-sequence-context.md",
        "media_type": "text/markdown",
    },
    "binding_affinity_and_thermodynamics": {
        "title": "Binding Affinity and Thermodynamics",
        "description": (
            "Equilibrium association and dissociation constants, occupancy, "
            "binding Gibbs energy, and kinetic rate constants."
        ),
        "source_path": "shared/binding-affinity-and-thermodynamics.md",
        "path": "knowledge/shared/binding-affinity-and-thermodynamics.md",
        "media_type": "text/markdown",
    },
    "basic_helix_loop_helix_and_ebox_recognition": {
        "title": "Basic Helix–Loop–Helix Proteins and E-box Recognition",
        "description": (
            "bHLH domain architecture, dimerization, E-box conventions, "
            "and recognition beyond a short motif core."
        ),
        "source_path": (
            "shared/basic-helix-loop-helix-and-ebox-recognition.md"
        ),
        "path": (
            "knowledge/shared/"
            "basic-helix-loop-helix-and-ebox-recognition.md"
        ),
        "media_type": "text/markdown",
    },
    "binding_energy_topography_by_sequencing": {
        "title": "Binding Energy Topography by Sequencing",
        "description": (
            "BET-seq assay principles, bound/input count enrichment, "
            "relative binding energy, and measurement limitations."
        ),
        "source_path": "shared/binding-energy-topography-by-sequencing.md",
        "path": "knowledge/shared/binding-energy-topography-by-sequencing.md",
        "media_type": "text/markdown",
    },
    "pho4_and_dna_recognition": {
        "title": "Pho4 and DNA Recognition",
        "description": (
            "Pho4 bHLH biology, CACGTG recognition, flanking-base contacts, "
            "and the distinction between affinity and cellular regulation."
        ),
        "source_path": (
            "design_bench/tfbind10_pho4/pho4-and-dna-recognition.md"
        ),
        "path": (
            "knowledge/design-bench/tfbind10_pho4/"
            "pho4-and-dna-recognition.md"
        ),
        "media_type": "text/markdown",
    },
}

_SOURCE_COLUMNS = {
    "flank": pa.string(),
    "tf_count": pa.int32(),
    "ref_count": pa.int32(),
    "tf": pa.float64(),
    "ref": pa.float64(),
    "ddG": pa.float64(),
    "protein": pa.string(),
    "rep": pa.int8(),
}
_OUTPUT_SCHEMA = pa.schema(
    [
        ("sequence", pa.string()),
        ("replicate_id", pa.int8()),
        ("bound_count", pa.int32()),
        ("input_count", pa.int32()),
        ("bound_fraction", pa.float64()),
        ("input_fraction", pa.float64()),
        ("observed_ddg", pa.float64()),
    ]
)


def build_tfbind10_pho4_release(
    archive_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Build an upload-ready HF config and return its provenance report."""

    archive = Path(archive_path)
    destination = Path(output_dir)
    _verify_archive(archive)
    data_path = (
        destination
        / "data"
        / TFBIND10_PHO4_CONFIG_NAME
        / f"{TFBIND10_PHO4_DEFAULT_SPLIT}.parquet"
    )
    data_path.parent.mkdir(parents=True, exist_ok=True)
    statistics = _write_pho4_parquet(archive, data_path)
    knowledge_artifacts = _write_knowledge_resources(destination)
    provenance = _build_provenance(
        archive,
        data_path,
        statistics,
        knowledge_artifacts=knowledge_artifacts,
    )
    _write_release_metadata(destination, provenance)
    return provenance


def _write_pho4_parquet(archive_path: Path, data_path: Path) -> dict[str, Any]:
    seen = np.zeros((4, SEQUENCE_COUNT), dtype=np.bool_)
    bound_by_replicate = np.zeros((4, SEQUENCE_COUNT), dtype=np.int32)
    input_by_replicate = np.zeros((4, SEQUENCE_COUNT), dtype=np.int32)
    rows_by_replicate = np.zeros(4, dtype=np.int64)
    finite_ddg = np.zeros(4, dtype=np.int64)
    positive_infinity_ddg = np.zeros(4, dtype=np.int64)
    negative_infinity_ddg = np.zeros(4, dtype=np.int64)
    source_rows = 0
    output_rows = 0

    with tarfile.open(archive_path, mode="r:gz") as archive:
        member = archive.getmember(SOURCE_MEMBER)
        if not member.isfile() or member.size != SOURCE_MEMBER_SIZE:
            raise ValueError("BET-seq counts member identity does not match")
        compressed = archive.extractfile(member)
        if compressed is None:
            raise ValueError("BET-seq counts member is unreadable")
        with gzip.GzipFile(fileobj=compressed, mode="rb") as source:
            reader = pacsv.open_csv(
                source,
                read_options=pacsv.ReadOptions(block_size=64 * 1024 * 1024),
                parse_options=pacsv.ParseOptions(delimiter="\t"),
                convert_options=pacsv.ConvertOptions(
                    include_columns=list(_SOURCE_COLUMNS),
                    column_types=_SOURCE_COLUMNS,
                    strings_can_be_null=False,
                ),
            )
            writer = pq.ParquetWriter(
                data_path,
                _OUTPUT_SCHEMA,
                compression="zstd",
                use_dictionary=["sequence"],
            )
            try:
                for batch in reader:
                    source_rows += batch.num_rows
                    selected = batch.filter(
                        pc.equal(batch.column("protein"), pa.scalar("pho4"))
                    )
                    if selected.num_rows == 0:
                        continue
                    _audit_batch(
                        selected,
                        seen=seen,
                        bound_by_replicate=bound_by_replicate,
                        input_by_replicate=input_by_replicate,
                        rows_by_replicate=rows_by_replicate,
                        finite_ddg=finite_ddg,
                        positive_infinity_ddg=positive_infinity_ddg,
                        negative_infinity_ddg=negative_infinity_ddg,
                    )
                    output = pa.RecordBatch.from_arrays(
                        [
                            selected.column("flank"),
                            selected.column("rep"),
                            selected.column("tf_count"),
                            selected.column("ref_count"),
                            selected.column("tf"),
                            selected.column("ref"),
                            selected.column("ddG"),
                        ],
                        schema=_OUTPUT_SCHEMA,
                    )
                    writer.write_batch(output)
                    output_rows += output.num_rows
            finally:
                writer.close()

    if source_rows != SOURCE_TOTAL_ROWS:
        raise ValueError(f"expected {SOURCE_TOTAL_ROWS} source rows, got {source_rows}")
    if output_rows != EXPECTED_OBSERVATION_ROWS:
        raise ValueError(
            f"expected {EXPECTED_OBSERVATION_ROWS} Pho4 rows, got {output_rows}"
        )
    if tuple(rows_by_replicate) != EXPECTED_ROWS_BY_REPLICATE:
        raise ValueError("unexpected Pho4 row counts by replicate")
    bound_depths = tuple(int(values.sum()) for values in bound_by_replicate)
    input_depths = tuple(int(values.sum()) for values in input_by_replicate)
    if bound_depths != EXPECTED_BOUND_DEPTHS:
        raise ValueError("unexpected Pho4 bound depths")
    if input_depths != EXPECTED_INPUT_DEPTHS:
        raise ValueError("unexpected Pho4 input depths")
    if tuple(finite_ddg) != EXPECTED_FINITE_DDG:
        raise ValueError("unexpected finite ddG counts")
    if tuple(positive_infinity_ddg) != EXPECTED_POSITIVE_INFINITY_DDG:
        raise ValueError("unexpected positive-infinity ddG counts")
    if tuple(negative_infinity_ddg) != EXPECTED_NEGATIVE_INFINITY_DDG:
        raise ValueError("unexpected negative-infinity ddG counts")
    if np.count_nonzero(np.any(seen, axis=0)) != SEQUENCE_COUNT:
        raise ValueError("Pho4 observations do not cover the complete DNA 10-mer space")
    if not np.array_equal(input_by_replicate[2], input_by_replicate[3]):
        raise ValueError("Pho4 replicates 3 and 4 must share the input library")

    return {
        "source_rows": source_rows,
        "pho4_observation_rows": output_rows,
        "unique_sequences": int(np.count_nonzero(np.any(seen, axis=0))),
        "rows_by_replicate": list(map(int, rows_by_replicate)),
        "bound_depths": list(bound_depths),
        "input_depths": list(input_depths),
        "finite_ddg_by_replicate": list(map(int, finite_ddg)),
        "positive_infinity_ddg_by_replicate": list(map(int, positive_infinity_ddg)),
        "negative_infinity_ddg_by_replicate": list(map(int, negative_infinity_ddg)),
        "duplicate_sequence_replicate_rows": 0,
        "shared_input_library": "replicates 3 and 4",
        "row_order": "pinned source order",
    }


def _audit_batch(
    batch: pa.RecordBatch,
    *,
    seen: np.ndarray,
    bound_by_replicate: np.ndarray,
    input_by_replicate: np.ndarray,
    rows_by_replicate: np.ndarray,
    finite_ddg: np.ndarray,
    positive_infinity_ddg: np.ndarray,
    negative_infinity_ddg: np.ndarray,
) -> None:
    sequences = batch.column("flank").to_pylist()
    sequence_ids = sequence_indices(sequences)
    replicate_ids = batch.column("rep").to_numpy(zero_copy_only=False).astype(np.int8)
    bound_counts = (
        batch.column("tf_count").to_numpy(zero_copy_only=False).astype(np.int32)
    )
    input_counts = (
        batch.column("ref_count").to_numpy(zero_copy_only=False).astype(np.int32)
    )
    bound_fractions = batch.column("tf").to_numpy(zero_copy_only=False)
    input_fractions = batch.column("ref").to_numpy(zero_copy_only=False)
    observed_ddg = batch.column("ddG").to_numpy(zero_copy_only=False)
    if np.any(replicate_ids < 1) or np.any(replicate_ids > 4):
        raise ValueError("Pho4 replicate IDs must be in [1, 4]")
    if np.any(bound_counts < 0) or np.any(input_counts < 0):
        raise ValueError("Pho4 counts must be non-negative")
    if np.any(~np.isfinite(bound_fractions)) or np.any(~np.isfinite(input_fractions)):
        raise ValueError("Pho4 source fractions must be finite")
    if np.any(bound_fractions < 0) or np.any(input_fractions < 0):
        raise ValueError("Pho4 source fractions must be non-negative")
    if np.any(np.isnan(observed_ddg)):
        raise ValueError("published Pho4 rows cannot contain NaN ddG")

    for replicate in range(1, 5):
        mask = replicate_ids == replicate
        if not np.any(mask):
            continue
        if not np.allclose(
            bound_fractions[mask],
            bound_counts[mask] / EXPECTED_BOUND_DEPTHS[replicate - 1],
            rtol=0.0,
            atol=1e-18,
        ):
            raise ValueError(
                f"Pho4 replicate {replicate} bound fractions do not match counts/depth"
            )
        if not np.allclose(
            input_fractions[mask],
            input_counts[mask] / EXPECTED_INPUT_DEPTHS[replicate - 1],
            rtol=0.0,
            atol=1e-18,
        ):
            raise ValueError(
                f"Pho4 replicate {replicate} input fractions do not match counts/depth"
            )
        indices = sequence_ids[mask]
        if np.any(seen[replicate - 1, indices]):
            raise ValueError("duplicate Pho4 sequence/replicate observation")
        if np.unique(indices).size != indices.size:
            raise ValueError("duplicate Pho4 sequence/replicate within source batch")
        seen[replicate - 1, indices] = True
        bound_by_replicate[replicate - 1, indices] = bound_counts[mask]
        input_by_replicate[replicate - 1, indices] = input_counts[mask]
        rows_by_replicate[replicate - 1] += int(np.count_nonzero(mask))
        finite_ddg[replicate - 1] += int(
            np.count_nonzero(np.isfinite(observed_ddg[mask]))
        )
        positive_infinity_ddg[replicate - 1] += int(
            np.count_nonzero(np.isposinf(observed_ddg[mask]))
        )
        negative_infinity_ddg[replicate - 1] += int(
            np.count_nonzero(np.isneginf(observed_ddg[mask]))
        )

    with np.errstate(divide="ignore", invalid="ignore"):
        expected_ddg = -THERMAL_ENERGY_KCAL_PER_MOL * np.log(
            bound_fractions / input_fractions
        )
    if not np.array_equal(np.isposinf(observed_ddg), np.isposinf(expected_ddg)):
        raise ValueError(
            "published positive-infinity ddG values do not match fractions"
        )
    if not np.array_equal(np.isneginf(observed_ddg), np.isneginf(expected_ddg)):
        raise ValueError(
            "published negative-infinity ddG values do not match fractions"
        )
    finite = np.isfinite(expected_ddg)
    if not np.allclose(
        observed_ddg[finite], expected_ddg[finite], rtol=0.0, atol=1e-12
    ):
        raise ValueError("published finite ddG values do not match source fractions")


def _verify_archive(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != SOURCE_ARCHIVE_SIZE:
        raise ValueError("BET-seq archive size mismatch")
    if _digest(path, "md5") != SOURCE_ARCHIVE_MD5:
        raise ValueError("BET-seq archive MD5 mismatch")
    if _digest(path, "sha256") != SOURCE_ARCHIVE_SHA256:
        raise ValueError("BET-seq archive SHA-256 mismatch")
    with tarfile.open(path, mode="r:gz") as archive:
        member = archive.getmember(SOURCE_MEMBER)
        source = archive.extractfile(member)
        if source is None or member.size != SOURCE_MEMBER_SIZE:
            raise ValueError("BET-seq counts member identity mismatch")
        digest = hashlib.sha256()
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
        if digest.hexdigest() != SOURCE_MEMBER_SHA256:
            raise ValueError("BET-seq counts member SHA-256 mismatch")


def _build_provenance(
    archive: Path,
    data_path: Path,
    statistics: dict[str, Any],
    *,
    knowledge_artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": "design-bench/tfbind10-pho4",
        "dataset_version": DATASET_VERSION,
        "config": TFBIND10_PHO4_CONFIG_NAME,
        "split": TFBIND10_PHO4_DEFAULT_SPLIT,
        "source_archive": {
            "name": SOURCE_ARCHIVE_NAME,
            "url": SOURCE_ARCHIVE_URL,
            "page": SOURCE_ARCHIVE_PAGE,
            "version": SOURCE_ARCHIVE_VERSION,
            "size_bytes": archive.stat().st_size,
            "md5": SOURCE_ARCHIVE_MD5,
            "sha256": SOURCE_ARCHIVE_SHA256,
        },
        "source_member": {
            "path": SOURCE_MEMBER,
            "compressed_size_bytes": SOURCE_MEMBER_SIZE,
            "compressed_sha256": SOURCE_MEMBER_SHA256,
            "uncompressed_size_bytes": SOURCE_TEXT_SIZE,
            "uncompressed_sha256": SOURCE_TEXT_SHA256,
        },
        "transformation": {
            "steps": [
                "select rows whose published protein field is pho4",
                "rename source columns without changing observation granularity",
                "cast counts and replicate IDs to bounded integer storage types",
                "preserve all finite and infinite published per-replicate ddG values",
                "retain source row order and do not create complement augmentation",
            ],
            "betseq_repository": BETSEQ_REPOSITORY,
            "betseq_commit": BETSEQ_COMMIT,
            "legacy_design_bench_processor": DESIGN_BENCH_PROCESSOR,
            "legacy_design_bench_commit": DESIGN_BENCH_COMMIT,
        },
        "statistics": statistics,
        "knowledge": knowledge_artifacts,
        "artifact": {
            "path": (
                f"data/{TFBIND10_PHO4_CONFIG_NAME}/"
                f"{TFBIND10_PHO4_DEFAULT_SPLIT}.parquet"
            ),
            "size_bytes": data_path.stat().st_size,
            "sha256": _digest(data_path, "sha256"),
            "features": {field.name: str(field.type) for field in _OUTPUT_SCHEMA},
        },
    }


def _write_release_metadata(destination: Path, provenance: dict[str, Any]) -> None:
    manifest_dir = destination / "manifests"
    provenance_dir = destination / "provenance" / TFBIND10_PHO4_CONFIG_NAME
    manifest_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir.mkdir(parents=True, exist_ok=True)

    collection_path = destination / "scimodelingbench.json"
    if collection_path.exists():
        collection = json.loads(collection_path.read_text(encoding="utf-8"))
    else:
        collection = {
            "schema_version": 1,
            "default_config": TFBIND10_PHO4_CONFIG_NAME,
            "configs": {},
        }
    collection["configs"][TFBIND10_PHO4_CONFIG_NAME] = {
        "manifest": f"manifests/{TFBIND10_PHO4_CONFIG_NAME}.json"
    }
    manifest = {
        "schema_version": 1,
        "dataset_id": "design-bench/tfbind10-pho4",
        "version": DATASET_VERSION,
        "default_split": TFBIND10_PHO4_DEFAULT_SPLIT,
        "description": (
            "Published Pho4 BET-seq read-count observations for the complete "
            "DNA 10-mer flank space, preserving four experimental replicates."
        ),
        "license": "cc-by-4.0",
        "source": [
            {
                "name": "BET-seq Processed Data",
                "url": SOURCE_ARCHIVE_PAGE,
                "version": SOURCE_ARCHIVE_VERSION,
                "checksum": f"sha256:{SOURCE_ARCHIVE_SHA256}",
                "notes": "Figshare DOI 10.6084/m9.figshare.5728467.v1.",
            },
            {
                "name": "BET-seq analysis code",
                "url": BETSEQ_REPOSITORY,
                "revision": BETSEQ_COMMIT,
            },
            {
                "name": "Design-Bench TFBind10 preprocessing",
                "url": DESIGN_BENCH_PROCESSOR,
                "revision": DESIGN_BENCH_COMMIT,
                "notes": "Recorded for legacy task provenance; not replayed by this release.",
            },
        ],
        "citation": [
            {
                "text": (
                    "Le et al. (2018), Comprehensive, high-resolution binding "
                    "energy landscapes reveal context dependencies of "
                    "transcription factor binding."
                ),
                "url": "https://doi.org/10.1073/pnas.1715888115",
            },
            {
                "text": "Fordyce Lab (2018), BET-seq Processed Data.",
                "url": "https://doi.org/10.6084/m9.figshare.5728467.v1",
            },
            {
                "text": "Trabucco et al. (2022), Design-Bench.",
                "url": "https://arxiv.org/abs/2202.08450",
            },
        ],
        "inputs": [
            {
                "name": "sequence",
                "description": (
                    "Ten variable DNA nucleotides flanking the fixed "
                    f"{FIXED_EBOX_CORE} E-box core. Characters 1 through "
                    f"{FLANK_LENGTH_PER_SIDE} are immediately upstream of the "
                    f"core and characters {FLANK_LENGTH_PER_SIDE + 1} through "
                    "10 are immediately downstream, in the displayed strand's "
                    "5-prime-to-3-prime orientation. The fixed core is excluded "
                    f"from this field; the full assayed site follows the template "
                    f"{FULL_SITE_TEMPLATE}."
                ),
                "constraints": [
                    {"kind": "alphabet", "symbols": ["A", "C", "G", "T"]},
                    {"kind": "length", "minimum": 10, "maximum": 10},
                ],
            }
        ],
        "targets": [
            {
                "name": "observed_ddg",
                "description": (
                    "Published per-replicate -RT log(bound_fraction/input_fraction); "
                    "zero counts are retained as signed infinities."
                ),
                "unit": "kcal/mol",
            }
        ],
        "context": [
            {
                "name": "replicate_id",
                "description": "Published Pho4 experimental replicate identifier.",
                "required": False,
                "constraints": [{"kind": "allowed_values", "values": [1, 2, 3, 4]}],
            },
            {
                "name": "bound_count",
                "description": "Raw read count in the Pho4-bound library.",
                "required": False,
                "constraints": [{"kind": "range", "minimum": 0}],
            },
            {
                "name": "input_count",
                "description": "Raw read count in the corresponding input library.",
                "required": False,
                "constraints": [{"kind": "range", "minimum": 0}],
            },
            {
                "name": "bound_fraction",
                "description": "Published bound_count divided by replicate bound depth.",
                "required": False,
                "constraints": [
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0.0, "maximum": 1.0},
                ],
            },
            {
                "name": "input_fraction",
                "description": "Published input_count divided by replicate input depth.",
                "required": False,
                "constraints": [
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0.0, "maximum": 1.0},
                ],
            },
        ],
        "splits": [
            {
                "name": TFBIND10_PHO4_DEFAULT_SPLIT,
                "description": "All published Pho4 source observations across four replicates.",
                "num_rows": EXPECTED_OBSERVATION_ROWS,
                "attributes": {
                    "protein": "Pho4",
                    "assay": "BET-seq",
                    "sequence_length": 10,
                    "unique_sequences": SEQUENCE_COUNT,
                    "replicates": 4,
                    "shared_input_library": "replicates 3 and 4",
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
    _write_json(manifest_dir / f"{TFBIND10_PHO4_CONFIG_NAME}.json", manifest)
    _write_json(
        provenance_dir / f"{TFBIND10_PHO4_DEFAULT_SPLIT}.json",
        provenance,
    )
    readme = destination / "README.md"
    if not readme.exists():
        readme.write_text(_dataset_card(provenance), encoding="utf-8")


def _dataset_card(provenance: dict[str, Any]) -> str:
    artifact = provenance["artifact"]
    return f"""---
configs:
- config_name: {TFBIND10_PHO4_CONFIG_NAME}
  data_files:
  - split: {TFBIND10_PHO4_DEFAULT_SPLIT}
    path: {artifact["path"]}
license: cc-by-4.0
---

# SciModelingBench Pho4 TFBind10 Data

This config preserves the published raw count, fraction, and per-replicate ddG
observations for all Pho4 DNA 10-mer flanks. It does not publish the derived
posterior affinity labels used by the benchmark Task.

```python
from datasets import load_dataset

data = load_dataset(
    "{DATASET_REPO_ID}",
    name="{TFBIND10_PHO4_CONFIG_NAME}",
    split="{TFBIND10_PHO4_DEFAULT_SPLIT}",
)
```

Source archive SHA-256: `{SOURCE_ARCHIVE_SHA256}`.
Canonical Parquet SHA-256: `{artifact["sha256"]}`.
Machine-readable provenance is stored at
`provenance/{TFBIND10_PHO4_CONFIG_NAME}/{TFBIND10_PHO4_DEFAULT_SPLIT}.json`.
"""


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _write_json(path: Path, content: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(content, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the raw-replicate Pho4 TFBind10 HF config."
    )
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    provenance = build_tfbind10_pho4_release(args.archive, args.output_dir)
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
