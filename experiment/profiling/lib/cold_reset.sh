# Make the next `flox activate` of $ENV_DIR cold by deleting that env's nix
# store closure. SAFE BY DESIGN: `nix store delete` refuses paths still
# referenced by other gc-roots, so it only removes this env's unshared closure.
# On a disposable Lima VM / container this yields a fully cold store; on a shared
# host store it yields the coldest state possible without breaking other envs.

cold_reset_env() {
  local env_dir="$1"   # path containing .flox (the profiling env)
  local run_link store_path
  # flox materializes the active env under .flox/run/<system>.<name>(.dev)
  run_link="$(ls -d "${env_dir}/.flox/run/"* 2>/dev/null | head -1 || true)"
  if [ -z "$run_link" ]; then
    echo "[cold-reset] no realized env at ${env_dir}/.flox/run — already cold" >&2
    return 0
  fi
  store_path="$(readlink -f "$run_link" 2>/dev/null || true)"
  echo "[cold-reset] deleting closure of ${store_path}" >&2
  # delete the realized env + its closure; nix skips still-referenced paths.
  nix store delete --recursive "$store_path" 2>&1 | tail -3 >&2 || true
  rm -f "$run_link" 2>/dev/null || true
}
