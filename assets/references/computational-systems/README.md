# Computational-systems figure references

These files are candidate source material for a SciModelingBench overview of
CellDAG-NAS and Hopper Controller. They are references, not a finished layout.

## NASBench-101

- `01-nasbench101-architecture.png`
- Source: `images/architecture.png` in the official
  [`google-research/nasbench`](https://github.com/google-research/nasbench)
  repository, pinned by the benchmark to revision
  `b94247037ee470418a3e56dcb83814e9be83f3a8`.
- License: Apache License 2.0.
- Relevance: the image contains the shared CNN skeleton, an Inception-like
  seven-vertex cell, and the channel-combination semantics used by
  NASBench-101. For the final montage, its graph should be redrawn as a clean
  vector using the official adjacency matrix and operation labels rather than
  pasted with its small embedded labels.

## Hopper-v5

- `02-hopper-v5-action-space.png`
- Source: `docs/environments/mujoco/action_space_figures/hopper.png` in the
  official Gymnasium repository; checked at revision
  `20b453de30ef725a538e235fcdec909f30c95783` and published at
  `https://gymnasium.farama.org/_images/hopper.png`.
- Relevance: identifies the exact articulated body and three controlled hinge
  torques; useful as a technical inset or redraw reference.

- `03-hopper-v5-frame-standing.png`
- `04-hopper-v5-frame-flexed.png`
- `05-hopper-v5-frame-landing.png`
- Source: representative frames extracted from
  `docs/_static/videos/mujoco/hopper.gif` at the same Gymnasium revision,
  published at `https://gymnasium.farama.org/_images/hopper.gif`.
- Relevance: actual MuJoCo-rendered environment states suitable for a compact
  three-pose motion sequence. The source animation is not retained locally.

Gymnasium is distributed under the MIT License. The benchmark itself fixes
Gymnasium 1.3.x, MuJoCo 3.10.x, Hopper-v5, 11 observations, three actions, and
a 1,000-step episode horizon. The final policy schematic should be original
vector artwork showing the benchmark's 11-64-64-3 network and 5,126-parameter
layout rather than a generic neural-network icon.
