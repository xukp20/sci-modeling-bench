# RNA Sequence, Structure, and Base Pairing

## Summary

RNA is a directional polymer whose sequence and intramolecular interactions
jointly determine an ensemble of structures. Watson–Crick A–U and G–C pairs,
G–U wobble pairs, stacking, ions, temperature, and molecular context all
contribute to folding. A single minimum-free-energy structure is a model of
one favorable state, not a complete description of the conformations present
in solution or in a cell.

## Scope

### Covered

- RNA nucleotide identity, 5′-to-3′ polarity, and DNA-alphabet notation.
- Canonical and wobble base pairing.
- Secondary-structure elements, folding free energy, and structural ensembles.
- Dependence of RNA structure on sequence and environment.

### Not covered

- A particular transcript, reporter construct, or sequence library.
- A particular folding program or feature-engineering method.
- Translation-specific regulatory mechanisms, which are covered separately.

## Key concepts and notation

| Term or symbol | Definition | Notes |
| --- | --- | --- |
| 5′ and 3′ | Ends defined by ribose-carbon numbering | RNA sequences are conventionally written 5′ to 3′ |
| A, C, G, U | RNA bases adenine, cytosine, guanine, and uracil | DNA uses T in place of U |
| Base pair | Hydrogen-bonded interaction between bases | A–U and G–C are canonical RNA pairs |
| G–U wobble | Common non-Watson–Crick RNA pair | Its geometry and stability differ from canonical pairs |
| Secondary structure | Pattern of base pairs and unpaired regions | Includes stems, hairpins, bulges, and internal loops |
| \(\Delta G\) | Gibbs free-energy change | Depends on temperature, ions, and the thermodynamic model |

## Core knowledge

### Chemical identity and direction

RNA nucleotides contain ribose, phosphate, and one of A, C, G, or U. Adjacent
nucleotides are connected by phosphodiester bonds, giving the polymer distinct
5′ and 3′ ends. Sequence direction is therefore chemically meaningful [1].

DNA-alphabet representations commonly replace RNA U with T. This substitution
changes notation rather than the base order: a 5′-to-3′ DNA string can denote
the corresponding RNA transcript by replacing every T with U.

### Pairing and structural elements

Complementary segments within one RNA molecule can pair. A–U and G–C are the
principal Watson–Crick pairs, while G–U is a frequent wobble interaction.
Paired runs form helices or stems; unpaired regions form hairpin loops,
internal loops, bulges, and multibranch junctions. Higher-order contacts can
produce tertiary structure [1,2].

Base pairing alone does not determine stability. Base stacking, loop
geometry, strand entropy, electrostatics, counterions, temperature, and
solvent conditions also contribute [2,3].

### Folding is an ensemble

At equilibrium, an RNA can populate multiple structures \(s\). Their relative
probabilities are related to free energy:

\[
P(s)=\frac{\exp[-\Delta G(s)/(RT)]}
{\sum_{s'}\exp[-\Delta G(s')/(RT)]}.
\]

Here \(R\) is the gas constant and \(T\) is absolute temperature. A
minimum-free-energy structure is the structure with the lowest predicted
\(\Delta G\) under a specified model. Alternative structures may nevertheless
have appreciable probability, especially when their energies are close [3].

### Cellular RNA is actively remodeled

In cells, RNA-binding proteins, helicases, ribosomes, chemical modifications,
transcription kinetics, and molecular crowding can shift the structural
ensemble. Structure measured or predicted for an isolated RNA in vitro may
therefore differ from structure in a translating messenger ribonucleoprotein
complex [2,4].

## Conditions, limitations, and uncertainty

- Thermodynamic parameters are empirical and are most reliable within the
  sequence, salt, and temperature regimes used to estimate them.
- A more negative predicted folding free energy does not by itself identify
  where a structure forms or prove that it persists in a cell.
- Long-range and pseudoknotted interactions are not represented equally by
  all secondary-structure models.
- Sequence composition affects both possible pairing and other biochemical
  properties; an observed composition effect need not be caused only by
  folding.
- DNA notation should not be confused with the chemical composition of the
  transcribed RNA.

## Related knowledge resources

- `eukaryotic_mrna_and_translation_initiation`: how ribosomes engage mRNA.
- `five_prime_utr_regulatory_elements`: regulatory consequences of 5′-leader sequence and structure.

## References

1. Alberts B, et al. *Molecular Biology of the Cell*, 4th ed. “The RNA World and the Origins of Life.” NCBI Bookshelf. https://www.ncbi.nlm.nih.gov/books/NBK26876/ [Textbook]
2. Mustoe AM, Busan S, Rice GM, Hajdin CE, Peterson BK, Ruda VM, Kubica N, Nutiu R, Baryza JL, Weeks KM. Pervasive Regulatory Functions of mRNA Structure Revealed by High-Resolution SHAPE Probing. *Cell*. 2018;173:181–195.e18. https://doi.org/10.1016/j.cell.2018.02.034
3. Turner DH, Mathews DH. NNDB: the nearest neighbor parameter database for predicting stability of nucleic acid secondary structure. *Nucleic Acids Research*. 2010;38:D280–D282. https://doi.org/10.1093/nar/gkp892
4. Bevilacqua PC, Ritchey LE, Su Z, Assmann SM. Genome-Wide Analysis of RNA Secondary Structure. *Annual Review of Genetics*. 2016;50:235–266. https://doi.org/10.1146/annurev-genet-120215-035034
