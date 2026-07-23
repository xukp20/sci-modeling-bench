# Superconductivity and Critical Temperature

## Summary

Superconductivity is a collective quantum state characterized by vanishing
dc electrical resistance under suitable conditions and by magnetic-field
screening through the Meissner effect. A superconducting critical temperature
\(T_c\) marks a transition between superconducting and normal states under
specified field, current, pressure, and sample conditions. \(T_c\) is distinct
from critical current and critical magnetic fields.

## Scope

### Covered

- Zero resistance, the Meissner effect, and Cooper pairing.
- \(T_c\), the superconducting energy gap, and critical fields.
- Type-I and type-II superconductivity.
- Conventional and unconventional pairing as scientific categories.

### Not covered

- A list or ranking of candidate materials.
- A particular table of measured critical temperatures.
- Detailed many-body calculations.
- Engineering design of superconducting devices.

## Key concepts and notation

| Symbol or term | Meaning |
| --- | --- |
| \(T_c\) | Superconducting transition temperature under stated conditions |
| \(\Delta\) | Superconducting quasiparticle energy gap |
| \(H_c\) | Thermodynamic critical field for a type-I superconductor |
| \(H_{c1}\), \(H_{c2}\) | Lower and upper critical fields for a type-II superconductor |
| \(J_c\) | Critical current density under a defined electric-field or resistivity criterion |
| Meissner effect | Expulsion or screening of magnetic flux on entering the superconducting state |
| Cooper pair | Correlated pair of electrons participating in the superconducting condensate |
| Flux vortex | Quantized magnetic-flux structure in the mixed state of a type-II superconductor |

## Core knowledge

### Zero resistance and magnetic screening

Below a transition and within critical field and current limits, a
superconductor can carry persistent current without measurable dc resistance.
Zero resistance alone is not the full thermodynamic definition. A
superconductor also screens an applied magnetic field, producing the Meissner
effect. Magnetic screening distinguishes a superconducting phase from a
hypothetical perfect conductor that merely preserves its prior flux state.

In finite samples, complete field expulsion can be reduced by geometry,
demagnetizing fields, trapped flux, defects, and vortex pinning. Magnetic
measurements therefore require sample and protocol context [1].

### The superconducting transition

\(T_c\) is the temperature at which superconducting order appears under a
specified measurement protocol. Electrical resistance, magnetic
susceptibility, heat capacity, and other probes can produce different
operational transition points when the transition has finite width.

The value is conditional: increasing magnetic field or applied current can
suppress superconductivity, and pressure can stabilize a different structure
or change interactions. A reported \(T_c\) should not be separated from those
conditions.

### Pairing and the energy gap

In Bardeen–Cooper–Schrieffer (BCS) theory, an effective attraction mediated by
lattice vibrations binds electrons near the Fermi surface into Cooper pairs.
The paired condensate has a gap in its low-energy excitation spectrum and
supports phase-coherent current [2].

BCS and its strong-coupling extension describe many conventional
electron–phonon superconductors. “Unconventional” generally denotes
superconductivity whose pairing symmetry or dominant pairing interaction is
not captured by the simplest phonon-mediated isotropic BCS picture. It does
not mean that collective pairing or macroscopic phase coherence is absent.

### Type I and type II

A type-I superconductor expels magnetic flux below a thermodynamic critical
field \(H_c\) and becomes normal above it. A type-II superconductor has two
critical fields. Below \(H_{c1}\) it is in the Meissner state; between
\(H_{c1}\) and \(H_{c2}\), quantized vortices carry magnetic flux through a
mixed state; above \(H_{c2}\), bulk superconductivity is destroyed [3].

The type-I/type-II distinction is governed by the ratio of magnetic
penetration depth to coherence length in Ginzburg–Landau theory. It is not a
classification by \(T_c\).

### Critical current is separate from \(T_c\)

Transport current produces magnetic fields and exerts forces on vortices.
Above a criterion-dependent \(J_c\), dissipation appears even below \(T_c\).
Practical current carrying capacity depends strongly on defects,
microstructure, connectivity, and vortex pinning. A material with higher
\(T_c\) need not have higher \(J_c\) under an operating field [1,3].

## Conditions, limitations, and uncertainty

- Resistance onset, zero resistance, and magnetic onset can yield different
  numerical transition temperatures.
- Field, current, pressure, isotope content, strain, and sample preparation
  can change the observed transition.
- Inhomogeneous or multiphase samples can show broad or multiple transitions.
- A high \(T_c\) does not by itself prove a pairing mechanism.
- The relation between microscopic parameters and \(T_c\) is material-family
  dependent; no single elemental-property rule covers all superconductors.

## Related knowledge resources

- `superconducting_material_families`: major chemical and structural families.
- `superconducting_transition_measurement_and_conditions`: operational measurement criteria.
- `composition_structure_phase_and_processing`: material state information beyond composition.

## References

1. Goldfarb RB, Lelental M, Thompson CA. Alternating-field susceptometry and magnetic susceptibility of superconductors. National Institute of Standards and Technology, NISTIR 3977. 1991. https://doi.org/10.6028/NIST.IR.3977. [Measurement reference]
2. Bardeen J, Cooper LN, Schrieffer JR. Theory of superconductivity. *Physical Review*. 1957;108(5):1175–1204. https://doi.org/10.1103/PhysRev.108.1175. [Primary theory]
3. Fickett FR. Standards for measurement of the critical fields of superconductors. *Journal of Research of the National Bureau of Standards*. 1985;90(2):95–113. https://pmc.ncbi.nlm.nih.gov/articles/PMC6687606/. [Measurement review]
4. Pickett WE. Colloquium: Room temperature superconductivity: the roles of theory and materials design. *Reviews of Modern Physics*. 2023;95:021001. https://doi.org/10.1103/RevModPhys.95.021001. [Review]
