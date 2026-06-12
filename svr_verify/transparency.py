# svr_verify/transparency.py
# SVR Transparency Profile verification against a Locus resolver, plus
# offline transparency bundles.
#
# Implements the verifier side of docs/SVR_TRANSPARENCY_BINDING.md
# (binding: locus-v1). Given a receipt hash and a pinned operator key,
# this module verifies the full chain:
#
#   receipt_hash -> ReceiptCommitment event (canonical bytes, BLAKE3 id,
#   Ed25519 event signature) -> Merkle inclusion path (locus.leaf.v1 /
#   locus.node.v1 contexts) -> signed checkpoint (locus.checkpoint.v1,
#   single-operator Ed25519) -> pinned operator key.
#
# Two transport modes share one verification core:
#   - Resolver mode: fetch the proof and the committing event over HTTP
#     (verify_transparency / verify_transparency_for_hash).
#   - Bundle mode: verify a self-contained offline bundle written earlier
#     by --save-bundle or assembled by make_bundle; no network at all
#     (verify_transparency_bundle / verify_bundle_for_hash).
#
# Network access happens only in fetch_proof / fetch_event; everything
# else is pure and testable against the pinned genesis vector.
#
# Dependencies: PyNaCl (already required) and blake3 (optional extra:
#   pip install svr-verify[transparency]
# or
#   pip install blake3
# ).
#
# Hash boundary, stated once: the receipt hash is SHA-256 computed by
# the issuer (canonical.canonical_hash). Everything Locus-internal in
# this module is BLAKE3 with versioned domain separation.

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from svr_verify.canonical import canonical_hash


# Versioned Locus domain separation contexts (normative; a change is a
# protocol version bump).
LEAF_CONTEXT = b"locus.leaf.v1"
NODE_CONTEXT = b"locus.node.v1"
CHECKPOINT_CONTEXT = b"locus.checkpoint.v1"

# Protocol payload type tag for ReceiptCommitment.
RECEIPT_COMMITMENT_TAG = 0x06

# Offline bundle format.
BUNDLE_VERSION = "1.0"
BUNDLE_BINDING = "locus-v1"


class TransparencyError(Exception):
    """Raised for resolver, format, or encoding failures."""


def _require_blake3():
    try:
        import blake3
        return blake3
    except ImportError:
        raise ImportError(
            "blake3 is required for transparency verification. "
            "Install with: pip install blake3 "
            "(or: pip install svr-verify[transparency])"
        )


def _b3(data):
    """BLAKE3 digest as 32 raw bytes."""
    blake3 = _require_blake3()
    return blake3.blake3(data).digest()


def _u32(n):
    return int(n).to_bytes(4, "little")


def _u64(n):
    return int(n).to_bytes(8, "little")


def _hex32(value, what):
    """Decode a 64-hex-char string to 32 bytes, or raise."""
    try:
        b = bytes.fromhex(value)
    except (TypeError, ValueError):
        raise TransparencyError("%s is not valid hex" % what)
    if len(b) != 32:
        raise TransparencyError("%s must be 32 bytes (64 hex chars)" % what)
    return b


def _string_field(s):
    b = s.encode("utf-8")
    return _u32(len(b)) + b


def _opt_string_field(s):
    if s is None:
        return b"\x00"
    return b"\x01" + _string_field(s)


def receipt_commitment_payload_bytes(payload):
    """Canonical payload encoding for a ReceiptCommitment.

    One type tag byte, then fields in struct order. Strings are u32 LE
    length prefix + UTF-8 bytes. Options are a one-byte presence flag
    followed by the encoded value if present.
    """
    try:
        out = bytearray()
        out += bytes([RECEIPT_COMMITMENT_TAG])
        out += _string_field(payload["svr_transparency_version"])
        out += _string_field(payload["leaf_type"])
        out += _string_field(payload["receipt_hash"])
        out += _string_field(payload["receipt_type"])
        out += _string_field(payload["issuer_key_id"])
        out += _opt_string_field(payload.get("subject_hash"))
        out += _string_field(payload["issued_at"])
        out += _string_field(payload["privacy_mode"])
        out += _opt_string_field(payload.get("policy_class"))
        return bytes(out)
    except KeyError as e:
        raise TransparencyError("payload missing field: %s" % e)


def event_canonical_bytes(event):
    """Canonical byte encoding of a Locus event (EventDto JSON form).

    Matches locus-core Event::canonical_bytes: fixed field order,
    little-endian integers, count and length prefixes for variable
    sections, vector clock entries sorted by stream id bytes.
    """
    try:
        out = bytearray()
        out += _hex32(event["stream_id"], "event.stream_id")
        out += _u64(event["sequence"])

        clock = event["clock"]
        out += _u64(clock["lamport_time"])
        entries = []
        for e in clock.get("vector_clock", []):
            entries.append(
                (_hex32(e["stream_id"], "vector_clock.stream_id"), int(e["value"]))
            )
        entries.sort(key=lambda t: t[0])
        out += _u32(len(entries))
        for sid, val in entries:
            out += sid
            out += _u64(val)
        out += _u64(clock["physical_time"])

        out += _u64(event["timestamp"])

        parents = event.get("parent_refs", [])
        out += _u32(len(parents))
        for p in parents:
            out += _hex32(p["event_id"], "parent.event_id")
            out += _hex32(p["stream_id"], "parent.stream_id")
            out += _u64(p["sequence"])

        payload = receipt_commitment_payload_bytes(event["payload"])
        out += _u32(len(payload))
        out += payload

        out += _u32(event["version"])
        return bytes(out)
    except KeyError as e:
        raise TransparencyError("event missing field: %s" % e)


def compute_event_id(event):
    """BLAKE3 event id over canonical bytes, as 32 raw bytes."""
    return _b3(event_canonical_bytes(event))


def leaf_hash(event_id):
    """Merkle leaf: BLAKE3('locus.leaf.v1' || event_id)."""
    return _b3(LEAF_CONTEXT + event_id)


def node_hash(left, right):
    """Merkle node: BLAKE3('locus.node.v1' || left || right)."""
    return _b3(NODE_CONTEXT + left + right)


def checkpoint_canonical_bytes(cp):
    """Canonical checkpoint bytes, excluding signatures."""
    try:
        out = bytearray()
        out += _u64(cp["sequence"])
        out += _u64(cp["timestamp"])
        out += _hex32(cp["state_root"], "checkpoint.state_root")
        out += _hex32(cp["event_merkle_root"], "checkpoint.event_merkle_root")
        out += _u64(cp["tree_size"])
        out += _hex32(cp["prev_checkpoint_hash"], "checkpoint.prev_checkpoint_hash")
        return bytes(out)
    except KeyError as e:
        raise TransparencyError("checkpoint missing field: %s" % e)


def compute_checkpoint_hash(cp):
    """BLAKE3('locus.checkpoint.v1' || canonical checkpoint bytes)."""
    return _b3(CHECKPOINT_CONTEXT + checkpoint_canonical_bytes(cp))


def root_from_inclusion(event_id, leaf_index, tree_size, path):
    """Recompute the root implied by an inclusion path.

    RFC 9162 section 2.1.3.2 algorithm adapted to the BLAKE3 contexts.
    Returns 32 root bytes, or None if the path is inconsistent with
    (leaf_index, tree_size).
    """
    if tree_size == 0 or leaf_index >= tree_size:
        return None
    f = int(leaf_index)
    s = int(tree_size) - 1
    r = leaf_hash(event_id)
    for p in path:
        if s == 0:
            return None
        if (f & 1) == 1 or f == s:
            r = node_hash(p, r)
            if (f & 1) == 0:
                while (f & 1) == 0 and f != 0:
                    f >>= 1
                    s >>= 1
        else:
            r = node_hash(r, p)
        f >>= 1
        s >>= 1
    if s != 0:
        return None
    return r


def verify_inclusion(event_id, leaf_index, tree_size, path, expected_root):
    """True if the path resolves to expected_root."""
    root = root_from_inclusion(event_id, leaf_index, tree_size, path)
    return root is not None and root == expected_root


def _ed25519_verify(pub_bytes, message, sig_hex):
    """Verify an Ed25519 signature; returns bool."""
    try:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError
    except ImportError:
        raise ImportError(
            "PyNaCl is required for signature verification. "
            "Install with: pip install pynacl"
        )
    try:
        sig = bytes.fromhex(sig_hex)
    except (TypeError, ValueError):
        return False
    if len(sig) != 64 or len(pub_bytes) != 32:
        return False
    try:
        VerifyKey(pub_bytes).verify(message, sig)
        return True
    except BadSignatureError:
        return False
    except Exception:
        return False


def _http_get_json(url, timeout):
    """GET a JSON document. Returns dict, or None on HTTP 404.

    Raises TransparencyError for any other failure.
    """
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        raise TransparencyError("HTTP %d from %s %s" % (e.code, url, detail))
    except urllib.error.URLError as e:
        raise TransparencyError(
            "cannot reach transparency resolver at %s (%s)" % (url, e.reason)
        )
    except Exception as e:
        raise TransparencyError("resolver request failed: %s" % e)
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        raise TransparencyError("resolver returned invalid JSON from %s" % url)


def fetch_proof(resolver, receipt_hash, timeout=10):
    """GET /v1/proofs/receipt/{receipt_hash}. None if not registered."""
    import urllib.parse

    base = resolver.rstrip("/")
    url = base + "/v1/proofs/receipt/" + urllib.parse.quote(receipt_hash, safe=":")
    return _http_get_json(url, timeout)


def fetch_event(resolver, event_id_hex, timeout=10):
    """GET /v1/events/{event_id}. None if not found."""
    base = resolver.rstrip("/")
    url = base + "/v1/events/" + event_id_hex
    return _http_get_json(url, timeout)


def _empty_result(receipt_hash):
    return {
        "status": "FAILED",
        "errors": [],
        "receipt_hash": receipt_hash,
        "log_id": None,
        "event_id": None,
        "log_index": None,
        "tree_size": None,
        "checkpoint_sequence": None,
        "checkpoint_hash": None,
    }


def _parse_operator(operator_key, errors):
    """Normalize the pinned operator key; returns 32 bytes or None."""
    operator_hex = (operator_key or "").strip().lower()
    try:
        op_bytes = bytes.fromhex(operator_hex)
    except ValueError:
        op_bytes = b""
    if len(op_bytes) != 32:
        errors.append("transparency operator key must be 64 hex chars (32 bytes)")
        return None
    return op_bytes


def _verify_documents(result, receipt_hash, proof, event, op_bytes, log_id):
    """Shared verification core over a proof document and an event
    document, regardless of how they were obtained (resolver or bundle).
    Mutates result in place: fills details, appends errors, and sets
    status to TRANSPARENT only when every check passes.
    """
    errors = result["errors"]
    operator_hex = op_bytes.hex()

    proof_log_id = str(proof.get("log_id") or "").lower()
    event_id_hex = str(proof.get("event_id") or "").lower()
    result["log_id"] = proof_log_id
    result["event_id"] = event_id_hex
    result["log_index"] = proof.get("log_index")
    result["tree_size"] = proof.get("tree_size")

    if log_id is not None and proof_log_id != log_id.strip().lower():
        errors.append("log_id mismatch: proof is from a different log than pinned")

    # Milestone 1 single-operator binding: log id is BLAKE3(operator key).
    expected_stream = _b3(op_bytes).hex()
    if proof_log_id != expected_stream:
        errors.append("log_id does not match BLAKE3 of the pinned operator key")

    try:
        computed_id = compute_event_id(event)
    except TransparencyError as e:
        errors.append("event canonicalization failed: %s" % e)
        return result

    if computed_id.hex() != event_id_hex:
        errors.append("event id does not match canonical event bytes")
    if str(event.get("id") or "").lower() != event_id_hex:
        errors.append("event id field does not match proof event id")

    payload = event.get("payload") or {}
    if payload.get("receipt_hash") != receipt_hash:
        errors.append("committing event binds a different receipt hash")
    if str(event.get("stream_id") or "").lower() != proof_log_id:
        errors.append("event stream does not match proof log id")
    try:
        if int(event.get("sequence", -1)) != int(proof.get("log_index", -2)):
            errors.append("event sequence does not match proof log index")
    except (TypeError, ValueError):
        errors.append("event sequence or log index is not an integer")

    # Event signature: Ed25519 over the event id, by the operator key
    # (the operator is the stream signer on a single-operator braid).
    if not _ed25519_verify(op_bytes, computed_id, str(event.get("signature") or "")):
        errors.append("event signature invalid under the pinned operator key")

    cp = proof.get("checkpoint") or {}
    try:
        cp_hash = compute_checkpoint_hash(cp)
    except TransparencyError as e:
        errors.append("checkpoint canonicalization failed: %s" % e)
        return result

    result["checkpoint_sequence"] = cp.get("sequence")
    result["checkpoint_hash"] = str(cp.get("checkpoint_hash") or "").lower()

    if cp_hash.hex() != result["checkpoint_hash"]:
        errors.append("checkpoint_hash does not match canonical checkpoint bytes")
    try:
        if int(proof.get("tree_size", -1)) != int(cp.get("tree_size", -2)):
            errors.append("proof tree_size does not match checkpoint tree_size")
    except (TypeError, ValueError):
        errors.append("tree_size is not an integer")

    sigs = cp.get("signatures") or []
    if len(sigs) != 1:
        errors.append("single-operator checkpoint must carry exactly one signature")
    else:
        s = sigs[0]
        if str(s.get("public_key") or "").lower() != operator_hex:
            errors.append("checkpoint signed by a key other than the pinned operator")
        elif not _ed25519_verify(op_bytes, cp_hash, str(s.get("signature") or "")):
            errors.append("checkpoint signature invalid")

    try:
        path = [_hex32(h, "inclusion path node") for h in (proof.get("path") or [])]
        root = root_from_inclusion(
            computed_id,
            int(proof.get("log_index")),
            int(proof.get("tree_size")),
            path,
        )
    except (TransparencyError, TypeError, ValueError) as e:
        errors.append("inclusion path malformed: %s" % e)
        root = None

    if root is None:
        errors.append("inclusion path does not resolve to a root")
    elif root.hex() != str(cp.get("event_merkle_root") or "").lower():
        errors.append("inclusion path does not match the checkpoint root")

    if not errors:
        result["status"] = "TRANSPARENT"
    return result


def verify_transparency_for_hash(
    receipt_hash,
    resolver,
    operator_key,
    log_id=None,
    timeout=10,
    include_documents=False,
):
    """Verify transparency registration for a known receipt hash via a
    live resolver.

    Args:
        receipt_hash: 'sha256:<64 hex>' canonical receipt hash.
        resolver: Base URL of a Locus v1 resolver.
        operator_key: Pinned operator public key, 64 hex chars.
        log_id: Optional pinned log id (64 hex chars). The log id is
                additionally checked against BLAKE3(operator key),
                the Milestone 1 single-operator binding.
        timeout: HTTP timeout in seconds.
        include_documents: When True and both documents were fetched,
                attach them under result['documents'] as
                {'proof': ..., 'event': ...} so a bundle can be saved.

    Returns:
        dict with:
            status: 'TRANSPARENT' | 'NOT_REGISTERED' | 'FAILED'
            errors: list of str (empty when TRANSPARENT)
            receipt_hash, log_id, event_id, log_index, tree_size,
            checkpoint_sequence, checkpoint_hash
            documents: only when include_documents and fetch succeeded
    """
    result = _empty_result(receipt_hash)
    errors = result["errors"]

    op_bytes = _parse_operator(operator_key, errors)
    if op_bytes is None:
        return result

    try:
        proof = fetch_proof(resolver, receipt_hash, timeout=timeout)
    except TransparencyError as e:
        errors.append(str(e))
        return result
    if proof is None:
        result["status"] = "NOT_REGISTERED"
        errors.append("receipt hash is not registered in the transparency log")
        return result

    event_id_hex = str(proof.get("event_id") or "").lower()
    try:
        event = fetch_event(resolver, event_id_hex, timeout=timeout)
    except TransparencyError as e:
        errors.append(str(e))
        return result
    if event is None:
        result["log_id"] = str(proof.get("log_id") or "").lower()
        result["event_id"] = event_id_hex
        result["log_index"] = proof.get("log_index")
        result["tree_size"] = proof.get("tree_size")
        errors.append("committing event not found on resolver")
        return result

    _verify_documents(result, receipt_hash, proof, event, op_bytes, log_id)
    if include_documents:
        result["documents"] = {"proof": proof, "event": event}
    return result


def make_bundle(receipt_hash, proof, event):
    """Assemble an offline transparency bundle.

    The bundle is self-contained: the receipt hash binding, the proof
    document (including its checkpoint), and the committing event
    document, exactly as served by the resolver. verify_bundle_for_hash
    re-verifies everything; nothing in the bundle is trusted as-is.
    """
    return {
        "bundle_version": BUNDLE_VERSION,
        "binding": BUNDLE_BINDING,
        "receipt_hash": receipt_hash,
        "proof": proof,
        "event": event,
    }


def verify_bundle_for_hash(receipt_hash, bundle, operator_key, log_id=None):
    """Verify transparency registration fully offline from a bundle.

    Runs the exact same verification core as the resolver path, minus
    the fetches. The bundle must bind the same receipt hash; bundles
    produced for a different receipt are rejected before any
    cryptographic work.
    """
    result = _empty_result(receipt_hash)
    errors = result["errors"]

    op_bytes = _parse_operator(operator_key, errors)
    if op_bytes is None:
        return result

    if not isinstance(bundle, dict):
        errors.append("bundle is not a JSON object")
        return result
    bv = bundle.get("bundle_version")
    if bv is not None and str(bv) != BUNDLE_VERSION:
        errors.append("unsupported bundle_version: %s" % bv)
        return result
    binding = bundle.get("binding")
    if binding is not None and binding != BUNDLE_BINDING:
        errors.append("unsupported bundle binding: %s" % binding)
        return result
    bound_hash = bundle.get("receipt_hash")
    if bound_hash is not None and bound_hash != receipt_hash:
        errors.append("bundle was produced for a different receipt hash")
        return result

    proof = bundle.get("proof")
    event = bundle.get("event")
    if not isinstance(proof, dict) or not isinstance(event, dict):
        errors.append("bundle missing proof or event document")
        return result

    return _verify_documents(result, receipt_hash, proof, event, op_bytes, log_id)


def verify_transparency_bundle(receipt, bundle, operator_key, log_id=None):
    """Verify an offline bundle for a receipt object.

    Computes the canonical receipt hash (SHA-256, issuer domain) and
    delegates to verify_bundle_for_hash.
    """
    receipt_hash = "sha256:" + canonical_hash(receipt)
    return verify_bundle_for_hash(receipt_hash, bundle, operator_key, log_id=log_id)


def verify_transparency(
    receipt,
    resolver,
    operator_key,
    log_id=None,
    timeout=10,
    include_documents=False,
):
    """Verify transparency registration for a receipt object via a live
    resolver.

    Computes the canonical receipt hash (SHA-256, issuer domain) and
    delegates to verify_transparency_for_hash.
    """
    receipt_hash = "sha256:" + canonical_hash(receipt)
    return verify_transparency_for_hash(
        receipt_hash,
        resolver,
        operator_key,
        log_id=log_id,
        timeout=timeout,
        include_documents=include_documents,
    )
