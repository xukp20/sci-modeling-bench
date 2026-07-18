from __future__ import annotations

import pytest

from sci_modeling_bench.suites.design_bench.gfp._sequence import (
    apply_amino_acid_mutations,
    mutation_count,
    read_reference_fasta,
)

from .conftest import REFERENCE


def test_reference_translation() -> None:
    # The full frozen sequence is exercised by the formal builder; the parser
    # rejects an incorrect header before translation.
    with pytest.raises(ValueError, match="header"):
        read_reference_fasta(">other\nAGC")
    assert len(REFERENCE) == 237


def test_apply_zero_based_mutations() -> None:
    assert apply_amino_acid_mutations(REFERENCE, "") == REFERENCE
    mutated = apply_amino_acid_mutations(REFERENCE, "SS0A:SK1C")
    assert mutated[:3] == "ACG"
    assert mutation_count("SS0A:SK1C") == 2


@pytest.mark.parametrize(
    "notation, message",
    [
        ("SA0C", "expects A"),
        ("SS237A", "outside"),
        ("SS0A:SS0C", "repeated"),
        ("bad", "unsupported"),
    ],
)
def test_reject_invalid_mutations(notation: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        apply_amino_acid_mutations(REFERENCE, notation)
