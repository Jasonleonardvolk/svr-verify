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
        Response = "response.pass.json"
        Receipt  = "receipt.pass.svr.json"
        Expect   = "Structure valid, verdict PASS"
    },
    @{
        Name     = "fail_valid"
        Response = "response.fail.json"
        Receipt  = "receipt.fail.svr.json"
        Expect   = "Structure valid, verdict FAIL"
    },
    @{
        Name     = "invalid_signature"
        Response = "response.pass.json"
        Receipt  = "receipt.invalid-signature.svr.json"
        Expect   = "Signature INVALID, host should reject"
    },
    @{
        Name     = "wrong_response_hash"
        Response = "response.pass.json"
        Receipt  = "receipt.wrong-response-hash.svr.json"
        Expect   = "Response hash mismatch, host should reject"
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
Write-Host "============================================================"
