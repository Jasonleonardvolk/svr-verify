# tests/test_locus_transparency.py
# Cross-language validation of the Locus transparency binding.
#
# The pinned vector in tests/vectors/locus_genesis_v1.json was produced
# by the Rust locus-core implementation. These tests prove the Python
# verifier computes byte-identical canonical encodings, BLAKE3 ids,
# Merkle roots, and checkpoint hashes, and that the full
# verify_transparency_for_hash pipeline returns TRANSPARENT against a
# faithful (offline, monkeypatched) resolver and FAILED against
# tampered responses.

from __future__ import annotations

import json
import os

import pytest

blake3 = pytest.importorskip("blake3")

from nacl.signing import SigningKey

from svr_verify import transparency
from svr_verify.canonical import canonical_hash
from svr_verify.cli import main as cli_main
from svr_verify.transparency import (
    checkpoint_canonical_bytes,
    compute_checkpoint_hash,
    compute_event_id,
    event_canonical_bytes,
    leaf_hash,
    make_bundle,
    root_from_inclusion,
    verify_bundle_for_hash,
    verify_transparency_for_hash,
)

VECTOR_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "vectors", "locus_genesis_v1.json"
)


def load_vector():
    with open(VECTOR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def event_from_vector(v):
    """Build the EventDto-shaped dict the resolver would return."""
    i = v["inputs"]
    return {
        "id": v["expected"]["event_id"],
        "stream_id": i["stream_id_hex"],
        "sequence": i["sequence"],
        "timestamp": i["timestamp"],
        "version": i["version"],
        "signature": v["expected"]["event_signature"],
        "clock": {
            "lamport_time": i["clock"]["lamport_time"],
            "physical_time": i["clock"]["physical_time"],
            "vector_clock": [
                {"stream_id": e["stream_id_hex"], "value": e["value"]}
                for e in i["clock"]["vector_clock"]
            ],
        },
        "parent_refs": [],
        "payload": i["payload"],
    }


def checkpoint_from_vector(v, signature_hex, operator_hex):
    i = v["inputs"]["checkpoint"]
    return {
        "sequence": i["sequence"],
        "timestamp": i["timestamp"],
        "state_root": i["state_root_hex"],
        "event_merkle_root": v["expected"]["merkle_root"],
        "tree_size": i["tree_size"],
        "prev_checkpoint_hash": i["prev_checkpoint_hash_hex"],
        "checkpoint_hash": v["expected"]["checkpoint_hash"],
        "signatures": [{"public_key": operator_hex, "signature": signature_hex}],
    }


def signing_key(v):
    return SigningKey(bytes.fromhex(v["inputs"]["signing_key_seed_hex"]))


def test_event_canonical_bytes_match_rust():
    v = load_vector()
    event = event_from_vector(v)
    assert event_canonical_bytes(event).hex() == v["expected"]["canonical_bytes_hex"]


def test_event_id_and_signature_match_rust():
    v = load_vector()
    event = event_from_vector(v)
    eid = compute_event_id(event)
    assert eid.hex() == v["expected"]["event_id"]

    sk = signing_key(v)
    assert sk.verify_key.encode().hex() == v["expected"]["operator_pubkey"]
    # The pinned signature verifies over the event id.
    sk.verify_key.verify(eid, bytes.fromhex(v["expected"]["event_signature"]))


def test_single_leaf_merkle_root_matches_rust():
    v = load_vector()
    eid = bytes.fromhex(v["expected"]["event_id"])
    assert leaf_hash(eid).hex() == v["expected"]["merkle_root"]
    root = root_from_inclusion(eid, 0, 1, [])
    assert root is not None
    assert root.hex() == v["expected"]["merkle_root"]


def test_checkpoint_hash_matches_rust():
    v = load_vector()
    sk = signing_key(v)
    operator_hex = sk.verify_key.encode().hex()
    cp = checkpoint_from_vector(v, signature_hex="00" * 64, operator_hex=operator_hex)
    assert len(checkpoint_canonical_bytes(cp)) == 8 + 8 + 32 + 32 + 8 + 32
    assert compute_checkpoint_hash(cp).hex() == v["expected"]["checkpoint_hash"]


def _patched_resolver(monkeypatch, proof, event):
    def fake_fetch_proof(resolver, receipt_hash, timeout=10):
        if receipt_hash == proof["_for_receipt_hash"]:
            return {k: val for k, val in proof.items() if not k.startswith("_")}
        return None

    def fake_fetch_event(resolver, event_id_hex, timeout=10):
        if event_id_hex == event["id"]:
            return event
        return None

    monkeypatch.setattr(transparency, "fetch_proof", fake_fetch_proof)
    monkeypatch.setattr(transparency, "fetch_event", fake_fetch_event)


def build_proof_and_event(v):
    sk = signing_key(v)
    operator_hex = sk.verify_key.encode().hex()
    event = event_from_vector(v)

    cp_unsigned = checkpoint_from_vector(v, "00" * 64, operator_hex)
    cp_hash = compute_checkpoint_hash(cp_unsigned)
    cp_sig = sk.sign(cp_hash).signature.hex()
    cp = checkpoint_from_vector(v, cp_sig, operator_hex)

    log_id = blake3.blake3(bytes.fromhex(operator_hex)).hexdigest()
    # The vector event was sealed with stream_id 0101...01, not the
    # operator-derived stream id, so the offline test pins log_id to the
    # event's stream and skips the operator-derivation check by using
    # the event stream as the proof log_id. The mismatch error for the
    # operator binding is asserted separately below.
    proof = {
        "_for_receipt_hash": v["inputs"]["payload"]["receipt_hash"],
        "log_id": event["stream_id"],
        "event_id": event["id"],
        "log_index": 0,
        "tree_size": 1,
        "path": [],
        "checkpoint": cp,
    }
    return proof, event, operator_hex, log_id


def test_verify_transparency_offline_pipeline(monkeypatch):
    v = load_vector()
    proof, event, operator_hex, derived_log_id = build_proof_and_event(v)
    _patched_resolver(monkeypatch, proof, event)

    result = verify_transparency_for_hash(
        v["inputs"]["payload"]["receipt_hash"],
        "http://offline.test",
        operator_hex,
    )

    # The genesis vector predates the operator-derived stream id rule
    # (its stream is 0101...01), so exactly that one binding error is
    # expected; every cryptographic check must pass.
    assert result["status"] == "FAILED"
    assert result["errors"] == [
        "log_id does not match BLAKE3 of the pinned operator key"
    ]
    assert result["event_id"] == event["id"]
    assert result["tree_size"] == 1
    assert derived_log_id != event["stream_id"]


def build_synthetic_transparent(v, receipt_hash=None):
    """Build a fully consistent event/proof pair where the stream id is
    BLAKE3(operator key), the Milestone 1 single-operator binding. Every
    value is computed live in Python; expect TRANSPARENT. Pass
    receipt_hash to bind the synthetic commitment to a real receipt.
    """
    sk = signing_key(v)
    operator_hex = sk.verify_key.encode().hex()
    stream_hex = blake3.blake3(bytes.fromhex(operator_hex)).hexdigest()

    if receipt_hash is None:
        receipt_hash = "sha256:" + "cd" * 32
    payload = dict(v["inputs"]["payload"])
    payload["receipt_hash"] = receipt_hash

    event = {
        "id": "",
        "stream_id": stream_hex,
        "sequence": 0,
        "timestamp": 1900000000000002,
        "version": 1,
        "signature": "",
        "clock": {
            "lamport_time": 1,
            "physical_time": 1900000000000002,
            "vector_clock": [{"stream_id": stream_hex, "value": 1}],
        },
        "parent_refs": [],
        "payload": payload,
    }
    eid = compute_event_id(event)
    event["id"] = eid.hex()
    event["signature"] = sk.sign(eid).signature.hex()

    root = leaf_hash(eid)
    cp = {
        "sequence": 0,
        "timestamp": 1900000000000003,
        "state_root": "00" * 32,
        "event_merkle_root": root.hex(),
        "tree_size": 1,
        "prev_checkpoint_hash": "00" * 32,
        "checkpoint_hash": "",
        "signatures": [],
    }
    cp_hash = compute_checkpoint_hash(cp)
    cp["checkpoint_hash"] = cp_hash.hex()
    cp["signatures"] = [
        {"public_key": operator_hex, "signature": sk.sign(cp_hash).signature.hex()}
    ]

    proof = {
        "_for_receipt_hash": receipt_hash,
        "log_id": stream_hex,
        "event_id": event["id"],
        "log_index": 0,
        "tree_size": 1,
        "path": [],
        "checkpoint": cp,
    }
    return proof, event, operator_hex, stream_hex, receipt_hash


def test_verify_transparency_offline_transparent(monkeypatch):
    v = load_vector()
    proof, event, operator_hex, stream_hex, receipt_hash = (
        build_synthetic_transparent(v)
    )
    _patched_resolver(monkeypatch, proof, event)

    result = verify_transparency_for_hash(
        receipt_hash,
        "http://offline.test",
        operator_hex,
        log_id=stream_hex,
    )
    assert result["errors"] == []
    assert result["status"] == "TRANSPARENT"
    assert result["log_id"] == stream_hex
    assert result["checkpoint_sequence"] == 0


def test_verify_transparency_rejects_tampering(monkeypatch):
    v = load_vector()
    proof, event, operator_hex, _ = build_proof_and_event(v)

    # Tamper: claim a different log index.
    proof["log_index"] = 1
    _patched_resolver(monkeypatch, proof, event)
    result = verify_transparency_for_hash(
        v["inputs"]["payload"]["receipt_hash"],
        "http://offline.test",
        operator_hex,
    )
    assert result["status"] == "FAILED"
    assert any("log index" in e for e in result["errors"])
    assert any("does not resolve" in e or "checkpoint root" in e for e in result["errors"])


def test_not_registered(monkeypatch):
    v = load_vector()
    proof, event, operator_hex, _ = build_proof_and_event(v)
    _patched_resolver(monkeypatch, proof, event)

    result = verify_transparency_for_hash(
        "sha256:" + "00" * 32,
        "http://offline.test",
        operator_hex,
    )
    assert result["status"] == "NOT_REGISTERED"


def _clean_proof(proof):
    """Strip test-only keys before bundling."""
    return {k: val for k, val in proof.items() if not k.startswith("_")}


def test_bundle_offline_transparent():
    v = load_vector()
    proof, event, operator_hex, stream_hex, receipt_hash = (
        build_synthetic_transparent(v)
    )
    bundle = make_bundle(receipt_hash, _clean_proof(proof), event)
    result = verify_bundle_for_hash(
        receipt_hash, bundle, operator_hex, log_id=stream_hex
    )
    assert result["errors"] == []
    assert result["status"] == "TRANSPARENT"
    assert result["checkpoint_sequence"] == 0


def test_bundle_wrong_receipt_hash():
    v = load_vector()
    proof, event, operator_hex, _stream, receipt_hash = (
        build_synthetic_transparent(v)
    )
    bundle = make_bundle(receipt_hash, _clean_proof(proof), event)
    other = "sha256:" + "ee" * 32
    result = verify_bundle_for_hash(other, bundle, operator_hex)
    assert result["status"] == "FAILED"
    assert any("different receipt hash" in e for e in result["errors"])


def test_cli_bundle_exit_zero(signed_receipt_file, tmp_path):
    """End to end, fully offline: a real signed receipt verifies core
    checks, the bundle proves transparency, exit code is 0 and the
    outcome is VALID_WITH_TRANSPARENCY.
    """
    path, receipt, key = signed_receipt_file
    rh = "sha256:" + canonical_hash(receipt)

    v = load_vector()
    proof, event, operator_hex, _stream, _rh = build_synthetic_transparent(
        v, receipt_hash=rh
    )
    bundle = make_bundle(rh, _clean_proof(proof), event)
    bundle_path = tmp_path / "receipt.transparency.bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    pinned = key.verify_key.encode().hex()
    code = cli_main(
        [
            path,
            "--pubkey",
            pinned,
            "--require-transparency",
            "--bundle",
            str(bundle_path),
            "--transparency-operator",
            operator_hex,
            "--quiet",
        ]
    )
    assert code == 0
