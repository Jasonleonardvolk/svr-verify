# svr-verify
# Standalone Signed Verification Receipt (SVR) verifier.
# Zero SATYA dependencies. Zero SIGMA dependencies.
# Requires PyNaCl for Ed25519 signature verification.
# Optional: blake3 for the SVR Transparency Profile (binding locus-v1).
#
# Install:
#   pip install svr-verify
#   pip install svr-verify[transparency]   # adds blake3
#
# Verify a receipt:
#   svr-verify receipt.svr.json
#   svr-verify receipt.svr.json --pubkey issuer.pub
#   svr-verify receipt.svr.json --pubkey issuer.pub \
#       --require-transparency \
#       --transparency-resolver http://127.0.0.1:8080 \
#       --transparency-operator operator.pub
#   svr-verify receipt.svr.json --pubkey issuer.pub \
#       --require-transparency \
#       --bundle receipt.transparency.bundle.json \
#       --transparency-operator operator.pub
#
# Python API:
#   from svr_verify import verify, validate_receipt
#   result = verify("receipt.svr.json")
#   result = verify("receipt.svr.json", pubkey="<hex or path>")
#   result = verify("receipt.svr.json", pubkey="<hex or path>",
#                   require_transparency=True,
#                   transparency_resolver="http://127.0.0.1:8080",
#                   transparency_operator="<hex>")
#   errors = validate_receipt(receipt_dict)
#
#   from svr_verify import verify_transparency_bundle
#   result = verify_transparency_bundle(receipt_dict, bundle_dict,
#                                       "<operator hex>")
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
from svr_verify.transparency import (
    TransparencyError,
    make_bundle,
    verify_bundle_for_hash,
    verify_transparency,
    verify_transparency_bundle,
    verify_transparency_for_hash,
)


def verify(
    path,
    pubkey=None,
    require_transparency=False,
    transparency_resolver=None,
    transparency_operator=None,
    transparency_log_id=None,
):
    """Verify an SVR file. Returns a result dict.

    Args:
        path: Path to a .svr.json file.
        pubkey: Optional pinned issuer public key. Either a
                hex-encoded Ed25519 public key string or a path
                to a file containing one. When provided, the
                signature is verified against this key and any
                embedded key must match it. Pinned keys are
                recommended for production trust decisions.
        require_transparency: When True, also require registration
                proof from a transparency log (binding locus-v1).
                transparency_resolver and transparency_operator
                are then required.
        transparency_resolver: Locus v1 resolver base URL.
        transparency_operator: Pinned log operator public key (hex).
        transparency_log_id: Optional pinned log id (hex).

    Returns:
        dict with keys:
            valid: bool (core verification only)
            result: VALID | VALID_WITH_TRANSPARENCY |
                    VALID_BUT_NOT_TRANSPARENT | INVALID
            signature_valid: bool
            pinned_key_used: bool
            structure_errors: list of str
            transparency: dict or None
            receipt_id: str
            verdict: str
            items_checked: int
            items_passed: int
            items_failed: int
    """
    transparency = None
    if require_transparency:
        transparency = {
            "resolver": transparency_resolver,
            "operator": transparency_operator,
            "log_id": transparency_log_id,
        }
    return verify_file(path, pubkey=pubkey, transparency=transparency)


__version__ = "1.1.0"

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
    "verify_transparency",
    "verify_transparency_for_hash",
    "verify_transparency_bundle",
    "verify_bundle_for_hash",
    "make_bundle",
    "TransparencyError",
    "EXCLUDED_FIELDS",
]
