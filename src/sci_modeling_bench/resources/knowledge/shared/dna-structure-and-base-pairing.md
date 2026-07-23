# DNA Structure and Base Pairing

## Summary

Deoxyribonucleic acid (DNA) is a directional polymer whose common duplex form
contains two complementary, antiparallel strands. Canonical Watson–Crick base
pairs match adenine with thymine and guanine with cytosine. The order of bases
determines not only the chemical groups exposed in the DNA grooves but also
local conformational and mechanical properties of the duplex. These properties
provide physical information that DNA-binding proteins can recognize.

## Scope

### Covered

- DNA strand direction, complementarity, and reverse complements.
- Canonical base pairing and the major and minor grooves of duplex DNA.
- Sequence-dependent base stacking, shape, and deformability.

### Not covered

- DNA replication, transcription, chromatin organization, or gene regulation.
- Noncanonical DNA structures in detail.
- Any particular protein's sequence preference.

## Key concepts and notation

| Term or symbol | Definition | Notes |
| --- | --- | --- |
| Nucleotide | A nitrogenous base, deoxyribose sugar, and phosphate group | DNA commonly uses A, C, G, and T |
| \(5'\) and \(3'\) | Ends defined by carbon positions in deoxyribose | A sequence is conventionally written \(5'\rightarrow3'\) |
| Complement | Base substitution A↔T and C↔G | Defined position by position |
| Reverse complement | Complement followed by reversal | Written in the same \(5'\rightarrow3'\) convention as the original strand |
| Base pair | Two bases paired across a duplex | Canonical pairs are A·T and G·C |
| Base-pair step | Two consecutive base pairs | Its geometry depends on both pairs and neighboring sequence |

## Core knowledge

### Directional, antiparallel strands

Phosphodiester bonds connect nucleotides into a strand with chemically
different \(5'\) and \(3'\) ends. In the common double-helical form, the two
strands run in opposite directions. If one strand is
\(5'\)-A G T C-\(3'\), its paired strand is \(3'\)-T C A G-\(5'\), which is
written \(5'\)-G A C T-\(3'\) when reported in the conventional direction.
This operation is the reverse complement, and applying it twice returns the
original sequence [1,2].

For ordinary double-stranded DNA, a sequence and its reverse complement
describe opposite orientations of the same base-pair tract. Orientation can
still matter when neighboring DNA, asymmetric protein complexes, chemical
labels, or the experimental construct distinguish the two directions.

### Canonical pairing and helix stabilization

Watson–Crick pairing matches A with T and G with C while maintaining a regular
duplex geometry [1]. Hydrogen bonding contributes pairing specificity, whereas
base stacking, solvent, ions, and the sugar-phosphate backbone all contribute
to duplex stability. Counting hydrogen bonds alone is therefore not a complete
description of sequence-dependent stability.

### Grooves expose sequence information

The geometry of the double helix produces a major groove and a minor groove.
The edges of base pairs expose patterns of hydrogen-bond donors, acceptors,
nonpolar groups, and electrostatic potential. The major groove distinguishes
the four Watson–Crick base-pair orientations more directly than the minor
groove, while minor-groove width and electrostatic potential can carry
sequence-dependent structural information [3,4].

### Sequence-dependent structure

DNA is not a perfectly uniform cylinder. Base stacking and backbone
constraints make parameters such as roll, twist, slide, propeller twist,
minor-groove width, and bending propensity depend on sequence and context
[3-5]. A nucleotide can therefore influence the physical presentation of
neighboring bases. Dinucleotide and longer contexts are often needed to
describe these effects; isolated single-base identities do not determine all
local geometry.

## Conditions, limitations, and uncertainty

- B-DNA is the prevalent reference form under many physiological conditions,
  but DNA can adopt other conformations and noncanonical base pairs.
- Salt concentration, temperature, pH, chemical modification, mismatches, and
  supercoiling can change duplex stability and shape.
- Reverse-complement equivalence is a property of an unoriented duplex tract,
  not a guarantee that every biological or experimental system treats both
  orientations identically.
- General shape tendencies do not uniquely determine a protein's binding
  preference; protein structure and assay conditions also matter.

## Related knowledge resources

- `transcription_factor_dna_binding`: how proteins read base chemistry and DNA shape.
- `binding_sites_motifs_and_sequence_context`: representations of recurring sequence preferences.

## References

1. Watson JD, Crick FHC. Molecular Structure of Nucleic Acids: A Structure for Deoxyribose Nucleic Acid. *Nature*. 1953;171:737–738. https://doi.org/10.1038/171737a0. [Primary research]
2. Dickerson RE. The DNA helix and how it is read. *Scientific American*. 1983;249:94–111. https://doi.org/10.1038/scientificamerican1283-94. [Review]
3. Rohs R, Jin X, West SM, Joshi R, Honig B, Mann RS. Origins of specificity in protein-DNA recognition. *Annual Review of Biochemistry*. 2010;79:233–269. https://doi.org/10.1146/annurev-biochem-060408-091030. [Review]
4. Slattery M, Zhou T, Yang L, Dantas Machado AC, Gordân R, Rohs R. Absence of a simple code: how transcription factors read the genome. *Trends in Biochemical Sciences*. 2014;39:381–399. https://doi.org/10.1016/j.tibs.2014.07.002. [Review]
5. Hunter CA. Sequence-dependent DNA structure: the role of base stacking interactions. *Journal of Molecular Biology*. 1993;230:1025–1054. https://doi.org/10.1006/jmbi.1993.1217. [Primary research]
