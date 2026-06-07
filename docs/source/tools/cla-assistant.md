# CLA Assistant

[CLA Assistant](https://cla-assistant.io) is a tool that automates the process of managing Contributor License Agreements (CLAs) for open source projects. It integrates with GitHub to ensure that all contributors have signed the appropriate CLA before their pull requests can be merged.

### Purpose and Problem Solved
CLA Assistant automates the process of managing Contributor License Agreements (CLAs) for open source projects. It ensures that all contributors have signed the appropriate CLA before their pull requests can be merged, helping maintain legal compliance and reducing manual tracking for maintainers.

### Key Benefits and Value Proposition
- ** maintains legal compliance** and streamlines the contribution process.
- **Automated CLA checks** on every pull request
- **Streamlined contributor experience** with a simple signing process
- **Legal protection** for project maintainers and organizations
- **Easy integration** with GitHub workflows


## Getting Started

### Basic Setup Steps
1. CLA Assistant is already configured for this repository via the [CLA Assistant dashboard](https://cla-assistant.io).
2. The required CLAs (individual and corporate) are stored in `docs/source/contributing/cla/`.
3. When a contributor opens a pull request, CLA Assistant checks if the contributor has signed the appropriate CLA.

### Quick Example
- Open a pull request on GitHub.
- If you have not signed the CLA, the CLA Assistant bot will comment with a link to sign.
- Sign the agreement via the provided link.
- The pull request status will update automatically once the CLA is signed.

## Usage

### Common Use Cases
- **First-time contributors**: Prompted to sign the CLA before their PR can be merged.
- **Returning contributors**: No action needed if the CLA is already signed.
- **Corporate contributors**: Can sign a corporate CLA if contributing on behalf of an organization.

### Command References and Syntax
- No local CLI commands are required. All interactions happen via GitHub pull requests and the CLA Assistant web interface.

## Configuration

### Key Configuration Options
- **CLA documents**: Located in `docs/source/contributing/cla/`.
- **Integration**: Managed via the [CLA Assistant dashboard](https://cla-assistant.io) and GitHub repository settings.

### Example Configuration
- To update the CLA text, edit the markdown files in `docs/source/contributing/cla/`.
- To change integration settings, visit the [CLA Assistant dashboard](https://cla-assistant.io) and log in with your GitHub account.

## Testing

### Standalone Testing
- Open a test pull request from a GitHub account that has not signed the CLA.
- Confirm that the CLA Assistant bot comments and blocks merging until the CLA is signed.

### Project-Specific Testing
- Fork the repository and open a pull request.
- Verify that the CLA Assistant bot appears and the PR status is blocked until the CLA is signed.
- After signing, ensure the PR status updates and merging is allowed.

## Disabling the Feature

### Temporarily or Permanently Disabling
- **Temporarily**: Maintainers can manually override the CLA check in GitHub branch protection rules (not recommended for compliance).
- **Permanently**: Remove the CLA Assistant integration via the [CLA Assistant dashboard](https://cla-assistant.io) and update repository settings to remove required status checks.

### Selective Disabling
- Not supported for individual PRs; the check applies to all contributors and pull requests.

## References

- [CLA Assistant Website](https://cla-assistant.io)
- [GitHub Marketplace: CLA Assistant](https://github.com/marketplace/cla-assistant)
- [Individual CLA](../contributing/cla/individual_cla.md)
- [Corporate CLA](../contributing/cla/corporate_cla.md)
- [Py Launch Blueprint Contribution Guide](../../../../CONTRIBUTING.md)
- [GitHub Docs: About required status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-required-status-checks)
