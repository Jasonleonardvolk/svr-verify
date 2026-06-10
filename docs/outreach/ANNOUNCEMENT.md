# Your AI Agent Just Took an Action. Where Is the Receipt?

*Trust infrastructure for the agent economy.*

Last week, Anthropic connected Claude to Westlaw, DocuSign, Everlaw, and 20 other legal platforms. Thomson Reuters rebuilt CoCounsel on Claude's agent SDK. Harvey hit an $11 billion valuation. Salesforce made Agentforce the center of its AI strategy. ServiceNow is expanding AI Control Tower.

Every major platform is moving toward internal verification, validation, grounding, review, or audit trails.

Here is the question nobody answered last week:

When the agent acts, where is the receipt?

Not the log line inside the platform. Not the confidence score the model assigned to itself. The receipt. The signed, portable, independently verifiable document that proves what was checked, what failed, what was repaired, and whether the result was safe to rely on.

The one you hand to opposing counsel. The one the auditor asks for. The one your insurer reads when adjusting your premium. The one the regulator demands when enforcement starts.

That receipt does not exist as a portable, vendor-neutral layer today. Not because verification is hard. Every major platform now verifies. The problem is that their verification lives inside their walls. The moment your work product leaves the platform, the verification disappears. You are holding an AI-generated artifact with no proof that anyone checked it.

Switch from CoCounsel to Harvey? Your verification history is gone. Export a brief and send it to co-counsel at another firm? They cannot confirm it was verified. Hand an agent's output from one system to an agent in another? The trust does not transfer.

That is not a bug in their product. It is their business model. Lock-in through trust infrastructure.

## What If the Proof Traveled With the Work?

Imagine a different model. Every time a verification engine checks an artifact, it produces a receipt. That receipt is a JSON file, signed with Ed25519, carrying the full audit result. It travels with the work product. Anyone who receives it can verify the signature with a single command, offline, without contacting the platform that issued it.

The receipt answers five questions:

What was checked? Every claim, citation, control, constraint, or agent output that was evaluated, listed individually with its verdict.

What failed? Specific items, with explanations of why. Not "something looks off." The mathematical structure of the contradiction, the energy localization showing exactly where the problem sits, and a plain-language explanation a professional can act on.

What is the repair path? A priority-ordered remediation plan. What to fix first, ranked by how much risk each fix eliminates. Evidence to collect. Owners to assign. Policies to update. Not "fix this." The Monday morning work queue.

Is it safe to rely on? A deterministic yes, no, or review-required, with the basis for the decision.

Can you verify it independently? Always. One command: `pip install svr-verify`. Point it at the receipt. VALID or INVALID. No account. No API key. No internet connection after install.

That is what a Signed Verification Receipt is.

## The Uncomfortable Field

Every SVR carries a required field called `verification_method`. It declares how the verification was performed.

`deterministic_algebraic`: zero probabilistic components. Same input, same result, every time. Replayable.

`probabilistic_llm`: an LLM is somewhere in the verification loop. Not replayable. Different run, potentially different result.

`deterministic_rule_based`: traditional rule engine. Replayable. No ML.

`human_review`: a person checked it. Not replayable by definition.

This field is not optional. Every receipt declares its method. The market reads it. The insurer reads it. The regulator reads it.

When two receipts sit side by side on an auditor's desk, one saying `deterministic_algebraic` with `parameter_count: 0` and `deterministic_replay: true`, and the other saying `probabilistic_llm` with `parameter_count: 70000000000` and `deterministic_replay: false`, the risk calculus is visible without opening either document.

Nobody has to argue about which approach is better. The receipts speak for themselves.

## Why Open?

A proprietary receipt format is a product. Products compete on features, price, and marketing. An open receipt format is infrastructure. Infrastructure gets adopted.

The SVR specification is published. The JSON schema is published. The Python verifier is live on PyPI. JavaScript and Go
verifier libraries are in the repository for cross-platform
verification across standard enterprise stacks. An OpenAPI spec defines the verification API. Everything is MIT licensed.

Any verification engine can issue SVRs. Thomson Reuters could issue them from CoCounsel. Harvey could issue them from their platform. Salesforce could issue them from Agentforce. The specification does not care who built the engine. It cares that the receipt is signed, structured, and verifiable.

The receipt ID prefix is issuer-defined. SATYA receipts start with `SATYA-`. A Thomson Reuters receipt would start with `TR-`. A Harvey receipt would start with `HARVEY-`. The verifier accepts any prefix. The standard is genuinely vendor-neutral.

We do not want to be another platform. We want to be the receipt layer underneath all of them.

## The Agent Economy Needs This

When a human lawyer drafts a brief, there is a signature line. When a financial advisor recommends a trade, there is a compliance record. When a doctor prescribes medication, there is a chart entry.

When an AI agent takes an action, there should be a receipt.

Not a log line that lives inside the platform's database. A signed, portable, independently verifiable receipt that travels with the work product and can be checked by anyone who touches it downstream.

As agents hand work to other agents, as outputs cross platform boundaries, as regulatory frameworks like the Colorado AI Act and EU AI Act Article 15(4) begin demanding evidence of "reasonable care" and "accuracy measures," the question will not be whether you verified. It will be whether you can prove it.

A receipt is proof. A log line is a claim.

## Where It Works

The SVR format is domain-agnostic. The same envelope carries receipts across every vertical where AI output carries professional or regulatory consequences:

Legal filings. SOC 2 readiness. SEC disclosures. Healthcare protocols. Defense workflows. Vendor risk assessments. AI governance compliance. RAG grounding verification. Scientific integrity. Autonomous systems safety.

Each vertical has its own extension schema with domain-specific fields, remediation vocabulary, and disclaimer language. The core receipt format is shared. One protocol. Many vertical extensions.

## The Numbers

The SATYA engine produces SVR receipts in 18.6 ms. Twelve constraints checked. Five obstruction-producing failures detected. Five proof sketches with Dirichlet energy localization. Five priority-ordered repairs. Zero Purity Gate violations. Valid Ed25519 signature. Valid receipt structure. Verified independently by a standalone tool with zero engine dependencies.

That is not a benchmark on a cluster. That is a laptop.

## Try It

Verify a receipt:
```
pip install svr-verify
svr-verify receipt.svr.json
```

Read the specification:
[SVR Spec v1.0](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/SVR_SPEC_v1.txt)

Browse the code:
[github.com/Jasonleonardvolk/svr-verify](https://github.com/Jasonleonardvolk/svr-verify)

Read the guide:
[How to Read an SVR](https://github.com/Jasonleonardvolk/svr-verify/blob/main/HOW_TO_READ_AN_SVR.md)

## The Line

Do not pay for another AI answer. Pay for a receipt proving whether the answer is safe to rely on.

Every agent action should leave a receipt.

---

*Invariant Research, 2026. [invariant.pro](https://invariant.pro)*

*The Signed Verification Receipt (SVR) specification is an open standard. The svr-verify tool is MIT licensed. The SATYA engine that produces SVRs is a commercial product of Invariant Research.*
