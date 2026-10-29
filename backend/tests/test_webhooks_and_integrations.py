import uuid
import pytest


@pytest.fixture
def webhook_project(client):
    uid = uuid.uuid4().hex[:8]
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": f"devops_{uid}@company.io",
        "password": "Password123!",
        "organization_name": f"DevOps Engineering {uid}"
    })
    token = reg_resp.json()["access_token"]
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": f"Continuous Delivery Pipeline {uid}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    proj_id = proj_resp.json()["id"]

    key_resp = client.post(
        f"/api/v1/projects/{proj_id}/api-keys",
        json={"name": "CI/CD Webhook Key"},
        headers={"Authorization": f"Bearer {token}"}
    )
    api_key = key_resp.json()["raw_key"]
    return {"token": token, "project_id": proj_id, "api_key": api_key}


def test_jenkins_webhook_integration(client, webhook_project):
    payload = {
        "job_name": "ecommerce-frontend-ci",
        "build_number": 42,
        "stage": "docker-build",
        "error_message": "Command 'docker build' returned non-zero exit code 1",
        "build_url": "https://jenkins.company.io/job/ecommerce/42/",
        "log_excerpt": "Step 4/12 : RUN npm run build\nERROR: out of memory",
        "branch": "feature/checkout-v2",
        "commit_sha": "a1b2c3d4",
        "severity": "high"
    }

    resp = client.post(
        "/api/v1/webhooks/jenkins",
        json=payload,
        headers={"X-API-Key": webhook_project["api_key"]}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert data["phase"] == "Build"
    assert "ecommerce-frontend-ci" in data["incident_id"] or data["is_new_incident"]


def test_github_actions_webhook_integration(client, webhook_project):
    payload = {
        "workflow": "Continuous Integration",
        "run_id": 992812,
        "job": "backend-unit-tests",
        "failed_step": "Run Pytest Suite",
        "message": "3 tests failed in test_auth.py",
        "repository": "company/backend-api",
        "branch": "main",
        "severity": "high"
    }

    resp = client.post(
        "/api/v1/webhooks/github",
        json=payload,
        headers={"X-API-Key": webhook_project["api_key"]}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert data["phase"] == "Testing"


def test_generic_webhook_integration(client, webhook_project):
    payload = {
        "event_type": "KubernetesPodCrashLoop",
        "summary": "Container payment-worker exited with code 137 (OOMKilled)",
        "component": "k8s-cluster-prod",
        "environment": "production",
        "severity": "critical"
    }

    resp = client.post(
        "/api/v1/webhooks/generic",
        json=payload,
        headers={"X-API-Key": webhook_project["api_key"]}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert data["severity"] == "critical"
