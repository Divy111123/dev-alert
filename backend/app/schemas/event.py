from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class EventIngest(BaseModel):
    project_id: Optional[str] = Field(None, max_length=100)
    event_id: Optional[str] = Field(None, max_length=100, description="Idempotency key")
    environment: str = Field(default="production", max_length=100)
    phase: Optional[str] = Field(default=None, max_length=100)
    service: str = Field(default="default", max_length=100)
    source: str = Field(default="python-sdk", max_length=100)
    error_type: str = Field(..., min_length=1, max_length=150)
    message: str = Field(..., min_length=1, max_length=10000)
    severity: str = Field(default="medium", max_length=20)
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    stack_trace: Optional[str] = Field(default=None, max_length=100000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    request_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    host: Optional[str] = Field(None, max_length=255)
    release: Optional[str] = Field(None, max_length=100)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        valid_severities = {"low", "medium", "high", "critical"}
        v_lower = v.lower().strip()
        if v_lower not in valid_severities:
            return "medium"
        return v_lower


class EventBatchIngest(BaseModel):
    events: List[EventIngest] = Field(..., min_length=1, max_length=50)


class EventResponse(BaseModel):
    id: str
    incident_id: str
    project_id: str
    event_id: Optional[str] = None
    environment: str
    phase: str
    service: str
    source: str
    error_type: str
    message: str
    severity: str
    timestamp: datetime
    sanitized_stack_trace: Optional[str] = None
    metadata_json: Dict[str, Any]
    request_data: Dict[str, Any]
    host: Optional[str] = None
    release: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IngestResult(BaseModel):
    status: str
    incident_id: str
    event_id: str
    is_new_incident: bool
    occurrence_count: int
    assigned_to: Optional[str] = None
    phase: str
    severity: str

