# SVR Specification v1.0

## 1. Overview

A Signed Verification Receipt (SVR) is a cryptographically signed, point-in-time attestation that a verification engine audited a specific input against specific sources and produced a specific result.

SVRs are designed to be portable, vendor-neutral, and independently verifiable. Any party with access to the receipt and the issuer's public key can verify authenticity without contacting the issuing engine.

The IANA-registered media type is `application/vnd.svr.receipt+json`.

## 2. Design principles

SVRs follow these principles:

- Determinism: the same input and source bundle must always produce the same verdict.
- Portability: receipts are self-contained JSON documents with no platform dependencies.
- Independent verifiability: verification requires only the receipt and the public key.
- Vendor neutrality: any compliant engine may issue SVRs.
- Auditability: every receipt includes item-level detail and a canonical hash.

## 3. Required fields

Every SVR must include the following 22 top-level fields:

| Field | Type | Description |
|---|---|---|
| svr_version | string | Specification version (currently "1.0") |
| receipt_id | string | Unique identifier, format: PREFIX-YYYYMMDD-HASH8 |
| receipt_type | string | Domain adapter label (e.g. "compliance", "agent", "rag") |
| mode | string | Verification mode (e.g. "full_verification", "incremental") |
| receipt_status | string | "evaluation" or "production" |
| input_hash | string | SHA-256 hash of the input that was verified |
| source_bundle_hash | string | SHA-256 hash of the source/reference bundle |
| verdict | string | Overall result (e.g. "verified", "unsafe_to_submit", "review_required") |
| safe_to_rely | boolean | Whether the result is safe for downstream use |
| filing_safety_status | string | "SAFE_TO_SUBMIT", "UNSAFE_TO_SUBMIT", or "REVIEW_REQUIRED" |
| reason | string | Human-readable explanation of the verdict |
| items_checked | integer | Total number of items checked |
| items_passed | integer | Number of items that passed |
| items_failed | integer | Number of items that failed |
| items_excluded | integer | Number of items excluded from checking |
| checked_items | array | Per-item detail (see Section 3.1) |
| timestamp_utc | string | ISO 8601 UTC timestamp |
| engine_version | string | Version of the issuing verification engine |
| public_key | string | Ed25519 public key (hex) or "unsigned" |
| signature | string | Ed25519 signature (hex) or empty string |
| signature_status | string | "VALID" or "UNSIGNED" |
| verification_method | string | How verification was performed (e.g. "deterministic_algebraic") |

### 3.1 Count invariant

The following invariant must hold:

    items_checked == items_passed + items_failed + items_excluded

Violations of this invariant indicate a malformed receipt.

### 3.2 Checked items

Each element of `checked_items` must include:

| Field | Type | Description |
|---|---|---|
| item_id | string | Unique identifier for this check |
| claim_or_authority | string | What was checked or cited |
| verdict | string | Result for this item |
| reason | string | Explanation |

## 4. Canonical serialization

Canonical serialization determines the byte sequence that is signed. This ensures any verifier can reproduce the exact bytes from the receipt JSON.

### 4.1 Steps

1. Start with the full receipt JSON object.
2. Remove excluded fields: `signature`, `signature_status`, `superseded_by`, `verify_url`, `receipt_status`, `latency_ms`, `retrieval_ms`, `compute_ms`, `evaluation`, `total_time_ms`.
3. Sort all keys lexicographically at every nesting level.
4. Serialize to compact JSON with no whitespace (separators: `(",", ":")`).
5. Encode as UTF-8 bytes.

### 4.2 Signing

The canonical byte sequence is signed using Ed25519. The signature (hex-encoded) is stored in the `signature` field. The public key (hex-encoded) is stored in the `public_key` field.

### 4.3 Verification

To verify a receipt:

1. Produce the canonical byte sequence (Section 4.1).
2. Decode the `public_key` from hex to 32 bytes.
3. Decode the `signature` from hex to 64 bytes.
4. Verify the Ed25519 signature over the canonical bytes using the public key.
5. Validate structural requirements (Section 3).

If both the signature and structure are valid, the receipt is VALID.

## 5. IANA registration

The media type `application/vnd.svr.receipt+json` is registered with IANA for SVR documents.

The machine-readable JSON Schema is published at [../schemas/svr_schema_v1.json](../schemas/svr_schema_v1.json).

## 6. Reference implementation

The reference implementation is available at:

- Python: https://pypi.org/project/svr-verify/
- Go: https://github.com/Jasonleonardvolk/svr-verify/tree/main/go
- JavaScript: https://github.com/Jasonleonardvolk/svr-verify/tree/main/js

## 7. License

This specification is released under the MIT license. Use it anywhere.
