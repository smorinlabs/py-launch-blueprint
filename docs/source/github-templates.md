# GitHub Issue and PR Templates

![GitHub](https://img.shields.io/badge/github-templates-blue)

## Introduction

GitHub issue and pull request templates are powerful features that help standardize and streamline contributions to your project. They provide structured forms for contributors to fill out when creating issues or pull requests, ensuring that you receive all the necessary information upfront and reducing back-and-forth communication.

This guide explains how GitHub templates work, how they're configured in this project, and how you can customize them for your own needs.

## What Are GitHub Templates?

GitHub templates are pre-defined forms that automatically populate when someone creates a new issue or pull request in your repository. They help:

- Guide contributors on what information to provide
- Collect consistent, structured data for each submission
- Improve the quality of bug reports and feature requests
- Streamline the review process
- Reduce incomplete submissions

## Templates in This Project

This project includes several template types:

### Issue Templates

We've created three distinct issue templates using GitHub's YAML-based issue forms:

1. **Bug Report** (`bug-report.yml`): For reporting errors or unexpected behavior
2. **Feature Request** (`feature-request.yml`): For suggesting new features or enhancements
3. **Documentation Request** (`documentation-request.yml`): For requesting new or improved documentation

Each template collects specific information relevant to that type of issue, using various form components like dropdowns, text areas, and checkboxes.

### Pull Request Template

We use a standard Markdown-based pull request template (`PULL_REQUEST_TEMPLATE.md`) that prompts contributors to:

- Describe the changes they've made
- Reference related issues
- Confirm they've tested their changes
- List any required follow-up work

## How Templates Work

When a contributor clicks "New Issue" on your repository, they'll see options for each of your configured templates:

```
[Bug Report]  [Feature Request]  [Documentation Request]  [Open a blank issue]
```

They select the appropriate template, which presents them with a form to complete. Once submitted, the issue is created with all the structured information and any automatically applied labels.

Pull request templates work similarly but are automatically loaded when someone creates a new pull request.

## Template Configuration

### Issue Templates Structure

Issue templates are stored in the `.github/ISSUE_TEMPLATE/` directory as YAML files. Each template has:

- A name and description
- An optional title prefix
- Optional automatic labels
- A body with form elements

### Anatomy of a Template

Here's an example of the structure for our feature request template:

```yaml
name: Feature Request
description: Suggest a new feature or enhancement
title: "[FEATURE]: "
labels: ["enhancement", "feature-request"]

body:
  - type: markdown
    attributes:
      value: |
        ## Feature Request
        Thanks for taking the time to suggest a new feature!

  - type: input
    id: feature-title
    attributes:
      label: Feature Title
      description: A concise name for this feature
      placeholder: e.g., Add Dark Mode Support
    validations:
      required: true

  # Additional form elements...
```

### Form Elements

Issue templates can include various input types:

- **markdown**: For explanatory text and formatting
- **input**: For single-line text input
- **textarea**: For multi-line text input
- **dropdown**: For selecting from predefined options
- **checkboxes**: For multiple-choice selections

## How to Customize Templates

If you've created your own project from this template, you can customize the issue and PR templates to suit your needs:

1. Navigate to the `.github/ISSUE_TEMPLATE/` directory in your repository
2. Edit the existing YAML files or create new ones
3. For PR templates, edit the `PULL_REQUEST_TEMPLATE.md` file in the repository root

## Advanced Configuration

For more advanced needs, you can create a `config.yml` file in the `.github/ISSUE_TEMPLATE/` directory to:

- Control whether blank issues are allowed
- Add external links for specific types of issues
- Customize the template selection experience

Example:

```yaml
blank_issues_enabled: false
contact_links:
  - name: Security Vulnerabilities
    url: https://example.com/security
    about: Please report security vulnerabilities here instead of GitHub issues
```

# Starting point for new issue templates

The templates included in this project are designed to be a good starting point, but you should customize them based on your specific project needs and workflow.

## Further Resources

- [GitHub Docs: About issue and pull request templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates)
- [GitHub Docs: Configuring issue templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
- [GitHub Docs: Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [GitHub Docs: Common Errors](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/common-validation-errors-when-creating-issue-forms)
