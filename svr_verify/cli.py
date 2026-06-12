# svr_verify/cli.py
# Command-line interface for SVR verification.
#
# Usage:
#   svr-verify receipt.svr.json
#   svr-verify receipt.svr.json --pubkey issuer.pub
#   svr-verify receipt.svr.json --pubkey issuer.pub --require-transparency
#       --transparency-resolver http://127.0.0.1:8080
#       --transparency-operator <hex or file>
#   svr-verify receipt.svr.json --pubkey issuer.pub --require-transparency
#       --bundle receipt.transparency.bundle.json
#       --transparency-operator <hex or file>
#   python -m svr_verify receipt.svr.json
#
# Outcomes (per the SVR Transparency Profile):
#   VALID                      core receipt verification passed
#   VALID_WITH_TRANSPARENCY    core passed and registration proven
#   VALID_BUT_NOT_TRANSPARENT  core passed, transparency required but
#                              not proven (not registered, or proof
#                              failed verification)
#   INVALID                    core receipt verification failed
#
# Transparency has two transports sharing one verification core:
# a live resolver (--transparency-resolver) or an offline bundle
# (--bundle). --save-bundle writes a bundle after a successful
# resolver verification so the proof can travel with the receipt.

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

from svr_verify.canonical import verify_signature, canonical_hash
from svr_verify.validate import validate_receipt


def _load_pinned_key(value):
    """Resolve a --pubkey argument to a hex-encoded key string.

    Accepts either a path to a file containing the hex key, or the
    hex key itself. Whitespace is stripped.
    """
    if value is None:
        return None
    if os.path.isfile(value):
        with open(value, "r", encoding="utf-8") as f:
            return f.read().strip()
    return value.strip()


def verify_file(path, pubkey=None, transparency=None):
    """Verify an SVR file on disk.

    Args:
        path: Path to a .svr.json file.
        pubkey: Optional pinned issuer public key (hex string or
                path to a file containing the hex string). If
                provided, the signature is verified against this
                key and any embedded key must match it.
        transparency: Optional dict enabling transparency checking:
                resolver: Locus v1 resolver base URL
                operator: pinned operator key, hex string (required)
                log_id:   pinned log id, hex string (optional)
                timeout:  HTTP timeout seconds (optional, default 10)
                bundle:   offline bundle dict; when present it is
                          verified instead of contacting the resolver
                include_documents: when True (resolver path only),
                          attach the fetched proof and event documents
                          to the transparency result for bundle saving

    Returns:
        dict with verification results. 'result' is one of VALID,
        VALID_WITH_TRANSPARENCY, VALID_BUT_NOT_TRANSPARENT, INVALID.
    """
    with open(path, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    pinned_key = _load_pinned_key(pubkey)

    structure_errors = validate_receipt(receipt)
    sig_valid = False
    sig_error = None

    try:
        sig_valid = verify_signature(receipt, pinned_key=pinned_key)
    except ImportError as e:
        sig_error = str(e)
    except Exception as e:
        sig_error = "Signature verification error: %s" % str(e)

    core_valid = sig_valid and len(structure_errors) == 0

    transparency_result = None
    if transparency is not None:
        if not core_valid:
            transparency_result = {
                "status": "SKIPPED",
                "errors": ["core verification failed; transparency not attempted"],
            }
        else:
            try:
                from svr_verify.transparency import (
                    verify_bundle_for_hash,
                    verify_transparency,
                )
                if transparency.get("bundle") is not None:
                    receipt_hash = "sha256:" + canonical_hash(receipt)
                    transparency_result = verify_bundle_for_hash(
                        receipt_hash,
                        transparency.get("bundle"),
                        transparency.get("operator"),
                        log_id=transparency.get("log_id"),
                    )
                else:
                    transparency_result = verify_transparency(
                        receipt,
                        transparency.get("resolver"),
                        transparency.get("operator"),
                        log_id=transparency.get("log_id"),
                        timeout=transparency.get("timeout", 10),
                        include_documents=transparency.get(
                            "include_documents", False
                        ),
                    )
            except ImportError as e:
                transparency_result = {
                    "status": "FAILED",
                    "errors": [str(e)],
                }

    if transparency is None:
        outcome = "VALID" if core_valid else "INVALID"
    elif not core_valid:
        outcome = "INVALID"
    elif transparency_result.get("status") == "TRANSPARENT":
        outcome = "VALID_WITH_TRANSPARENCY"
    else:
        outcome = "VALID_BUT_NOT_TRANSPARENT"

    return {
        "valid": core_valid,
        "result": outcome,
        "signature_valid": sig_valid,
        "signature_error": sig_error,
        "pinned_key_used": pinned_key is not None,
        "structure_errors": structure_errors,
        "transparency": transparency_result,
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


def _flag_value(args, flag):
    """Return the value following a flag, or None."""
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return None


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
        print("  --pubkey <key>   Pinned issuer public key: hex string")
        print("                   or path to a file containing it.")
        print("                   Recommended for production trust.")
        print("  --json           Output results as JSON")
        print("  --quiet          Only print the outcome word")
        print("  --render <path>  Render receipt as HTML file")
        print()
        print("Transparency (SVR Transparency Profile, binding locus-v1):")
        print("  --require-transparency")
        print("                   Require registration proof from a")
        print("                   transparency log. Outcome becomes")
        print("                   VALID_WITH_TRANSPARENCY or")
        print("                   VALID_BUT_NOT_TRANSPARENT.")
        print("  --transparency-resolver <url>")
        print("                   Locus v1 resolver base URL, e.g.")
        print("                   http://127.0.0.1:8080")
        print("  --transparency-operator <key>")
        print("                   Pinned log operator public key: hex")
        print("                   string or path to a file containing it.")
        print("                   Required with --require-transparency")
        print("                   and with --bundle.")
        print("  --transparency-log-id <hex>")
        print("                   Optional pinned log id (BLAKE3 of the")
        print("                   operator key on single-operator logs).")
        print("  --bundle <path>  Verify an offline transparency bundle")
        print("                   instead of contacting a resolver. The")
        print("                   bundle carries the proof, checkpoint,")
        print("                   and committing event; every check still")
        print("                   runs locally against the pinned key.")
        print("  --save-bundle <path>")
        print("                   After a successful resolver verification,")
        print("                   write an offline bundle to this path so")
        print("                   the proof can travel with the receipt.")
        print()
        print("Exit codes:")
        print("  0  VALID or VALID_WITH_TRANSPARENCY")
        print("  1  INVALID or VALID_BUT_NOT_TRANSPARENT")
        print("  2  File not found, parse error, or bad arguments")
        return 0

    path = args[0]
    json_output = "--json" in args
    quiet = "--quiet" in args

    pubkey = None
    if "--pubkey" in args:
        pubkey = _flag_value(args, "--pubkey")
        if pubkey is None:
            print("Error: --pubkey requires a value (hex string or file path)")
            return 2

    render_path = _flag_value(args, "--render")

    bundle_path = _flag_value(args, "--bundle")
    save_bundle = _flag_value(args, "--save-bundle")

    transparency = None
    if "--require-transparency" in args or bundle_path is not None:
        resolver = _flag_value(args, "--transparency-resolver")
        operator = _flag_value(args, "--transparency-operator")
        log_id = _flag_value(args, "--transparency-log-id")
        if not operator:
            print(
                "Error: transparency verification needs --transparency-operator "
                "<hex or file> (the pinned log operator key)"
            )
            return 2

        bundle = None
        if bundle_path is not None:
            try:
                with open(bundle_path, "r", encoding="utf-8") as f:
                    bundle = json.load(f)
            except FileNotFoundError:
                print("Error: Bundle file not found: %s" % bundle_path)
                return 2
            except json.JSONDecodeError as e:
                print("Error: Bundle is not valid JSON: %s" % str(e))
                return 2
        elif not resolver:
            print(
                "Error: --require-transparency needs --transparency-resolver "
                "<url> or --bundle <path>"
            )
            return 2

        transparency = {
            "resolver": resolver,
            "operator": _load_pinned_key(operator),
            "log_id": log_id,
            "bundle": bundle,
            "include_documents": bool(save_bundle),
        }

    try:
        result = verify_file(path, pubkey=pubkey, transparency=transparency)
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

    exit_code = 0 if result["result"] in ("VALID", "VALID_WITH_TRANSPARENCY") else 1

    # Save an offline bundle if requested and the resolver path proved
    # transparency. The file is written in every output mode; the
    # confirmation line prints only in human-readable mode.
    bundle_saved = None
    bundle_save_error = None
    if transparency is not None and save_bundle:
        t = result.get("transparency") or {}
        docs = t.get("documents")
        if t.get("status") == "TRANSPARENT" and docs:
            try:
                from svr_verify.transparency import make_bundle
                bundle_obj = make_bundle(
                    t.get("receipt_hash"), docs.get("proof"), docs.get("event")
                )
                with open(save_bundle, "w", encoding="utf-8") as f:
                    json.dump(bundle_obj, f, indent=2)
                    f.write("\n")
                bundle_saved = save_bundle
            except Exception as e:
                bundle_save_error = str(e)

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
        return exit_code

    if quiet:
        print(result["result"])
        return exit_code

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

    pub = result["public_key"]
    if pub and pub not in ("unsigned", "") and len(pub) > 16:
        print("  Public Key:      %s..." % pub[:16])
    else:
        print("  Public Key:      %s" % pub)

    if result["pinned_key_used"]:
        print("  Key Trust:       PINNED (out-of-band key)")
    else:
        print("  Key Trust:       EMBEDDED (receipt-supplied key)")
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

    # Transparency
    t = result.get("transparency")
    if t is not None:
        print()
        print("  Transparency:    %s" % t.get("status", "FAILED"))
        if transparency is not None and transparency.get("bundle") is not None:
            print("    Source:        offline bundle")
        if t.get("receipt_hash"):
            print("    Receipt Hash:  %s" % t["receipt_hash"])
        if t.get("log_id"):
            print("    Log ID:        %s" % t["log_id"])
        if t.get("log_index") is not None:
            print("    Log Index:     %s" % t["log_index"])
        if t.get("tree_size") is not None:
            print("    Tree Size:     %s" % t["tree_size"])
        if t.get("checkpoint_sequence") is not None:
            print("    Checkpoint:    #%s" % t["checkpoint_sequence"])
        if t.get("checkpoint_hash"):
            print("    Checkpoint Hash: %s" % t["checkpoint_hash"])
        for err in t.get("errors", []):
            print("    - %s" % err)
        if bundle_saved:
            print("    Bundle saved:  %s" % bundle_saved)
        if bundle_save_error:
            print("    Bundle save error: %s" % bundle_save_error)
        if save_bundle and not bundle_saved and not bundle_save_error:
            print("    Bundle not saved (transparency status: %s)" % t.get("status"))

    print()
    print("  RESULT: %s" % result["result"])
    print()
    print("=" * 60)

    return exit_code
