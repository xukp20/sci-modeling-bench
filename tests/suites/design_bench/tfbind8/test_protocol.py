from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

from sci_modeling_bench.exceptions import ProtocolError
from sci_modeling_bench.suites.design_bench.tfbind8 import (
    TFBind8Dataset,
    TFBind8DesignBenchProtocol,
)


def test_default_protocol_exposes_canonical_bottom_half(
    tiny_tfbind8_dataset: TFBind8Dataset,
) -> None:
    visible = TFBind8DesignBenchProtocol().build_input(tiny_tfbind8_dataset).data

    assert visible.column_names == ["sequence", "normalized_e_score"]
    assert visible.to_dict() == {
        "sequence": ["AAAAAAAA", "AAAAAAAC"],
        "normalized_e_score": [0.0, 0.25],
    }


def test_protocol_can_select_a_raw_score_percentile_range(
    tiny_tfbind8_dataset: TFBind8Dataset,
) -> None:
    protocol = TFBind8DesignBenchProtocol(
        min_percentile=50.0,
        max_percentile=100.0,
        target_field="e_score",
    )

    visible = protocol.build_input(tiny_tfbind8_dataset).data

    assert visible.column_names == ["sequence", "e_score"]
    assert visible.to_dict() == {
        "sequence": ["AACCGGTT", "TTTTTTTT"],
        "e_score": [0.25, 0.5],
    }


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    [(-1.0, 50.0), (0.0, 101.0), (75.0, 25.0)],
)
def test_protocol_rejects_invalid_percentile_ranges(
    minimum: float,
    maximum: float,
) -> None:
    with pytest.raises(ProtocolError):
        TFBind8DesignBenchProtocol(
            min_percentile=minimum,
            max_percentile=maximum,
        )


@pytest.mark.integration
def test_published_default_protocol_has_expected_unique_bottom_half(
    published_tfbind8_dataset: TFBind8Dataset,
) -> None:
    visible = TFBind8DesignBenchProtocol().build_input(published_tfbind8_dataset).data

    assert len(visible) == 32_768
    assert visible.column_names == ["sequence", "normalized_e_score"]
    assert len(set(visible["sequence"])) == 32_768
    assert max(visible["normalized_e_score"]) == pytest.approx(0.439296156167984)


@pytest.mark.integration
def test_published_protocol_matches_legacy_visible_candidate_set(
    published_tfbind8_dataset: TFBind8Dataset,
) -> None:
    legacy_data_dir = os.environ.get("SMB_TFBIND8_LEGACY_DATA_DIR")
    if legacy_data_dir is None:
        pytest.skip("SMB_TFBIND8_LEGACY_DATA_DIR is not configured")

    legacy_path = Path(legacy_data_dir)
    legacy_x = np.load(legacy_path / "tf_bind_8-x-0.npy", allow_pickle=False)
    legacy_y = np.load(legacy_path / "tf_bind_8-y-0.npy", allow_pickle=False)[:, 0]
    threshold = np.percentile(legacy_y, 50.0, method="linear")
    alphabet = "ACGT"
    legacy_visible = {
        "".join(alphabet[int(token)] for token in row)
        for row in legacy_x[legacy_y <= threshold]
    }

    visible = TFBind8DesignBenchProtocol().build_input(published_tfbind8_dataset).data

    assert len(legacy_x[legacy_y <= threshold]) == 32_898
    assert len(legacy_visible) == 32_768
    assert set(visible["sequence"]) == legacy_visible
