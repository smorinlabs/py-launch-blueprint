# Feature Pull Request

## Branch Naming Convention
<!-- IMPORTANT: Your branch should follow our naming convention -->
<!-- Format: feature/short-description-of-feature or feature/issue-number-description -->
<!-- Example: feature/user-authentication or feature/123-user-auth -->
Current branch: `<!-- Replace with your branch name -->`

## Related Issue
<!-- IMPORTANT: Please verify this issue number is correct and exists -->
<!-- Use the format: Closes #123 or Fixes #123 to automatically close the issue when this PR is merged -->
Closes #

## Feature Description
<!-- Provide a clear and concise description of the feature being implemented -->
<!-- Example: This PR adds user authentication via OAuth2 with GitHub provider, allowing users to log in with their GitHub accounts. This includes the login flow, user profile creation, and session management. -->

## Implementation Details
<!-- Provide a technical overview of how the feature was implemented -->
<!-- Include architectural decisions and design patterns used -->
<!-- Example:
- Implemented using the Strategy pattern to allow for multiple auth providers in the future
- Used JWT for session management with a 24-hour expiration
- Created a middleware layer to handle authentication checks
-->

## Changes Made
<!-- List the significant changes made to implement this feature -->
<!-- Example:
- Added AuthService class to handle authentication flow
- Created new database migrations for user table
- Updated configuration to support OAuth settings
- Added middleware for authenticated routes
- Created login/logout endpoints
-->
-
-
-

## Testing Performed
<!-- Describe the testing you've done to validate the feature -->
<!-- Include both automated and manual testing -->
<!-- Example:
- Added unit tests for AuthService with 95% coverage
- Added integration tests for authentication flow
- Manually tested login flow on Chrome, Firefox, and Safari
- Verified error handling for invalid credentials
-->

## Pre-commit and Testing Instructions
<!-- Follow these steps to run pre-commit hooks and tests before submitting -->

**Running Pre-commit Hooks:**
```bash
# These are basic defaults for testing.
# Please adjust as needed for complete testing of your changes

# Install pre-commit if not already installed
just pre-commit-setup

# Run pre-commit on all files
just pre-commit-run
```

**Running Tests:**
```bash
# Run all tests
just test
# Note: The `just test` command is a project-specific command for running tests.
# Please refer to the project documentation or the CONTRIBUTING.md file for setup instructions.
```

-->

## Documentation Updates
<!-- Describe any documentation changes made or needed -->
<!-- Include updates to Sphinx docs, README, etc. -->
<!-- Example:
- Updated authentication section in docs/usage.md
- Added new docs/auth.md file with detailed API documentation
- Updated README.md with new authentication instructions
- Added docstrings to all new classes and methods
-->

## Breaking Changes
<!-- List any backwards-incompatible changes this PR introduces -->
<!-- If none, state "None" -->
<!-- Example: The config format has changed, existing config files need to be updated following the migration guide in docs/migrations.md -->

## Checklist
<!-- Please verify each item by checking the box -->
- [ ] Branch name follows convention (`feature/description` or `feature/issue-number-description`)
- [ ] Ran `just check` (full quality pipeline; ITM-066) and it passed locally
- [ ] Commit messages follow Conventional Commits (lowercase subject; commitlint enforces — ITM-039)
- [ ] CHANGELOG.md entry: **none needed** — release-please will add one on PR merge based on conventional-commit messages (ADR-05; ITM-053)
- [ ] Lefthook pre-commit + pre-push hooks ran clean (gitleaks / editorconfig-checker / yamllint / codespell / bandit at push)
- [ ] Testing added to CI/CD pipeline in GitHub Actions
- [ ] Documentation added/updated in Sphinx
- [ ] Appropriate unit test coverage added (run `pytest --cov` to verify)
- [ ] New commands added to CLI (if applicable)
- [ ] All tests pass locally (`pytest` for default; `pytest -m ""` for full incl. slow/live) and in CI
- [ ] Self-review of code performed
- [ ] No debug print statements or commented-out code left in the codebase

## Reviewer Notes
<!-- Any specific areas that need careful review or explanation -->
<!-- Highlight complex parts or areas where you're seeking feedback -->
<!-- Example:
- The authentication flow in auth_service.py:125-150 is complex and needs careful review
- The database migration might need performance review for large datasets
- Security review needed for the token generation logic
-->
