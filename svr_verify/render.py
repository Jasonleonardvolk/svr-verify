# svr_verify/render.py
# SVR Receipt Renderer
#
# Produces a self-contained HTML document from any .svr.json dict.
# Uses the same design system as invariant.pro/receipts/receipt-svr.html.
# The HTML is fully self-contained (inline CSS, no external deps except
# Google Fonts and QRCode.js CDN for the QR code).
#
# Usage:
#   from svr_verify.render import render_html
#   html_str = render_html(receipt_dict)
#
#   # Write to file:
#   with open("receipt.html", "w") as f:
#       f.write(render_html(receipt_dict))

from __future__ import annotations
import json
import os
from typing import Any, Dict


def render_html(receipt, template_path=None):
    """Render an SVR receipt dict as a self-contained HTML string.

    The HTML embeds the receipt data as base64 in the URL hash,
    using the same receipt-svr.html template. When opened in a
    browser, it renders the full receipt with dark theme, print
    support, QR code, copy-to-clipboard, and download JSON.

    Args:
        receipt: SVR receipt dict (Python dict, not JSON string).
        template_path: Optional path to a custom receipt-svr.html
                       template. If None, uses the bundled template.

    Returns:
        Complete HTML string ready to write to a file.
    """
    import base64

    # Serialize receipt to compact JSON, then base64
    receipt_json = json.dumps(receipt, ensure_ascii=True, default=str)
    receipt_b64 = base64.b64encode(receipt_json.encode("utf-8")).decode("ascii")

    # Load template
    if template_path and os.path.isfile(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    else:
        # Use the bundled template (same directory)
        bundled = os.path.join(os.path.dirname(__file__), "receipt-svr.html")
        if os.path.isfile(bundled):
            with open(bundled, "r", encoding="utf-8") as f:
                template = f.read()
        else:
            # Fallback: generate a minimal redirect page
            return _minimal_render(receipt, receipt_b64)

    # Inject the receipt data directly into the page so it works
    # without URL hash (for file:// protocol and email attachments)
    inject_script = (
        '<script>window._svrDataDirect = %s;</script>' % receipt_json
    )

    # Insert before closing </head> tag
    if '</head>' in template:
        template = template.replace(
            '</head>',
            inject_script + '\n</head>'
        )

    # Also update the data loading logic to check _svrDataDirect first
    # by prepending a check before the existing hash-based loader
    direct_check = (
        "if(window._svrDataDirect){data=window._svrDataDirect;}"
    )
    # Insert after "var data = null;"
    template = template.replace(
        "var data = null;",
        "var data = null;\n    " + direct_check
    )

    return template


def _minimal_render(receipt, receipt_b64):
    """Fallback: generate a minimal standalone HTML receipt."""
    rid = receipt.get("receipt_id", "SVR")
    verdict = receipt.get("verdict", "unknown")
    fss = receipt.get("filing_safety_status", "REVIEW_REQUIRED")
    ic = receipt.get("items_checked", 0)
    ip = receipt.get("items_passed", 0)
    ifa = receipt.get("items_failed", 0)
    ss = receipt.get("signature_status", "UNSIGNED")

    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>SVR: %s</title>
<style>
body{font-family:monospace;background:#0a0a0c;color:#e8e6e3;padding:40px;max-width:600px;margin:0 auto}
h1{font-size:0.6rem;letter-spacing:0.2em;text-transform:uppercase;color:#4a4842}
.verdict{font-size:1.2rem;font-weight:700;margin:20px 0;padding:10px 30px;display:inline-block;border:3px solid %s;color:%s}
.row{display:flex;padding:3px 0;font-size:0.7rem}.key{color:#4a4842;width:150px}.val{color:#e8e6e3}
</style></head><body>
<h1>Signed Verification Receipt</h1>
<div class="verdict">%s</div>
<div class="row"><span class="key">Receipt ID</span><span class="val">%s</span></div>
<div class="row"><span class="key">Items checked</span><span class="val">%d</span></div>
<div class="row"><span class="key">Passed</span><span class="val">%d</span></div>
<div class="row"><span class="key">Failed</span><span class="val">%d</span></div>
<div class="row"><span class="key">Signature</span><span class="val">%s</span></div>
<div class="row"><span class="key">Verdict</span><span class="val">%s</span></div>
<p style="margin-top:30px;font-size:0.6rem;color:#4a4842">
<a href="https://invariant.pro/receipts/receipt-svr.html#%s" style="color:#2a8a4a">View full receipt</a>
</p>
</body></html>""" % (
        rid,
        "#c4392a" if "UNSAFE" in fss else "#2a8a4a" if "SAFE" in fss else "#d49a6a",
        "#c4392a" if "UNSAFE" in fss else "#2a8a4a" if "SAFE" in fss else "#d49a6a",
        fss.replace("_", " "),
        rid, ic, ip, ifa, ss, verdict,
        receipt_b64,
    )
