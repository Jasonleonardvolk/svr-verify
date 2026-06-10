# Issuing Signed Verification Receipts from Your Platform

This guide explains how any verification engine or AI platform
can issue Signed Verification Receipts (SVRs) that are
independently verifiable using the open-source svr-verify tool.

## What You Need

1. An Ed25519 key pair (for signing)
2. A verification engine that checks claims against sources
3. The SVR JSON Schema (for structural conformance)

## Minimal Implementation

### Step 1: Generate a Key Pair

```python
from nacl.signing import SigningKey

key = SigningKey.generate()
private_key_hex = key.encode().hex()
public_key_hex = key.verify_key.encode().hex()

# Store private_key_hex securely (HSM recommended for production)
# Publish public_key_hex so verifiers can check your receipts
print("Public key:", public_key_hex)
```

### Step 2: Build the Receipt

Your verification engine runs its checks and produces results.
Package them into the SVR format:

```python
import json
import hashlib
from datetime import datetime, timezone

receipt = {
    # Required envelope
    "svr_version": "1.0",
    "receipt_id": "YOUR_ENGINE-YYYYMMDD-HASH8",
    "receipt_type": "legal",  # or soc2, financial, rag, etc.
    "mode": "your_audit_mode",
    "receipt_status": "production",

    # Input provenance
    "input_hash": hashlib.sha256(input_bytes).hexdigest()[:16],
    "source_bundle_hash": "",  # hash of source documents

    # Verdict
    "verdict": "verified",  # or review_required, unsafe_to_submit
    "safe_to_rely": True,
    "filing_safety_status": "SAFE_TO_SUBMIT",
    "reason": "All checks passed.",

    # Counts
    "items_checked": len(results),
    "items_passed": sum(1 for r in results if r.passed),
    "items_failed": sum(1 for r in results if not r.passed),
    "items_excluded": 0,

    # Per-item results
    "checked_items": [
        {
            "item_id": i + 1,
            "claim_or_authority": r.claim,
            "verdict": "PASS" if r.passed else "FAIL",
            "reason": r.explanation,
        }
        for i, r in enumerate(results)
    ],

    # Engine provenance
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "engine_version": "your_engine/1.0.0",

    # Signature (filled in Step 3)
    "public_key": public_key_hex,
    "signature": "",
    "signature_status": "UNSIGNED",
}
```

### Step 3: Sign the Receipt

Use the canonical serialization from the SVR spec:

```python
# Canonical serialization: SVR Spec Section 4.1
EXCLUDED_FIELDS = {
    "signature", "signature_status", "superseded_by",
    "verify_url", "receipt_status",
    "latency_ms", "retrieval_ms", "compute_ms",
}

def sort_keys_recursive(obj):
    if isinstance(obj, dict):
        return {k: sort_keys_recursive(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [sort_keys_recursive(item) for item in obj]
    return obj

def canonical_bytes(receipt):
    filtered = {k: v for k, v in receipt.items() if k not in EXCLUDED_FIELDS}
    sorted_obj = sort_keys_recursive(filtered)
    return json.dumps(sorted_obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

# Sign
from nacl.signing import SigningKey

signing_key = SigningKey(bytes.fromhex(private_key_hex))
message = canonical_bytes(receipt)
signed = signing_key.sign(message)

receipt["signature"] = signed.signature.hex()
receipt["signature_status"] = "VALID"
```

### Step 4: Emit the Receipt

```python
with open("receipt.svr.json", "w") as f:
    json.dump(receipt, f, indent=2)
```

### Step 5: Verify It Works

```bash
pip install svr-verify
svr-verify receipt.svr.json
```

Expected output:
```
  Signature:       VALID
  Structure:       VALID
  RESULT: VALID
```

## Required Fields

The following 22 fields are required for a valid SVR:

| Field | Type | Description |
|-------|------|-------------|
| svr_version | string | "1.0" |
| receipt_id | string | Unique ID, format: PREFIX-YYYYMMDD-HASH8 |
| receipt_type | string | Domain (legal, soc2, financial, etc.) |
| mode | string | Audit mode identifier |
| receipt_status | string | "evaluation" or "production" |
| input_hash | string | SHA-256 of input, 16 hex chars |
| source_bundle_hash | string | SHA-256 of sources, or "" |
| verdict | string | Overall result |
| safe_to_rely | bool/null | Safe to use? |
| filing_safety_status | string | SAFE/UNSAFE/REVIEW |
| reason | string | Explanation |
| items_checked | int | Total items |
| items_passed | int | Passed count |
| items_failed | int | Failed count |
| items_excluded | int | Excluded count |
| checked_items | array | Per-item results |
| timestamp_utc | string | ISO 8601 |
| engine_version | string | Your engine version |
| public_key | string | Ed25519 public key hex |
| signature | string | Ed25519 signature hex |
| signature_status | string | "VALID" or "UNSIGNED" |

The count invariant MUST hold:
items_checked = items_passed + items_failed + items_excluded

## Optional but Recommended

- **proof_sketches**: Explain WHY failures occurred
- **remediation_summary**: Actionable repair plan
- **sheaf_metrics**: Mathematical verification measurements
- **constraint_results**: Per-constraint detail
- **vertical_extension**: Domain-specific data

## Publishing Your Public Key

For verifiers to trust your receipts, publish your public key:

1. On your website at a stable URL
2. In your API documentation
3. In a public key registry (when available)

Verifiers should pin to known public keys rather than accepting
any key presented in the receipt.

## Testing Against the Schema

```bash
pip install jsonschema
python -c "
import json, jsonschema
schema = json.load(open('svr_schema_v1.json'))
receipt = json.load(open('receipt.svr.json'))
jsonschema.validate(receipt, schema)
print('Schema valid')
"
```

## Need Help?

- Specification: https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/SVR_SPEC_v1.txt
- JSON Schema: https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/svr_schema_v1.json
- Verifier source: https://github.com/Jasonleonardvolk/svr-verify
- OpenAPI: https://github.com/Jasonleonardvolk/svr-verify/blob/main/openapi.yaml
- Contact: invariant.pro

---

Signed Verification Receipt (SVR) v1.0 | Open Standard | MIT Licensed
