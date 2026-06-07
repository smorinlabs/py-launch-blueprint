// ITM-039 — commitlint config (human-author path).
//
// Extends @commitlint/config-conventional with two body/footer cap raises
// from 100 to 200. The 100-char default routinely fails on commits whose
// bodies reference docs URLs, GitHub action permalinks, or long ITM/ADR
// identifier strings — none of which can be broken across lines. 200
// covers the realistic range while still flagging genuinely unbounded
// paragraphs.
//
// Dependabot PRs use a separate, laxer config
// (commitlint.dependabot.config.mjs) because dependabot embeds full
// release-notes / comparison URLs in its body that frequently exceed 200
// chars. See the commitlint.yml workflow for the per-author split.
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'body-max-line-length': [2, 'always', 200],
    'footer-max-line-length': [2, 'always', 200],
  },
};
