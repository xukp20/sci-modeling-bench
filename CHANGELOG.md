# Changelog

All notable changes to SciModelingBench are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/xukp20/sci-modeling-bench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/xukp20/sci-modeling-bench/releases/tag/v0.1.0
