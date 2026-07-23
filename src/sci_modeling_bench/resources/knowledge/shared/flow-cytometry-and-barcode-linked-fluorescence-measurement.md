# Flow Cytometry and Barcode-Linked Fluorescence Measurement

## Summary

Flow cytometry measures optical signals from individual particles or cells as
they pass through a focused light path. Fluorescence-activated cell sorting
can partition cells into intensity bins, while DNA barcodes can link sorted
measurements back to molecular variants in pooled libraries. The resulting
variant-level value depends on cytometer settings, gates, bin boundaries,
cell-to-cell variation, barcode coverage, and the chosen aggregation
procedure [1–3].

## Scope

### Covered

- Single-cell fluorescence acquisition and gating.
- Logarithmic intensity, sorting bins, and dynamic range.
- Barcode–variant linkage, sequencing counts, coverage, and aggregation.

### Not covered

- A particular instrument configuration or library.
- A universal estimator for reconstructing fluorescence from bins.
- Dataset-specific barcode identifiers, filtering, or labels.

## Key concepts and notation

| Term | Definition |
| --- | --- |
| event | One particle or cell recorded by the cytometer |
| gate | Rule selecting events by scatter or fluorescence measurements |
| FACS | Fluorescence-activated cell sorting |
| bin | Defined fluorescence interval receiving sorted events |
| barcode | Sequence identifier experimentally linked to a construct or variant |
| coverage | Number of cells or sequencing reads supporting an estimate |

## Core knowledge

### Single-cell measurement

A flow cytometer illuminates cells in a fluid stream and records forward
scatter, side scatter, and fluorescence channels. Scatter and viability
measurements can support gates that exclude debris, dead cells, or cell
aggregates. Compensation is required when emission from one fluorophore spills
into another detector channel [1].

Fluorescence distributions often span orders of magnitude, so instruments
commonly use logarithmic or biexponential display and transformation. A
reported `log10` intensity is a transformed instrument signal, not a
thermodynamic logarithm.

### Sorting into fluorescence bins

FACS can direct events into discrete bins bounded by fluorescence thresholds.
Sequencing the representation of a variant across bins permits reconstruction
of a distribution or summary intensity. Accuracy depends on bin boundaries,
numbers of sorted cells, sequencing depth, and the estimator used [2,3].

A bin assignment is interval-censored information: it identifies an intensity
range rather than an exact single-cell value. Wider bins lose resolution,
while narrow bins require more cells and reads to maintain coverage.

### Barcode linkage

In a pooled assay, a barcode is associated with a designed or observed
variant. Barcode sequencing after sorting connects fluorescence measurements
to that variant without individually culturing every construct [2,3].

Multiple barcodes for the same variant can provide technical replication and
can reveal barcode-specific or integration-specific variation. A single
barcode can nevertheless be misleading if linkage errors, mutations,
contamination, or low coverage occur.

### Aggregation and uncertainty

Variant-level means, medians, or inferred distribution parameters summarize
cellular and barcode-level measurements differently. Medians reduce the
influence of extreme observations but do not remove systematic bias.
Dispersion across cells and dispersion across barcodes represent different
sources of variability.

Sampling uncertainty generally decreases with greater independent cell and
barcode support, but raw read count alone does not guarantee accuracy.
Barcode linkage quality, gate selection, library bottlenecks, and sequencing
errors also matter.

### Measurement floors and ceilings

Autofluorescence and nonspecific signal create a lower floor. Detector or
amplifier saturation creates an upper ceiling. Values near either boundary
may fail to preserve the true ordering of molecular fluorescence. Instrument
settings and controls define the usable dynamic range [1].

## Conditions, limitations, and uncertainty

- Flow-cytometry intensity is relative unless calibrated with appropriate
  standards.
- Cell size, expression level, growth state, and maturation can broaden a
  distribution independently of intrinsic molecular brightness.
- Barcode support is technical evidence, not proof that every barcode is
  correctly linked.
- Sorting and sequencing introduce distinct sampling processes.
- Aggregated variant measurements do not recover all single-cell heterogeneity.

## Related knowledge resources

- `fluorescence_photophysics_and_brightness`: molecular and cellular sources
  of fluorescence intensity.
- `protein_fitness_landscapes_and_epistasis`: interpretation of variant-level
  phenotype landscapes.

## References

1. Cossarizza A, et al. Guidelines for the use of flow cytometry and cell sorting in immunological studies. *European Journal of Immunology*. 2017;47:1584–1797. https://doi.org/10.1002/eji.201646632. [Methods guideline]
2. Fowler DM, Fields S. Deep mutational scanning: a new style of protein science. *Nature Methods*. 2014;11:801–807. https://doi.org/10.1038/nmeth.3027. [Review]
3. Peterman N, Levine E. Sort-seq under the hood: implications of design choices on large-scale characterization of sequence-function relations. *BMC Genomics*. 2016;17:206. https://doi.org/10.1186/s12864-016-2533-5. [Methods analysis]
