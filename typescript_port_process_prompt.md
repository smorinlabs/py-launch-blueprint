# TypeScript Port Process Prompt

You are helping port a mature Python template project into a TypeScript clone.

This is **not** a blind one-to-one migration. Treat it as a deliberate **port**: preserve intent, capabilities, quality bars, workflows, and developer experience, while replacing Python-specific implementation details with TypeScript/Node ecosystem equivalents where appropriate.

The source project contains deliberate work across CLI behavior, versioning, web support, logging, documentation, linting, CI, release workflows, configuration, testing, packaging, and developer ergonomics.

Your job is to inspect every file, understand its purpose, identify the features and best-practice decisions embedded in it, review my existing repos for prior technology decisions, research TypeScript equivalents where needed, create a phased port plan, and then implement the port in tested vertical slices.

Do not assume every file maps one-to-one. Some files can be copied nearly identically. Some need small edits. Some need ecosystem-equivalent replacements. Some should be decomposed into multiple files. Some may not apply at all.

---

## Required Phase Order

Follow this order exactly:

1. **Create `TS_PORT_INDEX.md`**
   - Catalog every source file.
   - Identify purpose, capabilities, best-practice intent, Python-specific assumptions, possible TypeScript equivalents, and validation strategy.

2. **Extract embedded features and best practices**
   - Review the indexed files at the feature level.
   - Identify deliberate behavior around CLI, logging, versioning, config, docs, CI, testing, release, packaging, and developer experience.

3. **Create `TS_EXISTING_REPO_REVIEW.md`**
   - Review my recent and relevant existing repos.
   - Identify TypeScript, Bun, Oxide, TurboRepo, CI, release, docs, linting, testing, logging, and developer workflow decisions already made.
   - Treat recent deliberate choices as defaults unless there is a strong reason to deviate.
   - Preserve cross-platform tooling that does not need replacement.

4. **Create `TS_PORT_RESEARCH.md`**
   - Research TypeScript/Node equivalents only after considering existing repo decisions.
   - Separate decisions into reuse, adapt, fresh research, preserve cross-platform tool, replace Python-specific tool, or omit.

5. **Create `TS_PORT_PLAN.md`**
   - Define vertical implementation slices.
   - Base the plan on the index, feature extraction, existing repo review, and research.

6. **Maintain `TS_PORT_LOG.md` during implementation**
   - Record what actually changed.
   - Capture deviations from the plan.
   - Log validation results and follow-up tasks.

---

## Phase 1: Create the TypeScript Port Index

Before implementation, create a file named:

```text
TS_PORT_INDEX.md
```

This index must catalog **every file** in the source Python template project.

Use commands like:

```bash
find . -type f | sort
```

Also inspect hidden files, CI files, generated files, scripts, docs, examples, lockfiles, tests, fixtures, editor config, hooks, and template files.

Do not begin implementation until every file has at least a preliminary entry in `TS_PORT_INDEX.md`.

For each source file, include:

1. **Source path**
2. **Likely target path**
3. **Port category**
   - Copy as-is
   - Copy then modify
   - Translate to TypeScript equivalent
   - Replace with TypeScript/Node ecosystem equivalent
   - Split into multiple files
   - Merge into another file
   - Omit with reason
   - Needs research
4. **Purpose of the file**
5. **Features/capabilities contained in the file**
6. **Best-practice intent**
7. **Python-specific assumptions**
8. **Likely TypeScript/Node equivalent**
9. **Open questions**
10. **Validation strategy**
11. **Status**
    - Indexed
    - Needs research
    - Researched
    - Planned
    - Implemented
    - Tested
    - Verified

The index is not merely a list of files. It is a structured understanding of what the Python template does and what must be preserved, replaced, modified, or intentionally omitted in the TypeScript port.

---

## Phase 2: Identify Embedded Features and Best Practices

After the initial index is complete, review the project again at the feature level.

The Python project may contain deliberate design choices that are not obvious from file names alone. Identify these explicitly.

Pay special attention to:

- CLI behavior
- Command structure
- CLI flags and options
- Versioning behavior
- Release behavior
- Logging conventions
- Error handling
- Configuration loading
- Environment variable handling
- Web/server support
- Testing strategy
- Test fixtures
- Documentation conventions
- Open-source readiness
- CI checks
- GitHub Actions
- Linting
- Formatting
- Type checking
- Pre-commit or left-hook behavior
- Package publishing
- Dependency management
- Example projects
- Developer onboarding
- Security or supply-chain hygiene

For each meaningful feature or capability, update `TS_PORT_INDEX.md` with notes about where it appears and how it should be represented in the TypeScript project.

Do not reduce a source file to “Python file → TypeScript file.” Instead, identify the underlying feature or best-practice decision.

Example:

```text
The Python CLI module is not just source code. It contains command structure, argument parsing, help text conventions, logging behavior, version display, error handling, and exit-code behavior. Each of those must be ported or intentionally changed.
```

---

## Phase 3: Review Existing Repos for Prior TypeScript Decisions

After `TS_PORT_INDEX.md` is created and the embedded Python project features have been identified, review my existing repositories before doing fresh TypeScript ecosystem research.

The goal is to avoid re-deciding technologies we have already researched, selected, and standardized elsewhere.

I have existing repositories, including recent TypeScript projects, that may already contain deliberate decisions around tools such as:

- Bun
- Oxide
- TurboRepo
- TypeScript configuration
- package management
- monorepo structure
- build tooling
- linting
- formatting
- testing
- CI
- GitHub Actions
- release/versioning workflows
- package publishing
- documentation
- logging
- CLI structure
- developer workflow
- left-hook or other Git hook tooling

Create a file named:

```text
TS_EXISTING_REPO_REVIEW.md
```

This document should capture patterns and prior decisions from my existing repos.

For each relevant repo reviewed, include:

1. **Repo name**
2. **Why it is relevant**
3. **Recency**
4. **Language/runtime stack**
5. **Package manager**
6. **Build system**
7. **Monorepo tooling, if any**
8. **TypeScript configuration patterns**
9. **Linting and formatting approach**
10. **Testing approach**
11. **CI/GitHub Actions patterns**
12. **Release/versioning approach**
13. **Documentation approach**
14. **CLI or app structure patterns**
15. **Logging/configuration patterns**
16. **Reusable decisions**
17. **Decisions that should not be reused**
18. **Open questions**

Prioritize the most recent and most actively maintained repos, especially repos that already contain TypeScript.

Use the existing repos as a source of institutional memory. If a technology choice has already been made deliberately in a recent repo, treat it as the default choice unless there is a strong reason to deviate.

Examples:

- If recent repos have standardized on Bun, do not casually re-select npm, pnpm, or yarn.
- If recent repos use TurboRepo for monorepo structure, consider that the default for similar repo shapes.
- If recent repos use Oxide or other specific tooling, investigate whether that decision applies here before choosing an alternative.
- If left-hook is already used cross-platform, preserve it instead of replacing it.
- If shared GitHub Actions patterns exist, adapt them rather than starting from scratch.
- If shared TypeScript compiler settings exist, reuse or extend them unless this project has a specific reason not to.

Cross-platform tools should not be re-selected unnecessarily.

If a tool or pattern is already language-agnostic and works for both Python and TypeScript, preserve it when possible. Examples may include:

- left-hook
- EditorConfig
- GitHub issue templates
- GitHub PR templates
- CODEOWNERS
- release note templates
- shared shell scripts
- CI workflow structure
- security scanning
- dependency update config
- repo hygiene files

Do not replace these simply because the implementation language is changing.

The output of `TS_EXISTING_REPO_REVIEW.md` should feed directly into `TS_PORT_RESEARCH.md`.

When doing later TypeScript research, classify each technology decision as one of:

- **Reuse existing repo decision**
- **Adapt existing repo decision**
- **Fresh research required**
- **Keep source Python repo cross-platform tool**
- **Replace Python-specific tool with TypeScript equivalent**
- **Omit with rationale**

If existing repo patterns and fresh research disagree, document the tradeoff explicitly.

Prefer consistency with my existing repos when:

- The existing choice is recent
- The existing choice is working well
- The project shape is similar
- The choice affects contributor experience
- The choice affects shared workflows
- The choice is already used across multiple repos

Prefer a new choice only when:

- The existing choice is stale
- The existing choice does not fit this project
- The TypeScript ecosystem has clearly moved
- The source project has different constraints
- The new choice materially improves maintainability, performance, simplicity, or open-source usability

Do not silently diverge from established repo patterns.

---

## Phase 4: Create TypeScript Port Research

Before choosing TypeScript tools or patterns, create a file named:

```text
TS_PORT_RESEARCH.md
```

This research document should drive the tool and architecture selections for the port plan.

Research TypeScript/Node ecosystem equivalents for Python-specific tooling, libraries, and conventions, but only after reviewing the existing repo decisions in `TS_EXISTING_REPO_REVIEW.md`.

Research areas should include, where relevant:

- Package manager
- Runtime target
- Build system
- TypeScript compiler configuration
- Module format
- CLI framework
- Logging library
- Config loading
- Schema validation
- Test runner
- Assertion/mocking strategy
- Linting
- Formatting
- Type checking
- Git hooks / left-hook integration
- Documentation system
- API docs generation
- Release/versioning tooling
- npm package publishing
- GitHub Actions best practices
- Security scanning
- Dependency update strategy
- Open-source project conventions

For each research topic, include:

1. **Source Python tool or pattern**
2. **Purpose in the original project**
3. **Existing repo decision, if any**
4. **Decision classification**
   - Reuse existing repo decision
   - Adapt existing repo decision
   - Fresh research required
   - Keep source Python repo cross-platform tool
   - Replace Python-specific tool with TypeScript equivalent
   - Omit with rationale
5. **TypeScript/Node options considered**
6. **Recommended choice**
7. **Rationale**
8. **Tradeoffs**
9. **Migration implications**
10. **Validation strategy**
11. **Decision status**
    - Proposed
    - Accepted
    - Rejected
    - Needs follow-up

Use research to preserve the intent of the source project, not merely replace tools by name.

For example:

- A Python linter config should become the best TypeScript linting strategy.
- A Python formatter config should become the best TypeScript formatting strategy.
- Python type checking should map to TypeScript compiler checks and any supplementary checks.
- Python package publishing should map to npm package publishing.
- Python documentation conventions should map to TypeScript-appropriate documentation conventions.
- Python release automation should map to TypeScript/npm release automation.

Where a tool should remain shared across both ecosystems, such as `left-hook`, preserve it and adapt the commands.

Do not re-select technologies that are already cross-platform and still fit the project.

---

## Phase 5: Create the TypeScript Port Plan

After `TS_PORT_INDEX.md`, `TS_EXISTING_REPO_REVIEW.md`, and `TS_PORT_RESEARCH.md` exist, create a file named:

```text
TS_PORT_PLAN.md
```

The port plan should define the actual implementation sequence.

Implement in **vertical slices**, not broad horizontal layers.

A vertical slice should include enough functionality to be useful and testable end-to-end.

Examples of good slices:

1. Project skeleton + package manager + TypeScript config + basic test command
2. CLI entrypoint + one command + logging + tests
3. Versioning behavior + release metadata + tests
4. Config loading + validation + tests
5. GitHub Actions for install, lint, typecheck, and tests
6. Documentation scaffold + one migrated documentation page
7. Full CLI parity pass
8. Packaging and npm publishing dry run
9. Final polish, docs, examples, and verification

Each slice should include:

- Goal
- Source files/features involved
- Target files/features created or modified
- Research decisions applied
- Existing repo decisions reused or adapted
- Implementation tasks
- Tests
- Documentation updates
- CI validation
- Risks
- Definition of done

Do not port all configs first, then all source, then all tests. Build thin working paths and expand them.

---

## Phase 6: Maintain the TypeScript Port Log

During implementation, maintain a file named:

```text
TS_PORT_LOG.md
```

This log records what was actually done.

Use it to capture decisions, deviations, implementation notes, and validation results as the port progresses.

Every meaningful porting decision should be logged, especially when:

- The implementation differs from `TS_PORT_PLAN.md`
- A file is copied and modified instead of rewritten
- A Python tool is replaced with a TypeScript/Node equivalent
- A feature is preserved but implemented differently
- A source file maps to multiple target files
- Multiple source files collapse into one target file
- A Python-specific capability is omitted
- A CI check changes
- A dependency choice is made
- A documentation system changes
- A testing, linting, formatting, release, or versioning workflow changes
- An existing repo decision is reused
- An existing repo decision is adapted
- An existing repo decision is rejected
- A reviewer identifies an issue
- A validation step fails or requires rework

Each log entry should include:

1. **Date**
2. **Phase or slice**
3. **Source file(s)**
4. **Target file(s)**
5. **Decision or change**
6. **Rationale**
7. **Existing repo influence, if any**
8. **Deviation from plan, if any**
9. **Alternatives considered**
10. **Validation performed**
11. **Result**
12. **Follow-up tasks**

The log should not duplicate the index, repo review, research, or plan.

- The index says what exists.
- The repo review says what prior decisions already exist.
- The research says what should be chosen.
- The plan says what should happen.
- The log says what actually happened.

---

## Porting Methodology

### 1. Preserve Intent, Not Syntax

For each file, identify the intent behind it.

Examples:

- A Python linter config should become the best TypeScript linting equivalent.
- A Python formatter config should map to the TypeScript formatter strategy.
- A Python packaging file should map to the TypeScript package publishing setup.
- A Python docs system should map to a TypeScript-appropriate docs system.
- A Python CLI implementation should become a TypeScript CLI implementation with equivalent UX.
- A GitHub Action should preserve the underlying quality gate, not blindly copy Python commands.

### 2. Copy Generic Files Where Possible

Where files are mostly language-agnostic, copy them over first, then modify only the necessary subset.

Examples may include:

- `.gitignore`
- `.editorconfig`
- GitHub issue templates
- Pull request templates
- CODEOWNERS
- LICENSE
- README structure
- contribution docs
- release templates
- shared shell scripts
- left-hook configuration, if already language-neutral
- GitHub Actions that contain reusable structure

When copying and modifying, record the decision in `TS_PORT_LOG.md`.

### 3. Replace Ecosystem-Specific Tools Thoughtfully

For Python-specific tools, research and select TypeScript/Node equivalents.

For each replacement, document:

- What the Python tool did
- Whether my existing repos already selected a relevant equivalent
- What TypeScript tool replaces it
- Why that tool is the best fit
- What tradeoffs exist
- How the replacement will be validated

Do not make casual ecosystem choices. Some choices affect long-term maintainability, contributor experience, CI speed, package quality, and release safety.

### 4. Map Features, Not Just Files

For source files that contain meaningful behavior, map feature-to-feature.

For each substantial source file, identify:

- Public API
- CLI commands and flags
- Logging behavior
- Versioning behavior
- Configuration behavior
- Error handling behavior
- File system behavior
- Web/server behavior, if any
- Environment variable behavior
- Test coverage
- Documentation expectations
- Developer workflow implications

Then decide how each feature should be represented in the TypeScript project.

### 5. Handle Non-One-to-One Mappings Explicitly

When a file does not map directly, document the mapping.

Examples:

- One Python module becomes several TypeScript files.
- Several Python modules become one TypeScript module.
- A Python package config becomes `package.json`, `tsconfig.json`, and release config.
- A Python docs setup becomes a TypeScript documentation site.
- A Python CLI file becomes a command router plus command-specific files.
- Python tests become TypeScript tests with a different structure.

Do not force structural similarity when the TypeScript ecosystem has a clearer convention.

### 6. Reuse Structure Where It Makes Sense

Where the source code structure is still helpful, preserve it.

Reuse naming, folder boundaries, conceptual modules, and documentation structure when they improve continuity.

Prefer TypeScript conventions when the Python structure becomes awkward, misleading, or non-idiomatic.

### 7. Preserve Cross-Platform Decisions

Do not replace tools merely because the implementation language is changing.

If a tool, workflow, config, or repo convention is already cross-platform and still fits the TypeScript clone, preserve it.

Examples:

- left-hook
- EditorConfig
- issue templates
- PR templates
- CODEOWNERS
- shared scripts
- CI workflow shape
- release note structure
- repo hygiene files

When in doubt, check both the source Python repo and my existing repos before changing it.

---

## Validation Requirements

For every ported file or feature, define how it will be validated.

Possible validation methods:

- Unit tests
- Integration tests
- CLI smoke tests
- Type checking
- Linting
- Formatting check
- GitHub Action dry run
- Package build
- npm package publish dry run
- Documentation build
- Manual command execution
- Snapshot comparison
- Behavior comparison against the Python template

Where the original Python project has behavior, compare the TypeScript behavior against it.

---

## Sub-Agent Review Process

Use sub-agents or independent review passes to check the work.

At minimum, run these review passes:

### Reviewer 1: Completeness Auditor

Check that every source file appears in `TS_PORT_INDEX.md`.

Verify that no dotfiles, CI files, tests, docs, scripts, fixtures, or config files were missed.

### Reviewer 2: Feature Extraction Reviewer

Check whether meaningful project capabilities were identified.

Focus on CLI behavior, logging, versioning, configuration, release workflows, docs, tests, CI, and developer experience.

### Reviewer 3: Existing Repo Pattern Reviewer

Check whether relevant existing repos were reviewed before fresh research.

Verify that prior TypeScript, Bun, Oxide, TurboRepo, CI, release, docs, linting, testing, logging, and developer workflow decisions were captured.

Flag any places where the port re-selects a technology that was already deliberately chosen elsewhere.

### Reviewer 4: Ecosystem Fit Reviewer

Check whether TypeScript/Node replacements are idiomatic.

Flag Python-shaped decisions that should be replaced with better TypeScript ecosystem conventions.

### Reviewer 5: Port Plan Reviewer

Check whether `TS_PORT_PLAN.md` follows from `TS_PORT_INDEX.md`, `TS_EXISTING_REPO_REVIEW.md`, and `TS_PORT_RESEARCH.md`.

Verify that the implementation order uses vertical slices and has clear definitions of done.

### Reviewer 6: Feature Parity Reviewer

Check whether important source project capabilities were preserved.

Focus on user-facing behavior, CLI semantics, logging behavior, versioning, config behavior, docs, release, and CI.

### Reviewer 7: Implementation Reviewer

Check the actual code and config changes.

Verify that the implementation matches `TS_PORT_INDEX.md`, `TS_EXISTING_REPO_REVIEW.md`, `TS_PORT_RESEARCH.md`, `TS_PORT_PLAN.md`, and `TS_PORT_LOG.md`.

### Reviewer 8: Test and CI Reviewer

Check that validation is real, not superficial.

Verify that linting, formatting, typechecking, tests, builds, documentation builds, and smoke tests are meaningful.

Each reviewer should produce findings with:

- Severity
- File or feature affected
- Issue
- Recommendation
- Whether it blocks progress

---

## Working Rules

- Do not skip files.
- Do not start implementation before creating `TS_PORT_INDEX.md`.
- Do not create `TS_PORT_RESEARCH.md` before reviewing relevant existing repos in `TS_EXISTING_REPO_REVIEW.md`.
- Do not create `TS_PORT_PLAN.md` before completing `TS_PORT_INDEX.md`, `TS_EXISTING_REPO_REVIEW.md`, and the initial `TS_PORT_RESEARCH.md`.
- Do not assume one-to-one mapping.
- Do not blindly copy Python-specific patterns.
- Do not rewrite files unnecessarily when copy-and-modify is safer.
- Do not omit a feature without documenting the reason.
- Do not pick ecosystem tools casually when the choice affects long-term maintainability.
- Do not re-select cross-platform tools that still fit.
- Do not silently diverge from established repo patterns.
- Do not implement large horizontal batches without validation.
- Prefer small, working, tested vertical slices.
- Keep `TS_PORT_INDEX.md`, `TS_EXISTING_REPO_REVIEW.md`, `TS_PORT_RESEARCH.md`, `TS_PORT_PLAN.md`, and `TS_PORT_LOG.md` updated continuously.
- When uncertain, classify the item as `Needs research` and investigate before implementing.
- Make deliberate choices and document them.

---

## Expected Final Output

By the end of the process, the TypeScript clone should have:

1. A complete `TS_PORT_INDEX.md`
2. A complete `TS_EXISTING_REPO_REVIEW.md`
3. A complete `TS_PORT_RESEARCH.md`
4. A phased `TS_PORT_PLAN.md`
5. A maintained `TS_PORT_LOG.md`
6. A TypeScript project structure that reflects the original project’s intent
7. Equivalent or intentionally improved tooling
8. Consistency with my existing repo decisions where appropriate
9. Equivalent CLI, versioning, logging, config, docs, release, and CI capabilities where applicable
10. Clear documentation of any deliberate omissions
11. Passing validation for each implemented vertical slice
12. Reviewer findings resolved or explicitly accepted with rationale

The goal is not to make the TypeScript project look exactly like the Python project.

The goal is to make the TypeScript project carry forward the same product quality, developer experience, open-source readiness, and operational discipline in the idioms of the TypeScript ecosystem, while respecting prior technology decisions already made across my repos.

---

## Short Prepend Instruction

First create `TS_PORT_INDEX.md` by cataloging every source file and extracting the features, capabilities, and best-practice intent embedded in each one. Then create `TS_EXISTING_REPO_REVIEW.md` by reviewing my recent and relevant existing repos for prior TypeScript, Bun, Oxide, TurboRepo, CI, release, docs, linting, testing, logging, and developer workflow decisions. Then create `TS_PORT_RESEARCH.md` to choose idiomatic TypeScript/Node equivalents, reusing or adapting existing repo decisions where appropriate and preserving cross-platform tooling that still fits. Only after that, create `TS_PORT_PLAN.md` for phased vertical-slice implementation. During implementation, maintain `TS_PORT_LOG.md` to record what actually changed, where the work deviated from the plan, and how each slice was validated.
