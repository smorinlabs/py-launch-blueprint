// commitlint config for dependabot-authored PRs.
//
// Dependabot's body content is auto-generated from upstream release notes
// and embeds full GitHub compare URLs, changelog links, and dep-tree tables
// that routinely exceed the 200-char cap used for human commits. Dependabot
// exposes no knob to wrap or reformat body content (commit-message: only
// controls prefix/scope on the subject line).
//
// Trade-off: we still extend @commitlint/config-conventional so dependabot
// commits must be valid conventional commits (type, scope, subject) — only
// the line-length checks are relaxed. Per-author selection happens in
// .github/workflows/commitlint.yml via github.event.pull_request.user.login.
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'body-max-line-length': [0, 'always'],
    'footer-max-line-length': [0, 'always'],
  },
};
