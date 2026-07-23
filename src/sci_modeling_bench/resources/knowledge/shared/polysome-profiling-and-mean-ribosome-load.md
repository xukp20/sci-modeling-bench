# Polysome Profiling and Mean Ribosome Load

## Summary

Polysome profiling separates messenger ribonucleoprotein complexes according
to sedimentation through a density gradient. Fractions associated with
different numbers of ribosomes can be quantified by sequencing or other
assays. Mean ribosome load is a weighted average of the ribosome-number
distribution for an RNA species; it is an occupancy summary, not a direct
measurement of protein yield or of a single kinetic rate.

## Scope

### Covered

- Principle of monosome and polysome fractionation.
- Sequencing-based abundance across fractions.
- Weighted mean ribosome load and its interpretation.
- Replicates, normalization, resolution, and major confounders.

### Not covered

- A particular gradient protocol or library's numerical values.
- A benchmark target transformation.
- A model for inferring sequence effects.

## Key concepts and notation

| Term or symbol | Definition | Notes |
| --- | --- | --- |
| Monosome | mRNA associated with one ribosome | Often represented by an 80S fraction |
| Polysome | mRNA associated with multiple ribosomes | Heavier complexes sediment farther |
| \(c_k\) | Normalized abundance assigned to ribosome-load class \(k\) | May be estimated from sequencing counts |
| MRL | Mean ribosome load | Weighted mean ribosomes per transcript |
| Replicate | Independently processed biological or technical measurement | Scope should be recorded |

## Core knowledge

### Fractionation principle

Cell lysate is layered on a density gradient, commonly sucrose, and
centrifuged. Complexes sediment according to size, shape, and mass. Absorbance
profiles and collected fractions distinguish free subunits, monosomes, and
progressively heavier polysomes [1,2].

RNA abundance in each fraction can be measured by targeted assays,
microarrays, or sequencing. Sequencing-based approaches require library-size,
recovery, and fraction-specific normalization so that read counts can be
interpreted as a distribution rather than as unrelated libraries [2,3].

### Mean ribosome load

If \(c_k\) is the nonnegative abundance of a transcript assigned to a class
with \(k\) ribosomes, its mean ribosome load is

\[
\mathrm{MRL}=\frac{\sum_k k\,c_k}{\sum_k c_k}.
\]

The formula is an expectation over the measured occupancy distribution. When
a fraction represents a range rather than an exact count, an assigned
representative load is used, and that convention becomes part of the
measurement definition [3,4].

Replicate MRL values may be reported separately or combined. An arithmetic
mean across replicates summarizes those measurements but does not by itself
separate biological variability from sequencing and fractionation error.

### Relationship to translation

For otherwise comparable transcripts, greater ribosome occupancy can reflect
more frequent initiation. However, occupancy also depends on elongation time:
slow ribosome movement or pausing can increase the number of ribosomes present
without proportionally increasing completed proteins. Termination, ribosome
drop-off, RNA abundance, and quality-control pathways can also affect the
profile [1,2].

MRL is therefore distinct from translation efficiency defined as protein
output per RNA, from ribosome-profiling footprint density, and from total
protein abundance.

### Sources of uncertainty

Gradient resolution limits separation of neighboring load classes. Fraction
cross-contamination, RNA recovery, sequencing depth, PCR amplification, and
low counts contribute uncertainty. Replicates and spike-ins can reveal or
control some sources, but the measurement remains conditional on the
experimental protocol [2,3].

## Conditions, limitations, and uncertainty

- MRL is meaningful only with the fraction-to-ribosome-number assignment and
  count-normalization convention.
- A weighted mean can hide multimodal or broad occupancy distributions.
- Heavy-polysome association is not automatically equivalent to faster
  protein production.
- Differences among cell types, lysis conditions, inhibitors, and gradient
  collection can limit cross-study comparability.
- RNA chemistry and integrity can influence both translation and recovery.

## Related knowledge resources

- `eukaryotic_mrna_and_translation_initiation`: one process contributing to ribosome occupancy.
- `massively_parallel_translation_reporter_assays`: pooled use of polysome measurements.

## References

1. Arava Y, Wang Y, Storey JD, Liu CL, Brown PO, Herschlag D. Genome-wide analysis of mRNA translation profiles in *Saccharomyces cerevisiae*. *Proceedings of the National Academy of Sciences*. 2003;100:3889–3894. https://doi.org/10.1073/pnas.0635171100
2. Chassé H, Boulben S, Costache V, Cormier P, Morales J. Analysis of translation using polysome profiling. *Nucleic Acids Research*. 2017;45:e15. https://doi.org/10.1093/nar/gkw907
3. Sample PJ, et al. Human 5′ UTR design and variant effect prediction from a massively parallel translation assay. *Nature Biotechnology*. 2019;37:803–809. https://doi.org/10.1038/s41587-019-0164-5
4. Blair JD, Hockemeyer D, Doudna JA, Bateup HS, Floor SN. Widespread translational remodeling during human neuronal differentiation. *Cell Reports*. 2017;21:2005–2016. https://doi.org/10.1016/j.celrep.2017.10.095
