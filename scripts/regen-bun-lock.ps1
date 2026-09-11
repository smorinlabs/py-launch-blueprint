# Regenerate bun.lock FROM SCRATCH for the declared [[regenerate]] rule.
$ErrorActionPreference = "Stop"
if (-not (Get-Command bun -ErrorAction SilentlyContinue)) {
    Write-Error "regen-bun-lock: bun not found"
    exit 127
}
$expected = (Get-Content -Raw (Join-Path $PSScriptRoot "../.bun-version")).Trim()
$actual = (& bun --version | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $actual -ne $expected) {
    Write-Error "regen-bun-lock: expected bun $expected, found $actual; lock preserved"
    exit 1
}
Remove-Item -Force -ErrorAction SilentlyContinue bun.lock
if (Test-Path bun.lock) {
    # A surviving stale lock would keep the old workspace name through
    # `bun install` — fail loud instead of pressing a silent leak.
    Write-Error "regen-bun-lock: could not delete bun.lock"
    exit 1
}
bun install
exit $LASTEXITCODE
