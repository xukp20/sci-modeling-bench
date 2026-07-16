"""Reproducibly build the canonical TFBind8 SIX6_REF_R1 release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import struct
import zipfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from datasets import Dataset as HFDataset
from datasets import Features, Value

SOURCE_ARCHIVE_NAME = "TF_binding_landscapes.zip"
SOURCE_ARCHIVE_FILE_ID = "1xS6N5qSwyFLC-ZPTADYrxZuPHjBkZCrj"
SOURCE_ARCHIVE_URL = (
    f"https://drive.google.com/file/d/{SOURCE_ARCHIVE_FILE_ID}/view"
)
SOURCE_ARCHIVE_SHA256 = (
    "30778471f1c5167698ac3d2b18fb54098ddaddbaa0550448afb25567e5075231"
)
SOURCE_ARCHIVE_SIZE = 100_799_246
SOURCE_MEMBER = (
    "TF_binding_landscapes/landscapes/SIX6_REF_R1_8mers.txt"
)
SOURCE_MEMBER_SIZE = 1_421_903
SOURCE_MEMBER_CRC32 = 0x02451F02
SOURCE_ROW_COUNT = 32_896
LEGACY_ROW_COUNT = 65_792
CANONICAL_ROW_COUNT = 65_536
EXPECTED_DUPLICATE_ROWS = 256

DESIGN_BENCH_COMMIT = "e52939588421b5433f6f2e9b359cf013c542bd89"
DESIGN_BENCH_PROCESSOR_URL = (
    "https://github.com/brandontrabucco/design-bench/blob/"
    f"{DESIGN_BENCH_COMMIT}/process/process_raw_tf_bind_8.py"
)
LEGACY_X_SHA256 = (
    "8957a728704d2e6c5dbba921dd9e16cbd76797489b081c5dc7f39ca23582d95d"
)
LEGACY_Y_SHA256 = (
    "a61dd97796a4173d3a2a3d016db44e5d42e1f1d6a39d9f1ad2465d2c6b94fcb7"
)

DATASET_REPO_ID = "sci-modeling-bench/design-bench"
CONFIG_NAME = "tfbind8"
SPLIT_NAME = "six6_ref_r1"
DATASET_VERSION = "1.0.0"

_HEADER = ("8-mer", "8-mer", "E-score", "Median", "Z-score")
_ALPHABET = frozenset("ACGT")
_TOKEN = {"A": 0, "C": 1, "G": 2, "T": 3}
_COMPLEMENT = str.maketrans("ACGT", "TGCA")


@dataclass(frozen=True, slots=True)
class LandscapeRow:
    sequence: str
    reverse_complement: str
    e_score: float


def build_tfbind8_release(
    archive_path: str | Path,
    output_dir: str | Path,
    *,
    legacy_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Build one upload-ready HF repository and return its provenance report."""

    archive = Path(archive_path)
    destination = Path(output_dir)
    _verify_archive(archive)
    rows = read_landscape(archive)
    sequences, e_scores, normalized_scores, canonical_stats = canonicalize_rows(rows)
    legacy_parity = verify_legacy_parity(rows, legacy_data_dir)

    data_path = destination / "data" / CONFIG_NAME / f"{SPLIT_NAME}.parquet"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    features = Features(
        {
            "sequence": Value("string"),
            "e_score": Value("float64"),
            "normalized_e_score": Value("float32"),
        }
    )
    dataset = HFDataset.from_dict(
        {
            "sequence": sequences,
            "e_score": e_scores,
            "normalized_e_score": normalized_scores,
        },
        features=features,
    )
    dataset.to_parquet(data_path)

    provenance = _build_provenance(
        archive,
        data_path,
        canonical_stats=canonical_stats,
        legacy_parity=legacy_parity,
    )
    _write_release_metadata(destination, provenance)
    return provenance


def read_landscape(archive_path: str | Path) -> tuple[LandscapeRow, ...]:
    """Read the published SIX6_REF_R1 landscape from its source archive."""

    with zipfile.ZipFile(archive_path) as archive:
        info = archive.getinfo(SOURCE_MEMBER)
        if info.file_size != SOURCE_MEMBER_SIZE or info.CRC != SOURCE_MEMBER_CRC32:
            raise ValueError("SIX6_REF_R1 archive member identity does not match")
        with archive.open(info) as raw_file:
            text_file = io.TextIOWrapper(raw_file, encoding="utf-8", newline="")
            reader = csv.reader(text_file, delimiter="\t")
            header = tuple(next(reader))
            if header != _HEADER:
                raise ValueError(f"unexpected SIX6_REF_R1 columns: {header}")

            rows: list[LandscapeRow] = []
            for source_row, values in enumerate(reader, start=2):
                if len(values) != len(_HEADER):
                    raise ValueError(
                        f"source row {source_row} has {len(values)} columns"
                    )
                sequence, reverse_complement, raw_e_score = values[:3]
                _validate_sequence(sequence, source_row)
                _validate_sequence(reverse_complement, source_row)
                if reverse_complement != _reverse_complement(sequence):
                    raise ValueError(
                        f"source row {source_row} is not a reverse-complement pair"
                    )
                rows.append(
                    LandscapeRow(
                        sequence=sequence,
                        reverse_complement=reverse_complement,
                        e_score=float(raw_e_score),
                    )
                )

    if len(rows) != SOURCE_ROW_COUNT:
        raise ValueError(
            f"expected {SOURCE_ROW_COUNT} source rows, found {len(rows)}"
        )
    return tuple(rows)


def canonicalize_rows(
    rows: Sequence[LandscapeRow],
) -> tuple[list[str], list[float], list[float], dict[str, Any]]:
    """Expand reverse complements and remove only exact sequence duplicates."""

    score_by_sequence: dict[str, float] = {}
    multiplicity: dict[str, int] = {}
    for row in rows:
        for sequence in (row.sequence, row.reverse_complement):
            previous = score_by_sequence.get(sequence)
            if previous is not None and previous != row.e_score:
                raise ValueError(f"conflicting labels for sequence {sequence}")
            score_by_sequence[sequence] = row.e_score
            multiplicity[sequence] = multiplicity.get(sequence, 0) + 1

    legacy_rows = sum(multiplicity.values())
    duplicate_rows = legacy_rows - len(score_by_sequence)
    if legacy_rows != LEGACY_ROW_COUNT:
        raise ValueError(f"expected {LEGACY_ROW_COUNT} expanded rows, got {legacy_rows}")
    if len(score_by_sequence) != CANONICAL_ROW_COUNT:
        raise ValueError(
            f"expected {CANONICAL_ROW_COUNT} unique sequences, "
            f"got {len(score_by_sequence)}"
        )
    if duplicate_rows != EXPECTED_DUPLICATE_ROWS:
        raise ValueError(
            f"expected {EXPECTED_DUPLICATE_ROWS} duplicate rows, got {duplicate_rows}"
        )
    if any(count not in (1, 2) for count in multiplicity.values()):
        raise ValueError("unexpected TFBind8 sequence multiplicity")

    sequences = sorted(score_by_sequence)
    if sequences != [_sequence_from_index(index) for index in range(4**8)]:
        raise ValueError("canonical sequences do not cover the complete DNA 8-mer space")

    e_scores = [score_by_sequence[sequence] for sequence in sequences]
    minimum = min(e_scores)
    maximum = max(e_scores)
    normalized_scores = [
        _float32((value - minimum) / (maximum - minimum)) for value in e_scores
    ]
    palindrome_count = sum(
        sequence == _reverse_complement(sequence) for sequence in sequences
    )
    if palindrome_count != EXPECTED_DUPLICATE_ROWS:
        raise ValueError(
            f"expected {EXPECTED_DUPLICATE_ROWS} reverse-complement palindromes, "
            f"got {palindrome_count}"
        )

    return sequences, e_scores, normalized_scores, {
        "source_rows": len(rows),
        "expanded_legacy_rows": legacy_rows,
        "canonical_rows": len(sequences),
        "duplicate_rows_removed": duplicate_rows,
        "reverse_complement_palindromes": palindrome_count,
        "duplicate_label_conflicts": 0,
        "e_score_minimum": minimum,
        "e_score_maximum": maximum,
        "normalized_e_score_minimum": min(normalized_scores),
        "normalized_e_score_maximum": max(normalized_scores),
        "ordering": "lexicographic A<C<G<T",
    }


def verify_legacy_parity(
    rows: Sequence[LandscapeRow],
    legacy_data_dir: str | Path | None,
) -> dict[str, Any]:
    """Optionally compare reconstructed arrays with pinned Design-Bench NPY files."""

    expected = {
        "x_sha256": LEGACY_X_SHA256,
        "y_sha256": LEGACY_Y_SHA256,
    }
    if legacy_data_dir is None:
        return {"status": "not_run", "expected": expected}

    import numpy as np

    directory = Path(legacy_data_dir)
    x_path = directory / "tf_bind_8-x-0.npy"
    y_path = directory / "tf_bind_8-y-0.npy"
    if _sha256(x_path) != LEGACY_X_SHA256 or _sha256(y_path) != LEGACY_Y_SHA256:
        raise ValueError("legacy Design-Bench NPY checksum mismatch")

    legacy_sequences = [row.sequence for row in rows] + [
        row.reverse_complement for row in rows
    ]
    rebuilt_x = np.asarray(
        [[_TOKEN[symbol] for symbol in sequence] for sequence in legacy_sequences],
        dtype=np.int32,
    )
    source_scores = np.asarray([row.e_score for row in rows], dtype=np.float64)
    source_normalized = (
        (source_scores - source_scores.min())
        / (source_scores.max() - source_scores.min())
    ).reshape(-1, 1)
    rebuilt_y = np.concatenate(
        [source_normalized, source_normalized], axis=0
    ).astype(np.float32)

    legacy_x = np.load(x_path, allow_pickle=False)
    legacy_y = np.load(y_path, allow_pickle=False)
    x_equal = bool(np.array_equal(rebuilt_x, legacy_x))
    y_equal = bool(np.array_equal(rebuilt_y, legacy_y))
    if not x_equal or not y_equal:
        raise ValueError("reconstructed arrays do not match Design-Bench exactly")
    return {
        "status": "verified",
        "expected": expected,
        "x_exact_equal": x_equal,
        "y_exact_equal": y_equal,
        "x_mismatch_elements": int(np.count_nonzero(rebuilt_x != legacy_x)),
        "y_mismatch_elements": int(np.count_nonzero(rebuilt_y != legacy_y)),
        "y_max_absolute_difference": float(np.max(np.abs(rebuilt_y - legacy_y))),
    }


def _verify_archive(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != SOURCE_ARCHIVE_SIZE:
        raise ValueError(
            f"source archive size mismatch: expected {SOURCE_ARCHIVE_SIZE}, "
            f"got {path.stat().st_size}"
        )
    checksum = _sha256(path)
    if checksum != SOURCE_ARCHIVE_SHA256:
        raise ValueError(
            f"source archive checksum mismatch: expected {SOURCE_ARCHIVE_SHA256}, "
            f"got {checksum}"
        )


def _build_provenance(
    archive_path: Path,
    data_path: Path,
    *,
    canonical_stats: dict[str, Any],
    legacy_parity: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": "design-bench/tfbind8",
        "dataset_version": DATASET_VERSION,
        "config": CONFIG_NAME,
        "split": SPLIT_NAME,
        "source_archive": {
            "name": SOURCE_ARCHIVE_NAME,
            "url": SOURCE_ARCHIVE_URL,
            "file_id": SOURCE_ARCHIVE_FILE_ID,
            "size_bytes": archive_path.stat().st_size,
            "sha256": _sha256(archive_path),
        },
        "source_member": {
            "path": SOURCE_MEMBER,
            "size_bytes": SOURCE_MEMBER_SIZE,
            "crc32": f"{SOURCE_MEMBER_CRC32:08x}",
            "columns": list(_HEADER),
        },
        "upstream": {
            "publication": (
                "Barrera et al., Survey of variation in human transcription "
                "factors reveals prevalent DNA binding changes, Science (2016)"
            ),
            "publication_url": "https://doi.org/10.1126/science.aad2257",
            "uniprobe_accession": "BAR15A",
            "uniprobe_url": (
                "https://thebrain.bwh.harvard.edu/uniprobe/downloads.php"
            ),
        },
        "transformation": {
            "design_bench_commit": DESIGN_BENCH_COMMIT,
            "design_bench_processor": DESIGN_BENCH_PROCESSOR_URL,
            "steps": [
                "validate each published 8-mer and reverse-complement pair",
                "expand both sequence columns with their shared E-score",
                "remove exact duplicate palindromic sequences",
                "sort the complete 8-mer space lexicographically using A<C<G<T",
                "min-max normalize E-score and cast normalized values to float32",
            ],
        },
        "canonicalization": canonical_stats,
        "legacy_parity": legacy_parity,
        "artifact": {
            "path": f"data/{CONFIG_NAME}/{SPLIT_NAME}.parquet",
            "size_bytes": data_path.stat().st_size,
            "sha256": _sha256(data_path),
            "features": {
                "sequence": "string",
                "e_score": "float64",
                "normalized_e_score": "float32",
            },
        },
    }


def _write_release_metadata(destination: Path, provenance: dict[str, Any]) -> None:
    manifest_dir = destination / "manifests"
    provenance_dir = destination / "provenance" / CONFIG_NAME
    manifest_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir.mkdir(parents=True, exist_ok=True)

    collection = {
        "schema_version": 1,
        "default_config": CONFIG_NAME,
        "configs": {CONFIG_NAME: {"manifest": f"manifests/{CONFIG_NAME}.json"}},
    }
    manifest = {
        "schema_version": 1,
        "dataset_id": "design-bench/tfbind8",
        "version": DATASET_VERSION,
        "default_split": SPLIT_NAME,
        "description": (
            "Complete canonical DNA 8-mer binding landscape for the SIX6 "
            "reference allele, PBM replicate 1."
        ),
        "license": "other",
        "source": [
            {
                "name": "Barrera et al. PBM TF binding landscapes",
                "url": SOURCE_ARCHIVE_URL,
                "version": "BAR15A",
                "checksum": f"sha256:{SOURCE_ARCHIVE_SHA256}",
                "notes": (
                    "Published contiguous 8-mer landscape; redistribution "
                    "terms are described in the dataset card."
                ),
            },
            {
                "name": "Design-Bench TFBind8 preprocessing",
                "url": DESIGN_BENCH_PROCESSOR_URL,
                "revision": DESIGN_BENCH_COMMIT,
            },
        ],
        "citation": [
            {
                "text": (
                    "Barrera et al. (2016), Survey of variation in human "
                    "transcription factors reveals prevalent DNA binding changes."
                ),
                "url": "https://doi.org/10.1126/science.aad2257",
            },
            {
                "text": (
                    "Trabucco et al. (2022), Design-Bench: Benchmarks for "
                    "Data-Driven Offline Model-Based Optimization."
                ),
                "url": "https://arxiv.org/abs/2202.08450",
            },
        ],
        "inputs": [
            {
                "name": "sequence",
                "description": "DNA sequence of exactly eight nucleotides.",
                "constraints": [
                    {"kind": "alphabet", "symbols": ["A", "C", "G", "T"]},
                    {"kind": "length", "minimum": 8, "maximum": 8},
                ],
            }
        ],
        "targets": [
            {
                "name": "e_score",
                "description": (
                    "Published PBM enrichment score for the SIX6_REF_R1 condition."
                ),
                "constraints": [
                    {"kind": "finite"},
                    {"kind": "range", "minimum": -0.5, "maximum": 0.5},
                ],
            },
            {
                "name": "normalized_e_score",
                "description": (
                    "Condition-level min-max normalization of the published E-score."
                ),
                "constraints": [
                    {"kind": "finite"},
                    {"kind": "range", "minimum": 0.0, "maximum": 1.0},
                ],
            },
        ],
        "context": [],
        "splits": [
            {
                "name": SPLIT_NAME,
                "description": "SIX6 reference allele, PBM replicate 1.",
                "num_rows": CANONICAL_ROW_COUNT,
                "attributes": {
                    "transcription_factor": "SIX6",
                    "allele": "REF",
                    "replicate": 1,
                    "assay": "universal protein-binding microarray",
                },
            }
        ],
        "knowledge": {},
    }

    _write_json(destination / "scimodelingbench.json", collection)
    _write_json(manifest_dir / f"{CONFIG_NAME}.json", manifest)
    _write_json(provenance_dir / f"{SPLIT_NAME}.json", provenance)
    (destination / "README.md").write_text(_dataset_card(provenance), encoding="utf-8")


def _dataset_card(provenance: dict[str, Any]) -> str:
    artifact = provenance["artifact"]
    return f"""---
configs:
- config_name: {CONFIG_NAME}
  data_files:
  - split: {SPLIT_NAME}
    path: {artifact['path']}
license: other
---

# SciModelingBench Design-Bench Data

This repository contains canonical scientific observations derived from
Design-Bench datasets. The first release provides the complete TFBind8
`SIX6_REF_R1` condition.

## TFBind8

The split contains all 65,536 DNA 8-mers and two targets:

- `e_score`: the published PBM enrichment statistic;
- `normalized_e_score`: the Design-Bench-compatible condition-level min-max
  normalization, stored as float32.

The canonical table removes only the 256 repeated reverse-complement
palindromes introduced when the two source sequence columns are concatenated.
Non-palindromic reverse-complement pairs remain separate candidates. Rows use
deterministic `A<C<G<T` lexicographic order.

```python
from datasets import load_dataset

data = load_dataset(
    "{DATASET_REPO_ID}",
    name="{CONFIG_NAME}",
    split="{SPLIT_NAME}",
)
```

SciModelingBench users can load the same pinned repository through
`TFBind8Dataset`.

## Provenance

- Upstream experiment: Barrera et al., Science 2016, UniPROBE accession
  `BAR15A`.
- Source archive SHA-256: `{SOURCE_ARCHIVE_SHA256}`.
- Canonical Parquet SHA-256: `{artifact['sha256']}`.
- Design-Bench legacy `x` and `y` parity: `{provenance['legacy_parity']['status']}`.
- Full machine-readable report:
  `provenance/{CONFIG_NAME}/{SPLIT_NAME}.json`.

## License

The upstream publication states that the TF PBM data were deposited in
UniPROBE under accession `BAR15A`. UniPROBE makes PBM result data downloadable;
probe-sequence files are subject to a separate academic-research-use license.
This release contains only derived contiguous 8-mer observations, not the
licensed 60-mer probe sequences. The original publication and UniPROBE terms
apply to the observations. Design-Bench's MIT license applies to its software,
not automatically to these data. This repository uses `license: other` instead
of asserting a standard data license that was not stated by the source.
"""


def _validate_sequence(sequence: str, source_row: int) -> None:
    if len(sequence) != 8 or set(sequence) - _ALPHABET:
        raise ValueError(f"invalid DNA 8-mer at source row {source_row}: {sequence}")


def _sequence_from_index(index: int) -> str:
    symbols = ["A"] * 8
    for position in range(7, -1, -1):
        index, digit = divmod(index, 4)
        symbols[position] = "ACGT"[digit]
    return "".join(symbols)


def _reverse_complement(sequence: str) -> str:
    return sequence.translate(_COMPLEMENT)[::-1]


def _float32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, content: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(content, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the canonical TFBind8 SIX6_REF_R1 HF repository."
    )
    parser.add_argument(
        "--archive",
        type=Path,
        required=True,
        help=f"Path to the pinned {SOURCE_ARCHIVE_NAME} source archive.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Destination for the upload-ready Hugging Face dataset repository.",
    )
    parser.add_argument(
        "--legacy-data-dir",
        type=Path,
        help="Optional directory containing the two Design-Bench NPY files.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    provenance = build_tfbind8_release(
        args.archive,
        args.output_dir,
        legacy_data_dir=args.legacy_data_dir,
    )
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
