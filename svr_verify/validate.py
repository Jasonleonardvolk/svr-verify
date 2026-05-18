# svr_verify/validate.py
# Structural validation for Signed Verification Receipts (SVR).
#
# Checks required fields, count invariants, and schema conformance
# without requiring any verification engine.

from __future__ import annotations
from typing import Any, Dict, List


# Required top-level fields per SVR Spec Section 3
REQUIRED_FIELDS = [
    "svr_version",
    "receipt_id",
    "receipt_type",
    "mode",
    "receipt_status",
    "input_hash",
    "source_bundle_hash",
    "verdict",
    "safe_to_rely",
    "filing_safety_status",
    "reason",
    "items_checked",
    "items_passed",
    "items_failed",
    "items_excluded",
    "checked_items",
    "timestamp_utc",
    "engine_version",
    "public_key",
    "signature",
    "signature_status",
    "verification_method",
]

# Required fields per checked_item
CHECKED_ITEM_FIELDS = [
    "item_id",
    "claim_or_authority",
    "verdict",
    "reason",
]

# Valid verdict values (base set + common domain-specific)
VALID_VERDICTS = {
    "verified",
    "citation_audit_high_risk",
    "review_required",
    "unsafe_to_submit",
    "insufficient_data",
    "contradicted",
    "consistent",
    "filing_consistent",
    "material_contradictions",
    "going_concern_detected",
    "inconsistencies_detected",
}

# Valid filing safety statuses
VALID_SAFETY = {
    "SAFE_TO_SUBMIT",
    "UNSAFE_TO_SUBMIT",
    "REVIEW_REQUIRED",
}

# Valid signature statuses
VALID_SIG_STATUS = {"VALID", "UNSIGNED"}

# Valid receipt statuses
VALID_RECEIPT_STATUS = {"evaluation", "production"}


def validate_counts(receipt):
    """Validate the count invariant.

    items_checked == items_passed + items_failed + items_excluded

    Returns:
        None if valid, or an error message string.
    """
    checked = receipt.get("items_checked", 0)
    passed = receipt.get("items_passed", 0)
    failed = receipt.get("items_failed", 0)
    excluded = receipt.get("items_excluded", 0)
    total = passed + failed + excluded
    if checked != total:
        return (
            "Count invariant violated: items_checked=%d "
            "but passed(%d) + failed(%d) + excluded(%d) = %d"
            % (checked, passed, failed, excluded, total)
        )
    return None


def validate_structure(receipt):
    """Validate structural requirements without signature check.

    Returns:
        List of error strings. Empty means valid.
    """
    errors = []

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in receipt:
            errors.append("Missing required field: %s" % field)

    # Version
    version = receipt.get("svr_version", "")
    if version and not version.startswith("1."):
        errors.append(
            "Unrecognized major version: %s (expected 1.x)" % version
        )

    # receipt_id format: PREFIX-YYYYMMDD-HASH8 (prefix is issuer-defined)
    rid = receipt.get("receipt_id", "")
    if rid and "-" not in rid:
        errors.append(
            "receipt_id must contain at least one '-': got '%s'" % rid
        )

    # receipt_status
    rs = receipt.get("receipt_status", "")
    if rs and rs not in VALID_RECEIPT_STATUS:
        errors.append(
            "Invalid receipt_status: '%s' (expected: %s)"
            % (rs, ", ".join(sorted(VALID_RECEIPT_STATUS)))
        )

    # verdict - warn but don't error on unrecognized values
    # Domain-specific verdicts are permitted beyond the base set
    v = receipt.get("verdict", "")
    if v and v not in VALID_VERDICTS:
        errors.append(
            "Unrecognized verdict: '%s'" % v
        )

    # filing_safety_status
    fs = receipt.get("filing_safety_status", "")
    if fs and fs not in VALID_SAFETY:
        errors.append(
            "Invalid filing_safety_status: '%s'" % fs
        )

    # signature_status
    ss = receipt.get("signature_status", "")
    if ss and ss not in VALID_SIG_STATUS:
        errors.append(
            "Invalid signature_status: '%s'" % ss
        )

    # Count invariant
    count_err = validate_counts(receipt)
    if count_err:
        errors.append(count_err)

    # checked_items length
    items = receipt.get("checked_items", [])
    checked = receipt.get("items_checked", 0)
    if len(items) != checked:
        errors.append(
            "checked_items length (%d) != items_checked (%d)"
            % (len(items), checked)
        )

    # Per-item required fields
    for i, item in enumerate(items):
        for field in CHECKED_ITEM_FIELDS:
            if field not in item:
                errors.append(
                    "checked_items[%d] missing: %s" % (i, field)
                )

    return errors


def validate_receipt(receipt):
    """Full validation: structure + count invariant.

    Returns:
        List of error strings. Empty means valid.
    """
    return validate_structure(receipt)
