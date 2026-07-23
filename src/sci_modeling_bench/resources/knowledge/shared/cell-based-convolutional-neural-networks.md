# Cell-Based Convolutional Neural Networks

## Summary

A cell-based convolutional neural network separates a repeated local
computation module, the cell, from a larger macro-architecture that arranges
cells into stages. A cell is often represented as a directed computation graph
whose nodes or edges carry primitive operations. Reusing a cell specification
reduces architectural degrees of freedom, but network behavior still depends
on the macro-architecture, channel scaling, shape transitions, and training
procedure.

## Scope

### Covered

- Neural-network cells and macro- versus micro-architecture.
- Operation-on-node and operation-on-edge graph conventions.
- Repeated cells, stage transitions, and tensor compatibility.
- The relation between a cell graph and the instantiated network.

### Not covered

- A particular cell's serialization, legal graph limits, or operation set.
- The performance of a particular architecture.
- A neural architecture search procedure.

## Core knowledge

### Micro- and macro-architecture

The micro-architecture describes computation within a reusable module. The
macro-architecture specifies how modules are stacked, how spatial resolution
and channel width change, and where classification heads or other fixed
components appear. Cell-based search spaces hold much of the
macro-architecture fixed while varying a local cell [1].

The same cell can therefore produce different complete networks when repeated
a different number of times, assigned different channel widths, or placed in a
different outer skeleton. Performance is conditional on both levels.

### Cells as directed computation graphs

A cell commonly receives one or more input feature tensors and produces an
output tensor through a DAG. Primitive operations may be attached to vertices
or edges, depending on the search-space definition. These conventions are not
interchangeable: an operation-on-node graph and an operation-on-edge graph can
encode different computations even when their unlabelled topology is similar
[1,2].

Internal vertices combine predecessor tensors using a declared aggregation
rule. An output may be one selected vertex, a sum, or a concatenation of
selected vertices. The graph alone is incomplete unless these tensor
semantics are specified.

### Repetition and parameters

Repeating a cell means reusing its architectural pattern. It does not
necessarily mean sharing numerical weights across cell instances. In ordinary
feedforward CNNs, repeated cells usually have distinct learned parameters even
when their graph structures are the same.

Stages can increase channel count and reduce spatial resolution. A normal cell
typically preserves resolution, whereas a reduction module or fixed transition
changes it. Exact terminology varies among architecture families.

### Paths and effective depth

Cell topology creates paths with different numbers and types of operations.
When cells are stacked, local path choices compose into network-level
dependency paths. A cell's longest path contributes to effective depth, while
shorter branches can carry information through fewer transformations.

The number of graph vertices is not identical to network depth: parallel
vertices may lie at the same dependency depth, and primitive operations can
contain several internal layers such as convolution, normalization, and
activation.

### Why cell-based spaces are used

Searching a complete layer-by-layer network can create a very large and
variable design space. Repeating a cell introduces a structural prior and
reduces the search dimension. Published NAS systems have used cell-based
spaces to transfer a learned local motif into a larger network [1,3].

This restriction also limits expressivity. A good architecture outside the
fixed macro-architecture or primitive vocabulary cannot be represented by the
cell search space.

## Conditions, limitations, and uncertainty

- "Cell" is a design convention, not a uniquely standardized neural-network
  unit.
- Operation placement, aggregation, channel allocation, and preprocessing must
  be specified to define the function.
- Reusing graph structure does not imply shared weights.
- A cell evaluated within one macro-architecture, dataset, or training recipe
  need not preserve its ranking in another.
- Graph size and edge count are incomplete proxies for parameters, FLOPs,
  memory use, latency, and trainability.

## Related knowledge resources

- `directed_acyclic_computation_graphs_and_graph_isomorphism`: graph structure
  and representation equivalence.
- `neural_architecture_search_spaces_and_performance_evaluation`: how
  architecture spaces are defined and evaluated.

## References

1. Elsken T, Metzen JH, Hutter F. Neural architecture search: A survey.
   *Journal of Machine Learning Research*. 2019;20(55):1–21.
   https://www.jmlr.org/papers/v20/18-598.html [Review]
2. Ying C, Klein A, Christiansen E, Real E, Murphy K, Hutter F.
   NAS-Bench-101: Towards reproducible neural architecture search. *Proceedings
   of Machine Learning Research*. 2019;97:7105–7114.
   https://proceedings.mlr.press/v97/ying19a.html [Primary research]
3. Liu H, Simonyan K, Yang Y. DARTS: Differentiable architecture search.
   *International Conference on Learning Representations*. 2019.
   https://openreview.net/forum?id=S1eYHoC5FX [Primary research]
