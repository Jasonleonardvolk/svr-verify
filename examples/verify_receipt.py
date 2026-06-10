# examples/verify_receipt.py
# Verify a Signed Verification Receipt (SVR).
#
# Usage:
#   python examples/verify_receipt.py examples/receipts/sample_pass.svr.json
#   python examples/verify_receipt.py examples/receipts/sample_fail.svr.json
#   python examples/verify_receipt.py examples/receipts/sample_pass.svr.json --sign
#
# With --sign, the script generates a fresh Ed25519 keypair,
# signs the receipt, writes the signed copy, and then verifies it.

from __future__ import annotations

import json
import sys
import os
import hashlib


def canonical_bytes(receipt):
    """Canonical byte sequence per SVR Spec Section 4."""
    excluded = {
        "signature", "signature_status", "superseded_by",
        "verify_url", "receipt_status", "latency_ms",
        "retrieval_ms", "compute_ms", "evaluation", "total_time_ms",
    }
    filtered = {k: v for k, v in receipt.items() if k not in excluded}
    sorted_obj = _sort_keys(filtered)
    return json.dumps(
        sorted_obj, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _sort_keys(obj):
    if isinstance(obj, dict):
        return {k: _sort_keys(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_sort_keys(item) for item in obj]
    return obj


def sign_receipt(receipt):
    """Generate a fresh Ed25519 keypair and sign the receipt.

    Returns (signed_receipt, private_key_hex, public_key_hex).
    """
    from nacl.signing import SigningKey

    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    pub_hex = verify_key.encode().hex()
    receipt["public_key"] = pub_hex
    receipt["signature_status"] = "VALID"

    payload = canonical_bytes(receipt)
    signed = signing_key.sign(payload)
    sig_hex = signed.signature.hex()

    receipt["signature"] = sig_hex

    priv_hex = signing_key.encode().hex()
    return receipt, priv_hex, pub_hex


def verify_signature(receipt):
    """Verify the Ed25519 signature."""
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError

    pub_hex = receipt.get("public_key", "unsigned")
    sig_hex = receipt.get("signature", "")

    if pub_hex == "unsigned" or not sig_hex:
        return False, "unsigned"

    try:
        pub_bytes = bytes.fromhex(pub_hex)
        sig_bytes = bytes.fromhex(sig_hex)
    except ValueError:
        return False, "invalid hex encoding"

    payload = canonical_bytes(receipt)

    try:
        vk = VerifyKey(pub_bytes)
        vk.verify(payload, sig_bytes)
        return True, "valid"
    except BadSignatureError:
        return False, "bad signature"
    except Exception as e:
        return False, str(e)


def validate_structure(receipt):
    """Validate SVR structural requirements."""
    required = [
        "svr_version", "receipt_id", "receipt_type", "mode",
        "receipt_status", "input_hash", "source_bundle_hash",
        "verdict", "safe_to_rely", "filing_safety_status", "reason",
        "items_checked", "items_passed", "items_failed", "items_excluded",
        "checked_items", "timestamp_utc", "engine_version",
        "public_key", "signature", "signature_status",
        "verification_method",
    ]
    errors = []

    for field in required:
        if field not in receipt:
            errors.append("Missing required field: %s" % field)

    checked = receipt.get("items_checked", 0)
    passed = receipt.get("items_passed", 0)
    failed = receipt.get("items_failed", 0)
    excluded = receipt.get("items_excluded", 0)
    total = passed + failed + excluded
    if checked != total:
        errors.append(
            "Count invariant violated: items_checked=%d "
            "but passed(%d) + failed(%d) + excluded(%d) = %d"
            % (checked, passed, failed, excluded, total)
        )

    items = receipt.get("checked_items", [])
    if len(items) != checked:
        errors.append(
            "checked_items length (%d) != items_checked (%d)"
            % (len(items), checked)
        )

    item_fields = ["item_id", "claim_or_authority", "verdict", "reason"]
    for i, item in enumerate(items):
        for field in item_fields:
            if field not in item:
                errors.append("checked_items[%d] missing: %s" % (i, field))

    return errors


def print_report(receipt, sig_valid, sig_note, structure_errors):
    """Print the human-readable verification report."""
    print("=" * 60)
    print("SVR Verification Report")
    print("=" * 60)
    print()
    print("  Receipt ID:      %s" % receipt.get("receipt_id", ""))
    print("  SVR Version:     %s" % receipt.get("svr_version", ""))
    print("  Receipt Type:    %s" % receipt.get("receipt_type", ""))
    print("  Verdict:         %s" % receipt.get("verdict", ""))
    print("  Items Checked:   %d" % receipt.get("items_checked", 0))
    print("  Items Passed:    %d" % receipt.get("items_passed", 0))
    print("  Items Failed:    %d" % receipt.get("items_failed", 0))
    print()

    if sig_valid:
        print("  Signature:       VALID")
    elif sig_note == "unsigned":
        print("  Signature:       UNSIGNED (use --sign to generate)")
    else:
        print("  Signature:       INVALID (%s)" % sig_note)

    if structure_errors:
        print("  Structure:       INVALID (%d errors)" % len(structure_errors))
        for err in structure_errors:
            print("    - %s" % err)
    else:
        print("  Structure:       VALID")

    print()
    overall = sig_valid and len(structure_errors) == 0
    if overall:
        print("  RESULT: VALID")
    elif len(structure_errors) == 0 and sig_note == "unsigned":
        print("  RESULT: STRUCTURE VALID (unsigned)")
    else:
        print("  RESULT: INVALID")

    print()
    print("=" * 60)
    return overall


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: python verify_receipt.py <receipt.svr.json> [--sign]")
        print()
        print("  --sign    Generate Ed25519 keypair, sign the receipt,")
        print("            write signed copy, and verify it.")
        return

    path = args[0]
    do_sign = "--sign" in args

    try:
        with open(path, "r", encoding="utf-8") as f:
            receipt = json.load(f)
    except FileNotFoundError:
        print("Error: File not found: %s" % path)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print("Error: Invalid JSON: %s" % str(e))
        sys.exit(2)

    if do_sign:
        print("Generating Ed25519 keypair...")
        receipt, priv_hex, pub_hex = sign_receipt(receipt)

        signed_path = path.replace(".svr.json", ".signed.svr.json")
        if signed_path == path:
            signed_path = path + ".signed"

        with open(signed_path, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)

        print("Signed receipt written to: %s" % signed_path)
        print("Public key:  %s" % pub_hex)
        print("Private key: %s (keep secret)" % priv_hex)
        print()

    sig_valid, sig_note = verify_signature(receipt)
    structure_errors = validate_structure(receipt)
    valid = print_report(receipt, sig_valid, sig_note, structure_errors)

    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
