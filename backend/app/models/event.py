import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ErrorEvent(Base):
    __tablename__ = "error_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(100), nullable=True, index=True)  # Client idempotency ID
    
    environment = Column(String(100), default="production", index=True)
    phase = Column(String(100), default="Unknown", index=True)
    service = Column(String(100), default="default", index=True)
    source = Column(String(100), default="generic", index=True)  # python-sdk, jenkins, github-actions, generic-webhook
    
    error_type = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), default="medium")
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    stack_trace = Column(Text, nullable=True)
    sanitized_stack_trace = Column(Text, nullable=True)
    
    metadata_json = Column(JSON, default=dict)
    request_data = Column(JSON, default=dict)
    
    host = Column(String(255), nullable=True)
    release = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="events")
    project = relationship("Project", back_populates="events")

