# Agent State Verification

## The problem

Production AI agents mutate state: memory graphs, execution plans, tool call histories, retrieved contexts, and generated claims. As agents become more autonomous, the state they manage grows in complexity and the consequences of inconsistency grow in severity.

The current verification approach in most systems is to use another LLM as a judge. This means checking probabilistic output with a probabilistic checker. The result is a confidence score, not a proof. It cannot be audited, reproduced, or independently verified.

## Where deterministic verification applies

Not everything an agent does can be verified deterministically. Generation quality, tone, factual accuracy against the open world, and user satisfaction are inherently subjective or require external knowledge. These are not the target.

The target is structural consistency of the state graph: do the claims stored in the agent's memory, plan, or context contradict each other? This is a graph problem, not a language problem. It has a mathematical answer.

Specifically, deterministic verification applies to:

**Agent memory graphs.** An agent stores that a customer wants annual billing. A later interaction stores that the same customer rejected annual billing. Both facts are individually valid. Together they contradict. If both are retrieved into the same context window, the agent may produce incoherent output without knowing why.

**RAG pipeline state.** Retrieved documents make claims. If those claims contradict each other or contradict the agent's existing state, the contradiction should be detected before generation, not after.

**Tool call histories.** An agent calls a tool that returns a result. A later tool call returns a conflicting result for the same entity. The state graph now contains a structural contradiction.

**Compliance and audit workflows.** A policy says all accounts require MFA. An exception register says a privileged account has no MFA. Both are valid entries. Together they represent a control contradiction.

## How SIGMA addresses this

SIGMA models the agent's state as a graph where each vertex holds a stalk (a vector space of claims) and each edge holds a restriction map (a consistency constraint between adjacent vertices). This is the mathematical structure of a cellular sheaf.

The sheaf cohomology group H^1 measures obstructions to global consistency. If H^1 is trivial (dimension zero), all local claims can be assembled into one coherent global assignment. If H^1 is nontrivial, there exist structural contradictions that no local fix can resolve.

This detection is deterministic, reproducible, and produces a proof artifact (the SVR receipt) that any third party can verify.

## What an SVR receipt proves

An SVR receipt does not prove that the agent's claims are true in the real world. It proves that the claims are internally consistent under the configured graph model.

This is the correct scope for a verification layer. Truth requires external grounding. Consistency is a structural property that can be checked mathematically.

The receipt includes:

- The verdict (consistent or contradicted)
- Item-level detail (which checks passed, which failed, and why)
- The input hash (what was checked)
- The canonical hash (fingerprint of the receipt)
- An Ed25519 signature (unforgeable attestation)

## Integration points

SVR receipts can be integrated at several points in an agent architecture:

**Pre-generation gate.** Before the agent generates a response, verify that the retrieved context is internally consistent. If contradictions are detected, flag them before generation rather than hoping the LLM notices.

**Post-mutation audit.** After the agent writes to its memory graph, verify that the new state is consistent with existing state. If the write creates a contradiction, block or flag it.

**CI/CD pipeline check.** For systems with versioned knowledge graphs, run SIGMA as a pre-commit check. Contradictory graph states are rejected before deployment.

**Compliance ledger.** In regulated domains, SVR receipts provide an auditable trail of verification decisions. Each receipt is timestamped, signed, and independently verifiable.

## What this is not

This is not a replacement for LLM evaluation, RLHF, or human review. It is a specific, narrow tool for a specific, narrow problem: detecting structural contradictions in graph state. It does that deterministically, at CPU speed, with a signed receipt.
