# Protein Sequences, Amino Acids, and Substitutions

## Summary

A protein sequence is an ordered amino-acid polymer written from the
amino-terminal to the carboxyl-terminal end. The twenty standard genetically
encoded amino acids differ in size, charge, polarity, conformational
preference, and chemical reactivity. A substitution changes one residue in a
specified reference sequence, but its consequence depends on structural and
functional context rather than on residue identity alone [1,2].

## Scope

### Covered

- Protein direction, one-letter codes, and residue coordinates.
- Major physicochemical properties of amino-acid side chains.
- Reference-relative substitutions and conservative versus nonconservative
  changes.

### Not covered

- A universal prediction of substitution effects.
- Post-translational modifications or noncanonical amino acids in detail.
- The reference sequence or numbering of a particular dataset.

## Key concepts and notation

| Term | Meaning |
| --- | --- |
| N terminus | End bearing the free alpha-amino group |
| C terminus | End bearing the free alpha-carboxyl group |
| residue | Amino-acid unit incorporated into a polypeptide |
| position \(i\) | Coordinate defined relative to a stated reference sequence |
| substitution | Replacement of one reference residue by another |

## Core knowledge

### Sequence direction and alphabet

Protein sequences are conventionally written from N terminus to C terminus.
The standard one-letter alphabet is
`ACDEFGHIKLMNPQRSTVWY`. Ambiguity symbols and `*` for a stop codon are data
conventions rather than additional standard amino acids [1].

### Side-chain properties

At approximately neutral pH, Asp and Glu commonly carry negative charge,
whereas Lys and Arg commonly carry positive charge. His can change
protonation near physiological pH. Ser, Thr, Asn, and Gln are polar but
usually uncharged; Val, Leu, Ile, Met, Ala, and Pro are predominantly
nonpolar; Phe, Tyr, and Trp are aromatic [1,2].

Gly lacks a side-chain carbon and permits conformations unavailable to many
other residues. Pro constrains the backbone and lacks a conventional backbone
amide hydrogen. Cys can form disulfide bonds under oxidizing conditions.
These classes are useful descriptions, not interchangeable residue groups.

### Substitution semantics

A substitution is defined relative to a particular reference. Common protein
notation such as `G102A` states that glycine at one-based residue 102 is
replaced by alanine. The same characters are invalid if the stated reference
does not contain glycine at that coordinate.

“Conservative” usually means that source and destination residues share broad
properties such as charge or hydrophobicity. This does not guarantee a small
effect: a conservative change can disrupt precise packing or catalysis, while
a nonconservative change can be tolerated at an exposed, weakly constrained
site [2].

### Structural context

Buried residues participate in packing and the hydrophobic core. Surface
residues interact with solvent, ions, ligands, membranes, or other
macromolecules. Residues can also stabilize secondary structure, turns, salt
bridges, hydrogen-bond networks, active sites, and chromophore environments.
Consequently, identical substitutions at different positions need not have
similar effects.

### Reference and numbering conventions

Residue numbering can differ between an encoded precursor, mature protein,
crystal construct, tagged construct, alignment, or database entry. Removal of
an initiator methionine or signal peptide can shift all later coordinates.
Sequence comparison, rather than an assumed constant offset, is the reliable
way to relate conventions.

## Conditions, limitations, and uncertainty

- Protonation and charge depend on pH and local environment.
- Amino-acid classes summarize tendencies and do not determine structure.
- A sequence alone does not state oligomeric state, modifications, folding
  state, or experimental conditions.
- Mutation notation must declare its reference, direction, and coordinate
  convention.

## Related knowledge resources

- `mixcr_mutation_encoding`: one reference-relative edit serialization.
- `protein_folding_stability_and_mutational_effects`: energetic and kinetic
  effects of substitutions.

## References

1. IUPAC-IUB Joint Commission on Biochemical Nomenclature. Nomenclature and symbolism for amino acids and peptides. *European Journal of Biochemistry*. 1984;138:9–37. https://doi.org/10.1111/j.1432-1033.1984.tb07877.x. [Official nomenclature]
2. Betts MJ, Russell RB. Amino acid properties and consequences of substitutions. In: Barnes MR, Gray IC, editors. *Bioinformatics for Geneticists*. Wiley; 2003. https://doi.org/10.1002/0470867302.ch14. [Reference chapter]
