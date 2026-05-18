# svr_verify/cli.py
# Command-line interface for SVR verification.
#
# Usage:
#   svr-verify receipt.svr.json
#   python -m svr_verify receipt.svr.json

from __future__ import annotations

import json
import sys
from typing import Any, Dict

from svr_verify.canonical import verify_signature, canonical_hash
from svr_verify.validate import validate_receipt


def verify_file(path):
    """Verify an SVR file on disk.

    Args:
        path: Path to a .svr.json file.

    Returns:
        dict with verification results.
    """
    with open(path, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    structure_errors = validate_receipt(receipt)
    sig_valid = False
    sig_error = None

    try:
        sig_valid = verify_signature(receipt)
    except ImportError as e:
        sig_error = str(e)
    except Exception as e:
        sig_error = "Signature verification error: %s" % str(e)

    return {
        "valid": sig_valid and len(structure_errors) == 0,
        "signature_valid": sig_valid,
        "signature_error": sig_error,
        "structure_errors": structure_errors,
        "receipt_id": receipt.get("receipt_id", ""),
        "svr_version": receipt.get("svr_version", ""),
        "receipt_type": receipt.get("receipt_type", ""),
        "verdict": receipt.get("verdict", ""),
        "filing_safety_status": receipt.get("filing_safety_status", ""),
        "items_checked": receipt.get("items_checked", 0),
        "items_passed": receipt.get("items_passed", 0),
        "items_failed": receipt.get("items_failed", 0),
        "items_excluded": receipt.get("items_excluded", 0),
        "canonical_hash": canonical_hash(receipt),
        "public_key": receipt.get("public_key", "unsigned"),
        "timestamp_utc": receipt.get("timestamp_utc", ""),
        "engine_version": receipt.get("engine_version", ""),
    }


def main(args=None):
    """CLI entry point."""
    if args is None:
        args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("svr-verify: Signed Verification Receipt verifier")
        print()
        print("Usage:")
        print("  svr-verify <receipt.svr.json> [options]")
        print()
        print("Options:")
        print("  --json           Output results as JSON")
        print("  --quiet          Only print VALID or INVALID")
        print("  --render <path>  Render receipt as HTML file")
        print()
        print("Exit codes:")
        print("  0  Valid receipt with valid signature")
        print("  1  Invalid receipt or invalid signature")
        print("  2  File not found or parse error")
        return 0

    path = args[0]
    json_output = "--json" in args
    quiet = "--quiet" in args
    render_path = None
    if "--render" in args:
        ri = args.index("--render")
        if ri + 1 < len(args):
            render_path = args[ri + 1]

    try:
        result = verify_file(path)
    except FileNotFoundError:
        if quiet:
            print("ERROR")
        else:
            print("Error: File not found: %s" % path)
        return 2
    except json.JSONDecodeError as e:
        if quiet:
            print("ERROR")
        else:
            print("Error: Invalid JSON: %s" % str(e))
        return 2

    # Render HTML if requested
    if render_path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                receipt = json.load(f)
            from svr_verify.render import render_html
            html = render_html(receipt)
            with open(render_path, "w", encoding="utf-8") as f:
                f.write(html)
            if not quiet:
                print("Rendered: %s" % render_path)
        except Exception as e:
            print("Render error: %s" % str(e))

    if json_output:
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1

    if quiet:
        print("VALID" if result["valid"] else "INVALID")
        return 0 if result["valid"] else 1

    # Human-readable output
    print("=" * 60)
    print("SVR Verification Report")
    print("=" * 60)
    print()
    print("  Receipt ID:      %s" % result["receipt_id"])
    print("  SVR Version:     %s" % result["svr_version"])
    print("  Receipt Type:    %s" % result["receipt_type"])
    print("  Timestamp:       %s" % result["timestamp_utc"])
    print("  Engine:          %s" % result["engine_version"])
    print()
    print("  Verdict:         %s" % result["verdict"])
    print("  Safety:          %s" % result["filing_safety_status"])
    print("  Items Checked:   %d" % result["items_checked"])
    print("  Items Passed:    %d" % result["items_passed"])
    print("  Items Failed:    %d" % result["items_failed"])
    print("  Items Excluded:  %d" % result["items_excluded"])
    print()
    print("  Canonical Hash:  %s" % result["canonical_hash"])
    print("  Public Key:      %s" % result["public_key"][:16] + "...")
    print()

    # Signature
    if result["signature_valid"]:
        print("  Signature:       VALID")
    elif result["signature_error"]:
        print("  Signature:       ERROR (%s)" % result["signature_error"])
    else:
        print("  Signature:       INVALID")

    # Structure
    if result["structure_errors"]:
        print("  Structure:       INVALID (%d errors)" % len(result["structure_errors"]))
        for err in result["structure_errors"]:
            print("    - %s" % err)
    else:
        print("  Structure:       VALID")

    print()
    if result["valid"]:
        print("  RESULT: VALID")
    else:
        print("  RESULT: INVALID")
    print()
    print("=" * 60)

    return 0 if result["valid"] else 1
