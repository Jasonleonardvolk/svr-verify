# svr_verify/canonical.py
# Canonical serialization and Ed25519 signature verification
# for Signed Verification Receipts (SVR).
#
# This module implements Section 4 of the SVR v1.0 specification.
# It has ZERO dependencies on SATYA, SIGMA, or any verification engine.
# The only external dependency is PyNaCl for Ed25519.
#
# Any party holding an SVR and the issuer's public key can verify
# the receipt's authenticity using only this module.

from __future__ import annotations

import json
import hashlib
from typing import Any, Dict, Optional


# Fields excluded from canonical serialization (Section 4.1, Step 2).
# These are either computed or set after signing, presentation-layer
# or monetization aliases (receipt_status, evaluation),
# hardware-dependent timing (latency_ms, retrieval_ms, compute_ms,
# total_time_ms), or the signature itself.
EXCLUDED_FIELDS = frozenset({
    "signature",
    "signature_status",
    "superseded_by",
    "verify_url",
    "receipt_status",
    "latency_ms",
    "retrieval_ms",
    "compute_ms",
    "evaluation",
    "total_time_ms",
})


def _sort_keys_recursive(obj):
    """Recursively sort all object keys lexicographically."""
    if isinstance(obj, dict):
        return {
            k: _sort_keys_recursive(v)
            for k, v in sorted(obj.items())
        }
    if isinstance(obj, list):
        return [_sort_keys_recursive(item) for item in obj]
    return obj


def canonical_bytes(receipt):
    """Produce the canonical byte sequence for signature verification.

    Implements SVR Spec Section 4.1:
      1. Remove excluded fields.
      2. Sort all keys lexicographically at every nesting level.
      3. Serialize to compact JSON (no whitespace).
      4. Encode as UTF-8 bytes.

    Args:
        receipt: The SVR JSON object (as a Python dict).

    Returns:
        UTF-8 encoded bytes of the canonical JSON string.
    """
    filtered = {
        k: v for k, v in receipt.items()
        if k not in EXCLUDED_FIELDS
    }
    sorted_obj = _sort_keys_recursive(filtered)
    canonical_str = json.dumps(
        sorted_obj,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
    )
    return canonical_str.encode("utf-8")


def canonical_hash(receipt):
    """SHA-256 hash of the canonical serialization.

    Args:
        receipt: The SVR JSON object.

    Returns:
        Full SHA-256 hex digest.
    """
    return hashlib.sha256(canonical_bytes(receipt)).hexdigest()


def verify_signature(receipt, pinned_key=None):
    """Verify the Ed25519 signature on an SVR.

    Two trust modes:

    1. Embedded key (default): the signature is verified against the
       'public_key' field embedded in the receipt. This proves the
       receipt is internally consistent but does NOT establish that
       the key belongs to a trusted issuer.

    2. Pinned key: pass the issuer's public key (hex-encoded, 32
       bytes) via pinned_key. The signature is verified against the
       pinned key. If the receipt also embeds a public key and it
       differs from the pinned key, verification fails. Pinned keys
       are recommended for production trust decisions.

    Args:
        receipt: The SVR JSON object with 'signature' and
                 'public_key' fields present.
        pinned_key: Optional hex-encoded Ed25519 public key pinned
                    out-of-band. If provided, it is authoritative.

    Returns:
        True if the signature is valid under the selected key.
        False if unsigned, missing fields, key mismatch, or
        verification fails.

    Raises:
        ImportError: If PyNaCl is not installed.
    """
    try:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError
    except ImportError:
        raise ImportError(
            "PyNaCl is required for signature verification. "
            "Install with: pip install pynacl"
        )

    embedded_hex = receipt.get("public_key", "unsigned")
    sig_hex = receipt.get("signature", "")

    if not sig_hex:
        return False

    if pinned_key is not None:
        pinned_hex = pinned_key.strip().lower()
        # If the receipt embeds a real key, it must match the
        # pinned key. A mismatch is a hard failure: it indicates
        # the receipt was signed by a key the deployment does not
        # trust for this issuer.
        if embedded_hex not in ("unsigned", "", None):
            if embedded_hex.strip().lower() != pinned_hex:
                return False
        key_hex = pinned_hex
    else:
        if embedded_hex in ("unsigned", "", None):
            return False
        key_hex = embedded_hex

    try:
        pub_bytes = bytes.fromhex(key_hex)
        sig_bytes = bytes.fromhex(sig_hex)
    except ValueError:
        return False

    if len(pub_bytes) != 32:
        return False

    message = canonical_bytes(receipt)

    try:
        verify_key = VerifyKey(pub_bytes)
        verify_key.verify(message, sig_bytes)
        return True
    except BadSignatureError:
        return False
    except Exception:
        return False
