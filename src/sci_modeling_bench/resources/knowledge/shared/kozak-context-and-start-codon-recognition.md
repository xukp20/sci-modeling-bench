# Kozak Context and Start-Codon Recognition

## Summary

In vertebrate mRNAs, nucleotides surrounding an AUG influence how efficiently
a scanning pre-initiation complex recognizes it. Positions are numbered
relative to the A of AUG as +1; a purine at −3 and G at +4 are especially
important in the classical vertebrate Kozak context. This is a probabilistic,
context-dependent recognition principle, not a universal binary rule or a
complete predictor of translation.

## Scope

### Covered

- Start-site coordinate convention and vertebrate AUG context.
- Contributions of the −3 and +4 positions.
- Leaky scanning, near-cognate initiation, and context dependence.
- Limits of transferring a consensus among species and molecular contexts.

### Not covered

- Any dataset-specific strong/weak classification.
- A particular reporter's fixed or variable nucleotides.
- A scoring function or candidate-selection rule.

## Key concepts and notation

| Term or symbol | Definition |
| --- | --- |
| +1 | A nucleotide of an AUG start codon |
| −3 | Third nucleotide upstream of +1 |
| +4 | First nucleotide after AUG |
| R | Purine, A or G |
| Kozak consensus | Sequence preference around a eukaryotic start site |
| Leaky scanning | Bypass of a potential start site by some scanning complexes |
| Near-cognate start | Non-AUG codon differing from AUG by one nucleotide |

## Core knowledge

### Coordinate convention

For a start codon written 5′ to 3′, the A, U, and G of AUG occupy +1, +2, and
+3. Upstream nucleotides have negative coordinates and there is no position
zero. The +4 nucleotide is the first base after the AUG triplet [1,2].

### Vertebrate sequence preferences

Classical experiments and vertebrate sequence comparisons identified
\(5'\)-GCCRCCAUGG as a compact representation of a favorable start context,
where R denotes A or G. Broader versions include additional upstream bases,
but the purine at −3 and G at +4 are the most influential individual
positions in many mammalian systems [1–3].

Consensus means enrichment among effectively used sites, not that every
matching sequence initiates equally or every mismatch fails. Positions can
interact: the consequence of a +4 substitution can depend on the −3 base and
other nearby nucleotides [1,2].

### Recognition and leaky scanning

A favorable context helps the pre-initiation complex transition from scanning
to a start-recognition state. In a weak context, a fraction of complexes can
bypass an AUG and continue to a downstream site. This leaky-scanning
probability depends on the complete local context, RNA structure, initiation
factors, and experimental system [2,3].

Near-cognate codons such as CUG, GUG, and UUG can initiate translation in
some eukaryotic contexts, usually less efficiently than AUG. Their use is
particularly dependent on neighboring sequence and cellular conditions [3].

### Context extends beyond a short motif

RNA structure downstream of a weak start can pause a scanning complex and
sometimes increase recognition, whereas obstructive structure elsewhere can
reduce recruitment or scanning. Upstream starts, start-to-cap distance, and
initiation-factor activity also affect selection [2,3].

## Conditions, limitations, and uncertainty

- The canonical Kozak consensus was established mainly in vertebrate systems;
  preferred contexts differ in yeast, plants, and other taxa.
- A consensus is not a thermodynamic binding constant and does not specify a
  fixed fold change in protein production.
- Short categorical labels discard gradations and interactions among
  nucleotides.
- Start recognition is only one contributor to ribosome occupancy and protein
  output.
- A sequence match does not prove that a codon is used in a particular cell.

## Related knowledge resources

- `eukaryotic_mrna_and_translation_initiation`: scanning and ribosome assembly.
- `upstream_start_codons_and_upstream_open_reading_frames`: consequences of upstream initiation.

## References

1. Kozak M. An analysis of 5′-noncoding sequences from 699 vertebrate messenger RNAs. *Nucleic Acids Research*. 1987;15:8125–8148. https://doi.org/10.1093/nar/15.20.8125
2. Hinnebusch AG. Molecular mechanism of scanning and start codon selection in eukaryotes. *Microbiology and Molecular Biology Reviews*. 2011;75:434–467. https://doi.org/10.1128/MMBR.00008-11
3. Kearse MG, Wilusz JE. Non-AUG translation: a new start for protein synthesis in eukaryotes. *Genes & Development*. 2017;31:1717–1731. https://doi.org/10.1101/gad.305250.117
