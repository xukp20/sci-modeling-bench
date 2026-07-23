# MiXCR Mutation Encoding

## Summary

MiXCR mutation notation is a compact, reference-relative representation of
substitutions, deletions, and insertions. Each edit records an edit type, a
zero-based position in the target sequence, and the source or destination
symbol when applicable. The notation is meaningful only together with the
exact target sequence and coordinate convention. Although MiXCR defines the
grammar for nucleotide alignments, a data source can explicitly reuse the
same grammar with an amino-acid alphabet [1,2].

## Scope

### Covered

- The `S`, `D`, and `I` edit types.
- Zero-based, target-relative positions.
- Reference validation and multiple-edit strings.
- Explicit adaptation from nucleotide to amino-acid symbols.

### Not covered

- The reference sequence or columns of any particular dataset.
- HGVS nomenclature or conversion to a particular structure numbering scheme.
- The biological or phenotypic effect of an edit.

## Key concepts and notation

| Term | Definition |
| --- | --- |
| target sequence | Reference sequence to which coordinates and source symbols refer |
| query sequence | Sequence obtained after applying the encoded edits |
| `S` | Substitution |
| `D` | Deletion |
| `I` | Insertion |
| position | Zero-based absolute coordinate in the target sequence |

## Core knowledge

### Single-edit grammar

MiXCR represents one edit without spaces as [1]

```text
type [fromSymbol] position [toSymbol]
```

The source symbol is present for substitutions and deletions. The destination
symbol is present for substitutions and insertions.

`SA4T` means that target symbol `A` at index 4 is replaced by `T`. `DC12`
means that target symbol `C` at index 12 is deleted. `I15G` means that `G` is
inserted immediately before target index 15 [1].

### Coordinates and reference validation

All MiXCR positions are zero-based. For a substitution or deletion, a
well-formed reference-relative edit satisfies

\[
\mathrm{target}[\mathrm{position}]=\mathrm{fromSymbol}.
\]

This equality provides a direct check for reference, coordinate, or
serialization disagreement. Insertion coordinates describe a boundary in the
target rather than an existing target symbol [1].

### Multiple edits

MiXCR can concatenate multiple single-edit tokens into one mutation string.
Every position remains a coordinate in the original target sequence; it is
not renumbered after applying an earlier insertion or deletion. Decoding
therefore requires parsing edit boundaries and applying the complete
target-relative edit set consistently [1].

### Use with an amino-acid alphabet

The original MiXCR specification describes nucleotide symbols. A source can
declare an analogous protein notation in which source and destination symbols
are amino-acid one-letter codes. For example, the Sarkisyan GFP data
documentation defines zero-based protein mutation strings such as `SG101A`,
where `S` is the substitution operator, `G` is the reference residue, `101`
is the zero-based reference position, and `A` is the substituted residue [2].
This is an explicit reuse by that source, not an automatic property of every
protein mutation string.

### Difference from common protein numbering

Protein literature commonly numbers residues from one and often writes a
substitution without a separate edit-type prefix, for example `G102A`.
MiXCR-style `SG101A` and conventional `G102A` can denote the same edit only
when both refer to the same reference sequence and the sole coordinate
difference is zero-based versus one-based indexing. Initiator-methionine
processing, signal peptides, isoforms, tags, or alignment gaps can introduce
additional offsets.

## Conditions, limitations, and uncertainty

- A mutation string cannot identify a unique sequence without its target.
- Coordinates are not portable across reference sequences or isoforms.
- A leading `S` is an operator in this grammar, not a serine residue.
- The alphabet and token separator must be declared by the producing source.
- Similar-looking HGVS, VCF, common protein, and MiXCR strings should not be
  converted by appearance alone.

## Related knowledge resources

- `protein_sequences_amino_acids_and_substitutions`: amino-acid symbols and
  residue-coordinate semantics.

## References

1. MiLaboratories. Alignment and mutations encoding. MiXCR documentation. https://mixcr.com/mixcr/reference/ref-mutations-encoding/. Accessed 2026-07-23. [Official specification]
2. Sarkisyan KS, et al. Local fitness landscape of the green fluorescent protein: source dataset and notation. Figshare. 2016;version 1. https://doi.org/10.6084/m9.figshare.3102154.v1. [Primary research data]
