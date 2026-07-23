# Directed Acyclic Computation Graphs and Graph Isomorphism

## Summary

A directed acyclic graph (DAG) contains directed edges but no directed cycle.
DAGs represent computations whose dependencies can be evaluated in a
topological order. The same labeled computation graph can have multiple
topological orders and multiple adjacency-matrix representations because
internal vertices can be renamed. Labeled graph isomorphism distinguishes
changes of representation from changes of computation structure.

## Scope

### Covered

- Directed graphs, paths, reachability, and topological order.
- DAGs as computation graphs.
- Adjacency matrices and vertex ordering.
- Labeled graph isomorphism and automorphisms.

### Not covered

- A token vocabulary or serialization format for a particular dataset.
- A graph-search algorithm or predictive representation.
- Numerical behavior of a particular neural architecture.

## Key concepts and notation

| Term | Definition |
| --- | --- |
| \(G=(V,E)\) | Directed graph with vertices \(V\) and directed edges \(E\) |
| path | Sequence of vertices joined by consistently directed edges |
| predecessor | Vertex with an edge into another vertex |
| successor | Vertex reached by an outgoing edge |
| topological order | Linear order in which every edge points from earlier to later |
| graph isomorphism | Label-preserving bijection that preserves all edges |
| automorphism | Isomorphism from a graph to itself |

## Core knowledge

### Directed acyclic graphs

A directed cycle returns to its starting vertex by following edge directions.
A DAG contains no such cycle. A finite directed graph is acyclic exactly when
it admits a topological ordering. Topological order is generally not unique:
vertices without an ordering dependency may exchange positions [1,2].

For a computation graph, an edge \(u\rightarrow v\) indicates that the value at
\(v\) depends on the value produced at \(u\). A topological order provides a
valid evaluation sequence. A directed cycle would require a value to depend
recursively on itself unless additional state or recurrence semantics were
defined.

### Paths and complete participation

A path from a designated input to a designated output describes one chain of
data dependencies. Branching creates multiple paths; merging combines values
from multiple predecessors. A vertex that is unreachable from the input cannot
receive input-dependent information. A vertex from which the output is
unreachable cannot influence the output.

Path length counts edges, while graph depth usually refers to a longest
dependency path under a specified convention. The number of paths can grow
rapidly with branching and reconvergence, but path count alone does not specify
the operations applied along those paths.

### Adjacency matrices depend on vertex order

For ordered vertices \(v_0,\ldots,v_{n-1}\), an adjacency matrix \(A\) can be
defined by

\[
A_{ij} =
\begin{cases}
1,&(v_i,v_j)\in E,\\
0,&\text{otherwise}.
\end{cases}
\]

If the vertex order is topological, every edge points forward, so the
adjacency matrix is strictly upper triangular. Renaming or reordering internal
vertices permutes rows and columns together and can yield a different matrix
for the same abstract graph.

### Labeled graph isomorphism

Two directed labeled graphs are isomorphic when a bijection between their
vertices preserves edge direction and vertex labels. If \(\pi\) is the
permutation matrix of such a relabeling, their adjacency matrices satisfy

\[
A'=\pi A\pi^\mathsf{T},
\]

with operation labels permuted by the same mapping. Different serialized
orders can therefore denote the same computation [3].

An automorphism is a nontrivial relabeling that leaves a graph unchanged.
Symmetric branches or repeated operation labels can create automorphisms.
Consequently, the number of valid serializations is not simply the factorial
of the number of internal vertices.

### Structural and functional equivalence

Graph isomorphism is a structural equivalence. For deterministic operations
and matching tensor semantics, isomorphic labeled computation graphs compute
the same function after corresponding parameters are transferred. The
converse is not guaranteed: non-isomorphic networks can still compute the same
function because of parameter values, algebraic identities, or redundant
operations.

## Conditions, limitations, and uncertainty

- Isomorphism must preserve all labels and edge directions that carry
  computational meaning.
- An adjacency matrix without its vertex ordering and labels is not a complete
  description of a labeled computation graph.
- Topological-order aliases are representation duplicates, not repeated
  evaluations of the underlying computation.
- Graph structure alone does not determine tensor shapes, parameter values,
  training dynamics, or predictive accuracy.
- Hashes can provide stable graph identities only relative to the labeling and
  canonicalization rules used to construct them.

## Related knowledge resources

- `cell_based_convolutional_neural_networks`: computation graphs used as
  reusable neural-network modules.
- `pooling_branching_and_feature_aggregation`: meanings of branch and merge
  operations.

## References

1. Diestel R. *Graph Theory*. 6th ed. Graduate Texts in Mathematics 173.
   Springer; 2025. https://diestel-graph-theory.com/ [Textbook]
2. Cormen TH, Leiserson CE, Rivest RL, Stein C. Elementary graph algorithms.
   In: *Introduction to Algorithms*. 4th ed. MIT Press; 2022. [Textbook]
3. Ying C, Klein A, Christiansen E, Real E, Murphy K, Hutter F.
   NAS-Bench-101: Towards reproducible neural architecture search. *Proceedings
   of Machine Learning Research*. 2019;97:7105–7114.
   https://proceedings.mlr.press/v97/ying19a.html [Primary research]
