# Receipt-Backed T9 Verification for MCP Responses

A mechanism-neutral implementation note for MCP trust-boundary verification, with SVR as one concrete receipt profile.

## Status

This note is independent research from Invariant Research. It is not an official CoSAI, OASIS, MCP, or WS4 document. It is intended as a mechanism-neutral contribution to the discussion around MCP trust-boundary verification. SVR is presented as one concrete receipt profile, not as the exclusive implementation of the T9 principle.

## Problem

MCP responses cross trust boundaries. A model or tool produces an output; a downstream system, agent, or user relies on it. Between production and reliance, there is often no structured evidence that the output was checked, authorized, consistent, or safe to use.

Transport-layer security (TLS/mTLS) proves the bytes traveled safely. It does not prove the content was verified. Authorization frameworks prove the caller was permitted to ask. They do not prove the answer was checked before it was consumed.

The gap is application-layer verification evidence at the response trust boundary.

## Standards context

Several recent documents identify this gap:

**CoSAI WS4** (Coalition for Secure AI, OASIS Open). WS4's stated purpose is to research and develop secure design patterns for AI-based agentic systems, including threat models, high-level secure design patterns, infrastructure impacts, and agent integration needs. The MCP Security paper coordinates with Anthropic and the MCP maintainer community to keep recommendations practical and implementable.

**NSA Artificial Intelligence Security Center**. The May 2026 Cybersecurity Information Sheet on MCP warns that adoption has outpaced security safeguards and identifies risks including uncontrolled automated actions and insufficient screening of data passing between systems. The guidance says organizations should clearly define trust boundaries between MCP components.

**IANA media type registry**. The media type `application/vnd.svr.receipt+json` is registered with IANA for Signed Verification Receipts (contact: Jason_Volk, Invariant Research). This gives the receipt profile an external standards anchor independent of any single platform or vendor.

## Proposed pattern: receipt-backed T9 verification

T9 identifies a trust-boundary problem: MCP consumers may rely on model or tool outputs without sufficient evidence that the output was checked.

A receipt-backed T9 pattern separates the principle from the mechanism:

1. The MCP response crosses a trust boundary.
2. A verification gate evaluates the response, its evidence, and its policy constraints.
3. The gate emits or checks a receipt binding the response hash, verifier identity, verification result, and signature.
4. The caller decides whether to allow, quarantine, reject, or escalate the response.
5. The audit trail stores the receipt or its hash for later review.

This pattern is mechanism-neutral. The receipt could be an SVR, an in-toto attestation, a Sigstore bundle, or a domain-specific signed JSON object. What matters is that the relying party has a structured, verifiable evidence artifact at the trust boundary.

## Minimal flow

```
MCP tool/model output
    |
    v
[Verification gate]
    |
    +---> Emit receipt (response hash, verdict, signature)
    |
    v
[Relying party]
    |
    +---> Verify receipt (signature, response binding, verdict, key trust)
    |
    +---> Host action: allow / quarantine / reject / escalate
    |
    v
[Audit log: receipt or receipt hash]
```

## SVR profile

SVR is one concrete profile for this pattern.

- **Media type**: `application/vnd.svr.receipt+json` (IANA-registered)
- **Signature**: Ed25519 over canonical JSON serialization
- **Response binding**: SHA-256 of the response content, truncated to 16 hex characters, stored in `input_hash`
- **Verdict**: Machine-readable (`verified`, `unsafe_to_submit`, `review_required`, `insufficient_data`, `citation_audit_high_risk`)
- **Item-level detail**: Each checked claim includes item_id, verdict, and reason
- **Count invariant**: `items_checked == items_passed + items_failed + items_excluded`
- **Standalone verifier**: `pip install svr-verify` (MIT, no engine dependency)
- **Pinned-key support**: `svr-verify receipt.svr.json --pubkey issuer.pub` for production trust decisions

Full specification: [SVR_SPEC.md](SVR_SPEC.md)

## Non-goals

Receipt-backed T9 verification does not replace:

- **Authorization and permissioning**: who is allowed to call what
- **Transport security (TLS/mTLS)**: whether bytes were tampered in transit
- **Sandboxing and isolation**: whether a tool can escape its boundary
- **Prompt-injection defenses**: whether the model was manipulated
- **Tool permissioning**: whether the tool was allowed to run
- **Policy engines**: whether the action is permitted by organizational policy
- **Source-of-truth validation**: whether the underlying facts are true in the real world

The receipt says: a specific verifier checked a specific output and produced a specific result. It does not say the verifier was correct, the policy was complete, or the world hasn't changed since issuance. Deployments must establish key trust, freshness windows, revocation policy, and context-binding rules.

## Discrete interoperability artifact: conformance capsule

This repository includes a small MCP T9 conformance capsule under [examples/mcp-t9-conformance-capsule](../examples/mcp-t9-conformance-capsule/).

The capsule is not a benchmark and does not claim CoSAI/OASIS endorsement. It exists to make the receipt-backed T9 pattern executable. A reviewer can inspect a response, inspect the receipt, run the verifier, and compare the observed behavior against expected host actions.

The conformance cases cover: PASS with valid signature, FAIL with valid signature, invalid signature (reject), wrong response hash (reject), and the expected-behavior matrix is machine-readable in `expected-behavior.json`.

## Open questions for CoSAI WS4 / MCP implementers

1. Should MCP trust-boundary guidance define a generic receipt pattern for high-risk responses?
2. Should receipt-backed verification be modeled as middleware, host policy, gateway policy, or response metadata?
3. What fields are the minimum necessary for downstream reliance: response hash, verifier identity, verdict, policy version, evidence references, timestamp, and signature?
4. Should receipt media types be negotiated explicitly, or carried as attached artifacts?
5. How should implementations distinguish unsupported, contradicted, unauthorized, and unverifiable responses?
6. Should receipts be stored in full, stored by hash, or optionally registered in an append-only transparency log?
7. What should be the default caller behavior when a receipt is missing, invalid, expired, or produced by an untrusted verifier?

## Example

An MCP tool returns a response about a contract. The response is hashed; a verification gate checks whether the claims in the response are internally consistent. The gate emits a receipt:

```json
{
  "svr_version": "1.0",
  "receipt_id": "SIGMA-20260611-5A089C96",
  "receipt_type": "agent",
  "input_hash": "5a089c9639a7c638",
  "verdict": "unsafe_to_submit",
  "items_checked": 3,
  "items_passed": 1,
  "items_failed": 2,
  "verification_method": "deterministic_algebraic",
  "signature_status": "UNSIGNED"
}
```

The receipt says: two of three claims contradicted each other. The relying party should quarantine, reject, or escalate. The full receipt, response, and conformance capsule are in [examples/mcp-t9-conformance-capsule/](../examples/mcp-t9-conformance-capsule/).

## References

- CoSAI WS4: https://www.coalitionforsecureai.org
- MCP Specification: https://spec.modelcontextprotocol.io
- NSA AISC MCP Security Guidance (May 2026): Cybersecurity Information Sheet
- IANA media type: `application/vnd.svr.receipt+json`
- SVR standalone verifier: https://github.com/Jasonleonardvolk/svr-verify
- SVR PyPI package: https://pypi.org/project/svr-verify/
- in-toto Attestation Framework: https://github.com/in-toto/attestation (analogous signed-evidence pattern)
