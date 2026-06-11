# tests/test_reject_tampered_receipt.py
# Any post-signing mutation of a signed field must invalidate
# the signature. Mutation of excluded fields must NOT.

from __future__ import annotations

from nacl.signing import SigningKey

from svr_verify.canonical import verify_signature


def test_tampered_verdict_fails(signed_receipt):
    receipt, _key = signed_receipt
    receipt["verdict"] = "contradicted"
    assert verify_signature(receipt) is False


def test_tampered_item_reason_fails(signed_receipt):
    receipt, _key = signed_receipt
    receipt["checked_items"][0]["reason"] = "tampered"
    assert verify_signature(receipt) is False


def test_tampered_counts_fail(signed_receipt):
    receipt, _key = signed_receipt
    receipt["items_passed"] = 999
    assert verify_signature(receipt) is False


def test_excluded_field_mutation_does_not_break_signature(signed_receipt):
    # receipt_status is excluded from canonical serialization,
    # so changing it must not invalidate the signature.
    receipt, _key = signed_receipt
    receipt["receipt_status"] = "production"
    assert verify_signature(receipt) is True


def test_swapped_signature_fails(signed_receipt):
    receipt, _key = signed_receipt
    other_key = SigningKey.generate()
    from svr_verify.canonical import canonical_bytes
    receipt["signature"] = other_key.sign(
        canonical_bytes(receipt)
    ).signature.hex()
    # Signature made by a different key than the embedded one
    assert verify_signature(receipt) is False


def test_pinned_key_mismatch_fails(signed_receipt):
    # Receipt is validly signed by its embedded key, but the
    # deployment pins a DIFFERENT issuer key. Must fail closed.
    receipt, _key = signed_receipt
    stranger = SigningKey.generate()
    pinned = stranger.verify_key.encode().hex()
    assert verify_signature(receipt, pinned_key=pinned) is False


def test_garbage_hex_fails(signed_receipt):
    receipt, _key = signed_receipt
    receipt["signature"] = "zz-not-hex"
    assert verify_signature(receipt) is False
