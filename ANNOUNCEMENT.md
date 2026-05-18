# Announcing the Signed Verification Receipt: Trust Infrastructure for the Agent Economy

*Portable, cryptographically signed, vendor-neutral receipts for AI verification. Because trust shouldn't be locked inside a platform.*

As AI agents move from drafting to acting, enterprises need a
verification layer that produces signed evidence of what was
checked, what failed, what was repaired, and whether the result
is safe to rely on.

Every major platform is racing to solve this. Thomson Reuters
verifies citations inside CoCounsel. Salesforce built a trust
layer into Agentforce. ServiceNow is expanding AI Control Tower.
Harvey, Legora, and dozens of others are embedding verification
into their agent workflows. Billions of dollars of combined
investment, all converging on one message: you cannot deploy
AI agents without verification.

They're right. Verification is mandatory.

But their verification dies when you leave their walled garden.
If you switch platforms, your verification history disappears.
If an agent in one system hands work to an agent in another,
the verification doesn't travel. The trust is locked to the
platform that produced it.

That is lock-in through trust infrastructure.

We think that's the wrong architecture for an interoperable
agent economy.

We built something different.

## What is a Signed Verification Receipt?

A Signed Verification Receipt (SVR) is a cryptographically signed,
point-in-time attestation that a verification engine checked a
specific artifact against specific source evidence and produced a
specific result.

An SVR is:

- **Portable.** It's a JSON file. Take it anywhere. Attach it to
  an audit package, a court filing, an agent handoff, a vendor
  assessment, a regulatory submission. It is not locked to any
  platform.

- **Signed.** Ed25519 digital signature. Unforgeable. If a single
  byte changes, the signature breaks.

- **Independently verifiable.** Anyone can verify an SVR without
  the engine that produced it. Install `svr-verify` (open source,
  MIT licensed, available on PyPI), point it at the receipt, and
  get VALID or INVALID. No account. No API key. The public key of
  the issuer is embedded in the receipt or obtained once from a
  trusted source. After that, verification is purely local.

- **Vendor-neutral.** The SVR specification is an open standard.
  Any verification engine can issue SVRs. We publish the spec, the
  JSON schema, verifier libraries in Python, JavaScript, and Go,
  and an OpenAPI specification for the verification API. All MIT
  licensed.

## What Does an SVR Contain?

Every SVR answers five questions:

1. **What was checked?** A table of every claim, citation, control,
   constraint, or agent output that was evaluated.

2. **What failed?** Per-item verdicts with explanations.

3. **What was excluded?** Explicit scope boundaries.

4. **Is it safe to rely on?** A deterministic verdict with the
   mathematical basis for the decision.

5. **Can the receipt be independently verified?** Yes. Always.

Beyond the basics, SVRs can carry proof sketches (mathematical
explanations of WHY something failed, not just THAT it failed),
priority remediation plans (what to fix first, ordered by risk
reduction per unit effort), and assurance completion packs (the
auditor handoff: evidence to collect, owners to assign, policies
to update, closure receipt required).

Every receipt also declares its `verification_method`: whether
the engine used deterministic algebraic verification, probabilistic
LLM checking, rule-based analysis, or human review. This field
is required, not optional. The market can read it.

## Why Open?

We could have kept the receipt format proprietary. Charged per
verification. Built a walled garden just like everyone else.

We chose not to, for one reason: a proprietary receipt format is
a product. Products compete on features, price, and marketing.
An open receipt format is infrastructure. Infrastructure gets
adopted.

We want every AI platform, every agent framework, and every
enterprise governance stack to issue Signed Verification Receipts.
Not because they use our engine (though we'd welcome that), but
because every agent action should leave a receipt.

If Thomson Reuters, Salesforce, ServiceNow, Harvey, Anthropic,
or any other platform wants to issue SVRs, the specification is
public, the schema is published, and the verifier is free.

## How It Works

A verification engine (ours or anyone's) receives an artifact
and source documents. It runs a deterministic audit. It produces
an SVR with the results, signs it with Ed25519, and emits the
receipt.

The recipient can verify the receipt with a single command:

```
pip install svr-verify
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

The verification is purely mathematical. No network call. No API
key. No trust in any third party except the public key of the
issuer.

## Verticals

The SVR format is domain-agnostic. The same envelope carries
receipts for:

- Legal citation audits
- SOC 2 readiness verification
- SEC filing consistency analysis
- Healthcare compliance
- Defense source-chain audits
- Procurement and vendor risk
- AI governance compliance
- RAG grounding verification
- Scientific integrity checks
- Autonomous systems safety
- Protein structure validation
- Agent action verification

Each vertical has its own extension schema with domain-specific
fields, its own disclaimer language, and its own remediation
vocabulary. The core receipt format is shared.

One protocol. Many vertical extensions.

## The Agent Economy Needs Receipts

When a human drafts a brief, there's a signature line. When a
financial advisor recommends a trade, there's a compliance record.
When a doctor prescribes medication, there's a chart entry.

When an AI agent takes an action, there should be a receipt.

Not a log line. Not a probability score. A signed, replayable,
independently verifiable receipt showing what was checked, what
failed, and whether the result is safe to rely on.

That receipt should travel with the work, not die inside the
platform that produced it. That's what SVR is for.

## Get Involved

The specification, schema, and verifiers are all open source:

- **Specification**: [SVR Spec v1.0](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/SVR_SPEC_v1.txt)
- **JSON Schema**: [svr_schema_v1.json](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/svr_schema_v1.json)
- **Python verifier**: `pip install svr-verify` ([PyPI](https://pypi.org/project/svr-verify/))
- **JavaScript verifier**: [js/svr-verify.js](https://github.com/Jasonleonardvolk/svr-verify/tree/main/js)
- **Go verifier**: [go/svr.go](https://github.com/Jasonleonardvolk/svr-verify/tree/main/go)
- **OpenAPI spec**: [openapi.yaml](https://github.com/Jasonleonardvolk/svr-verify/blob/main/openapi.yaml)
- **How to Read an SVR**: [Guide](https://github.com/Jasonleonardvolk/svr-verify/blob/main/HOW_TO_READ_AN_SVR.md)

If you build a verification engine and want to issue SVRs,
implement the spec and publish your public key. That's it.

If you receive SVRs and want to verify them, install the
verifier. One command. MIT licensed. Works offline.

If you want to integrate SVR verification into your platform,
the OpenAPI spec defines the API.

## The Line

Do not pay for another AI answer. Pay for a receipt proving
whether the answer is safe to rely on.

---

*Invariant Research, 2026. invariant.pro*

*The Signed Verification Receipt (SVR) specification is an open
standard. The svr-verify tool is MIT licensed.*

*The SATYA engine that produces SVRs is a commercial product of
Invariant Research. Patent pending.*
