# Flox deep-profiling playbook

Root-cause flox's CI provisioning cost (see ADR-12 / experiment/FINDINGS.md).
Methodology: top-down — phase breakdown -> resource attribution -> drill. Do NOT
assume CPU; provisioning is usually I/O/network-bound.

## Install tools
- samply (cross-platform CPU sampler): `mise use -g samply` or `cargo install samply`
- macOS: fs_usage (built-in, needs sudo)
- Linux (Lima Ubuntu 24.04 aarch64, vz): `sudo apt install -y bpfcc-tools bpftrace linux-tools-$(uname -r)` + FlameGraph (`git clone https://github.com/brendangregg/FlameGraph`)
  - Confirm eBPF: `ls /sys/kernel/btf/vmlinux`

## Run
- Mac, cold: `experiment/profiling/profile-flox.sh --cache cold`
- Mac, warm: `experiment/profiling/profile-flox.sh --cache warm`
- Lima (deep): `lima experiment/profiling/profile-flox.sh --cache cold --deep`
- Outputs: `experiment/profiling/results/phases.json`, `report.md`, `*.svg` flame graphs.

## Analyze
1. Read `report.md` — find the dominant phase.
2. Open the flame graph for that phase (samply: `samply load realize.flox.json`;
   Linux off-CPU: open `realize.offcpu.svg`).
3. Classify: CPU vs off-CPU (blocked) vs disk vs network.
4. Fill `FINDINGS-perf.md` candidates.

## macOS vs Linux comparison
Run on both; compare phase tables to explain the ~3x macOS penalty (realize/download
vs build vs disk).
