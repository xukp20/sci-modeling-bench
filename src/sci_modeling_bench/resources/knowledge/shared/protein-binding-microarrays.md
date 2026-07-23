# Protein-Binding Microarrays

## Summary

Protein-binding microarrays (PBMs) are in-vitro assays that expose a
DNA-binding protein to many double-stranded DNA probes on a microarray and use
fluorescence to quantify relative binding. Universal PBM designs distribute
all words of a chosen length across longer probe sequences, allowing each word
to be observed in multiple sequence contexts. Probe intensity, median
word-associated intensity, and the rank-based enrichment score (E-score) are
different measurements and should not be interpreted interchangeably.

## Scope

### Covered

- Universal PBM construction, binding, detection, and normalization.
- How probe measurements are summarized into word-level intensities and E-scores.
- The definition, range, and interpretation of the PBM E-score.
- Major experimental and interpretive limitations.

### Not covered

- Any particular PBM experiment, transcription factor, or measurement collection.
- Microarray fabrication protocols in operational detail.
- A conversion from E-score to an absolute dissociation constant.

## Key concepts and notation

| Term or symbol | Definition | Unit or notes |
| --- | --- | --- |
| Probe | A longer DNA sequence immobilized at one microarray feature | Contains multiple overlapping sequence words |
| \(k\)-mer | A contiguous DNA word of length \(k\) | Gapped words can also be analyzed |
| Probe intensity | Fluorescence associated with protein bound at a feature | Relative, assay-dependent signal |
| Median \(k\)-mer intensity | Median normalized intensity among probes containing a \(k\)-mer | Context-aggregated relative signal |
| E-score | Rank-based enrichment of probes containing a word | Unitless; ranges from \(-0.5\) to \(+0.5\) in the published definition |

## Core knowledge

### Universal sequence coverage

Universal PBMs use combinatorial probe designs related to de Bruijn sequences
so that every possible word of a selected length occurs on the array [1,2].
The word instances are embedded in longer probes. Multiple probes contain the
same word in different surrounding contexts, allowing a word-level statistic
to aggregate across those occurrences rather than treating one isolated
oligonucleotide as the sole measurement.

Reverse-complement symmetry reduces the number of nonredundant double-stranded
words that must be represented. Palindromic words are their own reverse
complements and consequently have different occurrence counts in some array
designs [1,2].

### Binding and fluorescence measurement

Single-stranded probes are converted to double-stranded DNA. A purified,
typically epitope-tagged DNA-binding protein is incubated with the array, and
bound protein is detected with a fluorescent antibody. Separate DNA
fluorescence, spatial correction, controls, and scans at multiple powers can be
used to identify poor features and normalize technical variation [2].

Each probe contains multiple overlapping words, so a probe intensity is not
the direct response of only one \(k\)-mer. Conversely, each \(k\)-mer is
represented by a set of probes. The median normalized signal over probes
containing a word is used as one relative measure associated with that word
[2].

### Rank-based E-score

The published universal-PBM analysis ranks normalized probe intensities and,
for each word, separates probes into a foreground containing the word and a
background not containing it. In the protocol definition, the brightest half
of the foreground and background are considered. If \(F\) and \(B\) are their
sample sizes and \(r_F\) and \(r_B\) are the corresponding sums of ranks, the
enrichment statistic is [2]

\[
E=\frac{r_B/B-r_F/F}{B+F},
\]

under the protocol's convention that brighter probes receive better (smaller)
ranks. It ranges from \(-0.5\) for strongest depletion to \(+0.5\) for
strongest enrichment and is approximately an area-under-the-ROC statistic
minus \(0.5\) [1,2].

Because the E-score uses ranks, it is invariant to transformations that
preserve the probe ordering. Its magnitude describes relative enrichment of
word-containing probes within an experiment; it is not a fluorescence unit,
concentration, \(K_d\), or Gibbs energy. Differences between E-scores are not
fixed-fold changes in molecular affinity.

### Two complementary summaries

Median word-associated intensity retains information about relative signal
magnitude and has been observed to track relative affinities in validation
experiments. The E-score emphasizes robust ordering and enrichment. A
word-by-word table can retain preferences that a compact mononucleotide motif
loses, including some context or nucleotide-dependence effects; a motif offers
a more compact summary [1,2].

## Conditions, limitations, and uncertainty

- PBMs are surface-based in-vitro assays. Immobilization, probe synthesis,
  local surface effects, antibody detection, and signal saturation can affect
  measurements.
- Protein concentration, tag placement, protein construct, folding,
  oligomerization, buffer, competitors, and incubation conditions can change
  the observed profile.
- A longer probe contains overlapping words; aggregation across contexts
  reduces but does not prove the absence of context effects.
- Rank-based scores can be stable across changes in signal scale while losing
  information about absolute signal differences.
- Replicate agreement should be evaluated empirically. Different array designs
  provide useful context diversity but can also introduce design-specific
  variation.
- In-vitro sequence preference does not by itself establish genomic occupancy
  or transcriptional function.

## Related knowledge resources

- `binding_sites_motifs_and_sequence_context`: word tables, motifs, and positional dependence.
- `binding_affinity_and_thermodynamics`: quantities that E-score does not directly measure.
- `transcription_factor_dna_binding`: physical mechanisms behind sequence preference.

## References

1. Berger MF, Philippakis AA, Qureshi AM, He FS, Estep PW III, Bulyk ML. Compact, universal DNA microarrays to comprehensively determine transcription-factor binding site specificities. *Nature Biotechnology*. 2006;24:1429–1435. https://doi.org/10.1038/nbt1246. [Method paper]
2. Berger MF, Bulyk ML. Universal protein-binding microarrays for the comprehensive characterization of the DNA-binding specificities of transcription factors. *Nature Protocols*. 2009;4:393–411. https://doi.org/10.1038/nprot.2008.195. [Protocol]
3. Berger MF, Badis G, Gehrke AR, et al. Variation in homeodomain DNA binding revealed by high-resolution analysis of sequence preferences. *Cell*. 2008;133:1266–1276. https://doi.org/10.1016/j.cell.2008.05.024. [Primary research]
