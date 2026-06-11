# MCP T9 Receipt Conformance Capsule

This capsule is an independent implementation artifact from Invariant Research. It is not an official CoSAI, OASIS, or MCP document.

It demonstrates a mechanism-neutral receipt-backed verification pattern for MCP responses crossing a T9-style trust boundary. SVR is used here as one concrete receipt profile via the IANA-registered media type `application/vnd.svr.receipt+json`.

The goal is simple: an MCP host, gateway, scanner, or policy layer should be able to determine whether a response is receipt-backed, whether the receipt binds to the response hash, whether the signature is valid, and whether the verdict permits downstream reliance.

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

## Expected host behavior

| Case | Receipt state | Expected host behavior |
|---|---|---|
| PASS receipt, valid signature, matching response hash | Verified | Allow or rely according to local policy |
| FAIL receipt, valid signature, matching response hash | Verified failure | Quarantine, reject, or escalate |
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
| `expected-behavior.json` | Machine-readable conformance matrix |
| `trust-boundary-trace.json` | Lifecycle trace: response produced, hash bound, gate evaluated, receipt emitted, verified, host action |
| `verify-all.ps1` | PowerShell runner for all four cases |

## Trust boundary trace

The file `trust-boundary-trace.json` shows the lifecycle for a failing response:

1. MCP response produced
2. Response hash calculated and bound
3. Verification gate evaluates the response
4. Receipt emitted (media type: `application/vnd.svr.receipt+json`)
5. Relying party verifies receipt (signature, response hash, verdict, verifier key, policy version)
6. Host action selected (quarantine, reject, or escalate)

This is the mechanism-neutral pattern. SVR is one concrete profile; the pattern itself is independent of the receipt format.

## Related

- [Receipt-Backed T9 Verification for MCP Responses](../../docs/cosai-ws4-mcp-t9-receipt-backed-verification.md)
- [ROUTING_DEMO.md](../../ROUTING_DEMO.md) (deterministic verification bypass routing)
- [SVR Spec v1.0](../../docs/SVR_SPEC.md)
- [JSON Schema](../../schemas/svr_schema_v1.json)
