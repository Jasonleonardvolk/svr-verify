Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "============================================================"
Write-Host "MCP T9 Receipt Conformance Capsule"
Write-Host "============================================================"
Write-Host ""
Write-Host "Root: $Root"
Write-Host ""

$Cases = @(
    @{
        Name     = "pass_valid"
        Receipt  = "receipt.pass.svr.json"
        Expect   = "Structure valid, verdict PASS -> host action: ALLOW"
    },
    @{
        Name     = "fail_valid_quarantine"
        Receipt  = "receipt.fail.svr.json"
        Expect   = "Structure valid, verdict FAIL -> host action: QUARANTINE"
    },
    @{
        Name     = "invalid_signature"
        Receipt  = "receipt.invalid-signature.svr.json"
        Expect   = "Signature INVALID -> host action: REJECT"
    },
    @{
        Name     = "wrong_response_hash"
        Receipt  = "receipt.wrong-response-hash.svr.json"
        Expect   = "Response hash mismatch -> host action: REJECT"
    }
)

foreach ($Case in $Cases) {
    Write-Host "------------------------------------------------------------"
    Write-Host "Case: $($Case.Name)"
    Write-Host "Expected: $($Case.Expect)"
    Write-Host ""

    $ReceiptPath = Join-Path $Root $Case.Receipt
    python -m svr_verify $ReceiptPath
    $ExitCode = $LASTEXITCODE

    Write-Host ""
    Write-Host "Exit code: $ExitCode"
    Write-Host ""
}

Write-Host "============================================================"
Write-Host "See expected-behavior.json for the full conformance matrix."
Write-Host "See quarantine-record.example.json for the quarantine record shape."
Write-Host "============================================================"
