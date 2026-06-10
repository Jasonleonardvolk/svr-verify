# Building Signed Verification Receipts for AI Agents

AI agents are crossing tool boundaries. An agent drafts in one platform, reviews in another, files through a third. But the verification record stays inside whichever platform performed the check. The proof does not travel with the work.

I built an open receipt format to fix that.

## The Problem

When an AI agent produces an output, the platform may verify it internally: check citations, validate compliance, ground claims against source documents. But that verification lives inside the platform's database. Export the output, and the proof stays behind.

The downstream user, the auditor, the regulator, the insurer, all receive the work product with no independently verifiable evidence that it was checked.

## The Format: SVR (Signed Verification Receipt)

An SVR is a JSON file, signed with Ed25519, that carries the full audit result:

```json
{
  "svr_version": "1.0",
  "receipt_id": "SATYA-20260518-4C2388CC",
  "receipt_type": "compliance",
  "verdict": "contradicted",
  "items_checked": 12,
  "items_passed": 7,
  "items_failed": 5,
  "items_excluded": 0,
  "verification_method": "deterministic_algebraic",
  "verification_parameters": {
    "parameter_count": 0,
    "deterministic_replay": true,
    "gpu_required": false,
    "ml_models_used": 0
  },
  "checked_items": [
    {
      "item_id": 1,
      "claim_or_authority": "CC6.1 Access Control",
      "verdict": "PASS",
      "reason": "Evidence covers criterion"
    }
  ],
  "public_key": "ab7f1a49...",
  "signature": "c4754d58...",
  "signature_status": "VALID"
}
```

The `verification_method` field is required. It declares whether the engine used deterministic math, an LLM, a rule engine, or human review. That field is what makes receipts from different engines comparable.

## Install the Verifier

```bash
pip install svr-verify
```

## Verify a Receipt

```bash
svr-verify receipt.svr.json
```

Output:
```
SVR Verification Report
  Receipt ID:      SATYA-20260518-4C2388CC
  Verdict:         contradicted
  Items Checked:   12
  Items Passed:    7
  Items Failed:    5
  Signature:       VALID
  Structure:       VALID
  RESULT: VALID
```

## Python API

```python
from svr_verify import verify

result = verify("receipt.svr.json")
print(result["valid"])            # True/False
print(result["signature_valid"])  # True/False
print(result["structure_errors"]) # [] if clean
```

## How Signing Works

The canonical serialization is deterministic:
1. Remove excluded fields (signature, timing data, presentation fields)
2. Sort all keys recursively
3. Serialize with compact JSON (no spaces)
4. UTF-8 encode
5. Sign with Ed25519

Any implementation that follows these rules produces identical bytes. That is what makes cross-platform verification work.

```python
import json
from nacl.signing import SigningKey

EXCLUDED = {"signature", "signature_status", "receipt_status",
            "verify_url", "latency_ms", "total_time_ms"}

def canonical_bytes(receipt):
    filtered = {k: v for k, v in receipt.items() if k not in EXCLUDED}
    def sort_r(obj):
        if isinstance(obj, dict):
            return {k: sort_r(v) for k, v in sorted(obj.items())}
        if isinstance(obj, list):
            return [sort_r(x) for x in obj]
        return obj
    return json.dumps(
        sort_r(filtered), sort_keys=True,
        separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")

key = SigningKey.generate()
payload = canonical_bytes(receipt)
signed = key.sign(payload)
receipt["signature"] = signed.signature.hex()
receipt["public_key"] = bytes(key.verify_key).hex()
```

*Simplified example; the [package implementation](https://github.com/Jasonleonardvolk/svr-verify) is the source of truth for canonical serialization.*

## Issuing SVRs From Your Own Engine

Any verification engine can issue SVRs. The prefix in the receipt_id is issuer-defined (SATYA-, TR-, HARVEY-, YOUR_ENGINE-). The verifier accepts any prefix. The standard is vendor-neutral.

Full adoption guide: [PLATFORM_ADOPTION_GUIDE.md](https://github.com/Jasonleonardvolk/svr-verify/blob/main/PLATFORM_ADOPTION_GUIDE.md)

## What Is Next

An append-only transparency log for receipts, modeled on Certificate Transparency and modern Static CT-style logs: Merkle tree inclusion proofs, signed checkpoints, witness cosigning. The log stores only receipt hashes (content stays private). 102 tests passing on that layer now.

## Links

- **Repo**: [github.com/Jasonleonardvolk/svr-verify](https://github.com/Jasonleonardvolk/svr-verify)
- **PyPI**: [pypi.org/project/svr-verify](https://pypi.org/project/svr-verify/)
- **Spec**: [SVR_SPEC_v1.txt](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/SVR_SPEC_v1.txt)
- **Guide**: [How to Read an SVR](https://github.com/Jasonleonardvolk/svr-verify/blob/main/HOW_TO_READ_AN_SVR.md)

MIT licensed. The whole point is adoption.

---

Tags: #opensource #python #security #ai #compliance
