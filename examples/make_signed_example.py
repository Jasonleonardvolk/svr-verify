# examples/make_signed_example.py
# Produce a deterministic SIGNED demo receipt for the Locus transparency
# demo. Uses a fixed development seed so the demo issuer key is stable
# and documented. Never use this key for anything real.
#
# Outputs (relative to this file):
#   receipts/demo_signed.svr.json          signed receipt
#   keys/demo_issuer.pub                   issuer public key (hex)
#   receipts/demo_signed.receipt_hash.txt  "sha256:<canonical hash>"
#
# Run:
#   python examples/make_signed_example.py

from __future__ import annotations

import json
import os

from nacl.signing import SigningKey

from svr_verify.canonical import canonical_bytes, canonical_hash

DEMO_SEED = bytes([0x2A]) * 32


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "receipts", "sample_pass.svr.json")
    out_receipt = os.path.join(here, "receipts", "demo_signed.svr.json")
    out_hash = os.path.join(here, "receipts", "demo_signed.receipt_hash.txt")
    keys_dir = os.path.join(here, "keys")
    out_key = os.path.join(keys_dir, "demo_issuer.pub")

    with open(src, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    signing_key = SigningKey(DEMO_SEED)
    pub_hex = signing_key.verify_key.encode().hex()

    # Sign per SVR Spec Section 4: public_key participates in canonical
    # bytes; signature and signature_status are excluded fields and are
    # set after signing.
    receipt["public_key"] = pub_hex
    message = canonical_bytes(receipt)
    receipt["signature"] = signing_key.sign(message).signature.hex()
    receipt["signature_status"] = "VALID"

    os.makedirs(keys_dir, exist_ok=True)
    with open(out_receipt, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
    with open(out_key, "w", encoding="utf-8") as f:
        f.write(pub_hex + "\n")

    receipt_hash = "sha256:" + canonical_hash(receipt)
    with open(out_hash, "w", encoding="utf-8") as f:
        f.write(receipt_hash + "\n")

    print("Wrote %s" % out_receipt)
    print("Wrote %s" % out_key)
    print("Wrote %s" % out_hash)
    print()
    print("issuer public key: %s" % pub_hex)
    print("receipt hash:      %s" % receipt_hash)


if __name__ == "__main__":
    main()
