// Command verify is a one-command check of the SVR Go verifier.
//
// Run from the go module directory:
//
//	go run ./cmd/verify
//
// It loads the bundled sample receipt (or a path given as the first argument),
// prints the signature result and any structural validation issues, then
// demonstrates that a receipt containing &, <, and > in a signed field
// verifies, which is the behavior the SetEscapeHTML fix restores.
package main

import (
	"crypto/ed25519"
	"encoding/hex"
	"fmt"
	"os"

	svr "github.com/Jasonleonardvolk/svr-verify/go"
)

func main() {
	path := "testdata/sample.svr.json"
	if len(os.Args) > 1 {
		path = os.Args[1]
	}

	r, err := svr.LoadReceipt(path)
	if err != nil {
		fmt.Fprintf(os.Stderr, "load %s: %v\n", path, err)
		os.Exit(1)
	}
	fmt.Printf("sample: %s\n", path)
	fmt.Printf("  signature valid: %v\n", svr.VerifySignature(r))
	if errs := svr.Validate(r); len(errs) == 0 {
		fmt.Println("  structural validation: ok")
	} else {
		fmt.Printf("  structural validation: %d issue(s)\n", len(errs))
		for _, e := range errs {
			fmt.Printf("    - %s\n", e)
		}
	}

	// Demonstrate the HTML-escaping fix: a receipt with &, <, and > in a
	// signed field must verify.
	seed := make([]byte, ed25519.SeedSize)
	for i := range seed {
		seed[i] = byte(i + 1)
	}
	priv := ed25519.NewKeyFromSeed(seed)
	pub := priv.Public().(ed25519.PublicKey)
	demo := map[string]interface{}{
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
	msg, err := svr.CanonicalBytes(demo)
	if err != nil {
		fmt.Fprintf(os.Stderr, "canonical: %v\n", err)
		os.Exit(1)
	}
	sig := ed25519.Sign(priv, msg)
	demo["signature"] = hex.EncodeToString(sig)
	demo["signature_status"] = "VALID"
	fmt.Printf("ampersand/angle-bracket receipt verifies: %v\n", svr.VerifySignature(demo))
}
