# Protein Fitness Landscapes and Epistasis

## Summary

A genotype–phenotype or fitness landscape maps sequences to a measured
phenotype or reproductive fitness under stated conditions. Neighboring
protein genotypes commonly differ by one amino-acid substitution. Epistasis
occurs when a mutation's effect depends on genetic background; it can change
effect magnitude or even reverse effect direction. Landscape properties are
therefore conditional on the phenotype scale, reference genotype, and
environment [1,2].

## Scope

### Covered

- Sequence spaces, mutational neighborhoods, and paths.
- Additive expectations and pairwise epistasis.
- Magnitude, sign, reciprocal-sign, and higher-order epistasis.

### Not covered

- A landscape reconstructed from a particular dataset.
- Evolutionary fitness inferred automatically from a molecular phenotype.
- An optimization or model-selection procedure.

## Key concepts and notation

| Term | Definition |
| --- | --- |
| genotype | A particular sequence or set of alleles |
| phenotype \(y(g)\) | Measured property assigned to genotype \(g\) |
| mutational neighbor | Genotype separated by one defined edit |
| epistasis | Departure of a combined effect from a stated noninteracting model |
| sign epistasis | A mutation changes effect direction across backgrounds |

## Core knowledge

### Sequence space and landscapes

For a protein of length \(L\) over 20 standard amino acids, the full
fixed-length sequence space contains \(20^L\) sequences. A local landscape
usually samples only a connected neighborhood around one or more references.
Edges can represent single substitutions, while longer paths represent
successive edits [1].

The vertical landscape quantity may be organismal fitness, binding, activity,
fluorescence, stability, or another phenotype. These quantities are not
interchangeable. A phenotype landscape becomes an evolutionary fitness
landscape only when the measured quantity has the required relationship to
reproduction in the stated environment.

### Additive expectations

For reference genotype \(00\), two mutations \(A\) and \(B\), and a phenotype
scale \(y\), additive pairwise epistasis can be written

\[
\varepsilon
=y(AB)-y(A)-y(B)+y(00).
\]

\(\varepsilon=0\) is additive on that scale. A logarithmic scale converts a
multiplicative expectation on the original positive scale into an additive
one. Epistasis values therefore depend on the scale and null model [1].

### Magnitude and sign epistasis

Magnitude epistasis changes the size, but not the direction, of a mutation's
effect. Sign epistasis occurs when, for example,

\[
y(A)-y(00)>0
\quad\text{but}\quad
y(AB)-y(B)<0.
\]

The same mutation is beneficial relative to one background and deleterious
relative to another. Reciprocal sign epistasis means each of two mutations
changes sign depending on the other; this can create multiple local peaks in
a two-locus sublandscape [1,2].

### Higher-order interactions

Pairwise terms need not explain combinations of three or more mutations.
Higher-order epistasis is the residual interaction attributable to a
combination after lower-order terms under the chosen expansion are accounted
for. Its numerical value also depends on phenotype scale and sampling design.

### Mechanistic origins

Epistasis can arise from direct residue contacts, long-range conformational
coupling, shared effects on folding stability, pathway thresholds, or
saturation of a measurement. For example, several destabilizing mutations
can produce a nonlinear loss of folded population even if their underlying
free-energy contributions are approximately additive [3].

## Conditions, limitations, and uncertainty

- A landscape is conditional on assay, environment, genetic background, and
  phenotype transformation.
- Sparse observations cannot establish the topology of an entire sequence
  space.
- Measurement floors and ceilings can resemble biological epistasis.
- A local peak under one allowed edit set or environment need not be globally
  optimal or remain a peak elsewhere.

## Related knowledge resources

- `protein_folding_stability_and_mutational_effects`: one physical source of
  nonlinear genotype–phenotype relationships.
- `fluorescence_photophysics_and_brightness`: fluorescence as a conditional
  molecular and cellular phenotype.

## References

1. de Visser JAGM, Krug J. Empirical fitness landscapes and the predictability of evolution. *Nature Reviews Genetics*. 2014;15:480–490. https://doi.org/10.1038/nrg3744. [Review]
2. Poelwijk FJ, Kiviet DJ, Weinreich DM, Tans SJ. Empirical fitness landscapes reveal accessible evolutionary paths. *Nature*. 2007;445:383–386. https://doi.org/10.1038/nature05451. [Primary research]
3. Bershtein S, Segal M, Bekerman R, Tokuriki N, Tawfik DS. Robustness–epistasis link shapes the fitness landscape of a randomly drifting protein. *Nature*. 2006;444:929–932. https://doi.org/10.1038/nature05385. [Primary research]
