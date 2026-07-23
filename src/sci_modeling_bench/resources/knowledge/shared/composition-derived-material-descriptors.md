# Composition-Derived Material Descriptors

## Summary

Composition-derived descriptors convert a list of elements and their
fractions into fixed-length numerical summaries. A common construction applies
statistics such as mean, range, standard deviation, or entropy to tabulated
elemental properties. These descriptors are invariant to the written order of
elements and can represent average scale and elemental diversity, but they
discard crystal structure and can map chemically different compositions to
similar or identical summaries [1,2].

## Scope

### Covered

- Element fractions and elemental-property statistics.
- Weighted and unweighted means, geometric means, range, standard deviation,
  and entropy.
- Information retained and lost by composition-only descriptors.

### Not covered

- The field order of a particular dataset.
- A recommendation to use a particular descriptor or model.
- Crystal-graph, diffraction, electronic-structure, or learned
  representations.

## Notation

Let a composition contain \(m\) distinct elements. For element \(i\):

- \(x_i\geq 0\) is its atomic or amount fraction, with \(\sum_i x_i=1\);
- \(p_i\) is a tabulated elemental property;
- \(m\) counts present elements, not absent positions in a larger periodic
  table.

## Core knowledge

### Element fractions

The vector of elemental fractions is already a composition descriptor. It
retains exact elemental identity in a fixed element basis and is sparse for
compositions containing few elements. It is invariant to multiplying all
formula coefficients by a common factor.

### Unweighted and composition-weighted means

An unweighted mean treats every present element equally:

\[
\bar p=\frac{1}{m}\sum_{i=1}^{m}p_i.
\]

A composition-weighted mean uses elemental fractions:

\[
\bar p_w=\sum_{i=1}^{m}x_i p_i.
\]

These answer different questions. In a composition with one abundant element
and one trace dopant, the unweighted mean gives both elements equal influence,
whereas the weighted mean is dominated by the abundant element.

### Geometric means

For strictly positive \(p_i\), an unweighted geometric mean is

\[
g(p)=\left(\prod_{i=1}^{m}p_i\right)^{1/m},
\]

and a weighted geometric mean is

\[
g_w(p)=\exp\left(\sum_i x_i\ln p_i\right).
\]

Geometric means are undefined in the real logarithmic form when property
values are negative and require an explicit convention when a value is zero.
They emphasize multiplicative rather than additive scale.

### Range and standard deviation

The property range is

\[
\operatorname{range}(p)=\max_i p_i-\min_i p_i.
\]

It records the span among present elements but not which elements define the
endpoints.

An unweighted population standard deviation is

\[
\sigma(p)=
\sqrt{\frac{1}{m}\sum_i(p_i-\bar p)^2},
\]

while a composition-weighted form is

\[
\sigma_w(p)=
\sqrt{\sum_i x_i(p_i-\bar p_w)^2}.
\]

The two forms differ whenever fractions are unequal.

### Composition entropy

The Shannon entropy of elemental fractions is

\[
H(x)=-\sum_{i:x_i>0}x_i\ln x_i.
\]

It is zero for a single-element composition and is maximized by equal fractions
when the number of present elements is fixed. The logarithm base sets the unit.
This composition entropy is a mathematical diversity measure; it is not
automatically a thermodynamic entropy of the material.

Some descriptor systems also apply entropy-like formulas to normalized
elemental-property contributions. Their exact definition must be checked
rather than inferred from the word “entropy.”

### Element count and property families

The number of distinct elements is a basic stoichiometric descriptor.
Elemental-property statistics can then be calculated for atomic mass,
ionization energy, radius, electron affinity, valence, and reference-phase
bulk properties. Ward and colleagues demonstrated a general composition-based
representation that combines such statistics across many elemental
attributes [1]. Matminer implements related composition featurizers while
separating composition, oxidation-state, and structure-dependent feature
families [2].

### What composition statistics lose

Aggregating \(p_i\) to a few statistics is many-to-one. It can lose:

- the identity of the elements contributing each value;
- correlations between particular element pairs;
- oxidation states and site assignments;
- stoichiometric ordering and local coordination;
- crystal symmetry, phase, and defects;
- pressure, temperature, and processing history.

Consequently, similar descriptor vectors do not establish similar structure
or mechanism. A descriptor can correlate with a target without being a causal
physical law.

## Conditions, limitations, and uncertainty

- Weighted statistics require a declared fraction convention.
- Elemental-property sources must specify units, reference states, and missing
  value handling.
- Geometric means require positive inputs or an explicit transformation.
- Entropy-like fields may use different normalizations and logarithm bases.
- Composition descriptors cannot distinguish polymorphs with the same formula.
- A model validated on known compositions can still be unreliable for new
  chemical families.

## Related knowledge resources

- `chemical_composition_stoichiometry_and_formulas`: definition of elemental fractions.
- `elemental_properties_and_periodic_trends`: meanings of the properties being summarized.
- `composition_structure_phase_and_processing`: material information absent from composition-only statistics.

## References

1. Ward L, Agrawal A, Choudhary A, Wolverton C. A general-purpose machine learning framework for predicting properties of inorganic materials. *npj Computational Materials*. 2016;2:16028. https://doi.org/10.1038/npjcompumats.2016.28. [Primary methods research]
2. Ward L, Dunn A, Faghaninia A, et al. Matminer: An open source toolkit for materials data mining. *Computational Materials Science*. 2018;152:60–69. https://doi.org/10.1016/j.commatsci.2018.05.018. [Primary software paper]
3. Hamidieh K. A data-driven statistical model for predicting the critical temperature of a superconductor. *Computational Materials Science*. 2018;154:346–354. https://doi.org/10.1016/j.commatsci.2018.07.052. [Primary methods research]
