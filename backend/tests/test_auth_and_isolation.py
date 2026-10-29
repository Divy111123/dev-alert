import pytest


def test_user_registration_and_login(client):
    # Register User
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "alice@company.com",
        "password": "Password123!",
        "full_name": "Alice Developer",
        "organization_name": "Acme Corp"
    })
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == "alice@company.com"

    # Login User
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@company.com",
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data


def test_organization_isolation(client):
    # Register Alice in Acme Corp
    resp1 = client.post("/api/v1/auth/register", json={
        "email": "alice2@acme.com",
        "password": "Password123!",
        "full_name": "Alice Acme",
        "organization_name": "Acme Corp"
    })
    token1 = resp1.json()["access_token"]

    # Register Bob in Beta LLC
    resp2 = client.post("/api/v1/auth/register", json={
        "email": "bob@beta.com",
        "password": "Password123!",
        "full_name": "Bob Beta",
        "organization_name": "Beta LLC"
    })
    token2 = resp2.json()["access_token"]

    # Alice creates a project in Acme Corp
    create_proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Acme Backend Service", "description": "Core payment engine"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert create_proj_resp.status_code == 201
    acme_proj_id = create_proj_resp.json()["id"]

    # Bob lists projects in his organization -> Acme project must NOT appear!
    bob_proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Beta Analytics", "description": "Analytics stream"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert bob_proj_resp.status_code == 201

    bob_list_resp = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token2}"})
    assert bob_list_resp.status_code == 200
    bob_projects = bob_list_resp.json()
    bob_proj_ids = [p["id"] for p in bob_projects]
    assert acme_proj_id not in bob_proj_ids

    # Bob attempts direct access to Alice's project -> must be 404 (isolated)
    bob_direct_resp = client.get(f"/api/v1/projects/{acme_proj_id}", headers={"Authorization": f"Bearer {token2}"})
    assert bob_direct_resp.status_code == 404


def test_api_key_creation_and_revocation(client):
    # Register Admin
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "admin@keytest.com",
        "password": "Password123!",
        "full_name": "Admin Key",
        "organization_name": "Key Corp"
    })
    token = reg_resp.json()["access_token"]

    # Create Project
    proj_resp = client.post(
        "/api/v1/projects",
        json={"name": "Key Project"},
        headers={"Authorization": f"Bearer {token}"}
    )
    proj_id = proj_resp.json()["id"]

    # Create secondary API key
    key_resp = client.post(
        f"/api/v1/projects/{proj_id}/api-keys",
        json={"name": "Worker Node Key"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert key_resp.status_code == 201
    key_data = key_resp.json()
    assert "raw_key" in key_data
    raw_key = key_data["raw_key"]
    key_id = key_data["id"]

    # Ingest event with this key -> should succeed
    event_resp = client.post(
        "/api/v1/events",
        json={
            "error_type": "DatabaseTimeout",
            "message": "Timed out after 30s",
            "service": "worker"
        },
        headers={"X-API-Key": raw_key}
    )
    assert event_resp.status_code == 201

    # Revoke key
    revoke_resp = client.delete(
        f"/api/v1/projects/{proj_id}/api-keys/{key_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert revoke_resp.status_code == 204

    # Attempt to ingest with revoked key -> must fail 401
    failed_resp = client.post(
        "/api/v1/events",
        json={
            "error_type": "DatabaseTimeout",
            "message": "Timed out after 30s",
            "service": "worker"
        },
        headers={"X-API-Key": raw_key}
    )
    assert failed_resp.status_code == 401

