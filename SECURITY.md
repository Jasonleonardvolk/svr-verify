# Security Policy

## Reporting a vulnerability

Please report security issues privately to jason@invariant.pro.

Do not open public GitHub issues for vulnerabilities involving:

- Signature verification bypass
- Canonicalization mismatch between implementations
- Malformed receipt parsing
- Public-key handling or pinned-key mismatch logic
- Replay-policy confusion
- CLI exit-code inconsistencies

You will receive an acknowledgment within 72 hours. Coordinated disclosure is appreciated; credit will be given in release notes unless you request otherwise.

## Supported versions

The latest PyPI release of `svr-verify` is supported. Older releases do not receive security fixes.

## Scope

`svr-verify` verifies the SVR receipt artifact: structural validity and Ed25519 signature over the canonical payload. See the Threat Model section of the README for what this tool does and does not establish. Issues in the issuing engines (SATYA, SIGMA, sigma-guard) should be reported to the same address but are tracked separately.
