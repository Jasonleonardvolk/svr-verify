# SVR Alignment with NSA MCP Security Guidance

This note maps Signed Verification Receipts (SVR) and the standalone `svr-verify` verifier to the security concerns raised in recent national-security guidance on MCP and agentic AI systems. It is written for security architects evaluating whether SVR addresses a real gap.

## Reference guidance

On May 20, 2026, the NSA's Artificial Intelligence Security Center released a Cybersecurity Information Sheet, "Model Context Protocol (MCP): Security Design Considerations for AI-Driven Automation." The guidance warns that MCP adoption has outpaced security safeguards and identifies risks including uncontrolled automated actions and insufficient screening of data passing between systems.

On May 1, 2026, CISA, NSA, and allied agencies from Australia, Canada, New Zealand, and the United Kingdom jointly published "Careful Adoption of Agentic Artificial Intelligence (AI) Services," addressing cybersecurity risks of agentic AI systems that autonomously reason, plan, and execute actions by combining LLMs with external tools and data sources.

Readers should consult the primary documents. This note does not claim endorsement by any agency; it maps SVR's design to the concern categories those documents raise.

## The gap SVR addresses

Transport-layer security (TLS/mTLS) proves that bytes traveled safely between endpoints. It does not prove that an output was verified, what it was verified against, or that a downstream system can independently re-validate the evidence. In MCP chains, where model outputs, tool calls, and state mutations flow across trust boundaries, there is no standard application-layer artifact that says: this specific input was checked, by this specific verifier, with this specific result, and here is a signature you can verify yourself.

SVR is that artifact. It is a signed JSON receipt binding a verification result to input hashes, engine metadata, item-level results, and issuance metadata. The receipt is portable, vendor-neutral, and verifiable offline by any party holding the issuer's public key. `svr-verify` is the standalone MIT-licensed verifier: no engine dependency, one pip install, deterministic exit codes for CI/CD.

## Mapping to guidance concerns

**Uncontrolled automated actions.** A receipt-gated architecture requires a valid SVR covering a proposed action's precondition check before the action executes. The router semantics, including fail-closed bypass conditions, are specified in [ROUTING_DEMO.md](../ROUTING_DEMO.md).

**Insufficient input screening across system boundaries.** Each receipt binds an `input_hash` and `source_bundle_hash` to the verification result. A downstream consumer can confirm that what it received is exactly what was verified, byte for byte, before acting on it.

**Audit and accountability.** Every receipt is a timestamped, signed, item-level record of what was checked and what the verdict was. Receipts accumulate into an audit trail that third parties can validate without trusting the system that produced it. The count invariant (`items_checked == items_passed + items_failed + items_excluded`) makes silent omission of failed checks structurally detectable.

**Trust-boundary handoffs.** When an agent hands state to another agent or service, the receiving side can demand a receipt and verify it against a pinned issuer key (`svr-verify receipt.svr.json --pubkey issuer.pub`) rather than trusting the sender's claim that verification happened.

**Deterministic, reproducible checking.** The receipt's verdict is required to be a deterministic function of the recorded inputs. The same input and source bundle must always produce the same verdict. This is checkable: any auditor with the engine version and inputs can recompute.

## What SVR does not claim

SVR does not replace authorization, sandboxing, transport security, prompt-injection defenses, or source-of-truth validation. It does not prove the issuing verifier was correct, only that a specific verifier issued a specific result over specific inputs and that the artifact has not been altered since. Key trust, freshness windows, revocation, and context binding are deployment responsibilities, as detailed in the Threat Model section of the [README](../README.md).

## Relationship to CoSAI

The Coalition for Secure AI (CoSAI) workstreams address agentic AI security patterns. Our crosswalk analysis found no chain-level audit receipt schema in the existing workstream artifacts; the closest analogue is handshake-level metadata (MCP.Handshake.v1), which establishes session identity but not per-verification evidence. SVR is proposed as a complementary application-layer pattern: per-check signed evidence that survives the session and can be validated offline.

The proposed contribution is not an engine. It is a receipt-verification pattern. `svr-verify` is the standalone verifier; sigma-guard (https://github.com/Jasonleonardvolk/sigma-guard) is one implementation that issues SVRs, but any compliant verifier or agent security layer can issue receipts that downstream systems validate.

## Artifacts

- Standalone verifier: https://github.com/Jasonleonardvolk/svr-verify
- PyPI package: https://pypi.org/project/svr-verify/
- Routing demo (deterministic verification bypass): https://github.com/Jasonleonardvolk/svr-verify/blob/main/ROUTING_DEMO.md
- Sample receipts: https://github.com/Jasonleonardvolk/svr-verify/tree/main/examples/receipts
- SVR specification: https://github.com/Jasonleonardvolk/svr-verify/blob/main/docs/SVR_SPEC.md
- Issuer implementation: https://github.com/Jasonleonardvolk/sigma-guard

## Contact

Jason Volk, Invariant Research
jason@invariant.pro
