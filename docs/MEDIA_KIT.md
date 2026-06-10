# Media Kit: Invariant / SIGMA / SVR

## One-line summary

Invariant is a deterministic verification layer for AI systems that checks evolving graph state and emits signed receipts.

## Technical result

O(1)-in-n lazy edit ingestion for incremental sheaf cohomology under bounded local geometry, measured at 5M vertices with ~35 us median update latency and zero drift at synchronization.

## Why it matters

Production AI agents mutate memory, plans, claims, tool outputs, and execution state. Today, many systems use another LLM as the checker. Invariant replaces the parts that can be made deterministic with a CPU-side verifier that produces auditable receipts. The receipt is a mathematical proof artifact, not a confidence score.

## Key facts

- 5,000,000 vertices, ~15,000,000 streaming edits
- 35 microseconds median lazy update latency
- Zero measured drift between lazy and full-recompute results
- CPU-only, no GPU, no ML
- Ed25519 signed receipts (independently verifiable)
- IANA-registered media type: application/vnd.svr.receipt+json
- Verifier on PyPI: pip install svr-verify
- Open standard: any compliant engine can issue SVR receipts

## Angle for AI/ML newsletters

Agent systems are moving from generation to state mutation, but the verification layer is still often another LLM. Invariant gives them a deterministic receipt-producing alternative for the structural consistency checks that have a mathematical answer.

## Angle for developer newsletters

Most "AI verification" tools are probabilistic. This is a CPU-side library that uses algebraic topology (sheaf cohomology) to detect structural contradictions in knowledge graphs, agent memory, and compliance workflows. It runs at microsecond latency, produces signed receipts, and has a runnable demo on GitHub.

## Angle for security/compliance newsletters

Audit trails for AI decisions currently lack cryptographic verifiability. SVR receipts are signed, timestamped attestations that a specific verification was performed on specific input, with item-level detail and a canonical hash. They are independently verifiable without contacting the issuing engine.

## Links

- GitHub: https://github.com/Jasonleonardvolk/svr-verify
- Medium: https://medium.com/@jasonlvolk/streaming-exact-topology-at-5-million-vertices-how-we-made-sheaf-cohomology-o-1-per-edit-1420e7c76b7a
- arXiv: https://arxiv.org/abs/2606.04227
- PyPI: https://pypi.org/project/svr-verify/
- Website: https://invariant.pro
- sigma-guard (graph DB integration): https://github.com/Jasonleonardvolk/sigma-guard

## Contact

Jason Volk
Invariant Research
jason@invariant.pro
https://invariant.pro

## Suggested newsletter blurb (copy/paste ready)

Invariant SVR is a deterministic verification layer for AI agent state graphs. Instead of using another LLM as a checker, it uses sheaf cohomology to detect structural contradictions at CPU speed and emits cryptographically signed receipts. Benchmarked at 5M vertices with 35 us median update latency and zero drift. The verifier is on PyPI (pip install svr-verify) and the receipt format has an IANA-registered media type. GitHub repo includes a runnable demo.
