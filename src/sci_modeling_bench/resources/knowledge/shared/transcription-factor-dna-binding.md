# Transcription Factor–DNA Binding

## Summary

Sequence-specific transcription factors bind DNA through a combination of
direct contacts with base-pair edges, recognition of sequence-dependent DNA
shape, and interactions with the sugar-phosphate backbone. Binding specificity
describes relative preference among sequences, whereas affinity describes the
strength of a particular interaction under stated conditions. Protein domains,
oligomeric state, cofactors, DNA context, and experimental conditions can all
alter the observed interaction.

## Scope

### Covered

- Physical modes of sequence recognition by transcription factors.
- The distinction between affinity, specificity, occupancy, and regulatory activity.
- Effects of protein construct, cofactors, and DNA context.

### Not covered

- A complete classification of transcription-factor families.
- Genome-scale chromatin regulation.
- Sequence preferences of a particular transcription factor.

## Key concepts and notation

| Term | Definition | Notes |
| --- | --- | --- |
| Affinity | Strength of binding between specified molecular species | Commonly quantified by \(K_d\) under defined conditions |
| Specificity | Relative preference for one sequence or class over another | Requires a comparison set |
| Occupancy | Fraction or probability that a site is bound | Depends on affinity and molecular concentrations |
| Base readout | Recognition of chemical groups associated with base identity | May involve direct or water-mediated contacts |
| Shape readout | Recognition of sequence-dependent conformation or electrostatics | Includes local and global DNA shape |
| Nonspecific binding | Association without a uniquely preferred base pattern | Often includes backbone electrostatics |

## Core knowledge

### Base readout

Amino-acid side chains can contact hydrogen-bond donors, acceptors, and
hydrophobic groups exposed at base-pair edges. These contacts may be direct or
water-mediated. Because the major groove presents distinguishable chemical
patterns for Watson–Crick base-pair orientations, many transcription factors
use major-groove contacts for sequence discrimination [1,2].

### Shape readout

DNA sequence influences minor-groove width, roll, twist, bending,
deformability, and electrostatic potential. A protein can prefer a sequence
because that sequence already adopts, or can readily deform into, a compatible
shape. Base and shape readout are coupled rather than mutually exclusive:
base identity generates both chemical patterns and structural tendencies
[1-3].

### Backbone and nonspecific interactions

Positively charged protein surfaces frequently interact with the negatively
charged phosphate backbone. Such contacts can stabilize both specific and
nonspecific complexes. Nonspecific association can facilitate encounter and
one-dimensional motion along DNA, but it does not by itself define a
sequence-specific recognition pattern [4].

### Protein architecture and cooperative context

Different DNA-binding-domain families position recognition elements in
different ways. Full-length proteins can also contain dimerization,
cofactor-binding, regulatory, or disordered regions that change affinity,
specificity, or kinetics. Homodimers and heterodimers may recognize composite
sites whose spacing and orientation are part of the binding determinant.
Protein partners can stabilize a complex or change which DNA contacts are made
[2,5].

### Binding is not the same as regulation

In-vitro binding establishes that molecular species can interact under the
assay conditions. Cellular occupancy additionally depends on protein
concentration, competitors, chromatin accessibility, nucleosomes, chemical
modifications, cofactors, and genomic context. Occupancy itself does not
guarantee transcriptional activation or repression; regulatory outcome also
depends on interactions with the transcriptional machinery and other
regulators [2,5].

## Conditions, limitations, and uncertainty

- Affinity and specificity should be attached to a defined protein construct,
  DNA construct, buffer, temperature, and oligomeric state.
- A DNA-binding domain may behave differently from the full-length protein.
- A consensus motif is a compact summary, not a complete physical recognition
  code.
- Related transcription factors can share a broad motif yet differ in
  lower-affinity preferences or cofactor dependence.
- In-vitro and in-vivo measurements answer different questions and need not
  produce identical rankings of sequences.

## Related knowledge resources

- `dna_structure_and_base_pairing`: the chemical and structural substrate being recognized.
- `binding_sites_motifs_and_sequence_context`: compact descriptions of sequence preference.
- `binding_affinity_and_thermodynamics`: equilibrium quantities used to describe binding strength.

## References

1. Rohs R, Jin X, West SM, Joshi R, Honig B, Mann RS. Origins of specificity in protein-DNA recognition. *Annual Review of Biochemistry*. 2010;79:233–269. https://doi.org/10.1146/annurev-biochem-060408-091030. [Review]
2. Slattery M, Zhou T, Yang L, Dantas Machado AC, Gordân R, Rohs R. Absence of a simple code: how transcription factors read the genome. *Trends in Biochemical Sciences*. 2014;39:381–399. https://doi.org/10.1016/j.tibs.2014.07.002. [Review]
3. Zhou T, Shen N, Yang L, et al. Quantitative modeling of transcription factor binding specificities using DNA shape. *Proceedings of the National Academy of Sciences USA*. 2015;112:4654–4659. https://doi.org/10.1073/pnas.1422023112. [Primary research]
4. von Hippel PH, Berg OG. Facilitated target location in biological systems. *Journal of Biological Chemistry*. 1989;264:675–678. https://doi.org/10.1016/S0021-9258(19)84994-3. [Review]
5. Morgunova E, Taipale J. Structural perspective of cooperative transcription factor binding. *Current Opinion in Structural Biology*. 2017;47:1–8. https://doi.org/10.1016/j.sbi.2017.03.006. [Review]
