# svr-verify

[![PyPI](https://img.shields.io/pypi/v/svr-verify.svg)](https://pypi.org/project/svr-verify/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/svr-verify.svg)](https://pypi.org/project/svr-verify/)

Standalone verifier for **Signed Verification Receipts (SVR)**.

Deterministic verification receipts for AI systems: CPU-only, Ed25519-signed, reproducible, and independently verifiable. No SATYA engine required. No SIGMA dependency. Just the receipt and the public key.

**Benchmark:** 5M vertices, ~15M streaming edits, 35 us median lazy update latency, zero measured drift at synchronization.

---

## What a receipt looks like

```json
{
  "svr_version": "1.0",
  "receipt_id": "SIGMA-20260610-A3C9E7B2",
  "receipt_type": "agent",
  "mode": "full_verification",
  "input_hash": "a3c9e7b201f84d6e",
  "source_bundle_hash": "d4e7f0b2c5a8d1e4",
  "verdict": "verified",
  "safe_to_rely": true,
  "items_checked": 4,
  "items_passed": 4,
  "items_failed": 0,
  "items_excluded": 0,
  "timestamp_utc": "2026-06-10T12:00:00Z",
  "engine_version": "sigma-0.9.0",
  "verification_method": "deterministic_algebraic",
  "public_key": "ed25519 hex",
  "signature": "ed25519 hex"
}
```

Full receipts also carry per-item detail in `checked_items`. See [examples/receipts/](examples/receipts/) for complete PASS and FAIL samples. IANA-registered media type: [`application/vnd.svr.receipt+json`](https://www.iana.org/assignments/media-types/application/vnd.svr.receipt+json). File extension: `.svr.json`.

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
pip install pytest
python -m pytest tests/
python examples\verify_receipt.py examples\receipts\sample_pass.svr.json --sign
```

Output of the last command:

```
Generating Ed25519 keypair...
Signed receipt written to: examples\receipts\sample_pass.signed.svr.json

============================================================
SVR Verification Report
============================================================

  Receipt ID:      SIGMA-20260610-A3C9E7B2
  SVR Version:     1.0
  Receipt Type:    agent
  Verdict:         verified
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

## Verify a receipt

### Command line

```
svr-verify receipt.svr.json
svr-verify receipt.svr.json --pubkey issuer.pub
svr-verify receipt.svr.json --json
svr-verify receipt.svr.json --quiet
```

If the receipt embeds an issuer public key, `svr-verify` can verify directly. If your deployment pins issuer keys out-of-band, pass `--pubkey` with either a hex-encoded Ed25519 public key or a path to a file containing one. When a pinned key is supplied, the signature is verified against the pinned key, and any embedded key must match it; a mismatch fails closed. **Pinned keys are recommended for production trust decisions.**

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
result = verify("receipt.svr.json", pubkey="issuer.pub")

print(result["valid"])            # True/False
print(result["signature_valid"])  # True/False
print(result["pinned_key_used"])  # True if out-of-band key supplied
print(result["structure_errors"]) # [] if clean
```

### Low-level API

```python
import json
from svr_verify import canonical_bytes, verify_signature, validate_receipt

with open("receipt.svr.json") as f:
    receipt = json.load(f)

# Verify Ed25519 signature (embedded key)
sig_ok = verify_signature(receipt)

# Verify against a pinned issuer key
sig_ok = verify_signature(receipt, pinned_key="<hex>")

# Validate structure (required fields, count invariant)
errors = validate_receipt(receipt)

# Get canonical byte sequence (what was signed)
payload = canonical_bytes(receipt)
```

---

## What it checks

1. **Signature**: Recomputes the canonical serialization per SVR Spec Section 4, then verifies the Ed25519 signature against the embedded public key or a pinned issuer key.

2. **Structure**: Validates all 22 required fields, the count invariant (`items_checked == items_passed + items_failed + items_excluded`), per-item required fields, and enum constraints.

3. **Canonical Hash**: Produces a SHA-256 digest of the canonical payload for fingerprinting.

The test suite in [tests/](tests/) covers valid-receipt acceptance, tamper rejection, missing-field rejection, canonicalization stability under key reordering, pinned-key mismatch rejection, and CLI exit-code contracts.

---

## Threat model

`svr-verify` checks whether an SVR receipt is structurally valid and whether its Ed25519 signature verifies over the canonical payload.

It does not prove that the issuing verifier was correct, that the source extraction was correct, that the public key is trusted, or that the receipt is fresh under a deployment's replay policy. Deployments must establish key trust (pinned keys via `--pubkey` are the supported mechanism), freshness windows, revocation policy, and context-binding rules.

In other words: `svr-verify` verifies the receipt artifact. It does not replace authorization, sandboxing, TLS/mTLS, prompt-injection defenses, or source-of-truth validation.

Security reports: see [SECURITY.md](SECURITY.md).

---

## Why this matters for MCP

MCP lets agentic systems chain model outputs, tool calls, API actions, and downstream workflows. Transport security alone does not prove that an output was verified, that it was bound to a specific context, or that a downstream system can independently validate the evidence.

SVR provides an application-layer receipt: a signed JSON artifact binding a verification result to input hashes, context, engine metadata, and issuance metadata. `svr-verify` is the standalone verifier for that artifact.

Alignment with recent NSA and joint-agency guidance on MCP and agentic AI security: [docs/NSA_MCP_SECURITY_ALIGNMENT.md](docs/NSA_MCP_SECURITY_ALIGNMENT.md)

Receipt-based routing (memoizing repeated deterministic checks with fail-closed bypass conditions): [ROUTING_DEMO.md](ROUTING_DEMO.md)

---

## MCP / CoSAI WS4 alignment

SVR is designed as a receipt-backed verification pattern for AI and MCP trust boundaries. The repo includes an independent implementation note mapping SVR to MCP T9-style response verification, and a conformance capsule with test vectors any MCP host, gateway, or reviewer can run:

- [Receipt-Backed T9 Verification for MCP Responses](docs/cosai-ws4-mcp-t9-receipt-backed-verification.md)
- [Conformance capsule](examples/mcp-t9-conformance-capsule/) (responses, receipts, expected host behavior, PowerShell runner)

This is not an official CoSAI/OASIS document. It is intended to make the receipt pattern concrete and reviewable.

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
| Cells in final state | 25,473 |
| Algorithm | O(1) amortized incremental sheaf cohomology |
| Hardware | Intel i9-13900H, 64 GB RAM |
| GPU required | No |
| ML required | No |

Full methodology: [docs/BENCHMARK_5M.md](docs/BENCHMARK_5M.md)

---

## How SVR works

An SVR is a cryptographically signed, point-in-time attestation that a verification engine audited a specific input and produced a specific result.

The verification flow:

1. The issuing engine receives an input (for SIGMA: a graph state of vertices, edges, and claims).
2. It runs its deterministic checks (for SIGMA: sheaf cohomology over the graph to detect structural contradictions).
3. It emits a receipt containing the verdict, item-level results, and metadata.
4. The receipt is canonicalized per SVR Spec Section 4 and signed with Ed25519.
5. Anyone with `svr-verify` can independently check the signature and structure.

SVRs are:

- **Portable** - not locked to any platform or vendor
- **Signed** - Ed25519, unforgeable
- **Independently verifiable** - anyone with this library can check one
- **Vendor-neutral** - any compliant engine may issue SVRs
- **IANA-registered** - media type `application/vnd.svr.receipt+json`
- **Deterministic** - same input and source bundle, same verdict

---

## How SIGMA verifies graph-state consistency

SIGMA uses cellular sheaf cohomology to determine whether local claims attached to graph nodes can be assembled into one consistent global assignment. If they cannot, SIGMA reports a structural obstruction with a mathematical proof.

The key insight: sheaf cohomology group H^1 measures obstructions to global consistency. If H^1 is nontrivial, the graph contains a structural contradiction that no local fix can resolve. This is not a statistical guess. It is a deterministic algebraic invariant.

SIGMA's incremental architecture achieves O(1) amortized cost per streaming edit by maintaining a cellular decomposition and only recomputing affected cells when the graph changes. At 5M vertices with ~15M streaming edits, the median lazy update latency is 35 microseconds with zero measured drift between lazy and full-recompute results.

For the full theoretical treatment, see [arXiv:2606.04227](https://arxiv.org/abs/2606.04227).

---

## Specification

- [SVR Spec v1.0](docs/SVR_SPEC.md)
- [How to Read an SVR](docs/HOW_TO_READ_AN_SVR.md)
- [Platform Adoption Guide](docs/PLATFORM_ADOPTION_GUIDE.md)
- [Agent State Verification](docs/AGENT_STATE_VERIFICATION.md)
- [NSA MCP Security Alignment](docs/NSA_MCP_SECURITY_ALIGNMENT.md)
- [IANA Registration](docs/IANA_REGISTRATION.txt)
- [JSON Schema](schemas/svr_schema_v1.json) (canonical copy: [sigma repo](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/svr_schema_v1.json))

Implementations: [Python](svr_verify/) | [JavaScript](js/) | [Go](go/)

---

## Links

- **Medium:** [Streaming Exact Topology at 5 Million Vertices](https://medium.com/@jasonlvolk/streaming-exact-topology-at-5-million-vertices-how-we-made-sheaf-cohomology-o-1-per-edit-1420e7c76b7a)
- **arXiv:** [arXiv:2606.04227](https://arxiv.org/abs/2606.04227)
- **PyPI:** [svr-verify](https://pypi.org/project/svr-verify/)
- **Website:** [invariant.pro](https://invariant.pro)
- **sigma-guard (issuer implementation, graph DB integration):** [github.com/Jasonleonardvolk/sigma-guard](https://github.com/Jasonleonardvolk/sigma-guard)

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
