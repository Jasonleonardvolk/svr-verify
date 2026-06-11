# MCP T9 Receipt Conformance Capsule

This capsule is an independent implementation artifact from Invariant Research. It is not an official CoSAI, OASIS, or MCP document.

It demonstrates a mechanism-neutral receipt-backed verification pattern for MCP responses crossing a T9-style trust boundary. SVR is used here as one concrete receipt profile via the IANA-registered media type `application/vnd.svr.receipt+json`.

The goal is simple: an MCP host, gateway, scanner, or policy layer should be able to determine whether a response is receipt-backed, whether the receipt binds to the response hash, whether the signature is valid, and whether the verdict permits downstream reliance.

## Vendor-neutral bright line

This capsule demonstrates a receipt-backed MCP trust-boundary pattern.

SVR is the receipt profile used in these examples. SIGMA is one possible producer of SVR receipts. Neither SIGMA nor Invariant Research is required for the pattern itself.

Any conforming verifier can evaluate a receipt if it can:

1. Parse the receipt media type.
2. Validate the receipt schema.
3. Recompute and compare the bound response hash.
4. Verify the receipt signature against a trusted verifier key.
5. Interpret the receipt verdict according to local host policy.

This repository does not claim CoSAI, OASIS, or MCP endorsement. It is an independent implementation artifact intended to make receipt-backed T9 verification concrete and reviewable.

## CoSAI MCP threat-taxonomy mapping

| CoSAI MCP category | Concern | Receipt-backed interpretation |
|---|---|---|
| MCP-T6: Missing Integrity/Verification Controls | The MCP response or resource lacks a reliable verification artifact. | Bind the response hash, verifier identity, policy version, verdict, and signature into an SVR receipt. |
| MCP-T9: Trust Boundary and Privilege Design Failures | A downstream system relies on an output crossing a trust boundary without enough evidence. | Evaluate the receipt at the response boundary before the host allows, rejects, quarantines, or escalates the output. |
| MCP-T12: Insufficient Logging, Monitoring, and Auditability | The system cannot later prove what happened, what was checked, or why the host acted. | Store the receipt or receipt hash as an audit object tied to the host action. |

## Run the conformance cases

```
cd examples\mcp-t9-conformance-capsule
.\verify-all.ps1
```

Or verify individual receipts:

```
svr-verify receipt.pass.svr.json
svr-verify receipt.fail.svr.json
svr-verify receipt.invalid-signature.svr.json
```

## Host action model

A relying host SHOULD NOT treat receipt verification as only a binary allow/reject decision.

| Action | Meaning | Typical use |
|---|---|---|
| allow | Receipt is valid, verdict permits downstream reliance, and local policy accepts the verifier. | Low-risk or verified workflow continuation. |
| quarantine | Receipt is valid but the verdict, policy, evidence, verifier trust, or risk level requires review. | Human review queue, SOC queue, compliance review, legal review, agent supervisor queue. |
| reject | Receipt is invalid, missing required bindings, signed by an untrusted key, or contradicts local policy. | Block output or prevent tool result from being consumed downstream. |
| audit_only | Receipt is stored for traceability, but no enforcement action is taken. | Low-risk monitoring, migration mode, brownfield deployments. |
| reverify | Host asks another verifier or newer policy version to evaluate the response. | Stale policy, unknown verifier, high-value action, conflicting receipts. |

## Why quarantine matters

Quarantine is the preferred default for many enterprise MCP deployments because it avoids two bad extremes: blindly allowing unverified or contradicted agent output, and automatically blocking business workflows that may require human judgment.

A receipt-backed quarantine state gives the reviewer a compact evidence packet: the response, the receipt, the verdict, the evidence references, the obstruction or failure reason, the verifier identity, and the signature status. See `quarantine-record.example.json` for the shape of a quarantine record.

## Expected host behavior

| Case | Receipt state | Expected host behavior |
|---|---|---|
| PASS receipt, valid signature, matching response hash | Verified | Allow or rely according to local policy |
| FAIL receipt, valid signature, matching response hash | Verified failure | **Quarantine** by default; route to review queue |
| Invalid signature | Untrusted artifact | Reject receipt; do not treat response as verified |
| Wrong response hash | Receipt does not bind to output | Reject or quarantine |
| Missing receipt | No verification evidence | Treat as unverified; apply local risk policy |
| Unknown verifier key | Cannot establish trust | Reject receipt or require manual trust approval |
| Expired policy/version | Stale verification | Reverify or quarantine |

## What this capsule contains

| File | Purpose |
|---|---|
| `response.pass.json` | MCP response with internally consistent claims |
| `response.fail.json` | MCP response with structurally contradictory claims |
| `receipt.pass.svr.json` | SVR receipt: verdict PASS, binds to response.pass.json hash |
| `receipt.fail.svr.json` | SVR receipt: verdict FAIL, binds to response.fail.json hash |
| `receipt.invalid-signature.svr.json` | SVR receipt: structurally valid, but signature is garbage |
| `receipt.wrong-response-hash.svr.json` | SVR receipt: structurally valid, but input_hash does not match any response |
| `quarantine-record.example.json` | Example quarantine record: what the host writes when routing a FAIL to review |
| `expected-behavior.json` | Machine-readable conformance matrix |
| `trust-boundary-trace.json` | Lifecycle trace: response, hash, gate, receipt, verify, host action |
| `verify-all.ps1` | PowerShell runner for all four cases |

## Trust boundary flow

```
MCP response
  -> trust boundary
  -> receipt detected
  -> response hash checked
  -> signature checked
  -> verdict evaluated
  -> host action selected:
       PASS             -> allow or audit
       FAIL             -> quarantine by default
       INVALID SIGNATURE -> reject
       HASH MISMATCH    -> reject or quarantine
       MISSING RECEIPT  -> unverified policy path
```

## Related

- [Receipt-Backed T9 Verification for MCP Responses](../../docs/cosai-ws4-mcp-t9-receipt-backed-verification.md)
- [ROUTING_DEMO.md](../../ROUTING_DEMO.md) (deterministic verification bypass routing)
- [SVR Spec v1.0](../../docs/SVR_SPEC.md)
- [JSON Schema](../../schemas/svr_schema_v1.json)
