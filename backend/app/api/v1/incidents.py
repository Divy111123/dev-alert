from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.organization import OrganizationMember
from app.models.project import Project
from app.models.incident import Incident
from app.models.event import ErrorEvent
from app.models.notification import NotificationRecord
from app.schemas.incident import IncidentResponse, IncidentDetailResponse, IncidentUpdate
from app.schemas.event import EventResponse
from app.api.deps import get_current_user, get_current_membership
from app.services.audit_service import log_action
from app.services.ai_analyzer import analyze_error

router = APIRouter()


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    phase: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Incident)
        .join(Project, Incident.project_id == Project.id)
        .filter(Project.organization_id == membership.organization_id)
    )

    if project_id:
        query = query.filter(Incident.project_id == project_id)
    if status:
        query = query.filter(Incident.status == status.lower())
    if severity:
        query = query.filter(Incident.severity == severity.lower())
    if environment:
        query = query.filter(Incident.environment == environment.lower())
    if phase:
        query = query.filter(Incident.phase == phase)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Incident.title.ilike(search_filter)) |
            (Incident.error_type.ilike(search_filter)) |
            (Incident.message.ilike(search_filter)) |
            (Incident.service.ilike(search_filter))
        )

    incidents = query.order_by(Incident.last_seen.desc()).offset(offset).limit(limit).all()

    # Populate project_name on responses
    results = []
    for inc in incidents:
        resp = IncidentResponse.model_validate(inc)
        resp.project_name = inc.project.name if inc.project else None
        results.append(resp)
    return results


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(
    incident_id: str,
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    incident = (
        db.query(Incident)
        .join(Project, Incident.project_id == Project.id)
        .filter(
            Incident.id == incident_id,
            Project.organization_id == membership.organization_id
        )
        .first()
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    events = db.query(ErrorEvent).filter(ErrorEvent.incident_id == incident_id).order_by(ErrorEvent.timestamp.desc()).limit(20).all()
    notifications = db.query(NotificationRecord).filter(NotificationRecord.incident_id == incident_id).order_by(NotificationRecord.created_at.desc()).all()

    resp = IncidentDetailResponse.model_validate(incident)
    resp.project_name = incident.project.name if incident.project else None
    resp.events = [EventResponse.model_validate(e) for e in events]
    resp.notifications = notifications
    return resp


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: str,
    update_in: IncidentUpdate,
    membership: OrganizationMember = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    incident = (
        db.query(Incident)
        .join(Project, Incident.project_id == Project.id)
        .filter(
            Incident.id == incident_id,
            Project.organization_id == membership.organization_id
        )
        .first()
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    changed_fields = []
    if update_in.status is not None:
        valid_statuses = {"open", "acknowledged", "investigating", "resolved", "reopened"}
        if update_in.status.lower() in valid_statuses:
            incident.status = update_in.status.lower()
            changed_fields.append(f"status={incident.status}")

    if update_in.severity is not None:
        valid_severities = {"low", "medium", "high", "critical"}
        if update_in.severity.lower() in valid_severities:
            incident.severity = update_in.severity.lower()
            changed_fields.append(f"severity={incident.severity}")

    if update_in.assigned_user_id is not None:
        user = db.query(User).filter(User.id == update_in.assigned_user_id).first()
        if user:
            incident.assigned_user_id = user.id
            incident.assigned_email = user.email
            changed_fields.append(f"assigned_user={user.email}")

    if update_in.assigned_team is not None:
        incident.assigned_team = update_in.assigned_team
        changed_fields.append(f"assigned_team={update_in.assigned_team}")

    incident.updated_at = datetime.now(timezone.utc)

    log_action(
        db=db,
        organization_id=membership.organization_id,
        action="incident.update",
        resource_type="incident",
        resource_id=incident.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"changes": changed_fields}
    )

    db.commit()
    db.refresh(incident)

    resp = IncidentResponse.model_validate(incident)
    resp.project_name = incident.project.name if incident.project else None
    return resp


@router.post("/{incident_id}/ai-analyze")
async def trigger_ai_analysis(
    incident_id: str,
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    incident = (
        db.query(Incident)
        .join(Project, Incident.project_id == Project.id)
        .filter(
            Incident.id == incident_id,
            Project.organization_id == membership.organization_id
        )
        .first()
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    recent_event = db.query(ErrorEvent).filter(ErrorEvent.incident_id == incident_id).first()
    stack_trace = recent_event.sanitized_stack_trace if recent_event else None

    summary, fix = await analyze_error(
        error_type=incident.error_type,
        message=incident.message,
        service=incident.service,
        sanitized_stack_trace=stack_trace
    )

    incident.ai_summary = summary
    incident.ai_suggested_fix = fix
    db.commit()

    return {
        "status": "success",
        "ai_summary": summary,
        "ai_suggested_fix": fix
    }

