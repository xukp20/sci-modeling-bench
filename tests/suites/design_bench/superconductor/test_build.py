from __future__ import annotations

import os
from pathlib import Path

import pytest

from sci_modeling_bench.suites.design_bench.superconductor.build import (
    build_superconductor_release,
)


@pytest.mark.integration
def test_builder_replays_the_pinned_uci_archive(tmp_path: Path) -> None:
    archive = os.environ.get("SMB_SUPERCONDUCTOR_ARCHIVE")
    if archive is None:
        pytest.skip("SMB_SUPERCONDUCTOR_ARCHIVE is not configured")

    provenance = build_superconductor_release(archive, tmp_path)

    assert provenance["statistics"]["source_rows"] == 21_263
    assert provenance["statistics"]["composition_groups"] == 15_164
    assert provenance["statistics"]["conflict_groups_removed"] == 0
    assert (tmp_path / "data/superconductor/composition_groups.parquet").is_file()
