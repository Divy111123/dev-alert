# DevAlert Jenkins Pipeline Integration

DevAlert captures pipeline, build, image scan, and deployment failures from Jenkins and routes them immediately to the configured DevOps or Stage owner.

## Configuration Steps

1. In Jenkins, add your DevAlert Project API Key under **Manage Jenkins > Credentials** with ID `devalert-project-api-key`.
2. Include the `post { failure { ... } }` block in your `Jenkinsfile` (see `Jenkinsfile` in this directory).
3. DevAlert will automatically identify the failed stage (`Build`, `Test`, `Deploy`), map the development phase, evaluate routing rules, and dispatch an email alert to the responsible developer.
