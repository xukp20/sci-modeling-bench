# Aequorea victoria GFP and Engineered Variants

## Summary

The green fluorescent protein from *Aequorea victoria* (avGFP) has been
engineered into variants with altered excitation, maturation, folding,
solubility, oligomerization, and spectral properties. Well-known mutations
such as S65T, F64L, the cycle-3 substitutions, superfolder substitutions, and
A206K or A206V were established in different constructs and assays. Their
reported effects are conditional and should not be treated as independent,
universally beneficial residue rules [1–6].

## Scope

### Covered

- avGFP and selected historically important engineered variants.
- Experimentally established purposes of major mutation sets.
- Conventional one-based GFP residue numbering and evidence limitations.

### Not covered

- Candidate membership or measured values in a benchmark.
- A complete catalog of fluorescent-protein mutations.
- Transfer of a variant's phenotype to every genetic background or assay.

## Core knowledge

### Wild-type avGFP

avGFP was isolated from the jellyfish *Aequorea victoria*. Expression of its
coding sequence in heterologous organisms produces fluorescence without an
additional jellyfish-specific enzyme, establishing that chromophore formation
is encoded by the protein and cellular environment [1]. Wild-type avGFP has
major excitation behavior associated with distinct chromophore protonation
states and matures less conveniently in some heterologous expression
conditions than later engineered forms [2].

### S65T and enhanced GFP

Substitution S65T changes the first chromophore-forming residue. Heim,
Cubitt, and Tsien reported a shifted dominant excitation peak, faster
oxidation, and improved fluorescence characteristics under common
blue-excitation conditions [3].

Enhanced GFP lineages combine S65T with F64L and coding-sequence changes.
F64L was selected for improved folding or maturation at warmer expression
temperatures, while S65T primarily changes chromophore photophysics and
maturation [2,3]. The phenotype belongs to the combined construct and
conditions, not to an isolated universal rule.

### Cycle-3 folding mutations

The cycle-3 GFP variant contains F99S, M153T, and V163A. It was selected by
iterative mutagenesis for improved whole-cell fluorescence and folding-related
behavior. These residues are spatially distributed and demonstrate that
folding performance can be changed outside the chromophore-forming tripeptide
[4].

### Superfolder GFP

Superfolder GFP was selected for fluorescence when fused to proteins that
otherwise interfere with folding. Relative to its folding-reporter parent,
the reported superfolder set includes S30R, Y39N, N105T, Y145F, I171V, and
A206V. It showed faster folding, greater resistance to denaturant, and better
tolerance of circular permutation and difficult fusion partners [5].

Superfolder performance was established in a parent already containing other
engineered substitutions. The listed changes should therefore be interpreted
as a jointly tested lineage, not six context-free effects.

### Weak dimerization and monomerizing substitutions

GFP has a weak tendency to associate through an interface that includes
residue 206. A206K is widely used to disrupt this interface and make GFP
variants more monomeric; A206V is present in superfolder GFP but is not
equivalent to the charged A206K monomerizing substitution [5,6].
Oligomerization effects are especially relevant when local concentration or
fusion geometry is high.

### Spectral variants

Substitutions at chromophore residue Tyr66 produce chemically distinct
chromophores: Y66H is associated with blue fluorescent protein and Y66W with
cyan-shifted fluorescence. Changes around residues such as 203 can alter the
chromophore environment and shift spectra [2]. A detector configured for
green emission can therefore report a low signal from a folded fluorescent
variant whose spectrum has moved.

## Conditions, limitations, and uncertainty

- Residue numbers use conventional one-based avGFP numbering.
- Engineered variants contain backgrounds, codon choices, and mutation
  combinations that differ across publications.
- Improved folding, intrinsic molecular brightness, cellular intensity,
  monomericity, and photostability are different properties.
- A mutation selected in one parent may be neutral or harmful in another
  because of epistasis.
- Historical variant names are not always sufficient to reconstruct an exact
  amino-acid sequence; the source sequence must be checked.

## Related knowledge resources

- `gfp_structure_chromophore_and_maturation`: structural and chemical basis of
  GFP fluorescence.
- `protein_fitness_landscapes_and_epistasis`: dependence of mutational effects
  on genetic background.
- `protein_folding_stability_and_mutational_effects`: distinctions among
  folding, stability, and function.

## References

1. Chalfie M, Tu Y, Euskirchen G, Ward WW, Prasher DC. Green fluorescent protein as a marker for gene expression. *Science*. 1994;263:802–805. https://doi.org/10.1126/science.8303295. [Primary research]
2. Tsien RY. The green fluorescent protein. *Annual Review of Biochemistry*. 1998;67:509–544. https://doi.org/10.1146/annurev.biochem.67.1.509. [Review]
3. Heim R, Cubitt AB, Tsien RY. Improved green fluorescence. *Nature*. 1995;373:663–664. https://doi.org/10.1038/373663b0. [Primary research]
4. Crameri A, Whitehorn EA, Tate E, Stemmer WPC. Improved green fluorescent protein by molecular evolution using DNA shuffling. *Nature Biotechnology*. 1996;14:315–319. https://doi.org/10.1038/nbt0396-315. [Primary research]
5. Pédelacq J-D, Cabantous S, Tran T, Terwilliger TC, Waldo GS. Engineering and characterization of a superfolder green fluorescent protein. *Nature Biotechnology*. 2006;24:79–88. https://doi.org/10.1038/nbt1172. [Primary research]
6. Zacharias DA, Violin JD, Newton AC, Tsien RY. Partitioning of lipid-modified monomeric GFPs into membrane microdomains of live cells. *Science*. 2002;296:913–916. https://doi.org/10.1126/science.1068539. [Primary research]
