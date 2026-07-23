# Pho4 and DNA Recognition

## Summary

Pho4 is a sequence-specific basic helix–loop–helix transcriptional activator
from *Saccharomyces cerevisiae*. It binds DNA as a homodimer and recognizes
the CACGTG E-box core. Structural and biochemical studies show that Pho4
recognition can also include bases adjacent to that core. In living yeast,
Pho4 activity is controlled by phosphate-responsive phosphorylation and
nuclear localization, while chromatin accessibility, competition with Cbf1,
and cooperation with Pho2 help determine which potential sites are occupied
and which binding events activate transcription [1–6].

## Scope

### Covered

- Pho4 identity, protein family, and role in the yeast phosphate response.
- The CACGTG core, homodimeric recognition, and structural evidence for
  flanking-base contacts.
- Experimentally established distinctions between intrinsic DNA affinity,
  cellular occupancy, and transcriptional activation.

### Not covered

- Measurements or statistics from a benchmark dataset.
- A ranked list or purported optimum of Pho4-binding sequences.
- A recipe for constructing candidates or fitting a predictive model.
- A complete account of the PHO signaling network.

## Key entities and terms

| Entity or term | Meaning |
| --- | --- |
| Pho4 | Budding-yeast phosphate-responsive transcriptional activator |
| PHO4 / YFR034C | Standard gene name and systematic locus name |
| P07270 | Reviewed UniProtKB entry for *S. cerevisiae* Pho4 |
| bHLH | Basic helix–loop–helix DNA-binding and dimerization domain |
| CACGTG | Palindromic E-box core recognized by Pho4 |
| Pho2 | Homeodomain transcription factor that cooperates with Pho4 at many regulated genes |
| Cbf1 | Another yeast bHLH factor that can recognize CACGTG sites |
| PDB 1A0A | X-ray structure of a Pho4 bHLH-domain homodimer bound to DNA |

## Core knowledge

### Protein identity and physiological role

PHO4 encodes a 312-amino-acid, sequence-specific DNA-binding transcriptional
activator in budding yeast. It regulates genes involved in the response to
phosphate limitation. The reviewed UniProtKB entry identifies Pho4 as a
transcriptional activator of phosphate-responsive genes and records inhibition
by the Pho80–Pho85 cyclin-dependent kinase system under high-phosphate
conditions [1,2].

Phosphate availability regulates Pho4 phosphorylation and localization. Under
phosphate-rich conditions, phosphorylation favors its exclusion from the
nucleus. Under phosphate limitation, dephosphorylated Pho4 accumulates in the
nucleus and can bind regulatory DNA [2,5]. These signaling facts concern
cellular availability of the factor and are distinct from its intrinsic
affinity for an isolated DNA sequence.

### Core E-box recognition

Pho4 is a bHLH protein that binds the E-box core

\[
5^\prime\text{-CACGTG-}3^\prime.
\]

This core is its own reverse complement. Pho4 forms a homodimer, with the two
basic regions contacting DNA in the major groove [3,4]. A core consensus
identifies a central recognition element; it does not imply equal affinity for
all longer DNA sites containing that element.

### Structural evidence for flanking-base recognition

The Pho4 bHLH-domain–DNA complex deposited as PDB 1A0A was determined by
X-ray diffraction at 2.8 Å resolution. In that crystallized complex, the Pho4
homodimer directly reads both the CACGTG core and bases on its 3-prime side.
The authors report contacts to two 3-prime flanking guanines involving Pho4
Arg2 and His5 [3,4].

This is direct structural evidence that the physical recognition surface can
extend outside the conventional six-base core. It is not evidence that one
pair of flanking guanines is universally optimal: 1A0A contains a particular
protein fragment, DNA construct, crystal environment, and strand
representation.

### Broader flanking-sequence effects

High-throughput BET-seq measurements of Pho4 and Cbf1 examined sequence
variation surrounding their shared CACGTG core. For Pho4, changing flanking
bases produced a broad range of relative binding energies, demonstrating that
the identity and combination of bases outside the core can materially affect
intrinsic in vitro binding [6].

Flanking effects can arise from direct protein–base contacts, contacts to the
DNA backbone, and sequence-dependent DNA shape. Contributions need not be
independent at every position: a base substitution can alter the effect of a
second base by changing local contacts or duplex structure [3,6].

### Affinity, occupancy, and regulation are different

Pho4 and Cbf1 can recognize the same CACGTG core, but their cellular roles and
extended sequence preferences are not identical [5,6]. In vivo studies show
that nucleosomes restrict access to many potential Pho4 sites and that Cbf1
can compete for accessible sites. Binding by Pho4 is also not sufficient for
transcriptional activation; cooperation with Pho2 contributes to activation
at many phosphate-responsive genes [5].

Consequently, three statements are distinct:

1. a DNA sequence has intrinsic affinity for Pho4 in vitro;
2. Pho4 occupies that sequence in a living cell under a stated condition; and
3. occupancy produces a transcriptional response.

## Conditions, limitations, and uncertainty

- Structural contacts in PDB 1A0A are strong evidence for one bound complex,
  but do not enumerate all tolerated or high-affinity flanking sequences.
- Quantitative affinities depend on the protein construct, DNA length and
  orientation, buffer, temperature, ionic strength, and assay.
- Pho4 phosphorylation and localization alter cellular availability rather
  than changing the definition of an isolated in vitro sequence measurement.
- Chromatin, Cbf1, Pho2, and promoter organization affect in vivo behavior but
  are absent from assays of purified Pho4 and DNA.
- A motif logo or consensus does not encode all dependencies among core and
  flanking positions.

## Related knowledge resources

- `basic_helix_loop_helix_and_ebox_recognition`: bHLH architecture and E-box conventions.
- `binding_energy_topography_by_sequencing`: BET-seq assay and count-derived energy measurements.
- `binding_affinity_and_thermodynamics`: affinity constants and free-energy notation.
- `binding_sites_motifs_and_sequence_context`: motifs, strand orientation, and contextual bases.

## References

1. Saccharomyces Genome Database. PHO4 / YFR034C locus page. https://www.yeastgenome.org/locus/S000001930. Accessed 2026-07-23. [Curated organism database]
2. UniProt Consortium. UniProtKB P07270 (PHO4_YEAST), reviewed entry. https://www.uniprot.org/uniprotkb/P07270/entry. Accessed 2026-07-23. [Curated protein database]
3. Shimizu T, Toumoto A, Ihara K, Shimizu M, Kyogoku Y, Ogawa N, Oshima Y, Hakoshima T. Crystal structure of PHO4 bHLH domain-DNA complex: flanking base recognition. *The EMBO Journal*. 1997;16(15):4689–4697. https://doi.org/10.1093/emboj/16.15.4689. [Primary research]
4. RCSB Protein Data Bank. PDB 1A0A: phosphate system positive regulatory protein Pho4/DNA complex. https://doi.org/10.2210/pdb1A0A/pdb. Accessed 2026-07-23. [Structural database]
5. Zhou X, O’Shea EK. Integrated approaches reveal determinants of genome-wide binding and function of the transcription factor Pho4. *Molecular Cell*. 2011;42(6):826–836. https://doi.org/10.1016/j.molcel.2011.05.025. [Primary research]
6. Le DD, Shimko TC, Aditham AK, Keys AM, Longwell SA, Orenstein Y, Fordyce PM. Comprehensive, high-resolution binding energy landscapes reveal context dependencies of transcription factor binding. *Proceedings of the National Academy of Sciences of the United States of America*. 2018;115(16):E3702–E3711. https://doi.org/10.1073/pnas.1715888115. [Primary research]
