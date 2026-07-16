# Releasing SciModelingBench

Releases use one version tag to publish both GitHub release assets and the
Python distribution on PyPI. Ordinary pushes and pull requests do not run
GitHub Actions; development verification is performed locally.

## One-Time PyPI Setup

Create a PyPI Trusted Publisher with these values:

| Field | Value |
|---|---|
| PyPI project | `sci-modeling-bench` |
| GitHub owner | `xukp20` |
| Repository | `sci-modeling-bench` |
| Workflow | `release.yml` |
| Environment | `pypi` |

Create a GitHub environment named `pypi`. Requiring maintainer approval for
that environment is recommended. No long-lived PyPI API token is stored in
GitHub.

## Versioning

SciModelingBench uses Semantic Versioning:

- `PATCH` releases contain backward-compatible fixes and packaging or
  dependency corrections;
- `MINOR` releases add a public Dataset, Objective, Protocol, Task, benchmark
  suite, or another substantial backward-compatible capability;
- while the package is `0.x`, incompatible public API changes also increment
  `MINOR` and require an explicit migration note;
- after `1.0.0`, incompatible public API changes increment `MAJOR`.

Completing one coherent, independently usable Dataset or Task integration is a
normal minor-release boundary. Internal scaffolding, tests, and documentation
corrections can accumulate without creating a release by themselves.

## Changelog

`CHANGELOG.md` follows Keep a Changelog. User-visible development changes stay
under `[Unreleased]` and use `Added`, `Changed`, `Deprecated`, `Removed`,
`Fixed`, or `Security` headings. Internal refactors and CI changes are omitted
unless they affect installation, compatibility, release artifacts, or
security.

Incompatible changes belong under `Changed`, start with `**Breaking:**`, and
identify the affected old API, its replacement, and the minimum migration. At
release time, move the entries to `[<version>] - YYYY-MM-DD` and add the
corresponding release or comparison link.

## Release Checklist

1. Keep user-visible development changes under `[Unreleased]` and use a
   `.dev0` package version while preparing the next release.
2. Propose the final version, scope, compatibility impact, verification status,
   and known risks to the maintainer. Do not proceed without explicit release
   approval.
3. After approval, replace the `.dev0` version with the final version and move
   the changelog entries to `[<version>] - YYYY-MM-DD`.
4. Run `pytest`, `python -m build`, and
   `python -m twine check --strict dist/*` locally.
5. Commit and push the approved release state to `main`.
6. Create and push the matching `v<project.version>` tag. This is the only
   trigger for the release workflow.
7. Verify the Python-version test matrix, PyPI publication, GitHub release
   assets, and a clean PyPI installation.

The workflow rejects tags that do not exactly match the package version. It
tests every supported Python version, builds the source distribution and wheel
once, and publishes those files to PyPI through OIDC before attaching the same
files to the GitHub release. If the GitHub release step fails after PyPI
publication, retry that step rather than rebuilding the distributions.

Dataset repositories have independent versions, tags, provenance, and license
metadata. Publishing the Python package does not publish or relicense dataset
artifacts.
