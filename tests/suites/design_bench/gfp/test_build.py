from __future__ import annotations

import os
from pathlib import Path

import pytest

from sci_modeling_bench.suites.design_bench.gfp.build import build_gfp_release


@pytest.mark.integration
def test_formal_source_build(tmp_path: Path) -> None:
    source_dir_value = os.environ.get("SMB_GFP_SOURCE_DIR")
    if source_dir_value is None:
        pytest.skip("SMB_GFP_SOURCE_DIR is not configured")
    source_dir = Path(source_dir_value)

    provenance = build_gfp_release(
        source_dir / "amino_acid_genotypes_to_brightness.tsv",
        source_dir / "nucleotide_genotypes_to_brightness.tsv",
        source_dir / "barcodes_to_brightness.tsv",
        source_dir / "genotypes.tsv",
        source_dir / "avGFP_reference_sequence.fa",
        tmp_path,
    )

    assert provenance["statistics"]["canonical_proteins"] == 51_715
    assert provenance["statistics"]["clean_nucleotide_observations"] == 56_086
    assert provenance["statistics"]["clean_barcode_observations"] == 65_678
    assert provenance["statistics"]["default_protocol"] == {
        "visible_max_percentile": 80.0,
        "cutoff": 3.6496037176800002,
        "visible_proteins": 41_372,
        "candidate_pool": 10_343,
    }
    assert provenance["artifact"]["sha256"] == (
        "5340280e9e01b9ed2c32cbb429d2d4bb28513f44daa764511be4db8b6fb66d98"
    )
