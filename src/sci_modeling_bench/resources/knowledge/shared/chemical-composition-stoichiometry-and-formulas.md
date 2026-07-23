# Chemical Composition, Stoichiometry, and Formulas

## Summary

A chemical formula identifies the elements in a substance and gives their
relative stoichiometric amounts. Multiplying every stoichiometric coefficient
by the same positive number leaves the relative elemental composition
unchanged. A normalized elemental-composition vector records these relative
amounts as fractions that sum to one, but it does not by itself specify crystal
structure, oxidation states, phase, defects, or synthesis history.

## Scope

### Covered

- Element symbols, formula subscripts, and stoichiometric ratios.
- Amount fractions, atomic fractions, and mass fractions.
- Normalized elemental-composition vectors.
- Nonstoichiometry, substitution, and charge-balance limitations.

### Not covered

- The encoding used by a particular dataset.
- A procedure for selecting or ranking materials.
- Crystal-structure representations.
- Reaction balancing or synthesis planning.

## Key concepts and notation

| Term or symbol | Meaning |
| --- | --- |
| \(n_i\) | Stoichiometric amount assigned to element \(i\) |
| \(x_i\) | Normalized atomic or amount fraction of element \(i\) |
| \(w_i\) | Mass fraction of element \(i\) |
| Formula unit | Smallest formula-proportional description normally used for a nonmolecular solid |
| Empirical formula | Simplest whole-number ratio of elements when such a reduction is meaningful |
| Nonstoichiometry | Composition that varies over a range rather than one exact integer ratio |
| Substitutional doping | Partial replacement of one element by another on a material site |

## Core knowledge

### Formula subscripts express relative amounts

In a formula such as \(\mathrm{MgB_2}\), the omitted subscript on Mg is one and
the subscript on B is two. The formula therefore represents an Mg:B
stoichiometric ratio of 1:2. Parentheses multiply all enclosed subscripts, and
symbols such as \(x\), \(1-x\), or \(\delta\) are often used to represent
variable substitution or nonstoichiometry.

Stoichiometric coefficients are relative. The triples \((1,2,4)\) and
\((0.5,1,2)\) describe the same normalized elemental ratio. Formula reduction
removes a common factor but does not change composition.

### Atomic or amount fractions

For elemental stoichiometric amounts \(n_i\geq 0\), a normalized composition is

\[
x_i=\frac{n_i}{\sum_j n_j},
\qquad
\sum_i x_i=1.
\]

These are number- or amount-based fractions: they represent the fraction of
the total elemental stoichiometric count assigned to each element. IUPAC
defines a fraction generally as a ratio whose numerator describes one
constituent and whose denominator is the corresponding total [1].

The normalization is invariant to an overall formula multiplier. It preserves
element identities and relative amounts but discards the absolute scale of the
written formula unit.

### Mass fractions are different

If \(M_i\) is an appropriate atomic molar mass, the mass fraction is

\[
w_i=\frac{n_iM_i}{\sum_j n_jM_j}.
\]

Except for special cases, \(w_i\neq x_i\). Heavy elements contribute more to a
mass fraction than to an atomic fraction at the same atom count. A composition
representation must therefore state which fraction convention it uses.

### Formulas need not specify a unique material

A chemical formula can omit information needed to identify a physical solid:

- atomic arrangement and space group;
- polymorph or crystallographic phase;
- site occupancy and ordering;
- vacancies, interstitials, and extended defects;
- isotopic composition;
- grain size, texture, and microstructure;
- temperature, pressure, and preparation history.

Different materials can share the same nominal formula, and one material can
occupy a nonstoichiometric composition range. Formula equality is therefore
not sufficient evidence of identical structure or properties.

### Variable composition and doping

Expressions such as

\[
\mathrm{A_{1-x}B_xC}
\]

describe a substitution series in which \(x\) is a composition variable.
They do not state whether every value of \(x\) forms a stable single phase.
Phase stability, solubility limits, and site preference require additional
chemical or structural information.

Oxidation state is a formal electron-counting construct, not an element-only
constant. A neutral bulk formula constrains the sum of formal charges, but a
list of elements and fractions may admit several oxidation-state assignments
or none under a chosen ionic model [2]. Charge neutrality and chemical
plausibility cannot generally be established from nonnegative fractions alone.

## Conditions, limitations, and uncertainty

- “Atomic fraction,” “amount fraction,” and “mole fraction” are closely
  related for specified elemental entities, but mass fraction is different.
- Reduced formulas hide overall scale and can hide how a composition was
  experimentally reported.
- Decimal coefficients may represent an average over disorder or a nominal
  synthesis composition rather than exact occupancy in every unit cell.
- Elemental fractions do not encode bonding, oxidation state, coordination, or
  crystal symmetry.
- A formally valid composition is not necessarily stable, synthesizable, or a
  single phase.

## Related knowledge resources

- `elemental_properties_and_periodic_trends`: meanings and conventions of elemental properties.
- `composition_derived_material_descriptors`: statistics constructed from elemental fractions and properties.
- `composition_structure_phase_and_processing`: why composition does not uniquely identify material state.

## References

1. International Union of Pure and Applied Chemistry. Fraction. *Compendium of Chemical Terminology*, 5th ed., online version 5.0.0. 2025. https://doi.org/10.1351/goldbook.F02494. Accessed 2026-07-23. [Official definition]
2. Karen P, McArdle P, Takats J. Toward a comprehensive definition of oxidation state. *Pure and Applied Chemistry*. 2014;86(6):1017–1081. https://doi.org/10.1515/pac-2013-0505. [IUPAC recommendation]
