#!/bin/sh
# Regenerate bun.lock FROM SCRATCH for the declared [[regenerate]] rule.
# `bun install` never rewrites an existing lockfile's workspace name, so a
# pressed identity survives in bun.lock unless the lock is removed first.
set -e
# check-tools resolves this script, not the bun inside it: a missing bun
# must fail here with the lock still intact, before the rm.
command -v bun >/dev/null 2>&1 || { echo "regen-bun-lock: bun not found" >&2; exit 127; }
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
expected=$(tr -d '\r' < "$SCRIPT_DIR/../.bun-version")
actual=$(bun --version)
if [ "$actual" != "$expected" ]; then
    echo "regen-bun-lock: expected bun $expected, found $actual; lock preserved" >&2
    exit 1
fi
rm -f bun.lock
exec bun install
