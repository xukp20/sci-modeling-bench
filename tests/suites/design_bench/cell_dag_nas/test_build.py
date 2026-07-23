from __future__ import annotations

import json
from pathlib import Path

from sci_modeling_bench.suites.design_bench.cell_dag_nas.build import (
    ARCHITECTURE_ENCODING_DESCRIPTION,
    _write_release_metadata,
)


def test_manifest_discloses_architecture_token_encoding(tmp_path: Path) -> None:
    _write_release_metadata(
        tmp_path,
        {
            "default_protocol": {
                "visible_canonical_graphs": 1,
                "visible_alias_rows": 1,
            }
        },
    )

    manifest = json.loads(
        (
            tmp_path / "manifests" / "cell_dag_nas.json"
        ).read_text(encoding="utf-8")
    )
    description = manifest["inputs"][0]["description"]

    assert description == ARCHITECTURE_ENCODING_DESCRIPTION
    assert "0=start" in description
    assert "6=1x1 convolution" in description
    assert "7=3x3 convolution" in description
    assert "8=3x3 max-pooling" in description
    assert "9=no edge" in description
    assert "10=edge" in description
    assert "strict upper triangle" in description
    assert "(0,1), (0,2)" in description
    assert "at most 9 edges" in description
    assert "path from input to output" in description
