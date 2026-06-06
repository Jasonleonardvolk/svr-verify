// Package svr provides standalone verification for Signed Verification Receipts (SVR).
//
// Zero external dependencies. Uses Go stdlib crypto/ed25519.
//
// Usage:
//
//	receipt, _ := svr.LoadReceipt("receipt.svr.json")
//	ok := svr.VerifySignature(receipt)
//	errors := svr.Validate(receipt)
package svr

import (
	"bytes"
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"
)

// ExcludedFields are removed before canonical serialization (SVR Spec Section 4.1).
var ExcludedFields = map[string]bool{
	"signature":        true,
	"signature_status": true,
	"superseded_by":    true,
	"verify_url":       true,
	"receipt_status":   true,
	"latency_ms":       true,
	"retrieval_ms":     true,
	"compute_ms":       true,
	"evaluation":       true,
	"total_time_ms":    true,
}

// RequiredFields per SVR Spec Section 3.
var RequiredFields = []string{
	"svr_version", "receipt_id", "receipt_type", "mode",
	"receipt_status", "input_hash", "source_bundle_hash",
	"verdict", "safe_to_rely", "filing_safety_status",
	"reason", "items_checked", "items_passed", "items_failed",
	"items_excluded", "checked_items", "timestamp_utc",
	"engine_version", "public_key", "signature",
	"signature_status",
}

// CheckedItemFields required per checked_item entry.
var CheckedItemFields = []string{"item_id", "claim_or_authority", "verdict", "reason"}

// LoadReceipt reads and parses an SVR JSON file.
func LoadReceipt(path string) (map[string]interface{}, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var receipt map[string]interface{}
	if err := json.Unmarshal(data, &receipt); err != nil {
		return nil, err
	}
	return receipt, nil
}

// sortKeysRecursive produces a recursively sorted copy.
func sortKeysRecursive(v interface{}) interface{} {
	switch val := v.(type) {
	case map[string]interface{}:
		keys := make([]string, 0, len(val))
		for k := range val {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		sorted := make(map[string]interface{}, len(val))
		for _, k := range keys {
			sorted[k] = sortKeysRecursive(val[k])
		}
		return sorted
	case []interface{}:
		result := make([]interface{}, len(val))
		for i, item := range val {
			result[i] = sortKeysRecursive(item)
		}
		return result
	default:
		return v
	}
}

// CanonicalBytes produces the canonical byte sequence for signature verification.
// Implements SVR Spec Section 4.1.
func CanonicalBytes(receipt map[string]interface{}) ([]byte, error) {
	// Step 1: Remove excluded fields
	filtered := make(map[string]interface{}, len(receipt))
	for k, v := range receipt {
		if !ExcludedFields[k] {
			filtered[k] = v
		}
	}

	// Step 2: Sort keys recursively
	sorted := sortKeysRecursive(filtered)

	// Step 3: Compact JSON without HTML escaping.
	// json.Marshal escapes &, <, and > to \u0026, \u003c, \u003e, which would
	// diverge from the Python and JS verifiers. SetEscapeHTML(false) disables
	// that. Encoder.Encode appends a trailing newline, so it is stripped.
	// encoding/json sorts map keys on its own; sortKeysRecursive above makes
	// the ordering explicit and stable.
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(sorted); err != nil {
		return nil, err
	}
	return bytes.TrimRight(buf.Bytes(), "\n"), nil
}

// CanonicalHash returns the SHA-256 hex digest of the canonical serialization.
func CanonicalHash(receipt map[string]interface{}) (string, error) {
	data, err := CanonicalBytes(receipt)
	if err != nil {
		return "", err
	}
	hash := sha256.Sum256(data)
	return hex.EncodeToString(hash[:]), nil
}

// VerifySignature verifies the Ed25519 signature on an SVR.
func VerifySignature(receipt map[string]interface{}) bool {
	pubHex, _ := receipt["public_key"].(string)
	sigHex, _ := receipt["signature"].(string)

	if pubHex == "" || pubHex == "unsigned" || sigHex == "" {
		return false
	}

	pubBytes, err := hex.DecodeString(pubHex)
	if err != nil || len(pubBytes) != ed25519.PublicKeySize {
		return false
	}

	sigBytes, err := hex.DecodeString(sigHex)
	if err != nil || len(sigBytes) != ed25519.SignatureSize {
		return false
	}

	message, err := CanonicalBytes(receipt)
	if err != nil {
		return false
	}

	return ed25519.Verify(ed25519.PublicKey(pubBytes), message, sigBytes)
}

// ValidateCounts checks the count invariant.
func ValidateCounts(receipt map[string]interface{}) error {
	getInt := func(key string) int {
		v, _ := receipt[key].(float64)
		return int(v)
	}
	checked := getInt("items_checked")
	passed := getInt("items_passed")
	failed := getInt("items_failed")
	excluded := getInt("items_excluded")
	total := passed + failed + excluded
	if checked != total {
		return fmt.Errorf("count invariant violated: items_checked=%d but passed(%d)+failed(%d)+excluded(%d)=%d",
			checked, passed, failed, excluded, total)
	}
	return nil
}

// Validate runs all structural checks on an SVR.
// Returns a slice of error strings. Empty means valid.
func Validate(receipt map[string]interface{}) []string {
	var errors []string

	// Required fields
	for _, field := range RequiredFields {
		if _, ok := receipt[field]; !ok {
			errors = append(errors, "Missing required field: "+field)
		}
	}

	// Version
	if v, ok := receipt["svr_version"].(string); ok && v != "" {
		if !strings.HasPrefix(v, "1.") {
			errors = append(errors, "Unrecognized major version: "+v)
		}
	}

	// receipt_id format: PREFIX-YYYYMMDD-HASH8 (prefix is issuer-defined)
	if rid, ok := receipt["receipt_id"].(string); ok && rid != "" {
		if !strings.Contains(rid, "-") {
			errors = append(errors, "receipt_id must contain at least one '-': "+rid)
		}
	}

	// Count invariant
	if err := ValidateCounts(receipt); err != nil {
		errors = append(errors, err.Error())
	}

	// checked_items length
	items, _ := receipt["checked_items"].([]interface{})
	checked := 0
	if v, ok := receipt["items_checked"].(float64); ok {
		checked = int(v)
	}
	if len(items) != checked {
		errors = append(errors, fmt.Sprintf("checked_items length (%d) != items_checked (%d)", len(items), checked))
	}

	// Per-item fields
	for i, item := range items {
		m, ok := item.(map[string]interface{})
		if !ok {
			errors = append(errors, fmt.Sprintf("checked_items[%d] is not an object", i))
			continue
		}
		for _, field := range CheckedItemFields {
			if _, ok := m[field]; !ok {
				errors = append(errors, fmt.Sprintf("checked_items[%d] missing: %s", i, field))
			}
		}
	}

	return errors
}
