# SciModelingBench Task Montage

`build_benchmark_task_montage_v2.py` creates the published, source-native
task-level overview at `assets/sci-modeling-bench-task-montage.svg`. It does not
embed completed category figures as screenshots. Instead, it reuses the
original SVG groups and individual raster assets from:

- `assets/sci-modeling-bench-bio-overview.svg`
- `assets/figure_sources/materials/`
- `assets/sci-modeling-bench-computational-systems-overview.svg`

The output separates the benchmark into five framed task families:
biomolecular design, superconducting materials, preclinical toxicology, neural
architecture design, and embodied control. Existing source attribution remains
embedded in the reused SVG figures.

The builder:

- imports the original Bio layout nodes and its individual ribosome/structure
  assets;
- reconstructs the superconductor and toxicology panels from the cropped YBCO
  SVG, RDKit molecule SVGs, original photographs, and generated composition
  cells;
- extracts the original `(a)`, `(b)`, and `(c)` groups directly from
  `nasbench-model-structure.svg`;
- extracts the Hopper body and legend groups directly from
  `hopper-v5-action-space.svg`, then places the three original rollout PNGs in
  a separate vertical column.

Build it with:

```bash
python assets/figure_sources/overview/build_benchmark_task_montage_v2.py
```

The generated SVG is self-contained. Export the corresponding publication PNG
from that canonical SVG with CairoSVG.
