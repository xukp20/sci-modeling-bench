# Fluorescence Photophysics and Brightness

## Summary

Fluorescence follows light absorption, excited-state relaxation, and photon
emission. Molecular brightness combines how strongly a fluorophore absorbs
light with the fraction of absorbed photons emitted as fluorescence.
Measured intensity additionally depends on fluorophore abundance, excitation,
optical detection, environment, maturation, and photochemical history, so it
is not an intrinsic molecular constant by itself [1,2].

## Scope

### Covered

- Absorption, excitation, emission, and Stokes shift.
- Extinction coefficient, quantum yield, and molecular brightness.
- pH sensitivity, photobleaching, maturation, and cellular abundance.

### Not covered

- Instrument-specific calibration for a particular experiment.
- A conversion from arbitrary fluorescence units to molecule number.
- The brightness distribution of a benchmark dataset.

## Key concepts and notation

| Symbol or term | Definition | Unit or notes |
| --- | --- | --- |
| \(\lambda_\mathrm{ex}\) | Excitation wavelength | nm |
| \(\lambda_\mathrm{em}\) | Emission wavelength | nm |
| \(\varepsilon\) | Molar extinction coefficient | \(\mathrm{M^{-1}cm^{-1}}\) |
| \(\Phi\) | Fluorescence quantum yield | emitted photons / absorbed photons |
| molecular brightness | Common comparative quantity proportional to \(\varepsilon\Phi\) | Relative unless calibrated |
| photobleaching | Irreversible loss of fluorescence under illumination | Protocol dependent |

## Core knowledge

### Absorption and emission

An absorbed photon promotes a chromophore to an excited electronic state.
Relaxation processes precede radiative emission or nonradiative decay.
Emission usually occurs at a longer wavelength than the principal absorption
because energy is lost before emission; the separation is the Stokes shift
[1].

Excitation and emission are spectra rather than single wavelengths. A
fluorophore measured away from its excitation maximum can appear dim despite
high peak molecular brightness.

### Extinction coefficient

For an ideal dilute sample, Beer–Lambert absorption is

\[
A=\varepsilon c l,
\]

where absorbance \(A\) is dimensionless, \(c\) is molar concentration, and
\(l\) is optical path length. The coefficient \(\varepsilon\) depends on
wavelength and chromophore state [1].

### Quantum yield and molecular brightness

Fluorescence quantum yield is

\[
\Phi=\frac{N_\mathrm{emitted}}{N_\mathrm{absorbed}}.
\]

For comparisons near the relevant excitation maximum, intrinsic molecular
brightness is commonly taken as proportional to

\[
B_\mathrm{mol}\propto\varepsilon\Phi.
\]

This product does not include protein concentration, fraction matured,
instrument response, or excitation mismatch [1,2].

### Cellular fluorescence

Fluorescence from a cell population can depend on transcription, translation,
degradation, folding, chromophore maturation, oligomerization, cell size, and
the fraction of molecules in fluorescent protonation states. It therefore
combines molecular photophysics with biological abundance and state.

### Environmental and temporal effects

Chromophore protonation can make fluorescence pH-dependent. Temperature,
ionic environment, oxygen, and molecular interactions can change maturation
or photophysics. Repeated or intense illumination can cause photobleaching;
some fluorescent proteins also blink, photoswitch, or photoconvert [1,2].

Autofluorescence and detector background impose a low-intensity floor.
Detector saturation and finite dynamic range can compress high signals.

## Conditions, limitations, and uncertainty

- \(\varepsilon\Phi\) is an intrinsic comparison only under compatible
  spectral and chemical conditions.
- Arbitrary fluorescence units are instrument and gain dependent.
- Population medians do not describe every cell or molecule.
- Similar intensity can arise from different combinations of abundance,
  maturation, and per-molecule brightness.

## Related knowledge resources

- `flow_cytometry_and_barcode_linked_fluorescence_measurement`: measurement of
  fluorescence across cells and pooled libraries.
- `gfp_structure_chromophore_and_maturation`: molecular origin of GFP
  fluorescence.

## References

1. Lakowicz JR. *Principles of Fluorescence Spectroscopy*. 3rd ed. Springer; 2006. https://doi.org/10.1007/978-0-387-46312-4. [Textbook]
2. Cranfill PJ, et al. Quantitative assessment of fluorescent proteins. *Nature Methods*. 2016;13:557–562. https://doi.org/10.1038/nmeth.3891. [Primary comparative study]
