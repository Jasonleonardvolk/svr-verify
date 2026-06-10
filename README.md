# svr-verify

Standalone verifier for **Signed Verification Receipts (SVR)**.

Deterministic verification receipts for AI systems: CPU-only, Ed25519-signed, reproducible, and independently verifiable. No SATYA engine required. No SIGMA dependency. Just the receipt and the public key.

**Benchmark:** 5M vertices, ~15M streaming edits, 35 us median lazy update latency, zero measured drift at synchronization.

---

## What a receipt looks like

```json
{
  "svr_version": "1.0",
  "receipt_id": "SIGMA-20260610-BENCH5M",
  "receipt_type": "graph_consistency",
  "engine_version": "sigma-0.9.0",
  "verdict": "consistent",
  "graph_vertices": 5000000,
  "median_update_us": 35,
  "drift": 0,
  "safe_to_rely": true,
  "signature_scheme": "Ed25519",
  "content_type": "application/vnd.svr.receipt+json"
}
```

Every receipt is signed with Ed25519. Anyone with this library can check one. No engine required.

---

## Install

```
pip install svr-verify
```

## Quick start

```
git clone https://github.com/Jasonleonardvolk/svr-verify.git
cd svr-verify
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python examples\verify_receipt.py examples\receipts\sample_pass.svr.json --sign
```

Output:

```
Generating Ed25519 keypair...
Signed receipt written to: examples\receipts\sample_pass.signed.svr.json

============================================================
SVR Verification Report
============================================================

  Receipt ID:      SIGMA-20260610-BENCH5M
  SVR Version:     1.0
  Receipt Type:    graph_consistency
  Verdict:         consistent
  Items Checked:   4
  Items Passed:    4
  Items Failed:    0

  Signature:       VALID
  Structure:       VALID

  RESULT: VALID

============================================================
```

Try the failing receipt:

```
python examples\verify_receipt.py examples\receipts\sample_fail.svr.json --sign
```

Or run the graph consistency demo:

```
python examples\verify_graph_demo.py
```

---

## Why AI systems need deterministic receipts

Production AI agents mutate memory, plans, claims, tool outputs, and execution state. When something goes wrong, the current answer is usually "ask another LLM whether the first one was right." That is probabilistic checking of probabilistic output.

SVR replaces the parts that can be made deterministic with a CPU-side verifier that produces auditable, cryptographically signed receipts. The receipt is a mathematical proof artifact, not a confidence score. It either verifies or it does not.

This matters for agent memory graphs, RAG pipelines, compliance workflows, citation audits, and any system where the state graph evolves over time and consistency must be maintained across edits.

---

## Benchmark

| Metric | Value |
|---|---|
| Graph vertices | 5,000,000 |
| Streaming edits | ~15,000,000 |
| Median lazy update latency | 35 us |
| Drift at synchronization | 0 |
| Memory (RestrictionStore) | 0.50 MB |
| Cells touched per edit | 25,473 |
| Algorithm | O(1) amortized incremental sheaf cohomology |
| Hardware | Intel i9-13900H, 64 GB RAM |
| GPU required | No |
| ML required | No |

Full methodology: [docs/BENCHMARK_5M.md](docs/BENCHMARK_5M.md)

---

## Verify a receipt

### Command line

```
svr-verify receipt.svr.json
```

Output:

```
============================================================
SVR Verification Report
============================================================

  Receipt ID:      SATYA-20260518-4C2388CC
  SVR Version:     1.0
  Receipt Type:    compliance
  Verdict:         contradicted
  Items Checked:   12
  Items Passed:    7
  Items Failed:    5

  Signature:       VALID
  Structure:       VALID

  RESULT: VALID

============================================================
```

### Machine-readable output

```
svr-verify receipt.svr.json --json
```

### CI/CD integration

```
svr-verify receipt.svr.json --quiet
# Prints VALID or INVALID
# Exit code 0 = valid, 1 = invalid, 2 = file error
```

### Python API

```python
from svr_verify import verify

result = verify("receipt.svr.json")
print(result["valid"])            # True/False
print(result["signature_valid"])  # True/False
print(result["structure_errors"]) # [] if clean
```

### Low-level API

```python
import json
from svr_verify import canonical_bytes, verify_signature, validate_receipt

with open("receipt.svr.json") as f:
    receipt = json.load(f)

# Verify Ed25519 signature
sig_ok = verify_signature(receipt)

# Validate structure (required fields, count invariant)
errors = validate_receipt(receipt)

# Get canonical byte sequence (what was signed)
payload = canonical_bytes(receipt)
```

---

## What it checks

1. **Signature**: Recomputes the canonical serialization per SVR Spec Section 4, then verifies the Ed25519 signature against the embedded public key.

2. **Structure**: Validates all 22 required fields, the count invariant (`items_checked == items_passed + items_failed + items_excluded`), per-item required fields, and enum constraints.

3. **Canonical Hash**: Produces a SHA-256 digest of the canonical payload for fingerprinting.

---

## How SVR works

An SVR is a cryptographically signed, point-in-time attestation that a verification engine audited a specific input and produced a specific result.

The verification flow:

1. The SIGMA engine receives a graph state (vertices, edges, claims).
2. It computes sheaf cohomology over the graph to detect structural contradictions.
3. It emits a receipt containing the verdict, item-level results, and metadata.
4. The receipt is canonicalized per SVR Spec Section 4 and signed with Ed25519.
5. Anyone with `svr-verify` can independently check the signature and structure.

SVRs are:

- **Portable** - not locked to any platform or vendor
- **Signed** - Ed25519, unforgeable
- **Independently verifiable** - anyone with this library can check one
- **Vendor-neutral** - any compliant engine may issue SVRs
- **IANA registered** - media type `application/vnd.svr.receipt+json`

---

## How SIGMA verifies graph-state consistency

SIGMA uses cellular sheaf cohomology to determine whether local claims attached to graph nodes can be assembled into one consistent global assignment. If they cannot, SIGMA reports a structural obstruction with a mathematical proof.

The key insight: sheaf cohomology group H^1 measures obstructions to global consistency. If H^1 is nontrivial, the graph contains a structural contradiction that no local fix can resolve. This is not a statistical guess. It is a deterministic algebraic invariant.

SIGMA's incremental architecture achieves O(1) amortized cost per streaming edit by maintaining a cellular decomposition and only recomputing affected cells when the graph changes. At 5M vertices with ~15M streaming edits, the median lazy update latency is 35 microseconds with zero measured drift between lazy and full-recompute results.

For the full theoretical treatment, see [arXiv:2606.04227](https://arxiv.org/abs/2606.04227).

---

## Routing demo

For deterministic verification bypass routing (receipt-based memoization of repeated checks), see [ROUTING_DEMO.md](ROUTING_DEMO.md).

---

## Specification

- [SVR Spec v1.0](docs/SVR_SPEC.md)
- [How to Read an SVR](docs/HOW_TO_READ_AN_SVR.md)
- [Platform Adoption Guide](docs/PLATFORM_ADOPTION_GUIDE.md)
- [Agent State Verification](docs/AGENT_STATE_VERIFICATION.md)
- [IANA Registration](docs/IANA_REGISTRATION.txt)
- [JSON Schema](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/svr_schema_v1.json)

---

## Links

- **Medium:** [Streaming Exact Topology at 5 Million Vertices](https://medium.com/@jasonlvolk/streaming-exact-topology-at-5-million-vertices-how-we-made-sheaf-cohomology-o-1-per-edit-1420e7c76b7a)
- **arXiv:** [arXiv:2606.04227](https://arxiv.org/abs/2606.04227)
- **PyPI:** [svr-verify](https://pypi.org/project/svr-verify/)
- **Website:** [invariant.pro](https://invariant.pro)
- **IANA Registration:** `application/vnd.svr.receipt+json`
- **sigma-guard (graph DB integration):** [github.com/Jasonleonardvolk/sigma-guard](https://github.com/Jasonleonardvolk/sigma-guard)

---

## Citation

```bibtex
@misc{volk2026sigma,
  author       = {Jason Volk},
  title        = {{SIGMA}: Streaming Incremental Sheaf Cohomology
                  for Deterministic Graph-State Verification},
  year         = {2026},
  eprint       = {2606.04227},
  archivePrefix= {arXiv},
  primaryClass = {cs.DS},
  url          = {https://arxiv.org/abs/2606.04227}
}
```

---

## Contact

Jason Volk
Invariant Research, Garland TX
jason@invariant.pro
[invariant.pro](https://invariant.pro)

---

## License

MIT. Use it anywhere. Embed it in your platform. The whole point is adoption.
