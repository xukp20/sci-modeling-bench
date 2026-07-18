"""Reference translation and mutation parsing for the Sarkisyan GFP data."""

from __future__ import annotations

import re

AMINO_ACID_ALPHABET = tuple("ACDEFGHIKLMNPQRSTVWY")
AMINO_ACID_SET = frozenset(AMINO_ACID_ALPHABET)
GFP_PROTEIN_LENGTH = 237
GFP_REFERENCE_DNA_LENGTH = 714

_MUTATION_PATTERN = re.compile(r"S([A-Z*])(\d+)([A-Z*])")
_CODON_TABLE = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}


def read_reference_fasta(text: str) -> str:
    """Parse the single-record avGFP FASTA into uppercase DNA."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2 or lines[0] != ">avGFP_reference_sequence":
        raise ValueError("unexpected avGFP reference FASTA header")
    dna = "".join(lines[1:]).upper()
    if len(dna) != GFP_REFERENCE_DNA_LENGTH:
        raise ValueError(
            f"avGFP reference must contain {GFP_REFERENCE_DNA_LENGTH} nucleotides"
        )
    if set(dna) - {"A", "C", "G", "T"}:
        raise ValueError("avGFP reference contains non-DNA symbols")
    return dna


def translate_reference(dna: str) -> str:
    """Translate a coding sequence with one required terminal stop codon."""

    if len(dna) != GFP_REFERENCE_DNA_LENGTH or len(dna) % 3:
        raise ValueError("avGFP coding sequence has an invalid length")
    try:
        translated = "".join(
            _CODON_TABLE[dna[index : index + 3]]
            for index in range(0, len(dna), 3)
        )
    except KeyError as exc:
        raise ValueError(f"unknown DNA codon {exc.args[0]!r}") from exc
    if not translated.endswith("*") or "*" in translated[:-1]:
        raise ValueError("avGFP reference must have exactly one terminal stop codon")
    protein = translated[:-1]
    if len(protein) != GFP_PROTEIN_LENGTH:
        raise ValueError(
            f"avGFP reference must translate to {GFP_PROTEIN_LENGTH} residues"
        )
    return protein


def apply_amino_acid_mutations(reference: str, notation: str | None) -> str:
    """Apply the source's zero-based substitution notation to a protein."""

    if len(reference) != GFP_PROTEIN_LENGTH:
        raise ValueError(
            f"reference protein must contain {GFP_PROTEIN_LENGTH} residues"
        )
    value = notation or ""
    if not value:
        return reference

    sequence = list(reference)
    seen_positions: set[int] = set()
    for token in value.split(":"):
        match = _MUTATION_PATTERN.fullmatch(token)
        if match is None:
            raise ValueError(f"unsupported amino-acid mutation token {token!r}")
        source, position_text, target = match.groups()
        position = int(position_text)
        if position < 0 or position >= len(sequence):
            raise ValueError(f"mutation position {position} is outside the protein")
        if position in seen_positions:
            raise ValueError(f"mutation position {position} is repeated")
        if source not in AMINO_ACID_SET:
            raise ValueError(f"mutation source {source!r} is not a standard amino acid")
        if target not in AMINO_ACID_SET and target != "*":
            raise ValueError(f"mutation target {target!r} is not supported")
        if sequence[position] != source:
            raise ValueError(
                f"mutation {token!r} expects {source} at position {position}, "
                f"found {sequence[position]}"
            )
        sequence[position] = target
        seen_positions.add(position)
    return "".join(sequence)


def mutation_count(notation: str | None) -> int:
    """Count colon-separated substitutions after validating non-empty tokens."""

    value = notation or ""
    if not value:
        return 0
    tokens = value.split(":")
    if any(_MUTATION_PATTERN.fullmatch(token) is None for token in tokens):
        raise ValueError(f"unsupported mutation notation {value!r}")
    return len(tokens)
