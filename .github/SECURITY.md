# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Controls

- Automated scanning with GitHub CodeQL
- Dependabot alerts and updates
- Protected main branch
- Required code reviews
- Regular dependency audits
- SAST and SCA scanning
- Secure development practices

## Code Scanning Setup

This project ships **advanced** CodeQL setup: the analysis is configured in
`.github/workflows/codeql.yml` and `.github/codeql/codeql-config.yml`, kept in
version control so it is reviewed in pull requests and inherited by forks.

Because of this, GitHub's **default setup** for code scanning must stay
**disabled**. Enabling both makes the workflow fail at upload with
`CodeQL analyses from advanced configurations cannot be processed when the
default setup is enabled`. To check or disable default setup on your repo
(requires admin):

```bash
# check current state
gh api /repos/<OWNER>/<REPO>/code-scanning/default-setup

# disable it, handing control to the committed workflow
gh api --method PATCH /repos/<OWNER>/<REPO>/code-scanning/default-setup \
  -f state=not-configured
```

## Reporting Vulnerabilities

1. **Private Reporting**: Use GitHub's private vulnerability reporting
2. **Response Time**: Initial response within 48 hours
3. **Process**:
   - Acknowledgment
   - Investigation
   - Fix development
   - Security advisory publication
   - Public disclosure

## Security Best Practices

### For Contributors
- Use secure dependency versions
- Implement input validation
- Follow OWASP guidelines
- No hardcoded secrets
- Validate file operations

### For Users
- Keep dependencies updated
- Use environment variables
- Set appropriate file permissions
- Follow least privilege principle
- Enable 2FA for GitHub access

## Security Measures

### Authentication
- Token-based authentication
- Secure token storage
- Environment variable usage

### Data Protection
- No sensitive data in logs
- Secure file operations
- Input sanitization

## Compliance

Our security practices align with:
- OWASP Top 10
- CWE guidelines
- NIST standards
