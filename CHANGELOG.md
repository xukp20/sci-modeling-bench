# Changelog

All notable changes to SciModelingBench are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-07-18

### Added

- Uniform `AgentInputBundle` and disclosure-scoped `AgentInputManifest` public
  contracts covering Dataset identity, selected split, visible table schemas,
  table disclosure roles, field roles, descriptions, physical types, units,
  constraints, and Protocol-disclosed scientific constants.
- Public helpers for constructing Agent table views from canonical Dataset
  field specifications while requiring explicit semantics for renamed,
  flattened, or derived visible columns.

### Changed

- **Breaking:** `Protocol.build_input()` and `Task.build_input()` now return an
  `AgentInputBundle` instead of the domain-specific data object directly. Read
  the former return value from `bundle.data`; use `bundle.manifest` for the
  uniform machine-readable description. Task-built manifests additionally
  carry the concrete `task_id`.
- Every Design-Bench Protocol now publishes a manifest for exactly its
  Agent-visible views, including multilevel GFP measurements, UTR
  compositional inputs, Superconductor element order, Hopper policy layout,
  DrugMatrix condition context, and the three black-box optimization inputs.
  Complete canonical Dataset manifests and hidden Protocol fields are not
  forwarded.

## [0.5.0] - 2026-07-18

### Added

- Measured eGFP UTR MRL Dataset with 318,468 canonical 50-nt sequences,
  deterministic uAUG and Kozak annotations, a reproducible Hub release
  builder, and a label-hidden biological compositional Protocol.
- Finite-pool measured MRL Objective and compositional ranking Task using
  `global_ndcg` as its primary metric and preserving common candidate-quality
  diagnostics.
- Corrected Sarkisyan GFP Dataset with 51,715 unique protein genotypes,
  retained nucleotide and filtered-barcode measurement context, a reproducible
  Figshare v1 builder, and strict cross-level validation.
- GFP lower-to-higher measured-pool Protocol, protein-level measured Objective,
  and 128-sequence ranking Task using `global_ndcg` without the legacy learned
  Transformer oracle.
- DrugMatrix clinical-pathology Dataset preserving 10,605 individual-animal
  observations, six measured endpoints, audited molecular mappings, and a
  reproducible CEBS/ChEMBL release builder.
- DrugMatrix measured-condition Protocol, control-relative endpoint Objective,
  and six configurable 64-condition ranking settings using `global_ndcg`
  without the legacy context-free learned ChEMBL oracles.

### Changed

- **Breaking:** TFBind10 Pho4 now uses the v2 standard black-box optimization
  contract. Its Protocol directly returns lower-half observation rows instead
  of `TFBind10Pho4AgentInput`, submissions may contain any valid DNA 10-mer,
  and relative metrics use the complete `4^10` domain rather than an
  upper-half evaluation pool. Callers should use the returned Dataset directly
  and compare results only under the v2 Task ID.
- Objectives can translate a public candidate handle to its Dataset-schema
  validation view before evaluation, enabling condition-level measured lookup
  without adding derived Task IDs to observation tables.

### Fixed

- Optional semantic fields with null values now bypass physical feature
  encoding after required-field validation, allowing sparse scientific context
  columns to validate as declared.
- TFBind10 Pho4 Task input construction reuses the Objective's NumPy affinity
  landscape and row-to-sequence index instead of rebuilding the landscape,
  materializing a million-row score table, or re-encoding 4.16 million DNA
  strings.

## [0.4.0] - 2026-07-18

### Added

- Generic `BlackBoxOptimizationTask` and `CandidatePoolRankingTask` contracts
  with shared ordered-candidate metrics, finite-pool membership checks, and
  scored-prefix reporting for submissions longer than the configured `K`.
- Reproducible Hopper-v5 rollout builder and optional `hopper-sim` dependency
  group for auditing legacy Hopper Controller policies without adding MuJoCo
  to the base installation.
- Hopper Controller Dataset preserving 500 raw stochastic returns and episode
  outcomes for all 3,200 structured policies, with strict identity/summary
  validation, an upload-ready release builder, lower-60% observation Protocol,
  measured-mean Objective, and 32-policy candidate-pool ranking Task.

### Changed

- **Breaking:** concrete optimization Tasks now inherit the suite-independent
  `BlackBoxOptimizationTask`; the former Design-Bench-specific base class and
  import path were removed. Import the new base from `sci_modeling_bench.task`
  or the package root.
- **Breaking:** Superconductor is now
  `SuperconductorCandidatePoolRankingTask`. Submit full rows from
  `agent_input.candidates`; at least `submission_size` rows are accepted and
  only that leading prefix is evaluated. The former black-box optimization
  class and Task ID were removed.

## [0.3.0] - 2026-07-17

### Added

- Pho4 TFBind10 Dataset preserving 4,160,533 published BET-seq count,
  fraction, and observed-ddG rows across four replicates for the complete DNA
  10-mer space, with a reproducible Figshare builder and vectorized validator.
- Count-grounded Pho4 posterior affinity Objective, lower-half raw-observation
  Protocol, label-hidden upper-half candidate pool, and 128-candidate Task with
  `normalized_enrichment` as the default primary metric.
- Canonical Superconductor Dataset with all 21,263 UCI source measurements
  preserved across 15,164 normalized composition groups, published descriptor
  features, deterministic provenance, and a reproducible data builder.
- Superconductor lower-temperature observation Protocol, measured group-median
  Objective, and ordered hidden-pool optimization Task with `global_ndcg` as
  its default primary metric.
- Shared candidate metrics covering raw candidate quality, regret, normalized
  enrichment, global NDCG, and within-submission reranking NDCG.
- Canonical CellDAG-NAS integration for NASBench-101 with graph-aware
  validation, all token aliases, three raw 108-epoch training repeats, a
  low-40%-canonical offline Protocol, exact canonical Objective, and
  duplicate-aware 128-candidate Task evaluation.
- Reproducible `smb-build-cell-dag-nas` data builder with official TFRecord
  verification and exact parity checks against Design-Bench processed scores.

### Changed

- Objectives may declare derived output fields that are not persisted Dataset
  targets, enabling trusted aggregation of replicate observations without
  exposing evaluator labels in offline data.
- **Breaking:** black-box optimization Tasks now require ordered,
  canonical-unique submissions, allow `submission_size` and `primary_metric` to
  be configured at construction, and return the complete common metric set.
  Invalid or duplicate candidate batches retain diagnostics but no longer
  receive fabricated aggregate scores. Migrate a legacy submission by ranking
  it in descending predicted quality, canonicalizing and deduplicating it
  before submission, and reading the selected `primary_metric` from
  `evaluation.score` or the full `evaluation.metrics` mapping.
- **Breaking:** TFBind8 now uses `best_k_mean` as its default primary metric;
  `best_score` remains available for best-of-submission reporting. Existing
  top-1 comparisons should use `evaluation.metrics["best_score"]`; callers
  that require the former default score can construct the Task with
  `primary_metric="best_score"`.
- CellDAG-NAS now uses the shared candidate evaluation contract with canonical
  graph identity, `best_k_mean` as its default primary metric, a `full_domain`
  reference, and the complete common score and regret metric set.

### Known Limitations

- Dataset artifacts and upstream benchmark tables are public. Task APIs define
  a trusted evaluation boundary but do not prevent external lookup; controlled
  agent evaluations still require an external isolation and feedback harness.

## [0.2.0] - 2026-07-16

### Added

- Generic `Task`, `ObjectiveBackedTask`, and structured submission-evaluation
  contracts without requiring every Task to use an Objective.
- Design-Bench-compatible black-box optimization evaluation for fixed
  128-candidate submissions, with separate submission and candidate validation,
  per-candidate diagnostics, and top-1 normalized scoring.
- Default `TFBind8BlackBoxOptimizationTask` composition of the canonical
  Dataset, bottom-50% Protocol, and exact Objective.

## [0.1.0] - 2026-07-16

### Added

- Initial Python 3.10+ package with typed public exports.
- Core Dataset framework for resolving Hugging Face revisions to immutable
  commits, selecting collection configs and splits, loading regular or
  streaming datasets, and checking declared schemas and row counts.
- Strict collection and dataset manifests with provenance metadata, semantic
  input, target, and context fields, common constraints, and split metadata.
- Structured validation reports and dataset-specific validator hooks that
  report violations without mutating observations or candidates.
- Read-only, lazily loaded Knowledge resources pinned to the Dataset revision.
- Minimal Objective and Protocol contracts for validated target evaluation and
  construction of agent-visible inputs.
- One black-box optimization integration for TFBind8 `SIX6_REF_R1`, including
  the complete canonical 65,536-sequence landscape, exact E-score lookup, and
  a Design-Bench-compatible bottom-50% Protocol exposing 32,768 unique offline
  candidates.
- Reproducible TFBind8 release builder and `smb-build-tfbind8` command with
  source checks, canonicalization, integrity validation, provenance output,
  and optional parity checks against legacy Design-Bench arrays.
- Public documentation for the framework concepts and TFBind8 integration.

### Known Limitations

- Dataset, Objective, and Protocol interfaces remain experimental, and a Task
  or evaluation-harness interface is not included in this release.
- Dataset artifacts are distributed separately from the Python package and
  retain their own source, citation, provenance, and license metadata.

[Unreleased]: https://github.com/xukp20/sci-modeling-bench/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/xukp20/sci-modeling-bench/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/xukp20/sci-modeling-bench/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/xukp20/sci-modeling-bench/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/xukp20/sci-modeling-bench/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/xukp20/sci-modeling-bench/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/xukp20/sci-modeling-bench/releases/tag/v0.1.0
