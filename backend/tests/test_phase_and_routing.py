import pytest
from app.services.phase_detector import detect_phase


def test_phase_detector_priority():
    # Priority 1: Explicit validated phase
    phase, reason = detect_phase(
        explicit_phase="Deployment",
        environment="development",
        metadata={"job_name": "run-tests"}
    )
    assert phase == "Deployment"
    assert reason == "explicit_integration_metadata"

    # Priority 2: Trusted CI/CD metadata
    phase2, reason2 = detect_phase(
        explicit_phase=None,
        environment="production",
        metadata={"stage": "docker-build-and-push"}
    )
    assert phase2 == "Build"
    assert reason2 == "trusted_cicd_metadata"

    # Priority 3: Configured environment mapping
    phase3, reason3 = detect_phase(
        explicit_phase=None,
        environment="staging",
        metadata={}
    )
    assert phase3 == "Staging"
    assert reason3 == "environment_mapping"

    # Fallback: Unknown
    phase4, reason4 = detect_phase(
        explicit_phase=None,
        environment=None,
        metadata={},
        source="custom-script"
    )
    assert phase4 == "Unknown"
    assert reason4 == "unclassified"


def test_routing_rules_and_fallback(client):
    import uuid
    uid = uuid.uuid4().hex[:8]
    # Setup test project
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": f"routing_{uid}@test.io",
        "password": "Password123!",
        "organization_name": f"Routing Org {uid}"
    })
    token = reg_resp.json()["access_token"]
    proj_resp = client.post(
        "/api/v1/projects",
        json={
            "name": f"Routing Engine Test Project {uid}",
            "default_owner_email": f"fallback_{uid}@test.io",
            "default_team": "Core Operations"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    proj_id = proj_resp.json()["id"]

    # 1. Test fallback when no rules are configured
    test_res1 = client.post(
        f"/api/v1/routing/projects/{proj_id}/test",
        json={"service": "checkout", "environment": "production", "error_type": "NullPointerException", "severity": "medium"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert test_res1.status_code == 200
    data1 = test_res1.json()
    assert data1["target"] == f"fallback_{uid}@test.io"
    assert "Fallback" in data1["reason"]

    # 2. Add high-priority rule: Checkout service errors -> billing_lead@test.io
    create_rule_resp = client.post(
        f"/api/v1/routing/projects/{proj_id}/rules",
        json={
            "name": "Checkout Service Owner",
            "priority": 1,
            "conditions": {"service": "checkout"},
            "target_type": "email",
            "target_email": f"billing_{uid}@test.io"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_rule_resp.status_code == 201
    rule_id = create_rule_resp.json()["id"]

    # 3. Test routing again for checkout service -> must match Rule #1!
    test_res2 = client.post(
        f"/api/v1/routing/projects/{proj_id}/test",
        json={"service": "checkout", "environment": "production", "error_type": "NullPointerException", "severity": "medium"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert test_res2.status_code == 200
    data2 = test_res2.json()
    assert data2["matched_rule_id"] == rule_id
    assert data2["target"] == f"billing_{uid}@test.io"
    assert "Matched Rule #1" in data2["reason"]
