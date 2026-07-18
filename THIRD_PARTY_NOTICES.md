# Third-Party Notices

SciModelingBench integrates benchmark definitions and derived data from
third-party projects. The project code license does not replace the terms that
apply to external datasets and publications.

## Design-Bench

The TFBind8 integration reproduces task semantics and preprocessing from
Design-Bench. The optional Hopper Controller builder also consumes the
project's published policy arrays and follows its documented policy tensor
order:

- Project: https://github.com/brandontrabucco/design-bench
- Referenced revision: `e52939588421b5433f6f2e9b359cf013c542bd89`
- Copyright: Copyright (c) 2020 Brandon Trabucco
- License: MIT License

## Hopper Simulator

Optional Hopper rollout generation uses Gymnasium and MuJoCo; neither is part
of the base installation or redistributed by this repository:

- Gymnasium: https://github.com/Farama-Foundation/Gymnasium, MIT License
- MuJoCo: https://github.com/google-deepmind/mujoco, Apache License 2.0

The generated rollout artifact is not bundled with the Python package. Its
provenance metadata records the exact simulator versions, Hopper XML checksum,
Design-Bench source checksums, policy execution recipe, and seeds.

## TFBind8 Data

The TFBind8 observations originate from the protein-binding microarray data
published by Barrera et al. (Science, 2016), UniPROBE accession `BAR15A`.
SciModelingBench publishes only the derived contiguous 8-mer landscape and
does not assert that the project MIT license applies to those observations.
The Hugging Face Dataset card records the source, citations, checksums,
transformations, and applicable upstream terms.

## BET-seq TFBind10 Pho4 Data

The TFBind10 Pho4 integration derives its raw replicate table from the BET-seq
processed data published by the Fordyce Lab:

- Dataset: https://doi.org/10.6084/m9.figshare.5728467.v1
- Source publication: Le et al. (2018), PNAS, doi:10.1073/pnas.1715888115
- Analysis repository: https://github.com/FordyceLab/BET-seq
- Referenced revision: `d73e583dc2c0d73539b804f41775d8cb3d42e633`
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)

The release selects only published Pho4 rows, preserves source replicate
granularity and zero-count infinities, and records the archive, member, and
generated Parquet checksums in its Hugging Face provenance report.

## NASBench-101

The CellDAG-NAS integration derives canonical graph identities and training
records from NASBench-101 and preserves the Design-Bench 31-token aliases:

- Project: https://github.com/google-research/nasbench
- Referenced revision: `b94247037ee470418a3e56dcb83814e9be83f3a8`
- Copyright: Copyright 2019 The Google Research Authors
- License: Apache License 2.0

The graph-invariant hashing procedure in CellDAG-NAS follows the Apache-2.0
NASBench-101 `graph_util.hash_module` implementation.

## UCI Superconductivity Data

The Superconductor integration derives composition groups, measured targets,
and published descriptor features from UCI dataset 464:

- Dataset: https://archive.ics.uci.edu/dataset/464/superconductivty+data
- Source publication: Hamidieh (2018), Computational Materials Science
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)

The Hugging Face manifest and provenance report record the source archive and
member checksums, grouping transformation, retained observations, and artifact
checksum.
