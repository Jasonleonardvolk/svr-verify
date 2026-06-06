package svr

import (
	"bytes"
	"crypto/ed25519"
	"encoding/hex"
	"testing"
)

// TestVerifySampleSignature loads the bundled sample receipt and verifies it.
// The sample is signed by the reference issuer, so a passing result confirms
// the Go canonicalization agrees with the issuer byte-for-byte, and that the
// receipt_id check accepts an issuer-defined prefix.
func TestVerifySampleSignature(t *testing.T) {
	r, err := LoadReceipt("testdata/sample.svr.json")
	if err != nil {
		t.Fatalf("LoadReceipt: %v", err)
	}
	if !VerifySignature(r) {
		t.Fatal("sample receipt signature did not verify")
	}
	if errs := Validate(r); len(errs) != 0 {
		t.Fatalf("sample receipt failed structural validation: %v", errs)
	}
}

// TestHTMLEscapingRoundTrip proves the canonicalization does not HTML-escape.
// A receipt whose signed fields contain &, <, and > must sign then verify, and
// its canonical bytes must contain those characters literally rather than as
// \u0026, \u003c, \u003e. This is the regression test for the SetEscapeHTML
// fix.
func TestHTMLEscapingRoundTrip(t *testing.T) {
	seed := make([]byte, ed25519.SeedSize)
	for i := range seed {
		seed[i] = byte(i + 1)
	}
	priv := ed25519.NewKeyFromSeed(seed)
	pub := priv.Public().(ed25519.PublicKey)

	receipt := map[string]interface{}{
		"svr_version":          "1.0",
		"receipt_id":           "EXAMPLE-20260606-00000001",
		"receipt_type":         "agent",
		"mode":                 "agent_action",
		"receipt_status":       "evaluation",
		"input_hash":           "3333333333333333",
		"source_bundle_hash":   "",
		"verdict":              "supported",
		"safe_to_rely":         true,
		"filing_safety_status": "SAFE_TO_SUBMIT",
		"reason":               "Q2 & Q3 coverage where A < B and B > C",
		"items_checked":        0,
		"items_passed":         0,
		"items_failed":         0,
		"items_excluded":       0,
		"checked_items":        []interface{}{},
		"timestamp_utc":        "2026-06-06T00:00:00+00:00",
		"engine_version":       "satya/0.1.0 sigma/1.0.0",
		"verification_method":  "deterministic_algebraic",
		"public_key":           hex.EncodeToString(pub),
		"signature":            "",
		"signature_status":     "UNSIGNED",
	}

	msg, err := CanonicalBytes(receipt)
	if err != nil {
		t.Fatalf("CanonicalBytes: %v", err)
	}
	for _, lit := range []string{"&", "<", ">"} {
		if !bytes.Contains(msg, []byte(lit)) {
			t.Fatalf("canonical bytes missing literal %q: %s", lit, msg)
		}
	}
	for _, esc := range []string{`\u0026`, `\u003c`, `\u003e`} {
		if bytes.Contains(msg, []byte(esc)) {
			t.Fatalf("canonical bytes contain HTML escape %q: %s", esc, msg)
		}
	}

	sig := ed25519.Sign(priv, msg)
	receipt["signature"] = hex.EncodeToString(sig)
	receipt["signature_status"] = "VALID"

	if !VerifySignature(receipt) {
		t.Fatal("receipt with &, <, > in a signed field did not verify")
	}
}

// TestTamperRejected confirms a mutated receipt fails verification.
func TestTamperRejected(t *testing.T) {
	r, err := LoadReceipt("testdata/sample.svr.json")
	if err != nil {
		t.Fatalf("LoadReceipt: %v", err)
	}
	r["verdict"] = "supported" // sample says contradicted; flip it without re-signing
	if VerifySignature(r) {
		t.Fatal("tampered receipt verified but should not have")
	}
}
