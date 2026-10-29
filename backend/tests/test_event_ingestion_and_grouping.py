import uuid
import pytest


@pytest.fixture
def test_project(client):
    uid = uuid.uuid4().hex[:8]
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": f"tester_{uid}@devalert.io",
        "password": "Password123!",
        "full_name": "Test Engineer",
        "organization_name": f"QA Labs {uid}"
    })
    token = reg_resp.json()["access_token"]
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": f"Ingestion Testing App {uid}", "default_owner_email": f"tester_{uid}@devalert.io"},
        headers={"Authorization": f"Bearer {token}"}
    )
    proj_id = proj_resp.json()["id"]

    # Generate dedicated API key
    key_resp = client.post(
        f"/api/v1/projects/{proj_id}/api-keys",
        json={"name": "Ingestion Test Key"},
        headers={"Authorization": f"Bearer {token}"}
    )
    api_key = key_resp.json()["raw_key"]
    return {"token": token, "project_id": proj_id, "api_key": api_key}


def test_authentication_required(client):
    resp = client.post("/api/v1/events", json={
        "error_type": "RuntimeError",
        "message": "Crash without API Key"
    })
    assert resp.status_code == 401


def test_invalid_payload_rejection(client, test_project):
    # Missing required message and error_type
    resp = client.post(
        "/api/v1/events",
        json={"service": "api"},
        headers={"X-API-Key": test_project["api_key"]}
    )
    assert resp.status_code == 422


def test_idempotency_control(client, test_project):
    event_payload = {
        "event_id": "unique-idempotent-key-001",
        "error_type": "PaymentGatewayTimeout",
        "message": "Stripe timeout after 10000ms",
        "service": "billing",
        "severity": "high"
    }

    # First delivery
    resp1 = client.post("/api/v1/events", json=event_payload, headers={"X-API-Key": test_project["api_key"]})
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["status"] == "success"
    assert data1["is_new_incident"] is True

    # Second delivery with same event_id -> should return idempotent result without duplicating
    resp2 = client.post("/api/v1/events", json=event_payload, headers={"X-API-Key": test_project["api_key"]})
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["status"] == "idempotent_duplicate"
    assert data2["incident_id"] == data1["incident_id"]


def test_incident_grouping_and_occurrence_count(client, test_project):
    payload = {
        "error_type": "ConnectionRefusedError",
        "message": "Failed to connect to redis cache at 10.0.0.2:6379",
        "service": "cache-service",
        "severity": "medium",
        "stack_trace": "File 'cache.py', line 45, in get_session\n  redis.connect()"
    }

    # Occurrence 1
    resp1 = client.post("/api/v1/events", json=payload, headers={"X-API-Key": test_project["api_key"]})
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["occurrence_count"] == 1
    incident_id = data1["incident_id"]

    # Occurrence 2 (different timestamp/random number in msg)
    payload2 = dict(payload)
    payload2["message"] = "Failed to connect to redis cache at 10.0.0.2:6379 (attempt 2)"
    resp2 = client.post("/api/v1/events", json=payload2, headers={"X-API-Key": test_project["api_key"]})
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["incident_id"] == incident_id
    assert data2["occurrence_count"] == 2
    assert data2["is_new_incident"] is False


def test_incident_resolution_and_reopening(client, test_project):
    payload = {
        "error_type": "BrokenPipeError",
        "message": "Socket connection broken unexpectedly",
        "service": "stream-gateway"
    }

    resp = client.post("/api/v1/events", json=payload, headers={"X-API-Key": test_project["api_key"]})
    inc_id = resp.json()["incident_id"]

    # Resolve incident
    patch_resp = client.patch(
        f"/api/v1/incidents/{inc_id}",
        json={"status": "resolved"},
        headers={"Authorization": f"Bearer {test_project['token']}"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "resolved"

    # New occurrence of the same error -> incident must be automatically REOPENED!
    resp_again = client.post("/api/v1/events", json=payload, headers={"X-API-Key": test_project["api_key"]})
    assert resp_again.status_code == 201

    get_inc = client.get(f"/api/v1/incidents/{inc_id}", headers={"Authorization": f"Bearer {test_project['token']}"})
    assert get_inc.json()["status"] == "reopened"


def test_batch_event_ingestion(client, test_project):
    batch = {
        "events": [
            {"error_type": "ErrA", "message": "msg A", "service": "srv1"},
            {"error_type": "ErrB", "message": "msg B", "service": "srv2"},
            {"error_type": "ErrC", "message": "msg C", "service": "srv3"}
        ]
    }
    resp = client.post("/api/v1/events/batch", json=batch, headers={"X-API-Key": test_project["api_key"]})
    assert resp.status_code == 201
    results = resp.json()
    assert len(results) == 3
