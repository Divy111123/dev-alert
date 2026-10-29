import secrets
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import generate_api_key, hash_api_key
from app.models.user import User
from app.models.organization import OrganizationMember, OrgRole
from app.models.project import Project, ApiKey
from app.models.incident import Incident
from app.models.event import ErrorEvent
from app.models.notification import NotificationRecord
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse
)
from app.api.deps import get_current_user, get_current_membership
from app.services.audit_service import log_action
from app.tasks.email_tasks import dispatch_notification_async

router = APIRouter()


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    projects = db.query(Project).filter(Project.organization_id == membership.organization_id).all()
    results = []
    for proj in projects:
        resp = ProjectResponse.model_validate(proj)
        resp.open_incidents_count = db.query(Incident).filter(
            Incident.project_id == proj.id,
            Incident.status.in_(["open", "investigating", "reopened"])
        ).count()
        resp.total_events_count = db.query(ErrorEvent).filter(ErrorEvent.project_id == proj.id).count()
        results.append(resp)
    return results


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    proj_in: ProjectCreate,
    membership: OrganizationMember = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if membership.role not in [OrgRole.ADMIN.value, OrgRole.PROJECT_MANAGER.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to create projects.")

    slug = proj_in.name.lower().replace(" ", "-")
    # Generate webhook secret
    integration_secret = secrets.token_hex(24)

    default_settings = {
        "cooldown_minutes": 15,
        "notify_on_new": True,
        "notify_on_escalation": True,
        "notify_on_resolve": False,
        "min_severity_to_notify": "medium",
        "rate_limit_per_minute": 120
    }
    if proj_in.settings:
        default_settings.update(proj_in.settings)

    project = Project(
        organization_id=membership.organization_id,
        name=proj_in.name,
        slug=slug,
        description=proj_in.description,
        repository_url=proj_in.repository_url,
        default_owner_id=current_user.id,
        default_owner_email=proj_in.default_owner_email or current_user.email,
        default_team=proj_in.default_team or "Engineering",
        environments=proj_in.environments or ["development", "testing", "staging", "production"],
        integration_secret=integration_secret,
        settings=default_settings
    )
    db.add(project)
    db.flush()

    # Automatically generate an initial API key
    raw_key = generate_api_key(prefix="da_live")
    key_record = ApiKey(
        project_id=project.id,
        name="Default Backend Key",
        key_hash=hash_api_key(raw_key),
        prefix=raw_key[:12] + "..."
    )
    db.add(key_record)

    log_action(
        db=db,
        organization_id=membership.organization_id,
        action="project.create",
        resource_type="project",
        resource_id=project.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"project_name": project.name}
    )

    db.commit()
    db.refresh(project)

    resp = ProjectResponse.model_validate(project)
    resp.open_incidents_count = 0
    resp.total_events_count = 0
    return resp


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    resp = ProjectResponse.model_validate(project)
    resp.open_incidents_count = db.query(Incident).filter(
        Incident.project_id == project.id,
        Incident.status.in_(["open", "investigating", "reopened"])
    ).count()
    resp.total_events_count = db.query(ErrorEvent).filter(ErrorEvent.project_id == project.id).count()
    return resp


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    proj_in: ProjectUpdate,
    membership: OrganizationMember = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if membership.role not in [OrgRole.ADMIN.value, OrgRole.PROJECT_MANAGER.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to update projects.")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if proj_in.name is not None:
        project.name = proj_in.name
    if proj_in.description is not None:
        project.description = proj_in.description
    if proj_in.repository_url is not None:
        project.repository_url = proj_in.repository_url
    if proj_in.default_owner_email is not None:
        project.default_owner_email = proj_in.default_owner_email
    if proj_in.default_team is not None:
        project.default_team = proj_in.default_team
    if proj_in.environments is not None:
        project.environments = proj_in.environments
    if proj_in.settings is not None:
        current_settings = dict(project.settings or {})
        current_settings.update(proj_in.settings)
        project.settings = current_settings

    log_action(
        db=db,
        organization_id=membership.organization_id,
        action="project.update",
        resource_type="project",
        resource_id=project.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"updated_fields": list(proj_in.model_dump(exclude_unset=True).keys())}
    )

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    membership: OrganizationMember = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if membership.role != OrgRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Organization Admins can delete projects.")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    log_action(
        db=db,
        organization_id=membership.organization_id,
        action="project.delete",
        resource_type="project",
        resource_id=project.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"project_name": project.name}
    )

    db.delete(project)
    db.commit()
    return None


# --- API Key Management ---

@router.get("/{project_id}/api-keys", response_model=List[ApiKeyResponse])
def list_api_keys(
    project_id: str,
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    keys = db.query(ApiKey).filter(ApiKey.project_id == project_id).all()
    return keys


@router.post("/{project_id}/api-keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    project_id: str,
    key_in: ApiKeyCreate,
    membership: OrganizationMember = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if membership.role not in [OrgRole.ADMIN.value, OrgRole.PROJECT_MANAGER.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to manage API keys.")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    raw_key = generate_api_key(prefix="da_live")
    key_record = ApiKey(
        project_id=project.id,
        name=key_in.name,
        key_hash=hash_api_key(raw_key),
        prefix=raw_key[:12] + "..."
    )
    db.add(key_record)

    log_action(
        db=db,
        organization_id=membership.organization_id,
        action="api_key.create",
        resource_type="api_key",
        resource_id=str(key_record.id),
        user_id=current_user.id,
        user_email=current_user.email,
        details={"key_name": key_in.name, "prefix": key_record.prefix}
    )

    db.commit()
    db.refresh(key_record)

    return ApiKeyCreatedResponse(
        id=key_record.id,
        name=key_record.name,
        prefix=key_record.prefix,
        is_active=key_record.is_active,
        created_at=key_record.created_at,
        revoked_at=key_record.revoked_at,
        last_used_at=key_record.last_used_at,
        raw_key=raw_key
    )


@router.delete("/{project_id}/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    project_id: str,
    key_id: int,
    membership: OrganizationMember = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if membership.role not in [OrgRole.ADMIN.value, OrgRole.PROJECT_MANAGER.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to manage API keys.")

    key_record = db.query(ApiKey).join(Project).filter(
        ApiKey.id == key_id,
        ApiKey.project_id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not key_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")

    key_record.is_active = False
    key_record.revoked_at = datetime.now(timezone.utc)

    log_action(
        db=db,
        organization_id=membership.organization_id,
        action="api_key.revoke",
        resource_type="api_key",
        resource_id=str(key_record.id),
        user_id=current_user.id,
        user_email=current_user.email,
        details={"key_name": key_record.name}
    )

    db.commit()
    return None


@router.post("/{project_id}/test-email")
def send_test_email(
    project_id: str,
    target_email: Optional[str] = None,
    membership: OrganizationMember = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    recipient = target_email or project.default_owner_email or current_user.email

    notif = NotificationRecord(
        incident_id="",  # Test notification doesn't belong to real incident
        project_id=project.id,
        notification_type="test_notification",
        recipient_email=recipient,
        recipient_name=current_user.full_name or recipient,
        subject=f"[DevAlert Test] Notification Channel Verification for {project.name}",
        status="pending"
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    # Dispatch asynchronously
    dispatch_notification_async(notif.id)

    return {
        "status": "queued",
        "notification_id": notif.id,
        "recipient": recipient,
        "message": f"Test email dispatched to {recipient}. Check the notification log or inbox."
    }

