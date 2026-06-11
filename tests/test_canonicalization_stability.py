# tests/test_canonicalization_stability.py
# The canonical byte sequence must be stable under key reordering
# and insensitive to excluded fields. This is the property that
# makes independent verifier implementations interoperable.

from __future__ import annotations

import json

from svr_verify.canonical import (
    canonical_bytes,
    canonical_hash,
    EXCLUDED_FIELDS,
)


def test_key_order_does_not_change_canonical_bytes(unsigned_receipt):
    # Round-trip through JSON with reversed key insertion order
    reversed_receipt = {}
    for key in reversed(list(unsigned_receipt.keys())):
        reversed_receipt[key] = unsigned_receipt[key]
    assert canonical_bytes(unsigned_receipt) == canonical_bytes(reversed_receipt)


def test_excluded_fields_do_not_affect_hash(unsigned_receipt):
    base_hash = canonical_hash(unsigned_receipt)
    mutated = dict(unsigned_receipt)
    mutated["signature"] = "ff" * 64
    mutated["signature_status"] = "VALID"
    mutated["receipt_status"] = "production"
    mutated["latency_ms"] = 12345
    mutated["verify_url"] = "https://example.invalid/check"
    assert canonical_hash(mutated) == base_hash


def test_non_excluded_field_changes_hash(unsigned_receipt):
    base_hash = canonical_hash(unsigned_receipt)
    mutated = dict(unsigned_receipt)
    mutated["verdict"] = "contradicted"
    assert canonical_hash(mutated) != base_hash


def test_canonical_form_is_compact_sorted_json(unsigned_receipt):
    raw = canonical_bytes(unsigned_receipt).decode("utf-8")
    parsed = json.loads(raw)
    # No excluded fields present
    for field in EXCLUDED_FIELDS:
        assert field not in parsed
    # Compact: no spaces after separators
    assert ": " not in raw
    assert ", " not in raw
    # Top-level keys sorted
    keys = list(parsed.keys())
    assert keys == sorted(keys)


def test_nested_keys_are_sorted(unsigned_receipt):
    raw = canonical_bytes(unsigned_receipt).decode("utf-8")
    parsed = json.loads(raw)
    for item in parsed["checked_items"]:
        keys = list(item.keys())
        assert keys == sorted(keys)
