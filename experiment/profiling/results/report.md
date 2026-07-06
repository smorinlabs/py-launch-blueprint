# Flox provisioning — root-cause report

- env: macos/arm64 · cache: cold · flox 1.12.1
- total provisioning: 1.3s · Dominant phase: **lock-eval** (1.2s)

## Phase breakdown

| phase | seconds | % | max RSS (MB) | IO read (MB) | IO write (MB) |
| --- | ---: | ---: | ---: | ---: | ---: |
| lock-eval | 1.2 | 92.1% | 23 | 0 | 0 |
| realize-activate | 0.1 | 7.9% | 1 | 0 | 0 |

## Resource attribution

Dominant phase `lock-eval` — classify via the flame graphs / IO below:
- CPU-bound?  on-CPU flame graph hot stacks → (fill)
- Off-CPU (blocked)?  off-CPU flame graph (Linux) → (fill: read/write/futex)
- Disk?  IO write/read MB + biolatency → (fill)
- Network?  bytes downloaded / time → (fill)

## Flame graphs

- (none captured yet)

## Ranked optimization candidates

1. (fill: what · evidence · est. impact · where in flox/nix · upstream-fixable?)
