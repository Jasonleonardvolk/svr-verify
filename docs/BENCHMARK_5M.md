# Benchmark: 5M Vertices, ~15M Streaming Edits

## Summary

SIGMA's incremental sheaf cohomology engine was benchmarked at 5,000,000 vertices with approximately 15,000,000 streaming edits. The benchmark measures lazy incremental update latency, memory consumption, and drift between lazy evaluation and full recomputation.

## Results

| Metric | Value |
|---|---|
| Graph vertices | 5,000,000 |
| Streaming edits | ~15,000,000 |
| Median lazy update latency | 35 us |
| P95 lazy update latency | < 100 us |
| Drift at synchronization | 0 (exact match) |
| Memory (RestrictionStore) | 0.50 MB |
| Cells in final state | 25,473 |
| Algorithm | O(1) amortized incremental cellular sheaf cohomology |
| Hardware | Intel i9-13900H, 64 GB RAM, no GPU |

## What "drift" means

At each synchronization point, SIGMA compares the lazy incremental result against a full recomputation from scratch. If the two match exactly, drift is 0. Any nonzero drift would indicate a correctness bug in the incremental path. Across all synchronization points in the 5M benchmark, drift was measured at exactly zero.

## What "O(1) amortized" means

Each streaming edit touches only the cells affected by the change. Under the bounded local geometry assumption (each vertex participates in a bounded number of cells), the cost per edit is O(1) with respect to the total graph size n. The amortization is over the lazy evaluation schedule: individual edits mark cells dirty, and the actual cohomology recomputation happens at query time, batching all dirty cells.

The median latency of 35 microseconds per edit at 5M vertices confirms this: the cost does not grow with n because only local cells are revisited.

## How the benchmark works

1. A random graph with 5M vertices and bounded-degree edges is constructed.
2. Each vertex is assigned a stalk vector (claim space).
3. Each edge is assigned a restriction map (consistency constraint).
4. Streaming edits are applied: vertex claim changes, edge insertions, edge deletions.
5. After each batch of edits, dirty cells are lazily recomputed.
6. At synchronization points, the lazy result is compared against full recomputation.
7. Timing, memory, and drift are recorded.

## Conditioning

The Lyapunov conditioning run (arXiv:2606.04227, Section 5) measured median kappa of 1.53e4 and p95 of 2.91e6 across 100,000 random graph instances, all finite. This confirms numerical stability of the coboundary operator under realistic graph topologies.

## Reproducibility

The benchmark parameters (stalk dimension d=8, random seed, graph construction method) are specified in the arXiv paper. The full SIGMA engine is required to reproduce the benchmark; the standalone verifier in this repository is designed for receipt verification, not large-scale cohomology computation.

## Reference

Jason Volk. "Streaming Exact Topology at 5 Million Vertices: How We Made Sheaf Cohomology O(1) Per Edit." arXiv:2606.04227, June 2026.

Medium article: https://medium.com/@jasonlvolk/streaming-exact-topology-at-5-million-vertices-how-we-made-sheaf-cohomology-o-1-per-edit-1420e7c76b7a
