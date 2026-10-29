import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    repository_url = Column(String(500), nullable=True)
    
    # Ownership defaults
    default_owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    default_owner_email = Column(String(255), nullable=True)
    default_team = Column(String(100), default="Engineering")

    # Configurable environments: development, testing, staging, production
    environments = Column(JSON, default=lambda: ["development", "testing", "staging", "production"])
    
    # Integration secret for signing/webhooks
    integration_secret = Column(String(255), nullable=True)

    # Project settings: cooldown_minutes, severity_thresholds, rate_limit, notification_enabled
    settings = Column(JSON, default=lambda: {
        "cooldown_minutes": 15,
        "notify_on_new": True,
        "notify_on_escalation": True,
        "notify_on_resolve": False,
        "min_severity_to_notify": "medium",
        "rate_limit_per_minute": 120
    })

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="projects")
    default_owner = relationship("User", foreign_keys=[default_owner_id])
    api_keys = relationship("ApiKey", back_populates="project", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="project", cascade="all, delete-orphan")
    events = relationship("ErrorEvent", back_populates="project", cascade="all, delete-orphan")
    routing_rules = relationship("RoutingRule", back_populates="project", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, default="Default API Key")
    key_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    prefix = Column(String(16), nullable=False)  # Display prefix e.g. "da_live_ab12"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    revoked_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="api_keys")

