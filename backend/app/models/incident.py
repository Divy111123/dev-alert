import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    error_type = Column(String(150), nullable=False, index=True)
    message = Column(Text, nullable=False)
    severity = Column(String(50), default="medium", index=True)  # low, medium, high, critical
    status = Column(String(50), default="open", index=True)  # open, acknowledged, investigating, resolved, reopened
    
    environment = Column(String(100), default="production", index=True)
    phase = Column(String(100), default="Unknown", index=True)
    service = Column(String(100), default="default", index=True)
    
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    occurrence_count = Column(Integer, default=1)
    
    # Assignment & routing
    assigned_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_team = Column(String(100), nullable=True)
    assigned_email = Column(String(255), nullable=True)
    routing_reason = Column(String(500), nullable=True)
    
    # Notification suppression / cooldown
    last_notified_at = Column(DateTime, nullable=True)
    notification_count = Column(Integer, default=0)

    # AI Error Analysis
    ai_summary = Column(Text, nullable=True)
    ai_suggested_fix = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("project_id", "fingerprint", name="uq_project_fingerprint"),
    )

    project = relationship("Project", back_populates="incidents")
    assigned_user = relationship("User", back_populates="assigned_incidents")
    events = relationship("ErrorEvent", back_populates="incident", cascade="all, delete-orphan", order_by="desc(ErrorEvent.created_at)")
    notifications = relationship("NotificationRecord", back_populates="incident", cascade="all, delete-orphan")

