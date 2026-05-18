# svr-verify

Standalone verifier for **Signed Verification Receipts (SVR)**.

No SATYA engine required. No SIGMA dependency. Just the receipt and the public key.

## Install

```
pip install svr-verify
```

## Verify a Receipt

### Command Line

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

### Machine-Readable Output

```
svr-verify receipt.svr.json --json
```

### CI/CD Integration

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

### Low-Level API

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

## What It Checks

1. **Signature**: Recomputes the canonical serialization per SVR Spec Section 4, then verifies the Ed25519 signature against the embedded public key.

2. **Structure**: Validates all 22 required fields, the count invariant (`items_checked == items_passed + items_failed + items_excluded`), per-item required fields, and enum constraints.

3. **Canonical Hash**: Produces a SHA-256 digest of the canonical payload for fingerprinting.

## What Is an SVR?

A Signed Verification Receipt is a cryptographically signed, point-in-time attestation that a verification engine audited a specific input against specific sources and produced a specific result.

SVRs are:
- **Portable**: not locked to any platform
- **Signed**: Ed25519, unforgeable
- **Independently verifiable**: anyone with this library can check one
- **Vendor-neutral**: any compliant engine may issue SVRs

## Specification

- [SVR Spec v1.0](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/SVR_SPEC_v1.txt)
- [JSON Schema](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/svr_schema_v1.json)

## License

MIT. Use it anywhere. Embed it in your platform. The whole point is adoption.
