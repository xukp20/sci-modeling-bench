# Five-Prime UTR Regulatory Elements

## Summary

The eukaryotic 5′ untranslated region is a regulatory part of an mRNA that
can influence ribosome recruitment, scanning, and start-site choice. Its
effects arise from combinations of primary sequence, RNA structure, upstream
translation events, RNA-binding proteins, modifications, and specialized
initiation elements. The same element can behave differently when its
position, transcript context, cell type, or physiological condition changes.

## Scope

### Covered

- Major classes of sequence and structural elements in 5′ UTRs.
- Position and context dependence of translational regulation.
- Interactions among cis elements, RNA-binding proteins, and initiation machinery.

### Not covered

- A catalog of elements in one particular sequence library.
- A claim that nucleotide composition alone determines translation.
- A modeling or sequence-design strategy.

## Key concepts and notation

| Term | Definition |
| --- | --- |
| Cis-regulatory element | RNA feature acting on the molecule in which it occurs |
| RBP | RNA-binding protein |
| Hairpin | Stem capped by an unpaired loop |
| uORF | Open reading frame upstream of the main coding sequence |
| IRES | Internal ribosome entry site supported by functional evidence |
| TOP motif | Terminal oligopyrimidine tract found in a regulated transcript class |

## Core knowledge

### Sequence and structure influence initiation

Cap-proximal or internally positioned structures can alter access of
cap-binding factors and movement of scanning complexes. Stable structures
often impede canonical initiation, but structure can also organize
factor-binding sites or support specialized initiation. Position matters:
the same nominal stability placed near the cap, within the scanning path, or
downstream of a start site need not have the same effect [1,2].

The relationship between G/C content and structure is statistical rather than
deterministic. G- and C-rich sequences have more opportunities to form stable
G–C pairs, but actual folding depends on base order, competing pairings,
loops, ions, proteins, and temperature.

### Start sites and translated upstream elements

Upstream AUG and near-cognate start codons can change which ribosomes reach
the main coding sequence. An upstream start may begin a uORF, overlap the main
coding region, or be bypassed. Its effect depends on initiation context,
reading frame, stop-codon position, peptide-dependent stalling, and the
capacity for reinitiation [1,3].

### RNA-binding proteins and sequence motifs

RBPs recognize RNA through combinations of sequence and structure. Binding in
a 5′ UTR can recruit or exclude initiation factors, remodel structure,
localize an mRNA, or couple translation to signaling. A short motif is
therefore not a complete binding rule: accessibility, neighboring bases,
protein concentration, and competing factors matter [1,4].

Some transcript classes contain specialized elements. For example, terminal
oligopyrimidine motifs participate in growth-dependent regulation of many
translation-machinery transcripts. Internal ribosome entry sites can support
cap-independent recruitment, but functional IRES identity cannot be assigned
from a vaguely similar sequence alone [1,2].

### Regulatory features interact

Elements in one leader can interact non-additively. A hairpin may alter access
to a start codon or RBP motif; an RBP may stabilize one conformation; an
upstream translation event can remodel downstream RNA. The main start context,
coding sequence, 3′ UTR, poly(A) tail, and cellular state can also modify an
observed 5′-UTR effect [1,2].

## Conditions, limitations, and uncertainty

- A motif occurrence establishes sequence compatibility, not biochemical
  occupancy or a fixed effect size.
- Predicted structure does not establish the structure populated in a cell.
- Effects measured with one reporter, cell type, RNA chemistry, or delivery
  method may not transfer unchanged to another.
- Many 5′ UTRs use several mechanisms at once; single-feature explanations
  can be incomplete.
- Transcript abundance and translation are distinct layers of gene
  expression, although both contribute to protein output.

## Related knowledge resources

- `rna_sequence_structure_and_base_pairing`: physical basis of RNA folding.
- `upstream_start_codons_and_upstream_open_reading_frames`: upstream translation.
- `kozak_context_and_start_codon_recognition`: context-dependent start selection.

## References

1. Hinnebusch AG, Ivanov IP, Sonenberg N. Translational control by 5′-untranslated regions of eukaryotic mRNAs. *Science*. 2016;352:1413–1416. https://doi.org/10.1126/science.aad9868
2. Leppek K, Das R, Barna M. Functional 5′ UTR mRNA structures in eukaryotic translation regulation and how to find them. *Nature Reviews Molecular Cell Biology*. 2018;19:158–174. https://doi.org/10.1038/nrm.2017.103
3. Wethmar K. The regulatory potential of upstream open reading frames in eukaryotic gene expression. *Wiley Interdisciplinary Reviews: RNA*. 2014;5:765–778. https://doi.org/10.1002/wrna.1245
4. Gebauer F, Schwarzl T, Valcárcel J, Hentze MW. RNA-binding proteins in human genetic disease. *Nature Reviews Genetics*. 2021;22:185–198. https://doi.org/10.1038/s41576-020-00302-y
