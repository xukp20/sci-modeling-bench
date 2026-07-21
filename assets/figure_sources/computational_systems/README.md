# Computational systems overview figure

The editable figure is assembled from two original vector redraws and three
unaltered Gymnasium Hopper-v5 frames displayed through cropped SVG viewports:

- `nasbench-model-structure.svg` preserves the official shared NASBench-101
  network skeleton and the three repeated modules in stack 2;
- `hopper-v5-action-space.svg` preserves the body segments, controlled joints
  0/1/2, coordinate directions, and complete joint legend from the official
  Gymnasium action-space diagram;
- `computational-systems-overview-layout.svg` provides the two-row,
  three-column layout, with the NAS diagram spanning the left column and the
  four Hopper panels occupying the right two columns.

Run `build_computational_systems_overview.py` to generate the self-contained
`assets/sci-modeling-bench-computational-systems-overview.svg`, then rasterize
that SVG at 2x for the PNG preview.
