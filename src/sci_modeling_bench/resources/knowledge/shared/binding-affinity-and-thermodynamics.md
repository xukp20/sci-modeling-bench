# Binding Affinity and Thermodynamics

## Summary

For a simple reversible protein–DNA interaction, equilibrium affinity can be
described by an association or dissociation constant. Lower \(K_d\) means that
less free DNA is required to occupy a given fraction of protein binding sites
under the ideal one-to-one model. Standard binding Gibbs energy is
logarithmically related to the dimensionless equilibrium constant. These
thermodynamic quantities are distinct from kinetic rate constants,
fluorescence intensities, enrichment statistics, and cellular regulatory
activity.

## Scope

### Covered

- One-to-one equilibrium binding, \(K_a\), \(K_d\), occupancy, and standard Gibbs energy.
- Relative binding free energy and kinetic association/dissociation rates.
- Conditions required for interpreting and comparing affinity measurements.

### Not covered

- Detailed cooperative, allosteric, or multisite binding models.
- A calibration of any particular experimental score to affinity.
- Cellular transcriptional effects.

## Key concepts and notation

| Term or symbol | Definition | Unit or notes |
| --- | --- | --- |
| \(P\) | Free protein | Concentration or activity |
| \(D\) | Free DNA ligand | Concentration or activity |
| \(PD\) | Protein–DNA complex | Concentration or activity |
| \(K_a\) | Equilibrium association constant | Often reported in inverse concentration |
| \(K_d\) | Equilibrium dissociation constant | Often reported as concentration |
| \(k_{\mathrm{on}}\) | Association rate constant | For a bimolecular step, concentration\(^{-1}\) time\(^{-1}\) |
| \(k_{\mathrm{off}}\) | Dissociation rate constant | Time\(^{-1}\) |
| \(\Delta G^\circ_{\mathrm{bind}}\) | Standard Gibbs-energy change for association | Energy per mole |
| \(R\) | Molar gas constant | 8.314462618 J mol\(^{-1}\) K\(^{-1}\) |
| \(T\) | Thermodynamic temperature | kelvin |

## Core knowledge

### Equilibrium constants

For

\[
P + D \rightleftharpoons PD,
\]

the concentration-form dissociation constant is

\[
K_d=\frac{[P][D]}{[PD]},
\]

when activity coefficients and the standard-concentration factor are treated
according to the chosen convention. The corresponding association constant is
\(K_a=1/K_d\) when reciprocal units and the same convention are used [1].
Smaller \(K_d\), or larger \(K_a\), denotes tighter equilibrium binding.

For a single independent site, if free ligand concentration is effectively
known and ligand depletion is negligible, the bound fraction is

\[
\theta=\frac{[D]}{K_d+[D]}.
\]

Under these assumptions, \(\theta=1/2\) when \([D]=K_d\). This statement does
not generally hold unchanged for cooperative systems, multiple site classes,
or when total concentration is substituted for free concentration.

### Standard binding Gibbs energy

Thermodynamics defines a dimensionless standard equilibrium constant
\(K^\circ\) and relates it to standard reaction Gibbs energy by [2]

\[
\Delta G^\circ=-RT\ln K^\circ.
\]

For association, this can be written

\[
\Delta G^\circ_{\mathrm{bind}}=-RT\ln K_a^\circ
=RT\ln K_d^\circ,
\]

where \(K_a^\circ\) and \(K_d^\circ\) are dimensionless forms referenced to a
stated standard state. More negative \(\Delta G^\circ_{\mathrm{bind}}\)
indicates more favorable association.

For two DNA ligands measured under the same conditions and standard-state
convention,

\[
\Delta\Delta G^\circ
=\Delta G^\circ_2-\Delta G^\circ_1
=RT\ln\left(\frac{K_{d,2}}{K_{d,1}}\right).
\]

Thus free-energy differences correspond to ratios of equilibrium constants,
not linear differences in \(K_d\).

### Kinetics and equilibrium

For an elementary two-state interaction,

\[
K_d=\frac{k_{\mathrm{off}}}{k_{\mathrm{on}}}.
\]

Two complexes can have similar \(K_d\) values but different association and
dissociation rates. Residence time is related to \(k_{\mathrm{off}}\), whereas
equilibrium occupancy depends on the ratio of rates and the free
concentrations. More complicated mechanisms can contain intermediate states
and need not be described by one pair of rate constants [1,3].

### Relative assay scores

Fluorescence intensity, enrichment, rank statistics, and motif scores may
correlate with affinity within a calibrated regime, but they are not
thermodynamic quantities by definition. Converting such a score to \(K_d\) or
\(\Delta G^\circ\) requires an explicit calibration and assumptions about the
assay response.

## Conditions, limitations, and uncertainty

- Equilibrium comparisons require sufficient equilibration and clearly
  defined free molecular species.
- Temperature, ionic strength, pH, buffer composition, cofactors, competitors,
  DNA length, labels, and protein construct can change measured affinity.
- Reported concentration-form constants can depend on conventions and
  nonideal-solution effects; thermodynamic equilibrium constants use
  dimensionless activities.
- Apparent \(K_d\) values from complex or nonequilibrium assays may combine
  multiple physical processes.
- Binding affinity alone does not determine cellular occupancy or regulatory
  consequence.

## Related knowledge resources

- `transcription_factor_dna_binding`: specificity, occupancy, and molecular recognition.
- `protein_binding_microarrays`: rank and fluorescence measurements distinct from \(K_d\).

## References

1. International Union of Pure and Applied Chemistry. Equilibrium dissociation constant. *Compendium of Chemical Terminology*, 5th ed., online version 5.0.0. 2025. https://doi.org/10.1351/goldbook.14132. Accessed 2026-07-23. [Official definition]
2. International Union of Pure and Applied Chemistry. Standard equilibrium constant. *Compendium of Chemical Terminology*, 5th ed., online version 5.0.0. 2025. https://doi.org/10.1351/goldbook.S05915. Accessed 2026-07-23. [Official definition]
3. Hulme EC, Trevethick MA. Ligand binding assays at equilibrium: validation and interpretation. *British Journal of Pharmacology*. 2010;161:1219–1237. https://doi.org/10.1111/j.1476-5381.2009.00604.x. [Review]
