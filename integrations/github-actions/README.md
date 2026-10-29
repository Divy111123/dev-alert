# DevAlert GitHub Actions Integration

Report automated test and build failures in your GitHub Actions workflows to DevAlert.

## Setup Instructions

1. Add your DevAlert Project API Key as a repository secret named `DEVALERT_PROJECT_API_KEY` under **Settings > Secrets and variables > Actions**.
2. Add the `Notify DevAlert on Failure` step with condition `if: failure()` to your workflow file.
3. DevAlert groups duplicate build or test failures by workflow and step, determines the development phase, and triggers notifications according to your project's routing rules.
