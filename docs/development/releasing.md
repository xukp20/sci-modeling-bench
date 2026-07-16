# Releasing SciModelingBench

Releases use one version tag to publish both GitHub release assets and the
Python distribution on PyPI.

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

## Release Checklist

1. Update `project.version` in `pyproject.toml` and add the matching changelog
   entry.
2. Run `pytest`, `python -m build`, and `python -m twine check --strict dist/*`.
3. Commit and push the release state to `main`.
4. Create and push a tag matching `v<project.version>`.
5. Verify the `Release` workflow, GitHub release assets, and a clean PyPI
   installation.

The workflow rejects tags that do not exactly match the package version. It
builds the source distribution and wheel once, stores those artifacts, attaches
them to the GitHub release, and publishes the same files to PyPI through OIDC.

Dataset repositories have independent versions, tags, provenance, and license
metadata. Publishing the Python package does not publish or relicense dataset
artifacts.
