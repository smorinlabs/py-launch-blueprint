// ITM-039 — commitlint config.
// Baseline only: @commitlint/config-conventional with no overrides.
// Add rule overrides here if friction emerges (round-7 decision).
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Dependabot bodies include long URLs/metadata lines that are not wrapped.
    "body-max-line-length": [0, "always", 100],
  },
};
