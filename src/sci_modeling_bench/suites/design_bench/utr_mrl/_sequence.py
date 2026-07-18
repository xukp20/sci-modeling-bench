"""Sequence semantics shared by the UTR MRL Dataset and Protocol."""

from __future__ import annotations

UTR_LENGTH = 50
UTR_ALPHABET = frozenset("ACGT")
START_CODON = "ATG"

_STRONG_KOZAK = (
    frozenset(("A", "G")),
    frozenset(("C", "A")),
    frozenset(("C", "G", "A")),
)
_WEAK_KOZAK = (
    frozenset(("T",)),
    frozenset(("G",)),
    frozenset(("T", "C")),
)


def validate_utr_sequence(sequence: str) -> None:
    """Raise when a value is not one canonical 50-nt DNA-form UTR."""

    if not isinstance(sequence, str):
        raise TypeError("UTR sequence must be a string")
    if len(sequence) != UTR_LENGTH:
        raise ValueError(f"UTR sequence must contain exactly {UTR_LENGTH} bases")
    invalid = sorted(set(sequence) - UTR_ALPHABET)
    if invalid:
        raise ValueError(f"UTR sequence contains invalid symbols: {invalid}")


def has_uaug(sequence: str) -> bool:
    """Return whether the variable UTR contains an upstream AUG codon."""

    validate_utr_sequence(sequence)
    return START_CODON in sequence


def has_out_of_frame_uaug(sequence: str) -> bool:
    """Return whether any uAUG is out of frame with the fixed main CDS."""

    validate_utr_sequence(sequence)
    for position in range(UTR_LENGTH - 2):
        if sequence[position : position + 3] != START_CODON:
            continue
        if (UTR_LENGTH - position) % 3 != 0:
            return True
    return False


def kozak_quality(sequence: str) -> str:
    """Apply the simplified mRNABench rule to the final three UTR bases."""

    validate_utr_sequence(sequence)
    prefix = sequence[-3:]
    strong = all(base in allowed for base, allowed in zip(prefix, _STRONG_KOZAK))
    weak = all(base in allowed for base, allowed in zip(prefix, _WEAK_KOZAK))
    if strong == weak:
        return "mixed"
    return "strong" if strong else "weak"


def sequence_annotations(sequence: str) -> tuple[bool, bool, str]:
    """Return all deterministic annotations stored by the canonical Dataset."""

    return (
        has_uaug(sequence),
        has_out_of_frame_uaug(sequence),
        kozak_quality(sequence),
    )
