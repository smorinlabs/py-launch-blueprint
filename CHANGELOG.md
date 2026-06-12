# Changelog

## [2.1.1](https://github.com/smorinlabs/py-launch-blueprint/compare/v2.1.0...v2.1.1) (2026-06-12)


### Bug Fixes

* add PyPI fallback for just installation and fix CI skip paths ([#424](https://github.com/smorinlabs/py-launch-blueprint/issues/424)) ([cb983c0](https://github.com/smorinlabs/py-launch-blueprint/commit/cb983c0b453841c6f25fbea5fb39079dbdd1ccbd))
* **web:** log route=None for unmatched requests; clarify re-raise comment ([fb611be](https://github.com/smorinlabs/py-launch-blueprint/commit/fb611be28fcb62aed2887c79a9e6dba0fd1d6a38))

## [2.1.0](https://github.com/smorinlabs/py-launch-blueprint/compare/v2.0.1...v2.1.0) (2026-06-12)


### Features

* **cli:** error codes with hints, did-you-mean, pager, config init, doctor --bundle ([cee5ef5](https://github.com/smorinlabs/py-launch-blueprint/commit/cee5ef55b8e9bf5a43e0c3d0d6f1d0062ffc2734))
* **cli:** universal CLI polish — error codes, did-you-mean, pager, config init, doctor --bundle, windows paths, llms.txt ([#400](https://github.com/smorinlabs/py-launch-blueprint/issues/400)) ([9ef4271](https://github.com/smorinlabs/py-launch-blueprint/commit/9ef427117353dac3d7499bd1c9e4b88463d1b92f))
* **core:** windows-native default paths and windows ci matrix ([656e803](https://github.com/smorinlabs/py-launch-blueprint/commit/656e8039af185f51b4498b149f32e3e4828cea04))
* **env:** add mise and flox as first-class dev environments ([#403](https://github.com/smorinlabs/py-launch-blueprint/issues/403)) ([55a1bf6](https://github.com/smorinlabs/py-launch-blueprint/commit/55a1bf69b4cb88de6e6a02f2d61f46d108e96ed0))
* **setup:** two-level setup — make bootstrap (level 1) + just setup (level 2) ([#405](https://github.com/smorinlabs/py-launch-blueprint/issues/405)) ([6e268f6](https://github.com/smorinlabs/py-launch-blueprint/commit/6e268f6d549ae13e085346e8d608a163c67d1704))
* **web:** add fastapi service skeleton behind the web extra ([#395](https://github.com/smorinlabs/py-launch-blueprint/issues/395)) ([cdd6e26](https://github.com/smorinlabs/py-launch-blueprint/commit/cdd6e2685280d0977d7e812557cf08a141e5e758))
* **web:** bake in rest api best practices (contract, config, observability) ([#399](https://github.com/smorinlabs/py-launch-blueprint/issues/399)) ([90d1a8b](https://github.com/smorinlabs/py-launch-blueprint/commit/90d1a8bb027838f2e98f00fe25c5adcbb51cecf4))


### Bug Fixes

* **cli:** address coderabbit review findings ([b9fd146](https://github.com/smorinlabs/py-launch-blueprint/commit/b9fd146e4f74b66997de5ea0d9861421e3adb132))
* **cli:** gate pager on a real tty and keep first-run marker out of json mode ([80284cd](https://github.com/smorinlabs/py-launch-blueprint/commit/80284cd325910eb56913dfd0360b440428b01ff9))
* **deps:** drop unused questionary dep and finish ty cutover ([87219ac](https://github.com/smorinlabs/py-launch-blueprint/commit/87219acd83e15f38479674dfe711eb94b8cb58ed))
* **deps:** drop unused questionary dep and finish ty cutover ([#396](https://github.com/smorinlabs/py-launch-blueprint/issues/396)) ([cfaefd7](https://github.com/smorinlabs/py-launch-blueprint/commit/cfaefd795f3e129a39e0162145217b809eb84ff0))
* **docs:** build docs via uv run --group docs; drop broken docs/Makefile ([#402](https://github.com/smorinlabs/py-launch-blueprint/issues/402)) ([d63834d](https://github.com/smorinlabs/py-launch-blueprint/commit/d63834df91e8e17a972b0a912ad4a057f780ad49))
* gitleaks installer exit-trap crash aborting just setup on fresh machines ([85ddaeb](https://github.com/smorinlabs/py-launch-blueprint/commit/85ddaeb219bbb7421ba778d382408df7625014fa))


### Refactor

* **justfile:** remove legacy pip recipes and go toolchain dependency ([#401](https://github.com/smorinlabs/py-launch-blueprint/issues/401)) ([6ab697a](https://github.com/smorinlabs/py-launch-blueprint/commit/6ab697a6ba95f0d2b4e8372e09347219a35c1a66))
* **skill:** relocate to .claude/skills with codex symlink; de-just the runbook ([#409](https://github.com/smorinlabs/py-launch-blueprint/issues/409)) ([29ef63b](https://github.com/smorinlabs/py-launch-blueprint/commit/29ef63b4ec786788626a583efdda0753c8181f57))

## [2.0.1](https://github.com/smorinlabs/py-launch-blueprint/compare/v2.0.0...v2.0.1) (2026-06-11)


### Bug Fixes

* **test:** guard conftest _git() against running outside the temp sandbox ([#392](https://github.com/smorinlabs/py-launch-blueprint/issues/392)) ([078a01f](https://github.com/smorinlabs/py-launch-blueprint/commit/078a01f60231672db11de35987df7553f51c1328))

## [2.0.0](https://github.com/smorinlabs/py-launch-blueprint/compare/v1.1.7...v2.0.0) (2026-06-11)


### ⚠ BREAKING CHANGES

* **cli:** rename to plbp, layered TOML config, dotted config set (phase 1) ([#378](https://github.com/smorinlabs/py-launch-blueprint/issues/378))

### Features

* **ci:** codecov tokenless OIDC upload ([#365](https://github.com/smorinlabs/py-launch-blueprint/issues/365)) ([2e2b2d8](https://github.com/smorinlabs/py-launch-blueprint/commit/2e2b2d8c2c4e8ae0367df24400cb03c0d1caa070))
* **ci:** codecov tokenless OIDC upload ([#369](https://github.com/smorinlabs/py-launch-blueprint/issues/369)) ([68d54da](https://github.com/smorinlabs/py-launch-blueprint/commit/68d54da3fa0e727b577867a9eb0ac1c46ccb713d))
* **cli:** add doctor, config set, and a mutation safety pattern ([9376065](https://github.com/smorinlabs/py-launch-blueprint/commit/93760650c262a5e6dd25effa5736085bd394a274))
* **cli:** add gh-style pylb CLI with core library layer ([fda272d](https://github.com/smorinlabs/py-launch-blueprint/commit/fda272d756ed26cb601e68d7656e15ac608e5a8d))
* **cli:** dual-sink logging with rotating file sink (phase 3) ([#380](https://github.com/smorinlabs/py-launch-blueprint/issues/380)) ([7a6eab9](https://github.com/smorinlabs/py-launch-blueprint/commit/7a6eab9083a86eb6ada69fb1a802e98f900ca678))
* **cli:** gh-style pylb CLI with core library layer + structured logging ([#374](https://github.com/smorinlabs/py-launch-blueprint/issues/374)) ([6922305](https://github.com/smorinlabs/py-launch-blueprint/commit/6922305299b6a184666b8fce703247b360038bdc))
* **cli:** output-file, color precedence, format-from-config (phase 2) ([#379](https://github.com/smorinlabs/py-launch-blueprint/issues/379)) ([8cc36d7](https://github.com/smorinlabs/py-launch-blueprint/commit/8cc36d7f4fb5fa87d9d86edba2b49bb6b0c3deaf))
* **cli:** rename to plbp, layered TOML config, dotted config set (phase 1) ([#378](https://github.com/smorinlabs/py-launch-blueprint/issues/378)) ([03db3f5](https://github.com/smorinlabs/py-launch-blueprint/commit/03db3f505febe5db21d50680dd57da581142b721))
* **config:** xdg-compliant toml config; fix init rebrand completeness ([2ee9cea](https://github.com/smorinlabs/py-launch-blueprint/commit/2ee9ceac57eefe09640f87c88ed663978f2571d6))
* **init:** per-field drift coverage + derive non-contract internals (P01) ([#389](https://github.com/smorinlabs/py-launch-blueprint/issues/389)) ([b85c0af](https://github.com/smorinlabs/py-launch-blueprint/commit/b85c0af937a9b810b1e85933aea1cd25d42f0c46))
* **init:** rebrand the app short name via new app_name identity ([#381](https://github.com/smorinlabs/py-launch-blueprint/issues/381)) ([397cdab](https://github.com/smorinlabs/py-launch-blueprint/commit/397cdab52c14437c2071191c2c287625bc1166c0))
* **init:** reset CHANGELOG.md to a stub on init (fix the release-blocking leak) ([#391](https://github.com/smorinlabs/py-launch-blueprint/issues/391)) ([3dc7057](https://github.com/smorinlabs/py-launch-blueprint/commit/3dc70571ae011c8d27b0f7c185f2bc72dea2cda4))
* **init:** reset CHANGELOG.md to a stub on init instead of rewriting it ([3dc7057](https://github.com/smorinlabs/py-launch-blueprint/commit/3dc70571ae011c8d27b0f7c185f2bc72dea2cda4))


### Bug Fixes

* **dev:** repair broken local lefthook hooks (commitlint, editorconfig-checker, init-tests) ([#372](https://github.com/smorinlabs/py-launch-blueprint/issues/372)) ([16caf01](https://github.com/smorinlabs/py-launch-blueprint/commit/16caf014c070450e44e9f4052c3539f59e82ff70))
* **init:** iter_repo_files honors .gitignore via git ls-files ([4f1d848](https://github.com/smorinlabs/py-launch-blueprint/commit/4f1d8485be1132b02bf1feeaadfe31469d513cc3))
* **init:** manifest-drift hook honors .gitignore ([#360](https://github.com/smorinlabs/py-launch-blueprint/issues/360)) ([4f1d848](https://github.com/smorinlabs/py-launch-blueprint/commit/4f1d8485be1132b02bf1feeaadfe31469d513cc3))


### Refactor

* **cli:** single-source vocabularies, honest config-get source, one-parse config set ([#384](https://github.com/smorinlabs/py-launch-blueprint/issues/384)) ([970b42d](https://github.com/smorinlabs/py-launch-blueprint/commit/970b42d66b9cfe88333ab64423eb1e2f3cdf290a))
* remove legacy py-projects CLI and collapse command_name identity ([#388](https://github.com/smorinlabs/py-launch-blueprint/issues/388)) ([f587e48](https://github.com/smorinlabs/py-launch-blueprint/commit/f587e48b41bcf6535ba1b62f348147294911c48d))


### Reverts

* PR [#365](https://github.com/smorinlabs/py-launch-blueprint/issues/365) — restore 152 files wiped by phantom 'initial commit (fixture)' ([#366](https://github.com/smorinlabs/py-launch-blueprint/issues/366)) ([feb0938](https://github.com/smorinlabs/py-launch-blueprint/commit/feb0938b75709b3c3ffff15fe16be1360ed5c3a6))

## [1.1.7](https://github.com/smorinlabs/py-launch-blueprint/compare/v1.1.6...v1.1.7) (2026-06-07)


### Bug Fixes

* **contributors:** restore well-formed CONTRIBUTORS.md ([7cd28b7](https://github.com/smorinlabs/py-launch-blueprint/commit/7cd28b7f13a0e98de38150cc0b914c7475755241))
* **contributors:** restore well-formed CONTRIBUTORS.md ([#361](https://github.com/smorinlabs/py-launch-blueprint/issues/361)) ([82b4a17](https://github.com/smorinlabs/py-launch-blueprint/commit/82b4a177d7c13c81d10d6c02440aade86424ac08))

## [1.1.6](https://github.com/smorinlabs/py-launch-blueprint/compare/v1.1.5...v1.1.6) (2026-06-04)


### Bug Fixes

* **ci:** explicit ref input for flox-baked image build (checkout correct branch) ([aa65c98](https://github.com/smorinlabs/py-launch-blueprint/commit/aa65c984bea1f28628b58a93e413b6c45577bb2c))
* **ci:** use github.repository_owner in flox-baked image ref (init drift) ([a4b07a5](https://github.com/smorinlabs/py-launch-blueprint/commit/a4b07a5308d55acfd2d789aec4d10f12306f01cd))
* **contributors:** restore contributors-please markers in CONTRIBUTORS.md ([bb8afb9](https://github.com/smorinlabs/py-launch-blueprint/commit/bb8afb980cf8b908eee4aef27c22cc8126131748))
* **contributors:** restore CONTRIBUTORS.md markers ([#356](https://github.com/smorinlabs/py-launch-blueprint/issues/356)) ([3402c51](https://github.com/smorinlabs/py-launch-blueprint/commit/3402c5158a3f9385f017550eaecbc1bfb7554254))

## [1.1.5](https://github.com/smorinlabs/py-launch-blueprint/compare/v1.1.4...v1.1.5) (2026-06-04)


### Bug Fixes

* **contributors:** ignore release-please bot in render ([#351](https://github.com/smorinlabs/py-launch-blueprint/issues/351)) ([086bd2f](https://github.com/smorinlabs/py-launch-blueprint/commit/086bd2f4fa07751db38b52b21207434f69699109))
* **contributors:** ignore release-please-smorinlabs[bot] in render ([28e8090](https://github.com/smorinlabs/py-launch-blueprint/commit/28e809095321bfd92f014d157e4bc1ab0042089e))

## [1.1.4](https://github.com/smorinlabs/py-launch-blueprint/compare/v1.1.3...v1.1.4) (2026-06-04)


### Bug Fixes

* **ci:** bracket-notation for use-cache input; restore comma-separated doc (Copilot) ([0f939b1](https://github.com/smorinlabs/py-launch-blueprint/commit/0f939b1828d1a6c5cbda2508679f7b1bdc846e5d))
* **driver:** robust run-id correlation and exclude failed reps ([5b0c9cc](https://github.com/smorinlabs/py-launch-blueprint/commit/5b0c9ccefbd2f0b6c25fc4ed3265809682910b99))

## [1.1.3](https://github.com/smorinlabs/py-launch-blueprint/compare/v1.1.2...v1.1.3) (2026-05-29)


### Bug Fixes

* correct deprecated SpacesAftertabs key in editorconfig-checker config ([09a05b7](https://github.com/smorinlabs/py-launch-blueprint/commit/09a05b70a7e66c2a74cd2e980356bf286f7787ce))

## [1.1.2](https://github.com/smorinlabs/py-launch-blueprint/compare/v1.1.1...v1.1.2) (2026-05-26)


### Bug Fixes

* **contributors:** filter bot identities from CONTRIBUTORS.md ([d895eb6](https://github.com/smorinlabs/py-launch-blueprint/commit/d895eb69efb4964ff3bf23d50b17b5013e71c026))
* **contributors:** filter bot identities from CONTRIBUTORS.md ([#332](https://github.com/smorinlabs/py-launch-blueprint/issues/332)) ([c31c4b0](https://github.com/smorinlabs/py-launch-blueprint/commit/c31c4b0fba0bc5d317d81ad673adab52b0266c9f))

## [1.1.1](https://github.com/smorinlabs/py-launch-blueprint/compare/v1.1.0...v1.1.1) (2026-05-26)


### Performance Improvements

* **ci:** swap taplo install from cargo build to pre-built binary (~40x faster) ([1f58d5a](https://github.com/smorinlabs/py-launch-blueprint/commit/1f58d5a4945df647da032e538c0f3bdf5986dcc7))
* **ci:** swap taplo install from cargo build to pre-built binary (~40x faster) ([#327](https://github.com/smorinlabs/py-launch-blueprint/issues/327)) ([06c0590](https://github.com/smorinlabs/py-launch-blueprint/commit/06c0590e8076139c8b4311d834e801f8b7633882))

## [1.1.0](https://github.com/smorinlabs/py-launch-blueprint/compare/v1.0.0...v1.1.0) (2026-05-26)


### Features

* add .editorconfig (cross-editor baseline) ([45f9eba](https://github.com/smorinlabs/py-launch-blueprint/commit/45f9eba5b8727bb254f5c8ad7f3b037f3f65f8e6))
* add .editorconfig-checker.json (ITM-009) ([ba8da03](https://github.com/smorinlabs/py-launch-blueprint/commit/ba8da03d7e485a2148ee7c1d6dc554cb821f7fe4))
* add .gitleaks.toml secret-scan config (ITM-004) ([39a6fa1](https://github.com/smorinlabs/py-launch-blueprint/commit/39a6fa13d0b4568c14135abb0a77608a20e0d442))
* add .gitleaksignore (ITM-005) ([df94cea](https://github.com/smorinlabs/py-launch-blueprint/commit/df94ceafa305621754dbc31f8f27f48e11e3325c))
* add .yamllint config (ITM-012) ([3f411d4](https://github.com/smorinlabs/py-launch-blueprint/commit/3f411d47f78f8207d2caab0ba12b8a1d43fdfdbc))
* add 'alternatives considered' field to feature-request (itm-076) ([9252d48](https://github.com/smorinlabs/py-launch-blueprint/commit/9252d48657cc370fd47d2dd635f23c7d10e53937))
* add [project.urls] table (ITM-072) ([2d03d22](https://github.com/smorinlabs/py-launch-blueprint/commit/2d03d22a912c8c68c5c9ed9f0d00ecb21abc93dc))
* add [tool.codespell] config (ITM-015) ([2cb3c71](https://github.com/smorinlabs/py-launch-blueprint/commit/2cb3c71eba0920f7b75edd77920d76f819d6cb4a))
* add actionlint workflow (itm-029) ([3611bee](https://github.com/smorinlabs/py-launch-blueprint/commit/3611beebce2d85dc6bd1c8d1fbc69ad77810487f))
* add automated contributors tracking ([7fe17d9](https://github.com/smorinlabs/py-launch-blueprint/commit/7fe17d908996d96e2ef64e26d7fddcdb71f76750))
* add automated CONTRIBUTORS.md generation using COG ([891f728](https://github.com/smorinlabs/py-launch-blueprint/commit/891f7282b0bba91516830046e82655e80d68454b))
* add bandit + trufflehog ci workflows (itm-027 + itm-031) ([77cffa8](https://github.com/smorinlabs/py-launch-blueprint/commit/77cffa8840066616ec0dda2a637d16f7596eaa11))
* add commitlint.config.mjs (ITM-039) ([323f851](https://github.com/smorinlabs/py-launch-blueprint/commit/323f8510270159ba0463f2e4ef7fc0c990ceef31))
* add editorconfig-checker + yamllint + codespell ci jobs ([88ba93f](https://github.com/smorinlabs/py-launch-blueprint/commit/88ba93fdf12f62f833cea404206b64fdfe234ffa))
* Add force install targets to Makefile and refine setup guide & fix pre-commit fail on _version.py which is autogenerated  ([#256](https://github.com/smorinlabs/py-launch-blueprint/issues/256)) ([b1f4c51](https://github.com/smorinlabs/py-launch-blueprint/commit/b1f4c51d138c768d5594090f4c45d5c5df07a1b0))
* add helper to print PyPI/TestPyPI trusted-publisher form values ([450e261](https://github.com/smorinlabs/py-launch-blueprint/commit/450e261b43582e2328175c64a80d70a15c1575b1))
* add large-file ci guard (itm-028) ([7ac7716](https://github.com/smorinlabs/py-launch-blueprint/commit/7ac7716ef69d6f7f1a048642b1232a84201f045b))
* add lefthook.yml scaffolding (ITM-003) ([a1ff7d1](https://github.com/smorinlabs/py-launch-blueprint/commit/a1ff7d1a5fa3f6c060596bf5595a691ceb89dcf8))
* add LICENSE file (MIT, Steve Morin 2026) (ITM-078) ([6ddcf12](https://github.com/smorinlabs/py-launch-blueprint/commit/6ddcf12e43700407ea3429d723cb2a2aefbc709e))
* add make hook-check (itm-022) ([6ecf9a6](https://github.com/smorinlabs/py-launch-blueprint/commit/6ecf9a686852254f7155462450afbfd7937a4e76))
* add package.json + bun.lock (commitlint deps) (ITM-041) ([5643c9e](https://github.com/smorinlabs/py-launch-blueprint/commit/5643c9ed46f1d8dfef441e463bc21780569d27ae))
* add pre-filing verification to bug-report (itm-075) ([eabbc37](https://github.com/smorinlabs/py-launch-blueprint/commit/eabbc3792c4f48b2f064d49bf4a29122804ca544))
* add pytest marker taxonomy + default exclusion (ITM-046) ([b16ae40](https://github.com/smorinlabs/py-launch-blueprint/commit/b16ae40e900b9a305e33c0f418a5f2400260e04b))
* add script to bootstrap GitHub release environments ([00a0021](https://github.com/smorinlabs/py-launch-blueprint/commit/00a00218f30b1e7ffb3f443d392ed24d61cfca85))
* add scripts/check-gitleaks.sh wrapper (ITM-006) ([f225621](https://github.com/smorinlabs/py-launch-blueprint/commit/f2256217063cbad329d8f8a0cf9634c531f8d6af))
* add scripts/install-bun.sh installer (ITM-042) ([f270169](https://github.com/smorinlabs/py-launch-blueprint/commit/f270169cf66e864aacfdfb5db5f45329933e4d27))
* add scripts/install-gitleaks.sh installer (ITM-007) ([3e841ed](https://github.com/smorinlabs/py-launch-blueprint/commit/3e841ed270f2b21171748685e3fd878c4d50c260))
* add scripts/install-lefthook.sh installer (ITM-021) ([0bad271](https://github.com/smorinlabs/py-launch-blueprint/commit/0bad271d1ffa5768c7689d265193d0831d4d0778))
* bandit pre-push + codeql trio (itm-032 + itm-034/035/036) ([2bad8ed](https://github.com/smorinlabs/py-launch-blueprint/commit/2bad8ed3eacb684cbb668dcdafe510cbcd3e6b42))
* bump Python floor 3.10 -&gt; 3.12 (ITM-033 core) ([7076a55](https://github.com/smorinlabs/py-launch-blueprint/commit/7076a55200d030c9a81fb5abedc4bf3fcbe2af11))
* commitlint ci workflow (itm-037 + itm-038) ([b8f981f](https://github.com/smorinlabs/py-launch-blueprint/commit/b8f981f9822e1ec864eb9f313d21b1ba92b9c1bb))
* dependabot trio + retire cog/gitlint + changelog.yml workflow ([557a615](https://github.com/smorinlabs/py-launch-blueprint/commit/557a6152f80fd476f2081222f46722dc60cf4ae1))
* harden ci workflow (itm-024) ([7eed040](https://github.com/smorinlabs/py-launch-blueprint/commit/7eed040731deb807956e420095e20cb8f875332b))
* implement must-do project infrastructure ([15eef99](https://github.com/smorinlabs/py-launch-blueprint/commit/15eef99df5ea8eae07eac5e5c8ac505b5d72e7a3))
* **init:** add blueprint self-setup system (Phases 0-5) ([344e8eb](https://github.com/smorinlabs/py-launch-blueprint/commit/344e8ebb033435a7aa230e63f4d8636829d9fe76))
* **init:** add new-python-project skill — agent-guided bootstrap runbook ([71f11e2](https://github.com/smorinlabs/py-launch-blueprint/commit/71f11e26f21b06b42332af83b569e1c19d76ff25))
* **init:** add post_init.py — publishing/Codecov/RTD walkthrough ([5f5396e](https://github.com/smorinlabs/py-launch-blueprint/commit/5f5396e8f7c2b337b69cfcb5daa3654794b56d3d))
* integrate codecov for coverage reporting ([b95227f](https://github.com/smorinlabs/py-launch-blueprint/commit/b95227f15fa98d1a65c532b0864f64749b8b9fd2))
* justfile typecheck-&gt;ty + retire cog recipes + delete stale _version.py ([896375d](https://github.com/smorinlabs/py-launch-blueprint/commit/896375d8c1850b8668da3902e711ae14e0d84da2))
* justfile typecheck-&gt;ty + retire cog verify/bump/commit recipes ([ab4a9ed](https://github.com/smorinlabs/py-launch-blueprint/commit/ab4a9edfc9af6f3a84a318fce42f2fa0d5b72995))
* pep 639 license expression + py3.12/3.13 classifiers (ITM-070 partial) ([3d95bc8](https://github.com/smorinlabs/py-launch-blueprint/commit/3d95bc8ad3224b619c6afe9b9a4575ababa003d1))
* portable devcontainer (itm-067) ([bd3057d](https://github.com/smorinlabs/py-launch-blueprint/commit/bd3057dcd6b402a85cf5e0bf5f3b0e06cab9545e))
* pr template + release cutover doc (itm-077 + itm-060) ([9c54ecf](https://github.com/smorinlabs/py-launch-blueprint/commit/9c54ecfd4c34476e5c7eec6ee2239c79f8142e36))
* publish workflow + pypirc template (itm-048/049/050/051 + 059) ([1ec390c](https://github.com/smorinlabs/py-launch-blueprint/commit/1ec390cd8c4162de0f54b3ad1f06fd97c780c27f))
* readme badges + install/dev metadata (itm-081 + itm-082) ([7ccdb8e](https://github.com/smorinlabs/py-launch-blueprint/commit/7ccdb8e2d7df5afde4a78e0d465ff3305da01812))
* reconcile .gitignore (ITM-080 + ITM-064 cascade) ([d1e2156](https://github.com/smorinlabs/py-launch-blueprint/commit/d1e2156070ce0b36641a67a7b928564ad5dbb5e1))
* reconcile ruff config (ITM-018) ([48e3c08](https://github.com/smorinlabs/py-launch-blueprint/commit/48e3c081aa77e7164d789fe97b61156fc442e24c))
* release-please cluster (itm-052 + 053 + 054 + 055 + 056 + 057) ([1bd0344](https://github.com/smorinlabs/py-launch-blueprint/commit/1bd03440ff956cf073c9a0db59bd6f82cfdc1d44))
* retire pre-commit framework (itm-020 partial) ([fe96899](https://github.com/smorinlabs/py-launch-blueprint/commit/fe96899774e90bf4a5d0fc922856ccf7dab6f809))
* seed CHANGELOG.md for release-please (ITM-058) ([976dce8](https://github.com/smorinlabs/py-launch-blueprint/commit/976dce820351412642947dca68319ec2aa85a2bc))
* **skill:** adopt filter-after-trigger pattern — broad Python intent + Step 0 confirmation ([9fcb117](https://github.com/smorinlabs/py-launch-blueprint/commit/9fcb1173768ad8482e0d868cc63b3d99c6124433))
* split ci.yml into per-job structure (itm-025 + itm-026 + itm-030) ([8c98c2a](https://github.com/smorinlabs/py-launch-blueprint/commit/8c98c2ae42457891f1da14ccfd269a24594de4be))
* switch to pep 735 [dependency-groups] (itm-063) ([faba264](https://github.com/smorinlabs/py-launch-blueprint/commit/faba264e7a99c2c75413820bd2718d001a9def42))
* switch to uv_build + static version (adr-06 cutover; itm-073/074/070) ([5456b57](https://github.com/smorinlabs/py-launch-blueprint/commit/5456b57fa63cb0e294545886882c5a20d4ba29bf))
* track uv.lock (ITM-064) ([358a023](https://github.com/smorinlabs/py-launch-blueprint/commit/358a023d59177c4a6f6e589d846c6c2059305338))
* update contributors list and fix script paths ([208bd34](https://github.com/smorinlabs/py-launch-blueprint/commit/208bd346ec986b0e2b57ca742721215f2c42a4b0))
* update documentation to include Justfiles and versioning details ([adb937e](https://github.com/smorinlabs/py-launch-blueprint/commit/adb937e473614d052961312df8b850c3c81075a0))
* update documentation to include Justfiles and versioning details ([de5ac63](https://github.com/smorinlabs/py-launch-blueprint/commit/de5ac63f4ab2bcaa77e81056ad9fea38d304d4e6))
* wire bandit into lefthook pre-push (itm-032) ([a59668b](https://github.com/smorinlabs/py-launch-blueprint/commit/a59668b2d512ff153398fc75296ea3e84933099f))
* wire commitlint into lefthook commit-msg (ITM-040) ([8ef98e2](https://github.com/smorinlabs/py-launch-blueprint/commit/8ef98e2da2c523ad9215c80b75dd38bd75963535))
* wire editorconfig-checker + yamllint + codespell into lefthook pre-commit ([0de9787](https://github.com/smorinlabs/py-launch-blueprint/commit/0de9787ae73ae8960fc5220ca0e9b08c1da57e58))
* wire gitleaks into lefthook pre-commit (ITM-001) ([13672fa](https://github.com/smorinlabs/py-launch-blueprint/commit/13672fa312883efcddd2426f44c20af551987d37))
* wire gitleaks pre-push range scan (ITM-002) ([c89b1ed](https://github.com/smorinlabs/py-launch-blueprint/commit/c89b1ed956adba5705a0d08e4611a64898fedaf6))


### Bug Fixes

* add required permissions for GitHub Action ([af875bd](https://github.com/smorinlabs/py-launch-blueprint/commit/af875bddf4bdaef1e2be500a95c5c57dc704a53c))
* add ty to [dependency-groups].dev so 'uv run ty' works in ci ([d10a537](https://github.com/smorinlabs/py-launch-blueprint/commit/d10a5373d343f134d1407f35aca92adba0ac55d8))
* address all 9 copilot pr-review comments ([a5b8a65](https://github.com/smorinlabs/py-launch-blueprint/commit/a5b8a658fddcf3f514f6133ac02daa8a1bb0b19b))
* bump .windsurfrules + remaining doc reference to python 3.12+ ([8d83499](https://github.com/smorinlabs/py-launch-blueprint/commit/8d8349907f9fdf681b622bc47d4c2fab5242454e))
* bump readthedocs + docs/source python refs to 3.12+ (consistency) ([b07ed28](https://github.com/smorinlabs/py-launch-blueprint/commit/b07ed2836fd5e944d3ca4523845bc5814f8918c6))
* ci typecheck + projects.py _version import after adr-06 cutover ([115e65c](https://github.com/smorinlabs/py-launch-blueprint/commit/115e65cf0837d3091e66e18bca7b25ecd34fbff9))
* **ci:** apply ruff format + fix self-referencing codespell comment ([911dcab](https://github.com/smorinlabs/py-launch-blueprint/commit/911dcabfcc5d7ff22e4e9f96ad91c71d840ec1a3))
* ensure update-contributors branch exists before syncing ([#278](https://github.com/smorinlabs/py-launch-blueprint/issues/278)) ([268d80b](https://github.com/smorinlabs/py-launch-blueprint/commit/268d80bd14c8758d70afbed0fcabbfc9875c879c))
* improve GitHub Action configuration and add debugging ([347fd5f](https://github.com/smorinlabs/py-launch-blueprint/commit/347fd5f77266b7a626be6cdab73530d02267c1e5))
* indent issue-template contact_links list (itm-014 follow-up) ([e4619c6](https://github.com/smorinlabs/py-launch-blueprint/commit/e4619c612517d88f2f5d9866079254b9b73a734b))
* **init:** address CI failures — skill/ exclusion, lint config, codespell, manifest ([dea9b3d](https://github.com/smorinlabs/py-launch-blueprint/commit/dea9b3da476e05fb5f0e4df66405f1f8a0755606))
* **init:** address valid Copilot PR review comments ([2f74de7](https://github.com/smorinlabs/py-launch-blueprint/commit/2f74de7fe0ae7120164ebbd077cb7813d02882e0))
* install lefthook via Bun (ITM-021) ([2a33ec3](https://github.com/smorinlabs/py-launch-blueprint/commit/2a33ec35a861289dee7fde6ba2f21e7399ba4673))
* lefthook.yml — strip skip_output (v2 schema rejected both forms) ([dab7449](https://github.com/smorinlabs/py-launch-blueprint/commit/dab7449cf442a3e60f8d96eefb99e7991c5e9919))
* Refactor lint configuration and re-export main function ([7e78f3e](https://github.com/smorinlabs/py-launch-blueprint/commit/7e78f3e70a05207a0d0f932eb02d80dd7272b6da))
* repair changelog workflow cog config ([4ac53f2](https://github.com/smorinlabs/py-launch-blueprint/commit/4ac53f27edc2c8ee7a492d2bcec04fe97bd5be28))
* restore update-contributors.yml after broken reindent (cleanup) ([60b3933](https://github.com/smorinlabs/py-launch-blueprint/commit/60b3933d1a3131ffd62dee6b88701fc2f2812e23))
* switch to repo-sync/pull-request action ([f4050a6](https://github.com/smorinlabs/py-launch-blueprint/commit/f4050a604c64bb754d2757dd8c2d916434f92a2d))
* tests/test_cli.py _version import after adr-06 cutover ([3767972](https://github.com/smorinlabs/py-launch-blueprint/commit/376797219ea1a1eb37889babf908d06e920bf00d))
* tighten pypirc gitleaks allowlist ([270b47b](https://github.com/smorinlabs/py-launch-blueprint/commit/270b47b0c72eae884c7c8e93ace1a8db9436b8bd))
* update GitHub Action workflow for better compatibility ([5dd2e5d](https://github.com/smorinlabs/py-launch-blueprint/commit/5dd2e5d3e2120b80ad2122b3a2c4bb524db148f7))
* update setup-pypi-publishing.sh to reference publish.yml ([a54e901](https://github.com/smorinlabs/py-launch-blueprint/commit/a54e9012851ebf45d2756b5dd7e56faa2e233e6a))
* update workflow to use Python script instead of cog ([6379b4c](https://github.com/smorinlabs/py-launch-blueprint/commit/6379b4c91c4656ec05ee13940d6b489f4b602abd))
* use awk for more reliable text processing in GitHub Action ([13e73f7](https://github.com/smorinlabs/py-launch-blueprint/commit/13e73f7908f2010803b6c0c37caf569c3efc326a))
* use full ref path in git push command ([8f90a94](https://github.com/smorinlabs/py-launch-blueprint/commit/8f90a9462acfbfbf02bbf6482dd28415b611ef42))
* use PAT for GitHub Action authentication ([fa1e823](https://github.com/smorinlabs/py-launch-blueprint/commit/fa1e82321b0226a682a4e3e2d7a5fbc8a61abbca))
* uv_build module-root for flat layout (itm-074 follow-up) ([6accdce](https://github.com/smorinlabs/py-launch-blueprint/commit/6accdce85d98394dcbf469b82965c26f874f74f3))
* yamllint step-list indentation in must-do workflows ([25b571b](https://github.com/smorinlabs/py-launch-blueprint/commit/25b571b8b56cfed4c85bd79a1d4c07863bb548d5))


### Refactor

* simplify contributors update process ([9f6a6b4](https://github.com/smorinlabs/py-launch-blueprint/commit/9f6a6b4119e6e96f0a1bf5e65bfda602010627d2))
* **skill:** move skill from init/skill/ → skill/ ([48205ed](https://github.com/smorinlabs/py-launch-blueprint/commit/48205edecfd6ec16920776a00362c4d44bb64e38))

## Changelog

Entries below this line are generated by [release-please](https://github.com/googleapis/release-please)
from [Conventional Commits](https://www.conventionalcommits.org/) messages.
Do not edit by hand — the next release PR will overwrite manual changes.
