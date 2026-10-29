from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.schemas.event import EventResponse
from app.schemas.auth import UserResponse


class NotificationRecordResponse(BaseModel):
    id: int
    incident_id: str
    notification_type: str
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: str
    status: str
    attempts_count: int
    last_attempt_at: Optional[datetime] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    id: str
    project_id: str
    project_name: Optional[str] = None
    fingerprint: str
    title: str
    error_type: str
    message: str
    severity: str
    status: str
    environment: str
    phase: str
    service: str
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int
    assigned_user_id: Optional[int] = None
    assigned_team: Optional[str] = None
    assigned_email: Optional[str] = None
    routing_reason: Optional[str] = None
    last_notified_at: Optional[datetime] = None
    notification_count: int
    created_at: datetime
    updated_at: datetime
    assigned_user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class IncidentUpdate(BaseModel):
    status: Optional[str] = None  # open, acknowledged, investigating, resolved, reopened
    severity: Optional[str] = None
    assigned_user_id: Optional[int] = None
    assigned_team: Optional[str] = None
    assigned_email: Optional[str] = None


class IncidentDetailResponse(IncidentResponse):
    events: List[EventResponse] = []
    notifications: List[NotificationRecordResponse] = []
    ai_summary: Optional[str] = None
    ai_suggested_fix: Optional[str] = None

