# DevAlert — Integration Guide

This guide describes how to connect applications, CI/CD pipelines, and monitoring infrastructure to DevAlert.

---

## 1. Python SDK Integration (`devalert-python`)

The Python SDK provides non-blocking, safe exception ingestion with secret redaction and environment detection.

### Installation

```bash
pip install ./sdk/python
# Or in editable mode:
pip install -e ./sdk/python
```

### Basic Usage

```python
import devalert

devalert.init(
    api_key="da_live_YOUR_PROJECT_API_KEY",
    endpoint="http://localhost:8000/api/v1/events",
    environment="production",
    service="billing-api",
    release="v2.1.0"
)

try:
    process_order()
except Exception as e:
    devalert.capture_exception(
        exc=e,
        severity="high",
        metadata={"customer_id": "cust_12948"}
    )
```

### FastAPI Middleware

```python
from fastapi import FastAPI
import devalert
from devalert.integrations.fastapi import DevAlertFastAPIMiddleware

devalert.init(api_key="da_live_...", service="catalog-service")

app = FastAPI()
app.add_middleware(DevAlertFastAPIMiddleware, service_name="catalog-service")
```

### Flask Extension

```python
from flask import Flask
import devalert
from devalert.integrations.flask import DevAlertFlask

devalert.init(api_key="da_live_...", service="user-auth")

app = Flask(__name__)
DevAlertFlask(app, service_name="user-auth")
```

---

## 2. Jenkins Pipeline Integration

Incorporate this block into your `Jenkinsfile` under `post { failure { ... } }`:

```groovy
post {
    failure {
        script {
            def failedStage = env.STAGE_NAME ?: "Build"
            def payload = """{
                "job_name": "\${env.JOB_NAME}",
                "build_number": "\${env.BUILD_NUMBER}",
                "stage": "\${failedStage}",
                "branch": "\${env.BRANCH_NAME ?: 'main'}",
                "commit_sha": "\${env.GIT_COMMIT ?: ''}",
                "build_url": "\${env.BUILD_URL}",
                "repository": "\${env.GIT_URL ?: ''}",
                "environment": "testing",
                "severity": "high",
                "error_message": "Pipeline failure in stage '\${failedStage}'"
            }"""

            httpRequest(
                url: 'http://devalert-backend:8000/api/v1/webhooks/jenkins',
                httpMode: 'POST',
                contentType: 'APPLICATION_JSON',
                customHeaders: [[name: 'X-API-Key', value: "\${DEVALERT_API_KEY}"]],
                requestBody: payload
            )
        }
    }
}
```

---

## 3. GitHub Actions Workflow Integration

Add this step to any GitHub Actions workflow with condition `if: failure()`:

```yaml
- name: Notify DevAlert on Failure
  if: failure()
  run: |
    curl -X POST "http://devalert-backend:8000/api/v1/webhooks/github" \
      -H "X-API-Key: ${{ secrets.DEVALERT_PROJECT_API_KEY }}" \
      -H "Content-Type: application/json" \
      -d '{
        "workflow": "${{ github.workflow }}",
        "run_id": "${{ github.run_id }}",
        "job": "test-suite",
        "failed_step": "${{ steps.test.outcome == '\''failure'\'' && '\''Pytest'\'' || '\''Docker Build'\'' }}",
        "repository": "${{ github.repository }}",
        "branch": "${{ github.ref_name }}",
        "commit_sha": "${{ github.sha }}",
        "message": "GitHub Actions workflow failed on branch ${{ github.ref_name }}",
        "severity": "high",
        "environment": "testing"
      }'
```

---

## 4. Generic Webhook Contract

**Endpoint**: `POST /api/v1/webhooks/generic`  
**Header**: `X-API-Key: da_live_...`

```json
{
  "event_type": "KubernetesPodCrashLoop",
  "summary": "Container exited with code 137 (OOMKilled)",
  "component": "k8s-cluster-prod",
  "environment": "production",
  "phase": "Production",
  "severity": "critical",
  "trace": "Memory cgroup out of memory: Killed process 8192 (python)",
  "metadata": {
    "node": "k8s-worker-04",
    "namespace": "billing"
  }
}
```

