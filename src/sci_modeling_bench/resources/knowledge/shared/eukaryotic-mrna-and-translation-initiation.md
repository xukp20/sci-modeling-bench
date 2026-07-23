# Eukaryotic mRNA and Translation Initiation

## Summary

A mature eukaryotic messenger RNA typically contains a 5′ cap, a 5′
untranslated region (5′ UTR), a protein-coding sequence, a 3′ UTR, and a
poly(A) tail. In the canonical cap-dependent pathway, initiation factors
recruit a 43S pre-initiation complex near the cap, the complex scans the 5′
UTR, and start-codon recognition establishes the reading frame before the 60S
subunit joins. Initiation is regulated and context dependent; cap-independent
and non-AUG pathways also exist.

## Scope

### Covered

- Functional organization of eukaryotic mRNA.
- Canonical cap-dependent ribosome recruitment and scanning.
- Start-codon recognition and assembly of the 80S ribosome.
- Major alternatives and dependencies of initiation.

### Not covered

- Prokaryotic Shine–Dalgarno-mediated initiation.
- A particular 5′ UTR sequence, construct, or measurement.
- A recipe for predicting translation from sequence.

## Key concepts and notation

| Term | Definition |
| --- | --- |
| 5′ UTR | Transcribed region upstream of the main coding sequence |
| CDS | Coding sequence translated in the main open reading frame |
| \(m^7G\) cap | 7-methylguanosine-containing structure at the 5′ end |
| 43S PIC | 40S subunit with initiation factors and initiator Met-tRNA |
| Scanning | 5′-to-3′ movement of a pre-initiation complex along mRNA |
| Start site | Codon at which translation initiates and the reading frame is set |
| 80S ribosome | Joined 40S and 60S eukaryotic ribosomal subunits |

## Core knowledge

### Messenger-RNA organization

The 5′ UTR is transcribed but lies upstream of the main coding sequence. It
can influence ribosome recruitment, scanning, and start-site choice without
encoding the main protein. The 3′ UTR and poly(A) tail also participate in
RNA stability, localization, and translation, so the effect of a 5′ leader is
not necessarily independent of the rest of the transcript [1,2].

### Cap-dependent recruitment

In canonical initiation, eIF4E recognizes the \(m^7G\) cap. eIF4G acts as a
scaffold and eIF4A is an RNA helicase; together these proteins form eIF4F.
Interactions involving eIF3 recruit the 43S PIC, which includes the 40S
subunit and an eIF2–GTP–Met-tRNA\(_i\) ternary complex [1,3].

Poly(A)-binding protein can interact with eIF4G, functionally connecting the
3′ poly(A) tail and the cap-associated machinery. This communication is one
reason why translation is a property of the complete messenger
ribonucleoprotein context rather than of an isolated short sequence [3].

### Scanning and start recognition

The recruited complex generally scans from the 5′ end toward the coding
region. eIF1, eIF1A, eIF2, eIF5, and the ribosome help balance an open,
scanning-competent state against a closed state associated with start-codon
recognition. Base pairing between initiator tRNA and a start codon, together
with surrounding sequence and structural context, promotes recognition [2,4].

After start recognition and initiation-factor rearrangements, the 60S subunit
joins to form an elongation-competent 80S ribosome. The chosen start site fixes
the triplet reading frame for downstream decoding.

### Initiation is not an absolute first-AUG rule

Many transcripts follow the scanning model and initiate at an AUG encountered
in an effective context, but upstream codons can be bypassed by leaky
scanning. Ribosomes can also translate upstream open reading frames and later
reinitiate, and some mRNAs use near-cognate non-AUG starts [1,2].

Cap-independent initiation can recruit ribosomes internally or through
specialized factors and RNA structures. These mechanisms are important in
particular cellular and viral contexts but do not make all structured 5′ UTRs
internal ribosome entry sites [1,3].

## Conditions, limitations, and uncertainty

- Initiation-factor abundance, cell state, stress, and RNA modifications can
  change start-site selection and translation.
- Sequence context effects differ among species and experimental systems.
- Ribosome occupancy reflects the combined behavior of initiation,
  elongation, termination, and ribosome-associated quality control.
- A reporter preserves only the molecular context explicitly included in its
  construct.
- Cap-independent initiation requires specific evidence; it should not be
  inferred from sequence or structure alone.

## Related knowledge resources

- `kozak_context_and_start_codon_recognition`: sequence context around start sites.
- `upstream_start_codons_and_upstream_open_reading_frames`: upstream initiation events.
- `five_prime_utr_regulatory_elements`: cis-regulatory features of 5′ leaders.

## References

1. Hinnebusch AG, Ivanov IP, Sonenberg N. Translational control by 5′-untranslated regions of eukaryotic mRNAs. *Science*. 2016;352:1413–1416. https://doi.org/10.1126/science.aad9868
2. Hinnebusch AG. The scanning mechanism of eukaryotic translation initiation. *Annual Review of Biochemistry*. 2014;83:779–812. https://doi.org/10.1146/annurev-biochem-060713-035802
3. Leppek K, Das R, Barna M. Functional 5′ UTR mRNA structures in eukaryotic translation regulation and how to find them. *Nature Reviews Molecular Cell Biology*. 2018;19:158–174. https://doi.org/10.1038/nrm.2017.103
4. Hinnebusch AG. Molecular mechanism of scanning and start codon selection in eukaryotes. *Microbiology and Molecular Biology Reviews*. 2011;75:434–467. https://doi.org/10.1128/MMBR.00008-11
