# Regenerate bun.lock FROM SCRATCH for the declared [[regenerate]] rule.
$ErrorActionPreference = "Stop"
if (-not (Get-Command bun -ErrorAction SilentlyContinue)) {
    Write-Error "regen-bun-lock: bun not found"
    exit 127
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
