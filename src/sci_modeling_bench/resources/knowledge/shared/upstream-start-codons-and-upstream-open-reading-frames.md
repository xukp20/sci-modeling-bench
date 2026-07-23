# Upstream Start Codons and Upstream Open Reading Frames

## Summary

An upstream start codon lies in a 5′ leader before the main coding-sequence
start. It becomes an upstream open reading frame only when initiation there
defines a translated frame extending to a termination codon. Upstream
translation can reduce, redirect, or conditionally regulate main-protein
synthesis through leaky scanning, ribosome dissociation, reinitiation,
overlap, stalling, and peptide-dependent mechanisms.

## Scope

### Covered

- Distinction among uAUGs, upstream initiation sites, and uORFs.
- Reading frames, termination, overlap, leaky scanning, and reinitiation.
- Common mechanisms and context dependence of uORF regulation.

### Not covered

- An annotation convention for one dataset.
- A universal claim that every upstream AUG represses translation.
- A computational method for identifying useful sequence candidates.

## Key concepts and notation

| Term | Definition |
| --- | --- |
| uAUG | AUG located upstream of the main start codon |
| uTIS | Upstream translation initiation site |
| uORF | Translated upstream frame from a start site to a stop codon |
| Main ORF | Open reading frame encoding the principal annotated protein |
| Leaky scanning | Continued scanning past a potential initiation site |
| Reinitiation | New initiation after a ribosome translated and terminated an upstream ORF |
| Overlapping uORF | uORF whose translated interval overlaps the main ORF |

## Core knowledge

### A start codon is not by itself an open reading frame

An AUG triplet upstream of the main start is a potential initiation site.
Whether it produces an uORF depends on recognition by scanning complexes and
the downstream frame. Each start establishes one of three reading frames; the
first in-frame stop codon delimits the corresponding ORF. Near-cognate codons
can also serve as upstream starts in some contexts [1,2].

### Competing fates of scanning ribosomes

Some scanning complexes initiate at an upstream site, while others bypass it.
The fraction following each path depends on start-codon identity, neighboring
sequence, RNA structure, and initiation-factor state. Ribosomes that translate
an uORF may dissociate at its stop codon or retain/reacquire factors and
reinitiate downstream [2,3].

Reinitiation commonly depends on uORF length, the intercistronic distance
between the uORF stop and downstream start, and the time available to regain
an initiation-competent state. An uORF overlapping the main ORF can prevent
ordinary downstream reinitiation because the main start has already been
passed in another frame [1–3].

### Regulatory outcomes are diverse

Upstream translation often lowers initiation at a downstream main ORF by
diverting scanning complexes. It can also create conditional regulation.
Changes in initiation-factor availability, metabolites, stress, or ribosome
behavior can alter bypass and reinitiation. Some uORF-encoded peptides cause
sequence-dependent ribosome stalling, while other uORFs act without a
conserved peptide [1,3].

Multiple upstream starts can interact. Recognition of one site changes the
population of ribosomes that reaches later sites, so their effects need not be
independent or additive.

### Position and frame are mechanistically relevant

The same AUG sequence can have different consequences when moved because
start-to-cap distance, surrounding structure, reading frame, stop position,
and distance to the main start change. “Upstream AUG present” is therefore a
coarse property that does not fully specify the translational mechanism.

## Conditions, limitations, and uncertainty

- Sequence annotation identifies potential ORFs, not necessarily translated
  ORFs; experimental evidence can come from ribosome profiling, proteomics,
  or reporter perturbation.
- Near-cognate initiation and reinitiation efficiencies vary by organism and
  cell state.
- A translated uORF can affect RNA stability through pathways such as
  nonsense-mediated decay as well as affect translation.
- The absence of an AUG-initiated uORF does not exclude other 5′-leader
  regulation.
- The magnitude and even direction of an uORF effect cannot be assigned from
  its presence alone.

## Related knowledge resources

- `kozak_context_and_start_codon_recognition`: recognition probability of upstream and main starts.
- `five_prime_utr_regulatory_elements`: other interacting leader elements.

## References

1. Wethmar K. The regulatory potential of upstream open reading frames in eukaryotic gene expression. *Wiley Interdisciplinary Reviews: RNA*. 2014;5:765–778. https://doi.org/10.1002/wrna.1245
2. Hinnebusch AG, Ivanov IP, Sonenberg N. Translational control by 5′-untranslated regions of eukaryotic mRNAs. *Science*. 2016;352:1413–1416. https://doi.org/10.1126/science.aad9868
3. Young SK, Wek RC. Upstream open reading frames differentially regulate gene-specific translation in the integrated stress response. *Journal of Biological Chemistry*. 2016;291:16927–16935. https://doi.org/10.1074/jbc.R116.733899
