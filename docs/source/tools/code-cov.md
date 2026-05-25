# Codecov Integration

[Codecov](https://about.codecov.io/) provides hosted code-coverage reporting integrated with GitHub. This project uploads coverage from CI so each pull request gets a coverage delta and the README badge stays current.

## What is integrated

- **`pytest-cov`** runs alongside the test suite in the `test` job of `.github/workflows/ci.yml`.
- **`codecov/codecov-action@v5`** uploads `coverage.xml` from a single matrix combo (`ubuntu-latest` / Python 3.12) to avoid duplicate reports.
- **`.codecov.yml`** at the repo root configures precision, badge color range (70–100), and PR comment behavior.
- **`just coverage`** runs the same coverage locally and writes `htmlcov/` for browser inspection.

## Running coverage locally

```bash
just coverage              # term + html + xml reports
just open-coverage-report  # open htmlcov/index.html
```

`coverage.xml` and `htmlcov/` are git-ignored.

## CI configuration

The coverage upload step is gated to one matrix combo:

```yaml
- name: Upload coverage to Codecov
  if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12'
  uses: codecov/codecov-action@v5
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: coverage.xml
    flags: unittests
    fail_ci_if_error: false
```

`fail_ci_if_error: false` keeps a Codecov outage from blocking a merge.

## Required setup (one-time per repo)

1. Add the repo on [codecov.io](https://app.codecov.io).
2. Copy the repository upload token from Codecov settings.
3. Add it to GitHub repo settings → **Secrets and variables → Actions** as `CODECOV_TOKEN`.

For public repos, the token is technically optional but recommended (improves rate-limit behavior).

## Configuration reference

The `.codecov.yml` at the repo root:

```yaml
codecov:
  require_ci_to_pass: yes

coverage:
  precision: 2
  round: down
  range: "70...100"

comment:
  layout: "reach,diff,flags,footer"
  behavior: default
  require_changes: true

flags:
  unittests:
    paths:
      - tests/
```

- `range: "70...100"` only affects the badge color (red below 70, yellow 70–100, green at 100). It does **not** fail CI.
- `comment.require_changes: true` keeps Codecov from commenting on PRs where coverage is unchanged.

## Disabling

- **Temporarily:** comment out the `Upload coverage to Codecov` step in `.github/workflows/ci.yml`.
- **Permanently:** remove that step, delete `.codecov.yml`, remove the README badge, and remove `CODECOV_TOKEN` from repo secrets.

## References

- [Codecov docs](https://docs.codecov.com/)
- [`codecov/codecov-action`](https://github.com/codecov/codecov-action)
- [`pytest-cov`](https://pytest-cov.readthedocs.io/)
