# tests/conftest.py
# Shared fixtures for svr-verify tests.

from __future__ import annotations

import json
import copy
import pytest

from nacl.signing import SigningKey

from svr_verify.canonical import canonical_bytes


BASE_RECEIPT = {
    "svr_version": "1.0",
    "receipt_id": "TEST-20260611-ABCD1234",
    "receipt_type": "graph_consistency",
    "mode": "full_verification",
    "receipt_status": "evaluation",
    "input_hash": "sha256:" + "a" * 64,
    "source_bundle_hash": "sha256:" + "b" * 64,
    "verdict": "consistent",
    "safe_to_rely": True,
    "filing_safety_status": "SAFE_TO_SUBMIT",
    "reason": "All checks passed.",
    "items_checked": 2,
    "items_passed": 2,
    "items_failed": 0,
    "items_excluded": 0,
    "checked_items": [
        {
            "item_id": "check_one",
            "claim_or_authority": "test authority",
            "verdict": "verified",
            "reason": "ok",
        },
        {
            "item_id": "check_two",
            "claim_or_authority": "test authority",
            "verdict": "verified",
            "reason": "ok",
        },
    ],
    "timestamp_utc": "2026-06-11T00:00:00Z",
    "engine_version": "test-engine-0.0.1",
    "verification_method": "cellular_sheaf_cohomology_h1",
    "public_key": "unsigned",
    "signature": "",
    "signature_status": "UNSIGNED",
}


def make_unsigned_receipt():
    """Return a deep copy of the base unsigned receipt."""
    return copy.deepcopy(BASE_RECEIPT)


def sign(receipt, signing_key=None):
    """Sign a receipt in place. Returns (receipt, signing_key)."""
    if signing_key is None:
        signing_key = SigningKey.generate()
    receipt["public_key"] = signing_key.verify_key.encode().hex()
    receipt["signature_status"] = "VALID"
    payload = canonical_bytes(receipt)
    receipt["signature"] = signing_key.sign(payload).signature.hex()
    return receipt, signing_key


@pytest.fixture
def unsigned_receipt():
    return make_unsigned_receipt()


@pytest.fixture
def signed_receipt():
    receipt, key = sign(make_unsigned_receipt())
    return receipt, key


@pytest.fixture
def signed_receipt_file(tmp_path):
    receipt, key = sign(make_unsigned_receipt())
    path = tmp_path / "receipt.svr.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return str(path), receipt, key
