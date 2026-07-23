# Binding Energy Topography by Sequencing

## Summary

Binding Energy Topography by sequencing (BET-seq) is an in vitro method for
measuring relative protein–DNA binding energies across a pooled DNA library.
It combines equilibrium binding on a Mechanically Induced Trapping of
Molecular Interactions (MITOMI) microfluidic device with high-throughput
sequencing. The relative abundance of each DNA species in a protein-bound
fraction is compared with its abundance in the input library. Under stated
equilibrium and recovery assumptions, ratios of these enrichments are related
logarithmically to relative binding free energies [1,2].

## Scope

### Covered

- The physical BET-seq workflow.
- Input and bound-library sequencing counts and normalized fractions.
- The relationship between enrichment ratios and relative binding energy.
- Sampling depth, zero counts, replicates, and major assay limitations.

### Not covered

- Values from a particular BET-seq dataset or replicate.
- A particular sequence library layout.
- A prescribed statistical or machine-learning model.
- Cellular transcriptional activity.

## Key concepts and notation

| Term or symbol | Meaning |
| --- | --- |
| MITOMI | Microfluidic platform that mechanically traps molecular interactions |
| Input library | Pooled DNA library before affinity-dependent recovery |
| Bound library | DNA recovered while associated with immobilized protein |
| \(c_i^{\mathrm{in}}\) | Sequencing count for species \(i\) in the input library |
| \(c_i^{\mathrm{bound}}\) | Sequencing count for species \(i\) in the bound library |
| \(f_i^{\mathrm{in}}\) | Input count divided by total input-library counts |
| \(f_i^{\mathrm{bound}}\) | Bound count divided by total bound-library counts |
| Enrichment | Relative abundance in the bound library divided by relative abundance in the input library |
| \(\Delta\Delta G\) | Binding free-energy difference between two DNA species |

## Core knowledge

### Experimental workflow

BET-seq expresses a fluorescently labeled transcription factor in vitro and
captures it on a MITOMI microfluidic device. A pooled double-stranded DNA
library is introduced and allowed to interact with the surface-immobilized
protein. Pneumatic “button” valves are then actuated to trap equilibrium
protein–DNA complexes while unbound DNA is washed away. The trapped DNA is
recovered and quantified by high-throughput sequencing. An aliquot of the
input DNA pool is also sequenced to measure the starting abundance of each
library member [1,2].

This design measures many sequences in the same physical experiment. Input
sequencing is necessary because synthesis and amplification do not generally
place every sequence into the pool at exactly the same abundance.

### From counts to enrichment

For sequencing depths

\[
C^{\mathrm{in}}=\sum_i c_i^{\mathrm{in}}
\quad\text{and}\quad
C^{\mathrm{bound}}=\sum_i c_i^{\mathrm{bound}},
\]

normalized fractions can be written as

\[
f_i^{\mathrm{in}}=\frac{c_i^{\mathrm{in}}}{C^{\mathrm{in}}},
\qquad
f_i^{\mathrm{bound}}=
\frac{c_i^{\mathrm{bound}}}{C^{\mathrm{bound}}}.
\]

A relative enrichment is

\[
E_i=\frac{f_i^{\mathrm{bound}}}{f_i^{\mathrm{in}}}.
\]

Comparing two DNA species \(i\) and \(j\) cancels shared normalization and
recovery factors. In the ideal equilibrium regime used to motivate BET-seq,

\[
\Delta\Delta G_{i,j}
\approx -RT\ln\left(\frac{E_i}{E_j}\right),
\]

where \(\Delta\Delta G_{i,j}=G_i-G_j\) under this sign convention. Greater
relative enrichment corresponds to more favorable, lower binding free energy.
The approximation relies on the assay model: the measured bound fraction must
track equilibrium occupancy, and shared experimental factors must cancel in
the comparison [1,2].

An unreferenced quantity such as \(-RT\ln E_i\) contains an arbitrary common
offset set by library normalization, protein concentration, recovery, and
other experiment-wide terms. Obtaining absolute \(\Delta G\) or \(K_d\)
requires additional calibration rather than only a bound/input sequencing
ratio [1,2].

### Sequencing noise and depth

Sequencing counts are finite samples. The relative uncertainty of a rare
species is larger than that of a highly counted species, and a large library
requires greater total sequencing depth to achieve the same typical count per
species. BET-seq simulation and experimental analyses show that energetic
resolution depends on library size, sequencing depth, and the distribution of
binding energies [1,2].

A zero observed count means that no read for that species was sampled in that
library. It does not establish a physically infinite binding energy. Direct
log ratios involving a zero count are undefined or infinite, so censoring,
pseudocounts, likelihood-based treatment, or other uncertainty-aware analysis
may be used. The choice is an analysis convention and should be reported.

Independent experimental replicates can differ because of stochastic
sequencing, library preparation, protein preparation, device operation, and
other sources of variation. Combining evidence across replicates can improve
precision, but a composite estimate should preserve which uncertainty comes
from counting and which comes from between-replicate variation [1,2].

### Unique molecular identifiers

The detailed BET-seq protocol incorporates unique molecular identifiers
(UMIs) during library construction. UMIs label original molecules before some
amplification steps and can help identify polymerase-chain-reaction
duplicates. Their effectiveness depends on UMI complexity, assignment
quality, and the deduplication procedure [2].

## Conditions, limitations, and uncertainty

- The relation between enrichment and equilibrium energy assumes adequate
  equilibration and faithful trapping and recovery of bound molecules.
- Immobilization, fluorescent tags, protein truncations, buffer composition,
  temperature, ionic strength, and DNA construct design can alter binding.
- A pooled library introduces competition and possible ligand-depletion
  effects; assay design must keep these within the regime assumed by the
  analysis [1,2].
- PCR and sequencing can introduce sequence-dependent sampling biases. Input
  normalization corrects starting abundance but does not guarantee removal of
  every downstream bias.
- Low or zero counts carry asymmetric and sometimes censored uncertainty.
- BET-seq is an in vitro affinity assay. Chromatin accessibility, cofactors,
  competitors, localization, and gene-regulatory context are not measured.

## Related knowledge resources

- `binding_affinity_and_thermodynamics`: \(K_d\), occupancy, and Gibbs energy.
- `transcription_factor_dna_binding`: molecular recognition and the distinction between affinity and cellular function.
- `binding_sites_motifs_and_sequence_context`: sequence context around motif cores.

## References

1. Le DD, Shimko TC, Aditham AK, Keys AM, Longwell SA, Orenstein Y, Fordyce PM. Comprehensive, high-resolution binding energy landscapes reveal context dependencies of transcription factor binding. *Proceedings of the National Academy of Sciences of the United States of America*. 2018;115(16):E3702–E3711. https://doi.org/10.1073/pnas.1715888115. [Primary research]
2. Aditham AK, Shimko TC, Fordyce PM. BET-seq: Binding energy topographies revealed by microfluidics and high-throughput sequencing. *Methods in Cell Biology*. 2018;148:229–250. https://doi.org/10.1016/bs.mcb.2018.09.011. [Methods protocol]
