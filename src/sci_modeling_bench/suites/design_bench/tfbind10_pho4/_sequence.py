"""Canonical indexing for the complete uppercase DNA 10-mer space."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

SEQUENCE_LENGTH = 10
SEQUENCE_COUNT = 4**SEQUENCE_LENGTH
ALPHABET = "ACGT"

_DIGIT_BY_BYTE = np.full(256, -1, dtype=np.int8)
for _digit, _symbol in enumerate(ALPHABET.encode("ascii")):
    _DIGIT_BY_BYTE[_symbol] = _digit
_POSITION_WEIGHTS = np.asarray(
    [4**power for power in range(SEQUENCE_LENGTH - 1, -1, -1)],
    dtype=np.int64,
)


def sequence_indices(sequences: Sequence[str]) -> np.ndarray:
    """Return base-4 indices in lexicographic A<C<G<T order."""

    if not sequences:
        return np.empty(0, dtype=np.int64)
    if any(not isinstance(sequence, str) for sequence in sequences):
        raise ValueError("DNA candidates must be strings")
    if any(len(sequence) != SEQUENCE_LENGTH for sequence in sequences):
        raise ValueError(f"DNA candidates must contain {SEQUENCE_LENGTH} symbols")
    try:
        encoded = "".join(sequences).encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("DNA candidates must use ASCII symbols") from exc
    matrix = np.frombuffer(encoded, dtype=np.uint8).reshape(-1, SEQUENCE_LENGTH)
    digits = _DIGIT_BY_BYTE[matrix]
    if np.any(digits < 0):
        raise ValueError("DNA candidates may contain only A, C, G, and T")
    return digits.astype(np.int64, copy=False) @ _POSITION_WEIGHTS


def sequence_from_index(index: int) -> str:
    """Return the lexicographic DNA 10-mer at one base-4 index."""

    if not 0 <= index < SEQUENCE_COUNT:
        raise ValueError(f"sequence index must be in [0, {SEQUENCE_COUNT})")
    symbols = ["A"] * SEQUENCE_LENGTH
    for position in range(SEQUENCE_LENGTH - 1, -1, -1):
        index, digit = divmod(index, 4)
        symbols[position] = ALPHABET[digit]
    return "".join(symbols)


def all_sequences() -> list[str]:
    """Materialize the complete lexicographically ordered DNA 10-mer space."""

    return [sequence_from_index(index) for index in range(SEQUENCE_COUNT)]
