"""Build the canonical protein-level Sarkisyan GFP release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections.abc import Iterable
from importlib import resources
from pathlib import Path
from typing import Any

import numpy as np
from datasets import Dataset as HFDataset
from datasets import Features, Sequence, Value
from huggingface_hub import DatasetCard
from huggingface_hub.repocard_data import DatasetCardData

from sci_modeling_bench.suites.design_bench.gfp._sequence import (
    apply_amino_acid_mutations,
    mutation_count,
    read_reference_fasta,
    translate_reference,
)
from sci_modeling_bench.suites.design_bench.gfp.dataset import (
    EXPECTED_GFP_NUCLEOTIDE_OBSERVATIONS,
    EXPECTED_GFP_PROTEINS,
    GFP_CONFIG_NAME,
    GFP_DEFAULT_SPLIT,
    protein_id,
)

FIGSHARE_ARTICLE_ID = 3_102_154
FIGSHARE_DOI = "10.6084/m9.figshare.3102154.v1"
FIGSHARE_URL = f"https://doi.org/{FIGSHARE_DOI}"
DATASET_REPO_ID = "sci-modeling-bench/design-bench"
DATASET_ID = "design-bench/gfp"
DATASET_VERSION = "1.0.0"

SOURCE_ARTIFACTS = {
    "amino_acid_table": {
        "filename": "amino_acid_genotypes_to_brightness.tsv",
        "file_id": 4_820_647,
        "size_bytes": 2_334_128,
        "sha256": "5581230b9888f9960708a4769ce1c9b4453561f0b5f0374525445b4a984d54d5",
        "rows": 54_025,
    },
    "nucleotide_table": {
        "filename": "nucleotide_genotypes_to_brightness.tsv",
        "file_id": 4_820_650,
        "size_bytes": 4_131_487,
        "sha256": "d9c271c9706cefd04d790a1d30158602cac273ddc10c698d292ab01407798240",
        "rows": 58_417,
    },
    "reference_fasta": {
        "filename": "avGFP_reference_sequence.fa",
        "file_id": 4_820_653,
        "size_bytes": 740,
        "sha256": "2559ee1afe9d0f41e03ea75db96448a34178c2dd597c78e08f01b1ee4ab5e248",
    },
    "barcode_table": {
        "filename": "barcodes_to_brightness.tsv",
        "file_id": 4_820_656,
        "size_bytes": 5_599_807,
        "sha256": "1f63982aa666febaa9b3045431e7df3feddb8638830b6c76bfc11237ab8dafbc",
        "rows": 68_039,
    },
    "genotypes_table": {
        "filename": "genotypes.tsv",
        "file_id": 4_820_659,
        "size_bytes": 30_062_254,
        "sha256": "1682741c5f1237b30653658c904c2048ad0d9dd2671576e9b285f2538d139352",
        "rows": 302_998,
    },
}

_AMINO_COLUMNS = ("aaMutations", "uniqueBarcodes", "medianBrightness", "std")
_NUCLEOTIDE_COLUMNS = (
    "nMutations",
    "aaMutations",
    "uniqueBarcodes",
    "medianBrightness",
    "std",
)
_BARCODE_COLUMNS = ("barcode", "nMutations", "aaMutations", "brightness")
_GENOTYPE_COLUMNS = (
    "barcode",
    "minCoverage",
    "meanCoverage",
    "nMutations",
    "aaMutations",
)

KNOWLEDGE_RESOURCES = {
    "mixcr_mutation_encoding": {
        "title": "MiXCR Mutation Encoding",
        "description": (
            "Reference-relative substitution, deletion, and insertion notation, "
            "zero-based coordinates, validation, and amino-acid adaptation."
        ),
        "source_path": "shared/mixcr-mutation-encoding.md",
        "path": "knowledge/shared/mixcr-mutation-encoding.md",
        "media_type": "text/markdown",
    },
    "protein_sequences_amino_acids_and_substitutions": {
        "title": "Protein Sequences, Amino Acids, and Substitutions",
        "description": (
            "Protein sequence notation, amino-acid physicochemical classes, "
            "residue coordinates, and substitution semantics."
        ),
        "source_path": "shared/protein-sequences-amino-acids-and-substitutions.md",
        "path": (
            "knowledge/shared/"
            "protein-sequences-amino-acids-and-substitutions.md"
        ),
        "media_type": "text/markdown",
    },
    "protein_folding_stability_and_mutational_effects": {
        "title": "Protein Folding, Stability, and Mutational Effects",
        "description": (
            "Folding thermodynamics and kinetics, structural environments, "
            "aggregation, and mechanisms by which substitutions alter proteins."
        ),
        "source_path": "shared/protein-folding-stability-and-mutational-effects.md",
        "path": (
            "knowledge/shared/"
            "protein-folding-stability-and-mutational-effects.md"
        ),
        "media_type": "text/markdown",
    },
    "protein_fitness_landscapes_and_epistasis": {
        "title": "Protein Fitness Landscapes and Epistasis",
        "description": (
            "Genotype-to-phenotype landscapes, mutational neighborhoods, "
            "additive expectations, and magnitude and sign epistasis."
        ),
        "source_path": "shared/protein-fitness-landscapes-and-epistasis.md",
        "path": "knowledge/shared/protein-fitness-landscapes-and-epistasis.md",
        "media_type": "text/markdown",
    },
    "fluorescence_photophysics_and_brightness": {
        "title": "Fluorescence Photophysics and Brightness",
        "description": (
            "Absorption, excitation, emission, extinction coefficient, quantum "
            "yield, molecular brightness, photobleaching, and environmental effects."
        ),
        "source_path": "shared/fluorescence-photophysics-and-brightness.md",
        "path": "knowledge/shared/fluorescence-photophysics-and-brightness.md",
        "media_type": "text/markdown",
    },
    "flow_cytometry_and_barcode_linked_fluorescence_measurement": {
        "title": "Flow Cytometry and Barcode-Linked Fluorescence Measurement",
        "description": (
            "Single-cell fluorescence measurement, sorting bins, calibration, "
            "autofluorescence, barcode linkage, coverage, and aggregation."
        ),
        "source_path": (
            "shared/flow-cytometry-and-barcode-linked-fluorescence-measurement.md"
        ),
        "path": (
            "knowledge/shared/"
            "flow-cytometry-and-barcode-linked-fluorescence-measurement.md"
        ),
        "media_type": "text/markdown",
    },
    "gfp_structure_chromophore_and_maturation": {
        "title": "GFP Structure, Chromophore, and Maturation",
        "description": (
            "The GFP beta-barrel, central chromophore-forming residues, "
            "autocatalytic maturation, oxygen dependence, and protonation."
        ),
        "source_path": (
            "design_bench/gfp/gfp-structure-chromophore-and-maturation.md"
        ),
        "path": (
            "knowledge/design-bench/gfp/"
            "gfp-structure-chromophore-and-maturation.md"
        ),
        "media_type": "text/markdown",
    },
    "aequorea_victoria_gfp_and_engineered_variants": {
        "title": "Aequorea victoria GFP and Engineered Variants",
        "description": (
            "Experimentally established properties of avGFP and selected "
            "engineered GFP variants, with conventional residue numbering."
        ),
        "source_path": (
            "design_bench/gfp/aequorea-victoria-gfp-and-engineered-variants.md"
        ),
        "path": (
            "knowledge/design-bench/gfp/"
            "aequorea-victoria-gfp-and-engineered-variants.md"
        ),
        "media_type": "text/markdown",
    },
}


def build_gfp_release(
    amino_acid_table: str | Path,
    nucleotide_table: str | Path,
    barcode_table: str | Path,
    genotypes_table: str | Path,
    reference_fasta: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Build an upload-ready GFP config and return its provenance."""

    sources = {
        "amino_acid_table": Path(amino_acid_table),
        "nucleotide_table": Path(nucleotide_table),
        "barcode_table": Path(barcode_table),
        "genotypes_table": Path(genotypes_table),
        "reference_fasta": Path(reference_fasta),
    }
    for name, path in sources.items():
        _verify_source(path, SOURCE_ARTIFACTS[name])

    rows, statistics, reference_sequence = canonicalize_sources(
        sources["amino_acid_table"],
        sources["nucleotide_table"],
        sources["barcode_table"],
        sources["genotypes_table"],
        sources["reference_fasta"],
    )
    destination = Path(output_dir)
    data_path = destination / "data" / GFP_CONFIG_NAME / f"{GFP_DEFAULT_SPLIT}.parquet"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data = HFDataset.from_dict(rows, features=_features())
    data.to_parquet(data_path)

    provenance = _provenance(sources, data_path, statistics, reference_sequence)
    provenance["knowledge"] = _write_knowledge_resources(destination)
    _write_release_metadata(destination, provenance)
    return provenance


def canonicalize_sources(
    amino_acid_table: str | Path,
    nucleotide_table: str | Path,
    barcode_table: str | Path,
    genotypes_table: str | Path,
    reference_fasta: str | Path,
) -> tuple[dict[str, list[Any]], dict[str, Any], str]:
    """Build one canonical protein row with aligned lower-level observations."""

    reference_dna = read_reference_fasta(Path(reference_fasta).read_text(encoding="ascii"))
    reference = translate_reference(reference_dna)

    proteins: dict[str, dict[str, Any]] = {}
    stop_proteins = 0
    for row in _read_tsv(Path(amino_acid_table), _AMINO_COLUMNS):
        notation = row["aaMutations"]
        sequence = apply_amino_acid_mutations(reference, notation)
        if "*" in sequence:
            stop_proteins += 1
            continue
        if notation in proteins:
            raise ValueError(f"duplicate amino-acid genotype {notation!r}")
        proteins[notation] = {
            "protein_id": protein_id(sequence),
            "sequence": sequence,
            "aa_mutations": notation,
            "mutation_count": mutation_count(notation),
            "unique_barcodes": _positive_int(row["uniqueBarcodes"], "uniqueBarcodes"),
            "median_log10_brightness": _finite_float(
                row["medianBrightness"], "medianBrightness"
            ),
            "brightness_std": _optional_nonnegative_float(row["std"], "std"),
            "nucleotide_records": [],
            "barcode_records": [],
        }
    if len(proteins) != EXPECTED_GFP_PROTEINS or stop_proteins != 2_310:
        raise ValueError(
            f"expected {EXPECTED_GFP_PROTEINS} clean and 2310 stop proteins, "
            f"got {len(proteins)} and {stop_proteins}"
        )
    sequences = [row["sequence"] for row in proteins.values()]
    if len(set(sequences)) != len(sequences):
        raise ValueError("clean amino-acid genotypes must map to unique proteins")

    stop_nucleotides = 0
    clean_nucleotides = 0
    for row in _read_tsv(Path(nucleotide_table), _NUCLEOTIDE_COLUMNS):
        aa_notation = row["aaMutations"]
        if aa_notation not in proteins:
            if "*" not in aa_notation:
                raise ValueError(f"orphan nucleotide genotype for {aa_notation!r}")
            stop_nucleotides += 1
            continue
        record = {
            "mutations": row["nMutations"],
            "mutation_count": mutation_count(row["nMutations"]),
            "unique_barcodes": _positive_int(row["uniqueBarcodes"], "uniqueBarcodes"),
            "median_log10_brightness": _finite_float(
                row["medianBrightness"], "medianBrightness"
            ),
            "brightness_std": _optional_nonnegative_float(row["std"], "std"),
        }
        proteins[aa_notation]["nucleotide_records"].append(record)
        clean_nucleotides += 1
    if clean_nucleotides != EXPECTED_GFP_NUCLEOTIDE_OBSERVATIONS:
        raise ValueError(
            f"expected {EXPECTED_GFP_NUCLEOTIDE_OBSERVATIONS} clean nucleotide rows, "
            f"got {clean_nucleotides}"
        )

    barcode_rows = list(_read_tsv(Path(barcode_table), _BARCODE_COLUMNS))
    barcode_ids = [row["barcode"] for row in barcode_rows]
    if len(set(barcode_ids)) != len(barcode_ids):
        raise ValueError("filtered source barcode IDs must be unique")
    wanted = set(barcode_ids)
    genotype_by_barcode: dict[str, dict[str, str]] = {}
    for row in _read_tsv(Path(genotypes_table), _GENOTYPE_COLUMNS):
        barcode = row["barcode"]
        if barcode in wanted:
            genotype_by_barcode[barcode] = row
    if set(genotype_by_barcode) != wanted:
        missing = sorted(wanted - set(genotype_by_barcode))
        raise ValueError(f"filtered barcodes missing genotype context: {missing[:3]}")

    stop_barcodes = 0
    clean_barcodes = 0
    for row in barcode_rows:
        genotype = genotype_by_barcode[row["barcode"]]
        if (row["nMutations"], row["aaMutations"]) != (
            genotype["nMutations"],
            genotype["aaMutations"],
        ):
            raise ValueError(f"genotype disagreement for barcode {row['barcode']!r}")
        aa_notation = row["aaMutations"]
        if aa_notation not in proteins:
            if "*" not in aa_notation:
                raise ValueError(f"orphan filtered barcode for {aa_notation!r}")
            stop_barcodes += 1
            continue
        proteins[aa_notation]["barcode_records"].append(
            {
                "barcode": row["barcode"],
                "nucleotide_mutations": row["nMutations"],
                "nucleotide_mutation_count": mutation_count(row["nMutations"]),
                "log10_brightness": _finite_float(row["brightness"], "brightness"),
                "min_coverage": _nonnegative_int(
                    genotype["minCoverage"], "minCoverage"
                ),
                "mean_coverage": _nonnegative_float(
                    genotype["meanCoverage"], "meanCoverage"
                ),
            }
        )
        clean_barcodes += 1

    canonical_rows: list[dict[str, Any]] = []
    for row in proteins.values():
        nucleotide_records = sorted(
            row.pop("nucleotide_records"), key=lambda item: item["mutations"]
        )
        barcode_records = sorted(
            row.pop("barcode_records"), key=lambda item: item["barcode"]
        )
        if sum(item["unique_barcodes"] for item in nucleotide_records) != row["unique_barcodes"]:
            raise ValueError(
                f"nucleotide barcode totals disagree for {row['protein_id']}"
            )
        if len(barcode_records) != row["unique_barcodes"]:
            raise ValueError(f"filtered barcode count disagrees for {row['protein_id']}")
        row.update(
            {
                "nucleotide_mutations": [item["mutations"] for item in nucleotide_records],
                "nucleotide_mutation_counts": [
                    item["mutation_count"] for item in nucleotide_records
                ],
                "nucleotide_unique_barcodes": [
                    item["unique_barcodes"] for item in nucleotide_records
                ],
                "nucleotide_median_log10_brightness": [
                    item["median_log10_brightness"] for item in nucleotide_records
                ],
                "nucleotide_brightness_std": [
                    item["brightness_std"] for item in nucleotide_records
                ],
                "source_barcode_ids": [item["barcode"] for item in barcode_records],
                "barcode_nucleotide_mutations": [
                    item["nucleotide_mutations"] for item in barcode_records
                ],
                "barcode_nucleotide_mutation_counts": [
                    item["nucleotide_mutation_count"] for item in barcode_records
                ],
                "barcode_log10_brightness": [
                    item["log10_brightness"] for item in barcode_records
                ],
                "barcode_min_coverage": [
                    item["min_coverage"] for item in barcode_records
                ],
                "barcode_mean_coverage": [
                    item["mean_coverage"] for item in barcode_records
                ],
            }
        )
        canonical_rows.append(row)
    canonical_rows.sort(key=lambda row: row["protein_id"])

    columns = {
        name: [row[name] for row in canonical_rows]
        for name in _features()
    }
    targets = np.asarray(columns["median_log10_brightness"], dtype=np.float64)
    cutoff = float(np.percentile(targets, 80.0, method="linear"))
    visible = targets <= cutoff
    candidates = targets > cutoff
    statistics = {
        "source_rows": {
            "amino_acid": len(proteins) + stop_proteins,
            "nucleotide": clean_nucleotides + stop_nucleotides,
            "filtered_barcode": clean_barcodes + stop_barcodes,
            "genotype": SOURCE_ARTIFACTS["genotypes_table"]["rows"],
        },
        "filtered_stop_rows": {
            "amino_acid": stop_proteins,
            "nucleotide": stop_nucleotides,
            "filtered_barcode": stop_barcodes,
        },
        "canonical_proteins": len(canonical_rows),
        "clean_nucleotide_observations": clean_nucleotides,
        "clean_barcode_observations": clean_barcodes,
        "target": {
            "minimum": float(targets.min()),
            "median": float(np.median(targets)),
            "maximum": float(targets.max()),
            "floor_rows_at_log10_20_plus_0_001": int(
                np.count_nonzero(targets <= np.log10(20.0) + 0.001)
            ),
        },
        "multi_barcode_proteins": int(
            np.count_nonzero(np.asarray(columns["unique_barcodes"]) > 1)
        ),
        "rows_with_brightness_std": int(
            sum(value is not None for value in columns["brightness_std"])
        ),
        "default_protocol": {
            "visible_max_percentile": 80.0,
            "cutoff": cutoff,
            "visible_proteins": int(np.count_nonzero(visible)),
            "candidate_pool": int(np.count_nonzero(candidates)),
        },
    }
    return columns, statistics, reference


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


def _provenance(
    sources: dict[str, Path],
    data_path: Path,
    statistics: dict[str, Any],
    reference_sequence: str,
) -> dict[str, Any]:
    source_records = []
    for name, path in sources.items():
        specification = SOURCE_ARTIFACTS[name]
        source_records.append(
            {
                "role": name,
                "filename": specification["filename"],
                "figshare_file_id": specification["file_id"],
                "download_url": (
                    "https://ndownloader.figshare.com/files/"
                    f"{specification['file_id']}"
                ),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return {
        "schema_version": 1,
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "config": GFP_CONFIG_NAME,
        "split": GFP_DEFAULT_SPLIT,
        "source": {
            "figshare_article_id": FIGSHARE_ARTICLE_ID,
            "doi": FIGSHARE_DOI,
            "version": 1,
            "license": "CC BY 4.0",
            "artifacts": source_records,
            "optional_population_archive": {
                "filename": "populations.zip",
                "figshare_file_id": 4_820_662,
                "size_bytes": 206_224_415,
                "md5": "fca7709a544cac7f7b328d4ad35dbc18",
                "included": False,
            },
        },
        "reference": {
            "protein_sequence": reference_sequence,
            "protein_length": len(reference_sequence),
            "mutation_indexing": "zero_based",
        },
        "transformation": {
            "steps": [
                "verify five pinned Figshare v1 source artifacts",
                "translate the frozen avGFP nucleotide reference",
                "reconstruct proteins from zero-based amino-acid substitutions",
                "remove stop-containing protein genotypes",
                "retain the author protein-level median brightness without reaggregation",
                "join clean nucleotide aggregates by amino-acid genotype",
                "join filtered barcode brightness to genotype coverage by barcode",
                "retain aligned lower-level observations as list columns",
                "sort canonical rows by SHA-256-derived protein_id",
            ]
        },
        "statistics": statistics,
        "artifact": {
            "path": f"data/{GFP_CONFIG_NAME}/{GFP_DEFAULT_SPLIT}.parquet",
            "size_bytes": data_path.stat().st_size,
            "sha256": _sha256(data_path),
        },
    }


def _write_release_metadata(destination: Path, provenance: dict[str, Any]) -> None:
    manifest_dir = destination / "manifests"
    provenance_dir = destination / "provenance" / GFP_CONFIG_NAME
    manifest_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir.mkdir(parents=True, exist_ok=True)

    collection_path = destination / "scimodelingbench.json"
    if collection_path.exists():
        collection = json.loads(collection_path.read_text(encoding="utf-8"))
    else:
        collection = {
            "schema_version": 1,
            "default_config": GFP_CONFIG_NAME,
            "configs": {},
        }
    collection["configs"][GFP_CONFIG_NAME] = {
        "manifest": f"manifests/{GFP_CONFIG_NAME}.json"
    }

    context = [
        {
            "name": name,
            "description": description,
            "required": False,
        }
        for name, description in (
            ("protein_id", "Stable SHA-256-derived protein join identifier."),
            ("aa_mutations", "Author substitution notation relative to avGFP."),
            ("mutation_count", "Number of amino-acid substitutions."),
            ("unique_barcodes", "Barcodes supporting the protein aggregate."),
            ("brightness_std", "Nullable author-reported barcode dispersion."),
            ("nucleotide_mutations", "Aligned nucleotide substitution notations."),
            ("nucleotide_mutation_counts", "Aligned nucleotide substitution counts."),
            ("nucleotide_unique_barcodes", "Aligned nucleotide aggregate barcode counts."),
            ("nucleotide_median_log10_brightness", "Aligned nucleotide aggregate medians."),
            ("nucleotide_brightness_std", "Aligned nullable nucleotide dispersions."),
            ("source_barcode_ids", "Aligned author barcode identifiers for provenance."),
            ("barcode_nucleotide_mutations", "Aligned barcode nucleotide genotypes."),
            ("barcode_nucleotide_mutation_counts", "Aligned barcode mutation counts."),
            ("barcode_log10_brightness", "Aligned filtered barcode brightness values."),
            ("barcode_min_coverage", "Aligned minimum genotype sequencing coverage."),
            ("barcode_mean_coverage", "Aligned mean genotype sequencing coverage."),
        )
    ]
    manifest = {
        "schema_version": 1,
        "dataset_id": DATASET_ID,
        "version": DATASET_VERSION,
        "default_split": GFP_DEFAULT_SPLIT,
        "description": (
            "Canonical protein-level Sarkisyan GFP measurements with retained "
            "nucleotide and filtered-barcode source observations."
        ),
        "license": "CC-BY-4.0",
        "source": [
            {
                "name": "Sarkisyan GFP Figshare data",
                "url": FIGSHARE_URL,
                "version": "v1",
                "checksum": (
                    "sha256:"
                    + SOURCE_ARTIFACTS["amino_acid_table"]["sha256"]
                ),
            }
        ],
        "citation": [
            {
                "text": (
                    "Sarkisyan et al. (2016), Local fitness landscape of the "
                    "green fluorescent protein."
                ),
                "url": "https://doi.org/10.1038/nature17995",
            }
        ],
        "inputs": [
            {
                "name": "sequence",
                "description": "Uppercase 237-residue avGFP variant sequence.",
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
                "description": (
                    "Author protein-level median log-brightness over accepted barcodes."
                ),
                "unit": "log10 fluorescence intensity",
                "constraints": [{"kind": "finite"}],
            }
        ],
        "context": context,
        "splits": [
            {
                "name": GFP_DEFAULT_SPLIT,
                "description": "All clean canonical protein-level measurements.",
                "num_rows": EXPECTED_GFP_PROTEINS,
                "attributes": {
                    "reference": "avGFP",
                    "protein_length": 237,
                    "mutation_type": "substitution_only",
                    "target_aggregation": "author_protein_level_median",
                    "nucleotide_observations": provenance["statistics"][
                        "clean_nucleotide_observations"
                    ],
                    "barcode_observations": provenance["statistics"][
                        "clean_barcode_observations"
                    ],
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
    _write_json(manifest_dir / f"{GFP_CONFIG_NAME}.json", manifest)
    _write_json(
        provenance_dir / f"{GFP_DEFAULT_SPLIT}.json",
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
        if config.get("config_name") != GFP_CONFIG_NAME
    ]
    configs.append(
        {
            "config_name": GFP_CONFIG_NAME,
            "data_files": [
                {
                    "split": GFP_DEFAULT_SPLIT,
                    "path": provenance["artifact"]["path"],
                }
            ],
        }
    )
    metadata["configs"] = configs
    metadata["license"] = "other"
    card.data = DatasetCardData(**metadata)

    marker = "## GFP"
    section = f"""
## GFP

The `{GFP_CONFIG_NAME}` config contains {EXPECTED_GFP_PROTEINS:,} unique
237-residue proteins reconstructed from the Sarkisyan GFP Figshare v1 release.
It uses the authors' protein-level median brightness and retains aligned
nucleotide aggregates and filtered-barcode measurement context. The config is
CC BY 4.0; see `provenance/{GFP_CONFIG_NAME}/{GFP_DEFAULT_SPLIT}.json`.
"""
    if marker not in card.text:
        license_marker = "\n## License"
        if license_marker in card.text:
            before, after = card.text.split(license_marker, 1)
            card.text = before.rstrip() + "\n" + section + license_marker + after
        else:
            card.text = card.text.rstrip() + "\n" + section
    card.save(path)


def _read_tsv(path: Path, expected_columns: tuple[str, ...]) -> Iterable[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        if tuple(reader.fieldnames or ()) != expected_columns:
            raise ValueError(
                f"unexpected columns in {path.name}: expected {expected_columns}, "
                f"got {reader.fieldnames}"
            )
        for row in reader:
            yield {name: (row[name] or "") for name in expected_columns}


def _verify_source(path: Path, specification: dict[str, Any]) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != specification["size_bytes"]:
        raise ValueError(f"source size mismatch for {path.name}")
    if _sha256(path) != specification["sha256"]:
        raise ValueError(f"source SHA-256 mismatch for {path.name}")


def _positive_int(value: str, field: str) -> int:
    parsed = _nonnegative_int(value, field)
    if parsed < 1:
        raise ValueError(f"{field} must be positive")
    return parsed


def _nonnegative_int(value: str, field: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative")
    return parsed


def _finite_float(value: str, field: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not np.isfinite(parsed):
        raise ValueError(f"{field} must be finite")
    return parsed


def _nonnegative_float(value: str, field: str) -> float:
    parsed = _finite_float(value, field)
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative")
    return parsed


def _optional_nonnegative_float(value: str, field: str) -> float | None:
    return None if value == "" else _nonnegative_float(value, field)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
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
        description="Build the canonical protein-level Sarkisyan GFP HF config."
    )
    parser.add_argument("--amino-acid-table", type=Path, required=True)
    parser.add_argument("--nucleotide-table", type=Path, required=True)
    parser.add_argument("--barcode-table", type=Path, required=True)
    parser.add_argument("--genotypes-table", type=Path, required=True)
    parser.add_argument("--reference-fasta", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    provenance = build_gfp_release(
        args.amino_acid_table,
        args.nucleotide_table,
        args.barcode_table,
        args.genotypes_table,
        args.reference_fasta,
        args.output_dir,
    )
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
