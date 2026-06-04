# flox-ci-base — P0 scaffold

A Flox-preloaded GitHub Actions container image that bakes the `test` job's setup
(python + uv + warm dependency cache) into the image, so the running job executes
only the real test commands. Initial-verification scaffold for the experiment in
[`docs/superpowers/specs/2026-06-03-flox-ci-base-prd.md`](../../docs/superpowers/specs/2026-06-03-flox-ci-base-prd.md).

**Mirrors the REAL `test` job** of this repo (not the PRD's placeholder values):
python **3.12**, `uv sync --group dev`, `uv run pytest -m "" --cov`.

## Files
- `.flox/env/manifest.toml` — the baked env: `python312` + `uv` (the `setup-python`
  + `setup-uv` replacement). `UV_PYTHON_PREFERENCE=only-system` forces uv onto the
  Flox-provided interpreter.
- `Dockerfile` — pinned Flox install (1.12.2, arch-detected) + realize env at build
  + warm `uv sync --group dev`. `BASE` arg selects the arm (default minimal
  `ubuntu:24.04`; faithful `ghcr.io/catthehacker/ubuntu:act-24.04`).
- `consumer-ci-baked.yml` — reference treatment workflow (not wired into CI).
- `smoke-test.sh` — local build + end-to-end verification.

## Initial verification (P0)
Requires Docker running.
```bash
experiment/flox-ci-base/smoke-test.sh
```
Builds the minimal-base image (native arch), then proves: flox activates, python
3.12 + uv are baked, the uv cache is warm, and the real consumer flow
(`uv sync --group dev` + `uv run pytest`) runs.

## Status
- **P0 (this scaffold):** minimal base, one Python (3.12), native-arch local build.
- **Not yet:** GHCR publish, faithful base arm, amd64×arm64 matrix, the §7 benchmark
  vs. unmodified `ci.yml`. Those follow once the mechanics are verified.

## Notes / deviations from the PRD
- Commands/python adapted to this repo's **actual** `test` job (PRD assumed
  3.10/3.11 + `uvx mypy/ruff/pytest`; real job is 3.12/3.13 + `uv run pytest`).
- Flox **pinned** to 1.12.2 (the PRD sketch used the unversioned latest alias);
  both URLs resolve, pinning is for reproducible builds.
- Namespace `ghcr.io/smorinlabs/...` for verification here (the dedicated
  `ghcr.io/flox/flox-ci-base` is the PRD's eventual home).
