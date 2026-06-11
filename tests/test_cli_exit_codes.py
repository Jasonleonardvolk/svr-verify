# tests/test_cli_exit_codes.py
# CLI contract: 0 = valid, 1 = invalid, 2 = file/parse error.
# This is what CI/CD pipelines depend on.

from __future__ import annotations

import json

from svr_verify.cli import main


def test_valid_signed_receipt_exits_zero(signed_receipt_file):
    path, _receipt, _key = signed_receipt_file
    assert main([path, "--quiet"]) == 0


def test_valid_receipt_with_pinned_key_exits_zero(signed_receipt_file):
    path, _receipt, key = signed_receipt_file
    pinned = key.verify_key.encode().hex()
    assert main([path, "--pubkey", pinned, "--quiet"]) == 0


def test_pinned_key_file_exits_zero(signed_receipt_file, tmp_path):
    path, _receipt, key = signed_receipt_file
    keyfile = tmp_path / "issuer.pub"
    keyfile.write_text(key.verify_key.encode().hex() + "\n", encoding="utf-8")
    assert main([path, "--pubkey", str(keyfile), "--quiet"]) == 0


def test_wrong_pinned_key_exits_one(signed_receipt_file):
    path, _receipt, _key = signed_receipt_file
    from nacl.signing import SigningKey
    stranger = SigningKey.generate().verify_key.encode().hex()
    assert main([path, "--pubkey", stranger, "--quiet"]) == 1


def test_tampered_receipt_exits_one(signed_receipt_file, tmp_path):
    path, receipt, _key = signed_receipt_file
    receipt["verdict"] = "contradicted"
    bad_path = tmp_path / "tampered.svr.json"
    bad_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert main([str(bad_path), "--quiet"]) == 1


def test_unsigned_receipt_exits_one(unsigned_receipt, tmp_path):
    path = tmp_path / "unsigned.svr.json"
    path.write_text(json.dumps(unsigned_receipt), encoding="utf-8")
    assert main([str(path), "--quiet"]) == 1


def test_missing_file_exits_two(tmp_path):
    assert main([str(tmp_path / "does_not_exist.svr.json"), "--quiet"]) == 2


def test_malformed_json_exits_two(tmp_path):
    path = tmp_path / "garbage.svr.json"
    path.write_text("{not json", encoding="utf-8")
    assert main([str(path), "--quiet"]) == 2


def test_json_output_mode_exits_zero_on_valid(signed_receipt_file, capsys):
    path, _receipt, _key = signed_receipt_file
    code = main([path, "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert code == 0
    assert parsed["valid"] is True
    assert parsed["signature_valid"] is True
