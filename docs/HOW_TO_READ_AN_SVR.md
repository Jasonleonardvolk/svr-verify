# How to Read a Signed Verification Receipt (SVR)

A Signed Verification Receipt is a cryptographically signed document
that proves an AI-generated or human-submitted artifact was verified
against source evidence before use. This guide explains what each
section means and what to do with it.

## Who This Is For

- AI platform operators verifying agent outputs
- Compliance officers evaluating SOC 2 readiness
- Lawyers reviewing AI-assisted briefs
- Auditors verifying control evidence
- Risk managers reviewing SEC filings or vendor assessments
- Security engineers integrating verification into agent pipelines
- Procurement teams reviewing vendor risk artifacts
- Anyone who receives an SVR and needs to understand it

## The Five Questions Every SVR Answers

1. **What was checked?** The `checked_items` table lists every claim,
   citation, or control that was evaluated.

2. **What failed?** Items with verdict FAIL, CONTRADICTED, or
   UNSUPPORTED identified specific problems.

3. **What was excluded?** The `items_excluded` count and `exclusions`
   list show what was outside the audit scope.

4. **Is it safe to rely on?** The `safe_to_rely` field gives a
   boolean answer. The `filing_safety_status` gives the institutional
   answer: SAFE_TO_SUBMIT, UNSAFE_TO_SUBMIT, or REVIEW_REQUIRED.

5. **Can I verify this independently?** Yes. The Ed25519 signature
   can be checked by anyone using the open-source `svr-verify` tool.
   No account required. No engine required. Just the receipt and
   the public key.

---

## Receipt Sections Explained

### Header

```
"svr_version": "1.0"
"receipt_id": "SATYA-20260518-4C2388CC"
"receipt_type": "compliance"
"receipt_status": "evaluation"
```

- **svr_version**: Schema version. "1.0" is the current standard.
- **receipt_id**: Globally unique identifier. Format: SATYA-YYYYMMDD-HASH8.
  The SATYA prefix identifies the issuing engine, not the standard.
  Any compliant engine may issue SVRs with its own prefix.
- **receipt_type**: What kind of audit this is (legal, compliance,
  financial, clinical, defense, rag, scientific, etc.).
- **receipt_status**: "evaluation" means this is a free-tier receipt
  with an EVALUATION watermark on PDF output. "production" means
  full commercial use.

### Verdict

```
"verdict": "contradicted"
"safe_to_rely": false
"filing_safety_status": "UNSAFE_TO_SUBMIT"
"reason": "h1_source_conflict"
```

This is the bottom line. Read `filing_safety_status` first:

- **SAFE_TO_SUBMIT**: All checks passed. The artifact is internally
  consistent and supported by source evidence.
- **UNSAFE_TO_SUBMIT**: Structural contradictions or unsupported
  claims were found. Do not submit without remediation.
- **REVIEW_REQUIRED**: Partial results. Some checks could not
  complete. Manual review is needed.

The `reason` field gives a plain-language explanation of why.

### Summary Counts

```
"items_checked": 12
"items_passed": 7
"items_failed": 5
"items_excluded": 0
```

These four numbers tell you the scope and outcome at a glance.
The invariant always holds: checked = passed + failed + excluded.

### Checked Items

This is the detailed table. Each entry has:

- **item_id**: Sequential number (1, 2, 3...).
- **claim_or_authority**: What was checked. For legal receipts,
  this is a citation. For SOC 2, this is a control family.
  For SEC, this is a disclosure surface.
- **verdict**: PASS, FAIL, INSUFFICIENT_EVIDENCE, CONTRADICTED,
  SUPPORTED, UNSUPPORTED, or domain-specific values.
- **reason**: Human-readable explanation of the result.

Read the FAIL items first. Those are the problems.

### Proof Sketches (if present)

```
"proof_sketches": {
  "total_obstructions": 5,
  "critical": 4,
  "high": 1,
  ...
}
```

Proof sketches explain WHY something failed, not just THAT it
failed. Each sketch includes:

- **severity**: CRITICAL, HIGH, MEDIUM, or LOW. Based on the
  mathematical rotation angle (theta) in the sheaf complex.
  Higher theta = more severe structural contradiction.
- **claims_involved**: The specific claims that conflict.
- **energy_concentration**: Which edges in the verification
  graph carry the most contradiction energy. This is Dirichlet
  energy localization: the math pinpoints exactly where the
  problem sits.
- **remediation**: What to do about it.

### Priority Remediation Plan (if present)

This section tells you what to fix, in what order, Monday morning.

Each repair has:
- **repair_id**: R-001, R-002, etc.
- **repair_type**: ADD_EVIDENCE, CORRECT_VALUE, ADD_ASSIGNMENT,
  EXTEND_COVERAGE, UPDATE_DATE, INCREASE_FREQUENCY, etc.
- **target**: Which constraint or control to fix.
- **action**: Plain-language description of the fix.
- **severity**: CRITICAL or HIGH.
- **priority**: 1 = fix first (highest risk-reduction per effort).

The repairs are ordered by risk_reduction_ratio: how much
submission risk each fix eliminates per unit of effort. Fix #1
always has the highest bang-for-buck.

### Assurance Completion Pack (if present)

This is the auditor handoff. It breaks down into:

- **Evidence to collect**: Documents or logs you need to gather.
- **Owners to assign**: Controls that lack a responsible party.
- **Policy updates required**: Policies that don't cover the
  required criteria.
- **Recheck command**: The exact command to re-run verification
  after remediation.
- **Closure receipt required**: Whether a follow-up SVR is needed
  to prove the fixes were applied.

### Constraint Results (if present)

Technical detail for engineers. Each constraint shows:

- **constraint**: Which algebraic primitive was evaluated
  (DateBefore, MoneyEquals, SetSubset, etc.).
- **verdict**: PASS or FAIL.
- **compatibility**: Score from 0.0 (total conflict) to 1.0
  (perfect agreement).
- **theta_rad**: Rotation angle in radians. 0 = aligned.
  pi/2 = maximum contradiction.

### Sheaf Metrics (if present)

Mathematical measurements from the verification engine:

- **h1_dimension**: Number of structural contradictions found.
  0 = clean. Any positive number = contradictions exist.
- **cokernel_dimension**: Number of unsupported claims (claims
  with no source evidence).
- **grounding_ratio**: Percentage of claims supported by sources.
- **total_dirichlet_energy**: Total contradiction energy in the
  verification graph. Higher = more internal conflict.

### Verification Record (footer)

```
"public_key": "ab7f1a49..."
"signature": "c4754d58..."
"signature_status": "VALID"
```

This is the cryptographic proof. The Ed25519 signature covers
the entire receipt content (minus timing fields and the signature
itself). To verify:

1. Install the verifier: `pip install svr-verify`
2. Run: `svr-verify receipt.svr.json`
3. If it says VALID, the receipt is authentic and unmodified.
4. If it says INVALID, the receipt has been tampered with.

No account needed. No internet connection needed (except to
install the tool once). The verification is purely mathematical.

### Vertical Extension (if present)

Domain-specific data appended by the receipt type. For SOC 2,
this includes criteria_evaluated, coverage_summary, and
control_claims. For legal, this includes authorities_checked
and proposition support results. Each vertical has its own
extension schema.

---

## What an SVR Does NOT Do

- It does not determine intent, malpractice, or bad faith.
- It does not replace human judgment or auditor opinion.
- It does not assess the quality of sources (only whether
  claims are supported BY sources).
- It does not guarantee factual correctness of the underlying
  documents.
- It does not constitute legal advice.

An SVR proves one thing: at a specific moment in time, a
deterministic verification engine checked a specific artifact
against specific sources and produced a specific, signed,
replayable result.

---

## Verifying a Receipt You Received

If someone sends you an SVR file (.svr.json), verify it:

### Option 1: Command Line
```
pip install svr-verify
svr-verify receipt.svr.json
```

### Option 2: Python
```python
from svr_verify import verify
result = verify("receipt.svr.json")
print("Valid:", result["valid"])
print("Signature:", "VALID" if result["signature_valid"] else "INVALID")
```

### Option 3: Web
Open https://invariant.pro/receipts/receipt-svr.html and load
the receipt file.

### Option 4: JSON (for developers)
```
svr-verify receipt.svr.json --json
```

Returns machine-readable verification results.

---

## Glossary

- **SVR**: Signed Verification Receipt. The open standard.
- **Ed25519**: A modern elliptic-curve digital signature algorithm.
  Fast, secure, widely supported.
- **Canonical serialization**: The exact procedure for converting
  the receipt to bytes before signing. Ensures any verifier
  produces the same bytes and can check the signature.
- **H^1 dimension**: A topological measurement. Counts independent
  "loops" of contradiction in the verification graph.
- **Dirichlet energy**: A measure of how much disagreement exists
  across edges in the verification graph. Higher = more conflict.
- **Theta (rotation angle)**: How far a constraint rotates the
  local agreement space. 0 = perfect alignment. pi/2 = maximum
  contradiction.
- **Purity Gate**: A spectral bound (sigma_max <= 0.99) that
  ensures all restriction maps in the verification graph are
  well-conditioned. Prevents numerical instability.
- **Sheaf cohomology**: The mathematical framework that detects
  whether distributed local claims can be assembled into a
  globally consistent story. If they can't, contradictions exist.

---

## Further Reading

- [SVR Specification v1.0](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/SVR_SPEC_v1.txt)
- [JSON Schema](https://github.com/Jasonleonardvolk/sigma/blob/main/satya/spec/svr_schema_v1.json)
- [svr-verify on PyPI](https://pypi.org/project/svr-verify/)
- [svr-verify on GitHub](https://github.com/Jasonleonardvolk/svr-verify)
- [OpenAPI Spec](https://github.com/Jasonleonardvolk/svr-verify/blob/main/openapi.yaml)
- [invariant.pro](https://invariant.pro)

---

Signed Verification Receipt (SVR) v1.0 | Invariant Research | 2026
