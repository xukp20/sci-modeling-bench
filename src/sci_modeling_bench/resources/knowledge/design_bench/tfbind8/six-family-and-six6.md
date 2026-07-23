# The SIX Family and SIX6

## Summary

SIX6 is a vertebrate member of the SIX/sine oculis homeobox transcription
factor family and belongs to the SIX3/SIX6 subgroup. SIX proteins contain a
conserved SIX domain involved in protein interactions and a homeodomain
associated with DNA recognition. Experiments using defined SIX6 constructs
have reported binding to several homeodomain-related DNA elements, including
ATTA-containing sites and Trex/MEF3-class elements, while also showing that
sequences adjacent to the canonical homeodomain can be important for binding.
These observations establish finite, condition-dependent recognition
properties rather than an exhaustive sequence preference landscape.

## Scope

### Covered

- SIX-family classification and conserved protein architecture.
- Human SIX6 identity and broad developmental role.
- Published biochemical evidence about SIX6 DNA recognition and construct dependence.
- Cofactor and family-member considerations relevant to interpreting SIX proteins.

### Not covered

- Any particular high-throughput measurement collection or exhaustive ranked sequence table.
- A claim that an experimentally tested site is globally optimal.
- A complete motif or exhaustive specificity model for SIX6.

## Key concepts and notation

| Term | Definition | Notes |
| --- | --- | --- |
| SIX family | Metazoan homeobox transcription-factor family descended from *sine oculis* | Vertebrates have SIX1–SIX6 |
| SIX domain | Conserved domain N-terminal to the homeodomain | Participates in protein–protein interactions and can affect function |
| Homeodomain | Approximately 60-residue helix-turn-helix DNA-binding fold | SIX homeodomains are divergent from canonical homeodomains |
| SIX3/SIX6 subgroup | One of three vertebrate SIX paralog groups | Also called the Optix-related subgroup |
| Trex/MEF3 element | A class of DNA elements recognized by several SIX-family proteins | Evidence differs across family members and constructs |

## Core knowledge

### Family organization and protein architecture

Vertebrates have six SIX paralogs commonly grouped as SIX1/SIX2,
SIX3/SIX6, and SIX4/SIX5 on the basis of sequence and evolutionary
relationships [1,2]. SIX proteins contain a conserved SIX domain followed by a
homeodomain. The SIX domain participates in protein interactions; members of
the broader retinal-determination network interact with cofactors such as EYA
and DACH proteins. Family membership does not imply identical DNA specificity
or identical cofactor effects [1,3].

The reviewed human UniProt entry O95475 describes SIX6 as a 246-amino-acid
homeobox protein with evidence at protein level and sequence-specific
double-stranded-DNA-binding annotations [4]. Human SIX6 is associated with eye
development, and genetic experiments in vertebrates support roles in retinal
and pituitary progenitor biology [5].

### Homeodomain-related sequence recognition

Homeodomains commonly insert a recognition helix into the DNA major groove,
while an N-terminal arm can contact the minor groove. SIX-family
homeodomains are structurally divergent and cannot be assumed to follow one
universal homeodomain recognition rule [3,6].

Biochemical analysis by Hu and colleagues compared defined Six2 and Six6
protein fragments against two selected DNA classes: a Trex/MEF3 consensus
element and a sequence containing the ATTA core commonly associated with
homeodomain recognition [3]. The isolated SIX homeodomain lacked a canonical
basic N-terminal arm and did not by itself show the tested binding behavior.
For Six6, adding 14 residues immediately C-terminal to the homeodomain yielded
a construct that bound both tested DNA elements with nanomolar affinity. The
analogous Six2 construct did not behave identically despite conservation of
predicted DNA-contacting residues [3].

This result shows that residues outside the conventional homeodomain boundary
can materially affect SIX6 DNA binding and that specificity cannot be inferred
from the canonical contact residues alone. It does not establish that the two
tested sequence classes are the only, or strongest possible, SIX6 ligands.

### Evidence for ATTA-containing elements

Full-length or tagged Six6 has been tested on ATTA-containing regulatory
elements in cell extracts and reporter systems. In studies of gonadotropin-
releasing hormone regulation, Six6-containing complexes bound selected ATTA
sites by electrophoretic mobility-shift assay, and mutation of those elements
altered reporter responses [7]. ATTA is also recognized by many other
homeodomain proteins, so its presence is not unique evidence for SIX6.
Flanking bases, protein construct, and cellular cofactors remain relevant.

### Evidence for Trex/MEF3-class recognition

MEF3 elements were originally characterized in muscle regulatory regions and
are recognized by several SIX-family proteins. A commonly reported MEF3 core
is `TCAGGTT`, while related Trex elements tolerate substitutions at several
positions [8]. Evidence from one SIX member or tissue context cannot be
transferred quantitatively to SIX6 without direct measurement. The Six6
construct experiment described above supports binding to a selected
Trex/MEF3-class element, but it was not an exhaustive survey of all flanking
variants [3].

### Cofactors and paralog-specific behavior

SIX proteins participate in networks with EYA and DACH proteins. Cofactors may
alter transcriptional activity, localization, or DNA-binding behavior. In the
Hu et al. comparison, Eya increased Six2 DNA-binding affinity substantially
under the tested conditions but did not produce the same enhancement for
Six6 [3]. This is direct evidence that cofactor effects can be
paralog-specific rather than a universal property of the family.

## Conditions, limitations, and uncertainty

- Human SIX6, mouse Six6, and other vertebrate orthologs are related but not
  interchangeable without checking sequence and experimental context.
- Isolated domains, extended domains, and full-length proteins can exhibit
  different binding properties.
- ATTA and MEF3/Trex observations come from selected oligonucleotides,
  promoters, constructs, and assays; they do not define an exhaustive
  specificity landscape.
- A family-level motif cannot substitute for a measurement of one paralog.
- DNA binding in vitro does not alone determine the direction or magnitude of
  transcriptional regulation in a cell.
- Public motif collections may incorporate data from different assays or from
  experiments closely related to another measurement collection; their provenance must
  be checked before treating them as independent evidence.

## Related knowledge resources

- `transcription_factor_dna_binding`: base readout, shape readout, and construct dependence.
- `binding_sites_motifs_and_sequence_context`: limits of consensus sequences and motifs.
- `binding_affinity_and_thermodynamics`: interpretation of nanomolar affinity and \(K_d\).

## References

1. Kumar JP. The molecular circuitry governing retinal determination. *Biochimica et Biophysica Acta*. 2009;1789:306–314. https://doi.org/10.1016/j.bbagrm.2008.10.001. [Review]
2. Seo HC, Curtiss J, Mlodzik M, Fjose A. Six class homeobox genes in drosophila belong to three distinct families and are involved in head development. *Mechanisms of Development*. 1999;83:127–139. https://doi.org/10.1016/S0925-4773(99)00045-3. [Primary research]
3. Hu S, Mamedova A, Hegde RS. DNA-binding and regulation mechanisms of the SIX family of retinal determination proteins. *Biochemistry*. 2008;47:3586–3594. https://doi.org/10.1021/bi702186s. [Primary research]
4. UniProt Consortium. SIX6_HUMAN, UniProtKB O95475, reviewed entry. https://www.uniprot.org/uniprotkb/O95475/entry. Accessed 2026-07-23. [Curated database]
5. Li X, Perissi V, Liu F, Rose DW, Rosenfeld MG. Tissue-specific regulation of retinal and pituitary precursor cell proliferation. *Science*. 2002;297:1180–1183. https://doi.org/10.1126/science.1073263. [Primary research]
6. Gehring WJ, Affolter M, Bürglin T. Homeodomain proteins. *Annual Review of Biochemistry*. 1994;63:487–526. https://doi.org/10.1146/annurev.bi.63.070194.002415. [Review]
7. Larder R, Clark DD, Miller NLG, Mellon PL. Hypothalamic dysregulation and infertility in mice lacking the homeodomain protein Six6. *Journal of Neuroscience*. 2011;31:426–438. https://doi.org/10.1523/JNEUROSCI.1688-10.2011. [Primary research]
8. Spitz F, Demignon J, Porteu A, et al. Expression of myogenin during embryogenesis is controlled by Six/sine oculis homeoproteins through a conserved MEF3 binding site. *Proceedings of the National Academy of Sciences USA*. 1998;95:14220–14225. https://doi.org/10.1073/pnas.95.24.14220. [Primary research]
