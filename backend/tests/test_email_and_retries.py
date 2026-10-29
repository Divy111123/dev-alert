import pytest
from app.services.email_service import render_email, send_email_sync
from app.models.notification import NotificationRecord
from app.models.incident import Incident
from app.models.project import Project


def test_email_template_rendering():
    class DummyIncident:
        id = "inc_test_123"
        error_type = "DatabaseDeadlock"
        message = "Deadlock detected during payment processing"
        severity = "critical"
        phase = "Production"
        service = "payment-gateway"

    class DummyProject:
        name = "Alpha Payment Platform"

    context = {
        "subject": "[CRITICAL] Alpha Payment Platform: DatabaseDeadlock",
        "incident": DummyIncident(),
        "project": DummyProject(),
        "assigned_to": "backend-team@alpha.io",
        "dashboard_url": "http://localhost:5173",
        "stack_trace": "File 'payments.py', line 12",
        "ai_summary": "Check deadlocks in PostgreSQL relation 'accounts'"
    }

    html, text = render_email("critical_incident", context)
    assert "DatabaseDeadlock" in html
    assert "Alpha Payment Platform" in html
    assert "CRITICAL SEVERITY" in html
    assert "inc_test_123" in text


def test_send_test_email_endpoint(client):
    import uuid
    uid = uuid.uuid4().hex[:8]
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": f"notif_{uid}@test.io",
        "password": "Password123!",
        "organization_name": f"Alerting Org {uid}"
    })
    token = reg_resp.json()["access_token"]
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": f"Alerting Project {uid}", "default_owner_email": f"notif_{uid}@test.io"},
        headers={"Authorization": f"Bearer {token}"}
    )
    proj_id = proj_resp.json()["id"]

    test_email_resp = client.post(
        f"/api/v1/projects/{proj_id}/test-email",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert test_email_resp.status_code == 200
    data = test_email_resp.json()
    assert data["status"] == "queued"
    assert f"notif_{uid}@test.io" in data["recipient"]
