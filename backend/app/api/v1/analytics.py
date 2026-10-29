from datetime import datetime, timezone, timedelta
from typing import List
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.models.project import Project
from app.models.incident import Incident
from app.models.event import ErrorEvent
from app.schemas.analytics import OverviewAnalytics, MetricCount, TrendPoint
from app.api.deps import get_current_membership

router = APIRouter()


@router.get("/overview", response_model=OverviewAnalytics)
def get_overview_analytics(
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    org_id = membership.organization_id

    # Base project subquery for this org
    project_ids = [p.id for p in db.query(Project.id).filter(Project.organization_id == org_id).all()]
    if not project_ids:
        return OverviewAnalytics(
            total_events=0,
            open_incidents=0,
            critical_incidents=0,
            resolved_incidents=0,
            errors_by_project=[],
            errors_by_environment=[],
            errors_by_phase=[],
            errors_by_severity=[],
            error_trends=[]
        )

    # Incident counts
    total_incidents = db.query(Incident).filter(Incident.project_id.in_(project_ids)).count()
    open_incidents = db.query(Incident).filter(
        Incident.project_id.in_(project_ids),
        Incident.status.in_(["open", "investigating", "reopened"])
    ).count()
    critical_incidents = db.query(Incident).filter(
        Incident.project_id.in_(project_ids),
        Incident.severity == "critical",
        Incident.status != "resolved"
    ).count()
    resolved_incidents = db.query(Incident).filter(
        Incident.project_id.in_(project_ids),
        Incident.status == "resolved"
    ).count()

    # Total events
    total_events = db.query(ErrorEvent).filter(ErrorEvent.project_id.in_(project_ids)).count()

    # Errors by project
    proj_rows = (
        db.query(Project.name, func.count(ErrorEvent.id))
        .join(ErrorEvent, Project.id == ErrorEvent.project_id)
        .filter(Project.organization_id == org_id)
        .group_by(Project.name)
        .all()
    )
    errors_by_project = [MetricCount(name=r[0], count=r[1]) for r in proj_rows]

    # Errors by environment
    env_rows = (
        db.query(ErrorEvent.environment, func.count(ErrorEvent.id))
        .filter(ErrorEvent.project_id.in_(project_ids))
        .group_by(ErrorEvent.environment)
        .all()
    )
    errors_by_env = [MetricCount(name=r[0], count=r[1]) for r in env_rows]

    # Errors by phase
    phase_rows = (
        db.query(ErrorEvent.phase, func.count(ErrorEvent.id))
        .filter(ErrorEvent.project_id.in_(project_ids))
        .group_by(ErrorEvent.phase)
        .all()
    )
    errors_by_phase = [MetricCount(name=r[0], count=r[1]) for r in phase_rows]

    # Errors by severity
    sev_rows = (
        db.query(Incident.severity, func.count(Incident.id))
        .filter(Incident.project_id.in_(project_ids))
        .group_by(Incident.severity)
        .all()
    )
    errors_by_sev = [MetricCount(name=r[0], count=r[1]) for r in sev_rows]

    # Trends: last 7 days
    now = datetime.now(timezone.utc)
    trend_dict = { (now - timedelta(days=i)).strftime("%Y-%m-%d"): {"count": 0, "critical": 0} for i in range(6, -1, -1) }

    recent_events = (
        db.query(ErrorEvent.created_at, ErrorEvent.severity)
        .filter(
            ErrorEvent.project_id.in_(project_ids),
            ErrorEvent.created_at >= (now - timedelta(days=7))
        )
        .all()
    )
    for evt_time, sev in recent_events:
        d_str = evt_time.strftime("%Y-%m-%d")
        if d_str in trend_dict:
            trend_dict[d_str]["count"] += 1
            if sev == "critical":
                trend_dict[d_str]["critical"] += 1

    trends = [
        TrendPoint(date=k, count=v["count"], critical_count=v["critical"])
        for k, v in trend_dict.items()
    ]

    return OverviewAnalytics(
        total_events=total_events,
        open_incidents=open_incidents,
        critical_incidents=critical_incidents,
        resolved_incidents=resolved_incidents,
        errors_by_project=errors_by_project,
        errors_by_environment=errors_by_env,
        errors_by_phase=errors_by_phase,
        errors_by_severity=errors_by_sev,
        error_trends=trends
    )

