# SMILES, Molecular Graphs, and Chemical Identity

## Summary

The Simplified Molecular Input Line Entry System (SMILES) represents a
molecular graph as text. Atoms form graph vertices and bonds form graph edges;
branches, rings, aromatic atoms, formal charges, isotopes, and stereochemistry
are encoded with additional syntax. A SMILES string describes a molecular
structure, but chemical identity can also depend on protonation, tautomerism,
salt form, stereochemistry, and whether disconnected components are retained.

## Scope

This resource covers the chemical meaning and principal syntax of SMILES,
including common identity and standardization issues. It does not prescribe
molecular descriptors, fingerprints, predictive models, or a treatment of any
particular collection of compounds.

## Core knowledge

### Molecular graphs and traversal

A SMILES string is produced by traversing a molecular graph. Ordinary atoms
such as `C`, `N`, `O`, `S`, `P`, `F`, `Cl`, and `Br` may be written directly.
Adjacent atom symbols are connected by a bond. A single bond is usually
implicit; `=`, `#`, and `:` denote double, triple, and aromatic bonds.

Parentheses introduce branches from the preceding atom. Matching ring labels,
such as the two `1` characters in `C1CCCCC1`, connect atoms that are separated
in the text but adjacent in the molecular graph. Ring labels describe graph
closure, not a ring's size by themselves.

Lowercase symbols such as `c` and `n` represent aromatic atoms under the SMILES
aromaticity model. Aromatic notation is distinct from an alternating explicit
single/double-bond representation, although the two may describe the same
chemical connectivity after aromaticity perception.

### Bracket atoms, charge, isotopes, and hydrogens

Square brackets allow properties that cannot be expressed by a bare atom
symbol. They can specify an isotope, element, stereochemical class, hydrogen
count, and formal charge. For example, `[NH4+]` is a positively charged
nitrogen with four attached hydrogens, and `[13CH3]` specifies carbon-13.
Hydrogens are otherwise commonly implicit and inferred from valence rules.

Formal charge in SMILES is a property of the represented structure. It should
not be confused with an experimentally measured net charge under every pH
condition, because protonation state can change with chemical environment.

### Stereochemistry

The `@` and `@@` symbols encode local tetrahedral stereochemistry relative to
the order in which neighboring atoms occur in the SMILES traversal. Slash and
backslash bond symbols can specify relative geometry around double bonds.
Stereochemical meaning therefore depends on both the symbols and the local
ordering; `@` alone is not an absolute declaration of an R or S descriptor.

If stereochemistry is omitted, a SMILES representation generally does not
distinguish the corresponding stereoisomers. This can be chemically important
because stereoisomers can have different biological interactions.

### Disconnected components

A period separates disconnected components, as in a salt, solvate, or mixture.
The components remain part of the represented record even though no covalent
bond connects them. Removing counterions or retaining only the largest
component changes the represented chemical entity and is a standardization
decision rather than a property of SMILES syntax.

### Equivalent strings and canonicalization

Many graph traversals can encode the same molecular graph, so a molecule can
have multiple valid SMILES strings. Canonical SMILES algorithms choose a
deterministic traversal within a particular software implementation. Canonical
SMILES are useful for comparison, but canonicalization algorithms are not
fully universal across toolkits and versions.

Graph equivalence also depends on which features are compared. Connectivity,
isotopes, formal charge, and stereochemistry can each be included or omitted.
Tautomers and different protonation states normally have different molecular
graphs even when they are treated as forms of the same parent compound in a
particular scientific context.

### Identifiers and chemical identity

A registry identifier, systematic name, and structure representation describe
different aspects of identity. A registry record may refer to a particular
salt, stereoisomer, isotope, or mixture. Conversely, the same parent compound
may appear under identifiers for several forms. Structure-based identity
comparisons should therefore state how salts, solvents, protonation,
tautomerism, and stereochemistry are handled.

## Conditions, limitations, and uncertainty

SMILES records connectivity rather than a three-dimensional conformation or an
ensemble of solution conformations. Aromaticity and canonicalization involve
software conventions. A syntactically valid string is not evidence that the
structure is chemically stable, is the dominant species at a given pH, or
matches the intended experimental material. Missing stereochemical symbols can
mean unspecified, unknown, or deliberately pooled stereochemistry; those
possibilities cannot be distinguished from the string alone.

## References

1. Weininger D. SMILES, a chemical language and information system. 1.
   Introduction to methodology and encoding rules. *Journal of Chemical
   Information and Computer Sciences*. 1988;28(1):31–36.
   https://doi.org/10.1021/ci00057a005
2. Daylight Chemical Information Systems. SMILES — A Simplified Chemical
   Language. Accessed 2026-07-23.
   https://www.daylight.com/dayhtml/doc/theory/theory.smiles.html
3. Heller SR, McNaught A, Pletnev I, Stein S, Tchekhovskoi D. InChI, the IUPAC
   International Chemical Identifier. *Journal of Cheminformatics*.
   2015;7:23. https://doi.org/10.1186/s13321-015-0068-4
