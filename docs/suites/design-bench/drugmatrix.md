# DrugMatrix Clinical-Pathology Ranking

DrugMatrix is a context-aware measured-pool ranking Task built from repeated-dose
rat toxicology observations. It replaces Design-Bench's context-free ChEMBL
surrogate with individual-animal measurements, explicit treatment context, and
a deterministic control-relative evaluator.

## At a Glance

| Property | Default setting |
|---|---|
| Task | `DrugMatrixCandidatePoolRankingTask` |
| Task ID | `design-bench/drugmatrix-<endpoint>-candidate-pool-ranking-v3` |
| Hub config / split | `drugmatrix_clinical_pathology` / `observations` |
| Agent input | Measured control rows and labeled treatment conditions plus an unlabeled candidate pool |
| Scored prefix | First 16 distinct measured treatment conditions |
| Objective | Absolute endpoint deviation from matched controls |
| Primary metric | `global_ndcg` |
| Summary size | 5 conditions for the secondary `*_k_*` metrics |
| Endpoint | One of `mchc`, `mch`, `creatinine`, `sodium`, `chloride`, or `phosphorus` |

## Scientific Object

One source row is one Sprague-Dawley rat observation. A chemical candidate is
not just a molecule: it is a measured treatment condition containing a
molecule, dose, duration, vehicle, administration route, sex, and study.

The Dataset retains six clinical-pathology measurements from the same animal:

| Field | Source column | Meaning | Unit |
|---|---|---|---|
| `mchc` | `MCHC` | Mean corpuscular hemoglobin concentration | g/dL |
| `mch` | `MCH` | Mean corpuscular hemoglobin | pg |
| `creatinine` | `CREATININE` | Creatinine | mg/dL |
| `sodium` | `NA` | Sodium | mEq/L |
| `chloride` | `CHLORIDE` | Chloride | mEq/L |
| `phosphorus` | `PHOSPHORUS` | Phosphorus | mg/dL |

These are six target columns in one Dataset, not six unrelated datasets. A
Task selects one endpoint through an Objective parameter while all endpoints
share the same observations and measured candidate pool.

## Source And Dataset Schema

The source is the NIEHS Chemical Effects in Biological Systems (CEBS)
[DrugMatrix release](https://cebs.niehs.nih.gov/cebs/paper/15670), dataset DOI
`10.22427/NTP-DATA-107-022-001-000-3`. The canonical release uses the official
clinical chemistry/hematology workbook and curated chemical structure file.
The canonical Parquet SHA-256 is
`d597095922573c5b459ec2ce9e693b03a26b6098846dbc90f0bbb78a567099f4`.
The default immutable Hub revision is
`d8b9ea3c78ed33edf0869a427940a0651eb49f52`.

| Build input | SHA-256 |
|---|---|
| `DrugMatrix_ClinicalChemistry_Hematology.xlsx` | `0cc3a2aabe8585cab34c920d9d46d7323f1529d1caff452143c2d1ac818fc0fd` |
| `Drugmatrix_Curated_Chemicals_With_SMILES.txt` | `fa9509d438290e37059e1bcfb75d96c6fa500ec8a9a22ca8829b299c05f133bd` |
| ChEMBL `CHEMBL3885882` MCHC activity export | `c1349b3d65340e5d788db7f84c7807f7b9cef5a9a2de822a9dca27e927bd83f1` |

The ChEMBL export is used only as a structure crosswalk source. Endpoint truth
comes from the CEBS individual-animal workbook.

```python
from sci_modeling_bench.suites.design_bench import DrugMatrixDataset

dataset = DrugMatrixDataset.from_hub()
observations = dataset.load()
```

The `observations` split preserves 10,605 individual-animal rows. It does not
store treatment-group means, control-relative effects, candidate ranks, or a
precomputed Task partition.

| Field | Role | Meaning |
|---|---|---|
| `animal_id` | context | Unique source animal record |
| `study_id` | context | Source toxicology study |
| `casrn` | context | Chemical Abstracts Service identifier; null for controls |
| `canonical_smiles` | input | Audited molecular representation; null when no reliable mapping exists |
| `dose` | context | Source dose value; null for controls |
| `duration_days` | context | Exposure duration in days |
| `vehicle` | context | Administration vehicle |
| `treatment` | context | Chemical, vehicle-control, or untreated-control row |
| `sex` | context | Animal sex when reported |
| `route` | context | Administration route when reported |
| six endpoint fields | target | Nullable individual-animal measurements listed above |

`species=Rat` and `strain=Sprague Dawley` are release-level constants and are
not repeated in every row. `canonical_smiles` is the only value not copied or
renamed from the clinical-pathology workbook. The build records the source and
status of every molecule mapping and leaves unresolved non-small-molecule or
ambiguous treatments null rather than applying fuzzy name matching.

The source workbook contains 8,940 chemical rows, 1,650 vehicle-control rows,
15 untreated-control rows, 656 treatment names, and 101 studies. All 10,605
`animal_id` values are unique, and 10,359 rows contain all six selected
measurements. Exact-name structure resolution maps 640 treatment names; the 16
unresolved names remain null. The build uses 582 unique ChEMBL mappings and 58
CEBS-curated fallbacks without fuzzy matching.

## Source-To-Release Processing

The builder performs a narrow deterministic transformation:

1. verify source hashes, workbook sheets, headers, row counts, and fixed
   source invariants;
2. preserve identifiers as strings and retain source row order;
3. select and rename the declared fields without imputing endpoints;
4. join an audited name/CASRN-to-SMILES crosswalk and retain failed mappings as
   null;
5. verify non-null structures with RDKit during the build;
6. write the Parquet split, manifest, and provenance report, then reload the
   artifact through `DrugMatrixValidator`.

The release does not clip or winsorize measurements. This matters because the
source contains unusual extremes, including a sodium value of `1555 mEq/L`.
Such rows remain source observations; the finite measured candidate pool is
defined separately by the Protocol.

## Why This Is Not The Legacy ChEMBL Task

Design-Bench's six `CHEMBL3885882` processed arrays each contain about 1,100
rows but only the same 199 SMILES. The processor removed dose, duration, route,
vehicle, study, and animal-group structure before fitting RF or neural
oracles. In each endpoint, 198 of 199 molecules consequently have multiple
different labels, and many molecule identities cross the row-level visible and
hidden split.

SciModelingBench does not import those token IDs, learned oracles, or the
bottom-percentile row split. It restores experimental context and restricts
final evaluation to conditions with retained animal measurements.

## Agent Input Protocol

`DrugMatrixMeasuredPoolProtocol` returns exactly two tables:

```python
bundle = protocol.build_input(dataset)
agent_input = bundle.data
observations = agent_input.observations
candidates = agent_input.candidates
```

The bundle manifest assigns units, roles, physical types, and descriptions to
every visible animal and condition field. It is shared by all six endpoint
Tasks; `Task.build_input()` adds the endpoint-specific concrete `task_id`.

The frozen candidate setting selects five-day chemical conditions at the
largest observed dose for that CASRN, requires a reliable molecular mapping,
complete treatment and control measurements for all six endpoints, and an
exact control matched by study, duration, route, vehicle, and sex. This produces
390 candidate conditions representing 385 CASRNs and 385 canonical structures.
Because the source does not provide a separate dose-unit field, the global
maximum-dose rule is a frozen source-data convention rather than a claim that
all administration routes use directly comparable dose semantics.

Candidate treatment-animal rows are removed from `observations`. Exact-control
rows and the molecule's other measured dose/time conditions remain visible.
The candidate table contains only:

```text
condition_id, casrn, canonical_smiles, dose, duration_days,
vehicle, sex, route, study_id
```

It contains no candidate endpoint measurement or derived score. The AgentInput
does not carry an endpoint description or submission budget; those belong to
the Task statement and Task configuration.

## Endpoint Objective

One `DrugMatrixEndpointObjective` supports all six endpoint values:

```python
objective = DrugMatrixEndpointObjective(dataset, endpoint="sodium")
```

For each candidate condition it aggregates the retained individual animals and
their exact matched controls:

```text
raw_response       = arithmetic mean of treatment-animal endpoint values
control_deviation  = abs(log(raw_response / control-animal mean))
```

The Objective returns both values. The default Task maximizes
`control_deviation`; it does not claim that a larger raw sodium, creatinine, or
hematology value is desirable. Conditions with missing, non-finite, or
non-positive values needed by this formula are excluded before the candidate
pool is frozen rather than repaired with an epsilon.

This Objective is exact with respect to the frozen aggregation rule and source
measurements, not an exact biological simulator. Individual-animal noise,
unrecorded physiology, and limited context remain part of the scientific
uncertainty.

## Candidate-Pool Ranking Task

`DrugMatrixCandidatePoolRankingTask` reuses the common ordered finite-pool
submission contract:

```python
task = DrugMatrixCandidatePoolRankingTask.from_hub(endpoint="sodium")
bundle = task.build_input()
agent_input = bundle.data

submission = [
    {"condition_id": value}
    for value in agent_input.candidates["condition_id"][:16]
]
evaluation = task.evaluate(submission)
```

The default submission contains 16 unique candidate IDs in predicted
descending order. The Task rejects unknown, duplicate, or malformed IDs and
returns the standard `CandidatePoolRankingEvaluation`; no DrugMatrix-specific
evaluation schema is introduced.

All common candidate metrics are reported. The primary metric is
`global_ndcg`, which measures both selection from the full 390-condition pool
and submitted order. `normalized_enrichment`, raw score summaries, and regret
metrics remain available as secondary diagnostics.

### Metric audit

The current random audit uses `N=16`, `K=5`, seed `20260720`, and 5,000
independent random ordered submissions per endpoint. The earlier visible RF
diagnostic used `N=64` and trains on 1,516
labelable conditions constructed only from `agent_input.observations`; it uses
Morgan fingerprints, basic RDKit descriptors, dose, duration, route, and sex.
It remains evidence that the visible data contain predictive signal, but its
raw scores are not directly comparable with the current `N=16` contract.

| Endpoint | Random `global_ndcg`, mean +/- std | 10th--90th percentile |
|---|---:|---:|
| MCHC | 0.1733 +/- 0.0530 | 0.1190--0.2348 |
| MCH | 0.2669 +/- 0.0602 | 0.1942--0.3468 |
| Creatinine | 0.1955 +/- 0.0582 | 0.1273--0.2746 |
| Sodium | 0.1519 +/- 0.0509 | 0.0987--0.2159 |
| Chloride | 0.1689 +/- 0.0523 | 0.1123--0.2365 |
| Phosphorus | 0.2040 +/- 0.0544 | 0.1415--0.2740 |

### Current data-only reference baselines

One frozen data-only pipeline is shared unchanged across all six
endpoints. It derives visible treatment labels from matched public control
rows, uses raw dose and duration as standardized numeric fields, and one-hot
encodes the public CASRN, canonical SMILES, vehicle, sex, route, and study
categories. SMILES remains an opaque category: the baseline does not use
RDKit, Morgan or MACCS fingerprints, molecular descriptors, scaffolds, or
hidden candidate measurements.

The simple model is Ridge alpha 1. Three-fold visible-data CV selects from
Ridge alpha `0.1`, `1`, `10`, and one fixed sparse XGBoost configuration.
All values are official `global_ndcg` for the current `N=16` contract.

| Endpoint | Random mean | Fixed Ridge alpha 1 | CV-selected | Selected model |
|---|---:|---:|---:|---|
| MCHC | 0.173257 | 0.548295 | **0.630254** | XGBoost |
| MCH | 0.266876 | **0.444260** | 0.436404 | XGBoost |
| Creatinine | 0.195459 | 0.709716 | **0.727785** | XGBoost |
| Sodium | 0.151904 | 0.839711 | **0.857489** | Ridge alpha 10 |
| Chloride | 0.168923 | **0.431076** | 0.404368 | XGBoost |
| Phosphorus | 0.204023 | **0.532688** | 0.487150 | XGBoost |

The selected model is retained even when its official score is below the fixed
Ridge. CV uses visible labels only; using the trusted evaluator to switch the
model would turn the hidden pool into a tuning set.

The random distributions are not saturated at `N=16`. The smaller scored
prefix reduces one submission from 8.2% to 4.1% of the 390-condition pool and
better represents a finite follow-up list. MCH is intentionally retained
despite its weaker historical model signal rather than selecting only
favorable endpoints.

## Modeling Notes

Useful method families include:

- molecular fingerprints, physicochemical descriptors, functional groups, and
  scaffold-aware representations;
- dose/time response models that use earlier or lower-dose observations from
  the same molecule;
- study-, route-, and vehicle-aware hierarchical models;
- multi-output modeling of relations such as MCH/MCHC and sodium/chloride;
- repeated-measurement uncertainty, group-aware validation, and abstention.

The Protocol deliberately does not publish maintainer-generated fingerprints,
condition statistics, or fitted proxy labels. Those choices remain part of the
scientific modeling problem.

## Scope And Limitations

- The Task ranks a finite set of previously measured conditions; it does not
  evaluate arbitrary de novo SMILES.
- RDKit validity is only a syntax/valence check. It does not establish
  synthesis, formulation, dosing feasibility, or human safety.
- Control-relative deviation is an experimental prioritization score, not a
  clinical desirability or drug-quality score.
- Public source data can be found outside the Task API. Strict evaluations
  require an external harness to isolate the full Dataset, caches, repository,
  and network from the Agent.
- The CEBS page provides the source files and DOI but does not state a simple
  redistribution license for this artifact. Reusers should review the source
  terms and provenance rather than infer MIT licensing from the Python package.

## Rebuilding

Install the data-build dependencies and run:

```bash
python -m pip install "sci-modeling-bench[data-build]"
smb-build-drugmatrix \
  --clinical-pathology DrugMatrix_ClinicalChemistry_Hematology.xlsx \
  --curated-chemicals Drugmatrix_Curated_Chemicals_With_SMILES.txt \
  --chembl-activity MCHC.json \
  --output-dir release
```

The builder verifies all three fixed source hashes, writes the canonical
Parquet and manifest, and records the complete 656-name mapping audit and
measured-pool score hashes in provenance.
