# tests/test_verify_valid_receipt.py
# A correctly signed, structurally valid receipt must verify.

from __future__ import annotations

from svr_verify.canonical import verify_signature
from svr_verify.validate import validate_receipt


def test_signed_receipt_signature_verifies(signed_receipt):
    receipt, _key = signed_receipt
    assert verify_signature(receipt) is True


def test_signed_receipt_structure_is_clean(signed_receipt):
    receipt, _key = signed_receipt
    assert validate_receipt(receipt) == []


def test_signed_receipt_verifies_with_matching_pinned_key(signed_receipt):
    receipt, key = signed_receipt
    pinned = key.verify_key.encode().hex()
    assert verify_signature(receipt, pinned_key=pinned) is True


def test_unsigned_receipt_does_not_verify(unsigned_receipt):
    assert verify_signature(unsigned_receipt) is False
