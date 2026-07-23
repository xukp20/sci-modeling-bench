# Binding Sites, Motifs, and Sequence Context

## Summary

A transcription-factor binding site is a particular DNA segment that can be
bound under specified conditions. A motif summarizes recurring sequence
preferences across multiple sites or measurements, but is not itself a single
physical site. Position-frequency matrices, position-weight matrices, and
sequence logos preserve more information than a consensus string, although
standard position-wise models do not represent every dependency between
nucleotides.

## Scope

### Covered

- Binding sites, consensus sequences, motifs, PFM/PWM representations, and sequence logos.
- Strand orientation and reverse-complement representations.
- Positional dependence, flanking sequence, and motif syntax.

### Not covered

- A motif for any particular protein.
- Motif-discovery algorithms or modeling recommendations.
- Claims that motif occurrence proves binding or regulatory function in cells.

## Key concepts and notation

| Term or symbol | Definition | Notes |
| --- | --- | --- |
| Binding site | A specific DNA segment involved in a protein–DNA interaction | Evidence depends on assay and conditions |
| Motif | A representation of recurring sequence preference | May be a consensus, matrix, or richer model |
| Consensus | One representative symbol or ambiguity code per position | Discards frequency and dependence information |
| PFM \(n_{b,i}\) | Count or frequency of base \(b\) at position \(i\) | Usually derived from aligned sites |
| PWM \(w_{b,i}\) | Position-specific weight for base \(b\) at position \(i\) | Often a log-odds value |
| Sequence logo | Graphic showing base frequencies and information by position | A visualization, not an independent assay |

## Core knowledge

### Sites and motifs are different objects

A binding site is a concrete sequence in a particular molecular or genomic
context. A motif is a summary of a collection of sites or quantitative
preferences. Different sites can conform to the same motif with different
affinities, and two proteins can share a broad motif while differing in
lower-preference sequences [1,2].

A consensus sequence retains only a representative base or ambiguity symbol at
each position. It does not preserve the full frequency distribution, the
magnitude of preference, or correlations between positions.

### Position-frequency and position-weight matrices

For aligned sites of length \(L\), a position-frequency matrix records
\(n_{b,i}\), the count or estimated frequency of base
\(b\in\{A,C,G,T\}\) at position \(i\). A common log-odds position weight is

\[
w_{b,i}=\log_2\left(\frac{p_{b,i}}{q_b}\right),
\]

where \(p_{b,i}\) is the estimated probability of base \(b\) at position \(i\)
and \(q_b\) is its background probability. Under a position-independent PWM,
the score of sequence \(s=s_1\ldots s_L\) is

\[
S(s)=\sum_{i=1}^{L} w_{s_i,i}.
\]

Pseudocounts are commonly used when estimating \(p_{b,i}\) so that unobserved
bases do not create infinite weights. Scores depend on the background model,
pseudocounts, and logarithm convention and are not automatically comparable
between independently constructed matrices [1,3].

### Information and sequence logos

For a four-base alphabet, the information content at a position can be written
relative to a background distribution. With a uniform background and ignoring
small-sample correction,

\[
R_i=2+\sum_b p_{b,i}\log_2 p_{b,i}
\]

bits. A sequence logo typically uses total stack height to display positional
information and letter heights to display base frequencies [4]. A logo
therefore summarizes a matrix; it does not show all pairwise dependencies or
the experimental uncertainty behind the matrix.

### Orientation and reverse complements

Motifs and sites are conventionally written \(5'\rightarrow3'\). For a
protein binding an unoriented double-stranded site, the reverse complement is
the alternative strand representation of the same tract. Motif databases may
choose one orientation for display. Asymmetric complexes, composite motifs, or
oriented genomic features can give the displayed orientation additional
meaning.

### Dependencies and surrounding sequence

The standard PWM factorizes contributions by position. Experimental and
computational studies have identified transcription factors for which
nucleotide pairs or longer combinations contribute non-additively [5,6].
Nearby bases outside a compact motif can also alter DNA shape, deformability,
or contacts and thereby alter binding. For complexes containing multiple
factors, spacing and orientation between component sites can be part of the
recognition syntax [2,7].

## Conditions, limitations, and uncertainty

- A motif depends on the source assay, protein construct, sequence background,
  alignment, and representation method.
- PWM scores are model quantities, not universally calibrated \(K_d\) or
  Gibbs-energy measurements.
- A matrix that assumes independent positions cannot express all higher-order
  sequence effects.
- Motif occurrence alone does not establish cellular occupancy or regulatory
  function.
- A motif inferred from selected high-affinity sites can underrepresent
  moderate-affinity or alternative binding modes.

## Related knowledge resources

- `dna_structure_and_base_pairing`: strand orientation and sequence-dependent DNA structure.
- `transcription_factor_dna_binding`: physical sources of sequence specificity.
- `protein_binding_microarrays`: one assay that measures broad sequence preferences.

## References

1. Stormo GD. DNA binding sites: representation and discovery. *Bioinformatics*. 2000;16:16–23. https://doi.org/10.1093/bioinformatics/16.1.16. [Review]
2. Slattery M, Zhou T, Yang L, Dantas Machado AC, Gordân R, Rohs R. Absence of a simple code: how transcription factors read the genome. *Trends in Biochemical Sciences*. 2014;39:381–399. https://doi.org/10.1016/j.tibs.2014.07.002. [Review]
3. Stormo GD. Modeling the specificity of protein-DNA interactions. *Quantitative Biology*. 2013;1:115–130. https://doi.org/10.1007/s40484-013-0012-4. [Review]
4. Schneider TD, Stephens RM. Sequence logos: a new way to display consensus sequences. *Nucleic Acids Research*. 1990;18:6097–6100. https://doi.org/10.1093/nar/18.20.6097. [Method paper]
5. Zhou Q, Liu JS. Modeling within-motif dependence for transcription factor binding site predictions. *Bioinformatics*. 2004;20:909–916. https://doi.org/10.1093/bioinformatics/bth006. [Method paper]
6. Barrera LA, Vedenko A, Kurland JV, et al. Survey of variation in human transcription factors reveals prevalent DNA binding changes. *Science*. 2016;351:1450–1454. https://doi.org/10.1126/science.aad2257. [Primary research]
7. Jolma A, Yin Y, Nitta KR, et al. DNA-dependent formation of transcription factor pairs alters their binding specificity. *Nature*. 2015;527:384–388. https://doi.org/10.1038/nature15518. [Primary research]
