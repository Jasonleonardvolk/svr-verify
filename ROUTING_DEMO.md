# SVR Routing Demo: Deterministic Verification Bypass

This demo does not bypass safety policy, enforcement, or novel semantic judgment.

It bypasses repeated recomputation of deterministic verification checks when a signed receipt already covers the same invariant, state digest, dependency frontier, and scope.

## 1. Tasks considered

The SVR routing layer applies to a narrow set of deterministic agent-runtime checks over structured state:

- **Proposed memory / graph writes.** Before committing a write to the agent's state graph, the verifier checks whether the write introduces a structural contradiction. The check is deterministic: same graph state + same proposed write = same verdict.

- **Claim-set consistency checks.** Before committing extracted facts into a knowledge graph or memory store, the verifier checks whether the new claims are consistent with existing claims. This is a coboundary-norm computation over the affected subgraph.

- **Plan or action precondition checks.** Before executing a planned action, the verifier checks whether the action's preconditions hold against the current state. If the state has not changed since the last check, the precondition result has not changed either.

- **Local-to-global consistency after graph edits.** After a batch of edits, the verifier checks whether local consistency (each edge's restriction map is satisfied) implies global consistency (H^1 is trivial). This is the core sheaf cohomology computation.

All of these produce a binary, reproducible result given the same inputs. None of them involve semantic judgment, generation quality, or open-world factual grounding.

## 2. Verification tasks bypassed

Only repeated deterministic checks are bypassed. The first time a condition appears, the verifier runs the full computation and emits a Signed Verification Receipt (SVR). The receipt records the verdict, the input hash, the state digest, the dependency frontier, and the scope of the check.

If the agent later retries, replans, or asks the same verification question again, the router can reuse the receipt instead of recomputing the same check or asking the model to re-check it.

This is memoization of deterministic verification with a signed, auditable receipt. The receipt is the cache entry. The signature is the integrity guarantee.

In an IFC-style planner, a receipt would cover a specific permitted transition, label-flow result, or state/action check, and remain reusable only while the relevant state and policy frontier are unchanged.

## 3. Bypass conditions

The router bypasses only when ALL of the following conditions hold:

1. **Receipt signature verifies.** The Ed25519 signature on the receipt is valid against the issuer's public key.
2. **Invariant / policy / verifier version matches.** The receipt was issued by the same version of the verification engine with the same policy configuration.
3. **State digest matches or intervening edits are outside the receipt dependency frontier.** Either the graph state has not changed at all, or the changes are in a region of the graph that does not affect the receipt's verdict.
4. **Requested check is covered by the receipt scope.** The query being asked is subsumed by the scope of the existing receipt.
5. **Receipt has not expired or been revoked.** The receipt's TTL has not elapsed and no revocation event has invalidated it.
6. **Task is deterministic and side-effect-free from the verifier's point of view.** The receipt applies only to checks whose verdict is fully determined by the recorded input hash, state digest, invariant/policy version, dependency frontier, and verifier version.

If any condition fails, the router falls through to normal verification. There is no partial bypass. The behavior is fail-closed: any uncertainty about applicability results in a fresh verification run.

## Trace

| Call | Task | Receipt present? | Bypass? | Reason |
|---:|---|---|---|---|
| 1 | Proposed graph write A | No | No | Verifier runs and emits receipt R_A |
| 2 | Retry of write A against same state digest | Yes, R_A | Yes | Same invariant, same state digest, same dependency frontier |
| 3 | Proposed graph write B touching new frontier | No / not covered | No | Falls through to verifier and emits receipt R_B |
| 4 | Consistency query covered by R_A scope | Yes, R_A | Yes | Query is subsumed by existing receipt scope |
| 5 | Write A after unrelated edit outside frontier | Yes, R_A | Yes | Intervening edits do not intersect R_A dependency frontier |
| 6 | Write A after edit inside frontier | Yes, R_A | No | Dependency frontier changed; receipt invalidated; falls through |

## Pilot metrics

- **Receipt hit rate.** Fraction of verification calls that reuse an existing receipt instead of recomputing.
- **Avoided verifier/model time.** Wall-clock time saved by receipt reuse versus fresh computation.
- **Fail-closed behavior.** Confirmation that every state or policy change that intersects a receipt's dependency frontier correctly invalidates the receipt and triggers fresh verification.

## Receipt format

Receipts are Signed Verification Receipts (SVR) per the SVR v1.0 specification. The IANA-registered media type is `application/vnd.svr.receipt+json`. The standalone verifier is available on PyPI:

```
pip install svr-verify
svr-verify receipt.svr.json
```

Full specification: [SVR_SPEC_v1.txt](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/SVR_SPEC_v1.txt)
