#!/bin/sh
# Regenerate bun.lock FROM SCRATCH for the declared [[regenerate]] rule.
# `bun install` never rewrites an existing lockfile's workspace name, so a
# pressed identity survives in bun.lock unless the lock is removed first.
set -e
# check-tools resolves this script, not the bun inside it: a missing bun
# must fail here with the lock still intact, before the rm.
command -v bun >/dev/null 2>&1 || { echo "regen-bun-lock: bun not found" >&2; exit 127; }
rm -f bun.lock
exec bun install
