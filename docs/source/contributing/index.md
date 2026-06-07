# Contributing to Py Launch Blueprint

Thank you for your interest in contributing to Py Launch Blueprint! We welcome contributions from the community and appreciate your efforts in improving the project.

## How to Contribute

### Reporting Bugs
If you find a bug, please open an issue on GitHub with the following details:
- **Title**: A clear, concise description of the issue.
- **Description**: A detailed explanation of the problem.
- **Reproduction Steps**: Steps to replicate the issue.
- **Additional Information**: Logs, screenshots, or other relevant details.

### Suggesting Enhancements
We welcome feature requests and improvements! To suggest an enhancement, open a GitHub issue with:
- **Title**: A concise summary of your suggestion.
- **Description**: A detailed explanation of the feature.
- **Use Cases**: How it improves the project and potential applications.

### Submitting Pull Requests
To contribute code, follow the steps in the [Development Workflow](../tasks/contributing_code.md#development-workflow) guide and send a pull request.

#### Pull Request Guidelines
- Follow the project's **coding style**.
- Ensure **all tests pass**.
- Update **documentation** where applicable.
- Provide a **clear description** of the change in the pull request.

## Contributor License Agreement (CLA)
Before your contributions can be accepted, you must sign a **Contributor License Agreement (CLA)**.

### Setting Up the CLA
 - **Follow the steps in the [CLA Setup Guide](./cla/cla-setup-guide.md) to configure and enable the CLA for your repository.**

### Signing the CLA
- **Individual Contributors**: Sign the [Individual CLA](./cla/individual_cla.md).
- **Corporate Contributors**: Sign the [Corporate CLA](./cla/corporate_cla.md).

### CLA Assistant Bot
When you open a pull request, the **CLA Assistant Bot** will check if you've signed the CLA. If not, it will provide a link to complete the process.

## Tracking Contributors
This project uses [`contributors-please`](https://github.com/smorinlabs/contributors-please-action) to track contributors automatically in [`CONTRIBUTORS.md`](https://github.com/smorinlabs/py-launch-blueprint/blob/main/CONTRIBUTORS.md). The list updates when:
1. A push is made to the main branch.
2. A pull request is merged.
3. Manually, using the following command:
   ```bash
   just contributors
   ```

### How Contributors are Tracked

Contributors are tracked based on git commit history. The system:
- Counts commits per contributor
- Shows contribution statistics
- Joins commit authors to GitHub logins using no-reply addresses and `.contributors.yml`
- Sorts contributors by number of commits

For more details, see the [contributors-please action](https://github.com/smorinlabs/contributors-please-action).
## Code of Conduct
We are committed to fostering a **welcoming and inclusive** community. Please review and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Documentation Contributions
- All documentation is located in `docs/source/`.
- Maintain the existing directory structure.
- Use **Sphinx syntax** for cross-referencing (e.g., `:doc:` or `:ref:`).

## Getting Help
If you have questions, feel free to:
- Open an issue on GitHub.
- Reach out to the maintainers.


```{toctree}
---
maxdepth: 2
---
cla_faq
CODE_OF_CONDUCT
cla/individual_cla
cla/corporate_cla
```
