/**
 * svr-verify.js
 * Standalone Signed Verification Receipt (SVR) verifier for JavaScript.
 * Works in Node.js and browsers (with tweetnacl).
 *
 * Zero SATYA/SIGMA dependencies. Only requires tweetnacl for Ed25519.
 *
 * Usage (Node.js):
 *   const { verify, verifySignature, validateReceipt } = require('svr-verify');
 *   const receipt = JSON.parse(fs.readFileSync('receipt.svr.json', 'utf8'));
 *   console.log(verifySignature(receipt)); // true/false
 *   console.log(validateReceipt(receipt)); // [] if valid
 *
 * Usage (Browser):
 *   <script src="https://cdn.jsdelivr.net/npm/tweetnacl/nacl-fast.min.js"></script>
 *   <script src="svr-verify.js"></script>
 *   <script>
 *     var result = SVR.verifySignature(receiptObj);
 *   </script>
 *
 * MIT License | Invariant Research | 2026
 */

(function(root, factory) {
    if (typeof module !== 'undefined' && module.exports) {
        // Node.js / CommonJS
        module.exports = factory(require('tweetnacl'));
    } else if (typeof define === 'function' && define.amd) {
        // AMD
        define(['tweetnacl'], factory);
    } else {
        // Browser global
        root.SVR = factory(root.nacl);
    }
})(typeof globalThis !== 'undefined' ? globalThis : this, function(nacl) {
    'use strict';

    // Fields excluded from canonical serialization (SVR Spec Section 4.1)
    var EXCLUDED_FIELDS = [
        'signature',
        'signature_status',
        'superseded_by',
        'verify_url',
        'receipt_status',
        'latency_ms',
        'retrieval_ms',
        'compute_ms',
        'evaluation',
        'total_time_ms'
    ];

    // Required top-level fields (SVR Spec Section 3)
    var REQUIRED_FIELDS = [
        'svr_version', 'receipt_id', 'receipt_type', 'mode',
        'receipt_status', 'input_hash', 'source_bundle_hash',
        'verdict', 'safe_to_rely', 'filing_safety_status',
        'reason', 'items_checked', 'items_passed', 'items_failed',
        'items_excluded', 'checked_items', 'timestamp_utc',
        'engine_version', 'public_key', 'signature',
        'signature_status'
    ];

    var CHECKED_ITEM_FIELDS = ['item_id', 'claim_or_authority', 'verdict', 'reason'];

    // ================================================================
    // CANONICAL SERIALIZATION
    // ================================================================

    function sortKeysRecursive(obj) {
        if (Array.isArray(obj)) {
            return obj.map(sortKeysRecursive);
        }
        if (obj !== null && typeof obj === 'object') {
            var sorted = {};
            var keys = Object.keys(obj).sort();
            for (var i = 0; i < keys.length; i++) {
                sorted[keys[i]] = sortKeysRecursive(obj[keys[i]]);
            }
            return sorted;
        }
        return obj;
    }

    /**
     * Produce the canonical byte sequence for signature verification.
     * Implements SVR Spec Section 4.1.
     *
     * @param {Object} receipt - The SVR JSON object.
     * @returns {Uint8Array} UTF-8 encoded canonical bytes.
     */
    function canonicalBytes(receipt) {
        // Step 1: Remove excluded fields
        var filtered = {};
        var keys = Object.keys(receipt);
        for (var i = 0; i < keys.length; i++) {
            if (EXCLUDED_FIELDS.indexOf(keys[i]) === -1) {
                filtered[keys[i]] = receipt[keys[i]];
            }
        }

        // Step 2: Sort keys recursively
        var sorted = sortKeysRecursive(filtered);

        // Step 3: Compact JSON
        var jsonStr = JSON.stringify(sorted);

        // Step 4: UTF-8 encode
        if (typeof TextEncoder !== 'undefined') {
            return new TextEncoder().encode(jsonStr);
        }
        // Node.js fallback
        return Buffer.from(jsonStr, 'utf8');
    }

    /**
     * SHA-256 hash of the canonical serialization.
     *
     * @param {Object} receipt - The SVR JSON object.
     * @returns {Promise<string>} Hex digest.
     */
    function canonicalHash(receipt) {
        var bytes = canonicalBytes(receipt);
        if (typeof crypto !== 'undefined' && crypto.subtle) {
            // Browser
            return crypto.subtle.digest('SHA-256', bytes).then(function(buf) {
                return Array.from(new Uint8Array(buf))
                    .map(function(b) { return b.toString(16).padStart(2, '0'); })
                    .join('');
            });
        }
        // Node.js
        var crypto_node = require('crypto');
        var hash = crypto_node.createHash('sha256').update(bytes).digest('hex');
        return Promise.resolve(hash);
    }

    // ================================================================
    // SIGNATURE VERIFICATION
    // ================================================================

    function hexToBytes(hex) {
        var bytes = new Uint8Array(hex.length / 2);
        for (var i = 0; i < hex.length; i += 2) {
            bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
        }
        return bytes;
    }

    /**
     * Verify the Ed25519 signature on an SVR.
     *
     * @param {Object} receipt - The SVR JSON object.
     * @returns {boolean} True if signature is valid.
     */
    function verifySignature(receipt) {
        if (!nacl || !nacl.sign) {
            throw new Error(
                'tweetnacl is required for signature verification. ' +
                'Install with: npm install tweetnacl'
            );
        }

        var pubHex = receipt.public_key || 'unsigned';
        var sigHex = receipt.signature || '';

        if (pubHex === 'unsigned' || !sigHex) {
            return false;
        }

        try {
            var pubBytes = hexToBytes(pubHex);
            var sigBytes = hexToBytes(sigHex);
            var message = canonicalBytes(receipt);

            // tweetnacl uses detached verify
            return nacl.sign.detached.verify(message, sigBytes, pubBytes);
        } catch (e) {
            return false;
        }
    }

    // ================================================================
    // STRUCTURAL VALIDATION
    // ================================================================

    /**
     * Validate the count invariant.
     *
     * @param {Object} receipt
     * @returns {string|null} Error message or null.
     */
    function validateCounts(receipt) {
        var checked = receipt.items_checked || 0;
        var passed = receipt.items_passed || 0;
        var failed = receipt.items_failed || 0;
        var excluded = receipt.items_excluded || 0;
        var total = passed + failed + excluded;
        if (checked !== total) {
            return 'Count invariant violated: items_checked=' + checked +
                ' but passed(' + passed + ') + failed(' + failed +
                ') + excluded(' + excluded + ') = ' + total;
        }
        return null;
    }

    /**
     * Validate structural requirements.
     *
     * @param {Object} receipt
     * @returns {string[]} Array of error messages. Empty means valid.
     */
    function validateReceipt(receipt) {
        var errors = [];

        // Required fields
        for (var i = 0; i < REQUIRED_FIELDS.length; i++) {
            if (!(REQUIRED_FIELDS[i] in receipt)) {
                errors.push('Missing required field: ' + REQUIRED_FIELDS[i]);
            }
        }

        // Version
        var version = receipt.svr_version || '';
        if (version && version.indexOf('1.') !== 0) {
            errors.push('Unrecognized major version: ' + version);
        }

        // receipt_id format: PREFIX-YYYYMMDD-HASH8 (prefix is issuer-defined)
        var rid = receipt.receipt_id || '';
        if (rid && rid.indexOf('-') === -1) {
            errors.push("receipt_id must contain at least one '-': " + rid);
        }

        // Count invariant
        var countErr = validateCounts(receipt);
        if (countErr) errors.push(countErr);

        // checked_items length
        var items = receipt.checked_items || [];
        var checked = receipt.items_checked || 0;
        if (items.length !== checked) {
            errors.push('checked_items length (' + items.length +
                ') != items_checked (' + checked + ')');
        }

        // Per-item fields
        for (var i = 0; i < items.length; i++) {
            for (var j = 0; j < CHECKED_ITEM_FIELDS.length; j++) {
                if (!(CHECKED_ITEM_FIELDS[j] in items[i])) {
                    errors.push('checked_items[' + i + '] missing: ' +
                        CHECKED_ITEM_FIELDS[j]);
                }
            }
        }

        return errors;
    }

    // ================================================================
    // PUBLIC API
    // ================================================================

    return {
        canonicalBytes: canonicalBytes,
        canonicalHash: canonicalHash,
        verifySignature: verifySignature,
        validateCounts: validateCounts,
        validateReceipt: validateReceipt,
        EXCLUDED_FIELDS: EXCLUDED_FIELDS,
        REQUIRED_FIELDS: REQUIRED_FIELDS,
        version: '1.0.3'
    };
});
