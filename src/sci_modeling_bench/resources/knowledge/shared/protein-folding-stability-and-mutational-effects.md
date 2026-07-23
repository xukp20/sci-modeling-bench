# Protein Folding, Stability, and Mutational Effects

## Summary

Protein folding reflects a balance among intramolecular interactions,
solvation, conformational entropy, and environmental conditions. Thermodynamic
stability describes the free-energy difference between folded and unfolded
ensembles, whereas folding and unfolding rates describe kinetics. A mutation
can alter stability, folding pathways, aggregation, expression, or a local
functional site; these effects are related but not equivalent [1,2].

## Scope

### Covered

- Folding free energy and mutation-induced stability change.
- Folding kinetics, structural packing, and aggregation.
- Common physical mechanisms of mutational effects.

### Not covered

- A sequence-only method for calculating stability.
- A claim that stability is identical to biological activity.
- Effects inferred from a particular benchmark dataset.

## Key concepts and notation

| Symbol or term | Definition | Notes |
| --- | --- | --- |
| \(\Delta G_\mathrm{fold}\) | \(G_\mathrm{folded}-G_\mathrm{unfolded}\) | Negative under a convention favoring the folded state |
| \(\Delta G_\mathrm{unfold}\) | \(G_\mathrm{unfolded}-G_\mathrm{folded}\) | Positive for a thermodynamically stable folded state |
| \(\Delta\Delta G\) | Mutant folding free energy minus reference value | Sign depends on the stated folding/unfolding convention |
| kinetic stability | Resistance to unfolding determined by activation barriers | Not identical to equilibrium stability |

## Core knowledge

### Folding thermodynamics

At equilibrium, folded and unfolded populations are related by their free
energy difference. Using the unfolding convention,

\[
\Delta G_\mathrm{unfold}=G_\mathrm{unfolded}-G_\mathrm{folded}
=-RT\ln K_\mathrm{unfold},
\]

where \(K_\mathrm{unfold}=[U]/[F]\) for an idealized two-state system. A larger
positive \(\Delta G_\mathrm{unfold}\) means the folded ensemble is more
thermodynamically favored [1].

For a mutation,

\[
\Delta\Delta G_\mathrm{unfold}
=\Delta G_{\mathrm{unfold,mut}}
-\Delta G_{\mathrm{unfold,ref}}.
\]

Under this convention, a positive value is stabilizing. Many publications
instead define folding free energy, reversing the sign; the convention must
always be checked.

### Physical contributions

Hydrophobic burial, van der Waals packing, hydrogen bonds, electrostatic
interactions, and solvent reorganization all contribute to folding.
Favorable interactions are substantially offset by loss of conformational
entropy, so modest local changes can shift the population balance [1].

A substitution can create a cavity, steric clash, unsatisfied polar group, or
electrostatic mismatch. It can also alter backbone preferences, secondary
structure, loop dynamics, or a network of coupled interactions. The same
chemical change can therefore have different effects in different structural
environments.

### Kinetics and maturation

Thermodynamically stable proteins can fold slowly or become kinetically
trapped. Folding and unfolding rate constants depend on activation barriers,
not only on the final-state free-energy difference. In cells, translation
rate, chaperones, degradation, and molecular crowding further affect the
amount of correctly folded protein [2].

### Aggregation and solubility

Partially folded or misfolded states can expose hydrophobic surfaces and
associate. Aggregation depends on concentration, temperature, expression
conditions, and the accessible conformational ensemble. A mutation that
changes aggregation propensity can change soluble protein abundance without
directly changing the intrinsic activity of correctly folded molecules.

### Stability and function are distinct

Function can be lost through a local active-site, binding-site, or chromophore
perturbation even when the global fold remains stable. Conversely, a
stabilizing substitution need not improve a measured function. Observed
cellular activity may combine folded fraction, abundance, maturation,
intrinsic molecular activity, and measurement conditions.

## Conditions, limitations, and uncertainty

- Two-state equations are approximations for proteins with intermediates,
  oligomerization, or irreversible aggregation.
- \(\Delta\Delta G\) sign and standard state must be stated.
- In-vitro equilibrium stability may not predict cellular soluble abundance.
- Static structures do not fully describe folding pathways or conformational
  ensembles.

## Related knowledge resources

- `protein_sequences_amino_acids_and_substitutions`: residue chemistry and
  sequence notation.
- `protein_fitness_landscapes_and_epistasis`: background-dependent combined
  mutational effects.

## References

1. Dill KA, MacCallum JL. The protein-folding problem, 50 years on. *Science*. 2012;338:1042–1046. https://doi.org/10.1126/science.1219021. [Review]
2. Bartlett AI, Radford SE. An expanding arsenal of experimental methods yields an explosion of insights into protein folding mechanisms. *Nature Structural & Molecular Biology*. 2009;16:582–588. https://doi.org/10.1038/nsmb.1592. [Review]
