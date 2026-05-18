# svr-verify
# Standalone Signed Verification Receipt (SVR) verifier.
# Zero SATYA dependencies. Zero SIGMA dependencies.
# Only requires PyNaCl for Ed25519 signature verification.
#
# Install:
#   pip install svr-verify
#
# Verify a receipt:
#   svr-verify receipt.svr.json
#
# Python API:
#   from svr_verify import verify, validate
#   result = verify("receipt.svr.json")
#   errors = validate(receipt_dict)
#
# May 2026 | Invariant Research
# MIT License

from svr_verify.canonical import (
    canonical_bytes,
    canonical_hash,
    verify_signature,
    EXCLUDED_FIELDS,
)

from svr_verify.validate import (
    validate_receipt,
    validate_counts,
    validate_structure,
)

from svr_verify.cli import verify_file
from svr_verify.render import render_html


def verify(path):
    """Verify an SVR file. Returns a result dict.

    Args:
        path: Path to a .svr.json file.

    Returns:
        dict with keys:
            valid: bool
            signature_valid: bool
            structure_errors: list of str
            receipt_id: str
            verdict: str
            items_checked: int
            items_passed: int
            items_failed: int
    """
    return verify_file(path)


__version__ = "1.0.0"

__all__ = [
    "canonical_bytes",
    "canonical_hash",
    "verify_signature",
    "validate_receipt",
    "validate_counts",
    "validate_structure",
    "verify",
    "verify_file",
    "EXCLUDED_FIELDS",
]
