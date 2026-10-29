from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.organization import OrganizationMember
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from app.api.deps import get_current_membership

router = APIRouter()


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    project_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog).filter(AuditLog.organization_id == membership.organization_id)
    if project_id:
        query = query.filter(AuditLog.project_id == project_id)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs

