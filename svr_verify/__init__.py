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
#   svr-verify receipt.svr.json --pubkey issuer.pub
#
# Python API:
#   from svr_verify import verify, validate_receipt
#   result = verify("receipt.svr.json")
#   result = verify("receipt.svr.json", pubkey="<hex or path>")
#   errors = validate_receipt(receipt_dict)
#
# June 2026 | Invariant Research
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


def verify(path, pubkey=None):
    """Verify an SVR file. Returns a result dict.

    Args:
        path: Path to a .svr.json file.
        pubkey: Optional pinned issuer public key. Either a
                hex-encoded Ed25519 public key string or a path
                to a file containing one. When provided, the
                signature is verified against this key and any
                embedded key must match it. Pinned keys are
                recommended for production trust decisions.

    Returns:
        dict with keys:
            valid: bool
            signature_valid: bool
            pinned_key_used: bool
            structure_errors: list of str
            receipt_id: str
            verdict: str
            items_checked: int
            items_passed: int
            items_failed: int
    """
    return verify_file(path, pubkey=pubkey)


__version__ = "1.0.4"

__all__ = [
    "canonical_bytes",
    "canonical_hash",
    "verify_signature",
    "validate_receipt",
    "validate_counts",
    "validate_structure",
    "verify",
    "verify_file",
    "render_html",
    "EXCLUDED_FIELDS",
]
