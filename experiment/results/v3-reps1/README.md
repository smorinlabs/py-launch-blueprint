# v3 reps=1 snapshot — post-all-fixes

A single-rep (n=1) re-collection of the full matrix with every audit/config fix
active, kept alongside (not replacing) the cleaned reps=5 data in `../REPORT.md`.

**Fixes reflected here:**
- Cross-OS contamination fixed (driver verifies runner OS; here run single-OS at
  a time with `verify_os=false`, so 0 cross-OS contamination by construction).
- Driver `gh` calls `timeout`-guarded (no more hangs).
- All three provisioning toolchains aligned to the SAME 15 tools (mise gained
  `editorconfig-checker` + `make`-via-conda).
- flox-noaction macOS `.pkg` install retry; flox-baked git safe.directory.

**Caveats:** every cell is **n=1** — directional, not statistical. `traditional·
macOS·cold` caught a runner-queue outlier (206s total; its setup/job is a normal
~4s). For statistical claims use the reps=5 `../REPORT.md`; this snapshot's value
is confirming the fixes hold and that mise-at-15-tools costs ~the same as 13.

Coverage: 38 cells (ubuntu 20 + macOS 18; flox-baked is ubuntu-only), 0 empty,
0 cross-OS contamination.
