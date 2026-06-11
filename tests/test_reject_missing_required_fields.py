# tests/test_reject_missing_required_fields.py
# Structural validation must flag every missing required field
# and every count-invariant violation.

from __future__ import annotations

from svr_verify.validate import (
    validate_receipt,
    validate_counts,
    REQUIRED_FIELDS,
)


def test_complete_receipt_has_no_errors(unsigned_receipt):
    assert validate_receipt(unsigned_receipt) == []


def test_each_missing_required_field_is_reported(unsigned_receipt):
    for field in REQUIRED_FIELDS:
        receipt = dict(unsigned_receipt)
        del receipt[field]
        errors = validate_receipt(receipt)
        assert any(field in e for e in errors), (
            "Expected error mentioning missing field '%s', got: %s"
            % (field, errors)
        )


def test_count_invariant_violation_is_reported(unsigned_receipt):
    receipt = dict(unsigned_receipt)
    receipt["items_passed"] = 1  # checked=2, passed=1, failed=0, excluded=0
    err = validate_counts(receipt)
    assert err is not None
    assert "Count invariant" in err


def test_checked_items_length_mismatch_is_reported(unsigned_receipt):
    receipt = dict(unsigned_receipt)
    receipt["checked_items"] = receipt["checked_items"][:1]
    errors = validate_receipt(receipt)
    assert any("checked_items length" in e for e in errors)


def test_item_missing_subfield_is_reported(unsigned_receipt):
    import copy
    receipt = copy.deepcopy(unsigned_receipt)
    del receipt["checked_items"][0]["reason"]
    errors = validate_receipt(receipt)
    assert any("checked_items[0] missing: reason" in e for e in errors)


def test_bad_version_is_reported(unsigned_receipt):
    receipt = dict(unsigned_receipt)
    receipt["svr_version"] = "2.0"
    errors = validate_receipt(receipt)
    assert any("major version" in e for e in errors)
