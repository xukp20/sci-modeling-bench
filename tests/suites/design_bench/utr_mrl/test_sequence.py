from __future__ import annotations

import pytest

from sci_modeling_bench.suites.design_bench.utr_mrl._sequence import (
    has_out_of_frame_uaug,
    has_uaug,
    kozak_quality,
    validate_utr_sequence,
)

from .conftest import NO_UAUG_STRONG, NO_UAUG_WEAK, UAUG_STRONG, UAUG_WEAK


def test_sequence_annotations_match_compositional_groups() -> None:
    assert not has_uaug(NO_UAUG_STRONG)
    assert has_uaug(UAUG_STRONG)
    assert kozak_quality(NO_UAUG_STRONG) == "strong"
    assert kozak_quality(NO_UAUG_WEAK) == "weak"
    assert kozak_quality(UAUG_STRONG) == "strong"
    assert kozak_quality(UAUG_WEAK[0]) == "weak"
    assert has_out_of_frame_uaug(UAUG_WEAK[0])


@pytest.mark.parametrize("sequence", ["A" * 49, "N" * 50, "a" * 50])
def test_sequence_validation_rejects_noncanonical_values(sequence: str) -> None:
    with pytest.raises(ValueError):
        validate_utr_sequence(sequence)
