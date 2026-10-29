from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    priority = Column(Integer, default=10, nullable=False, index=True)  # Lower number = higher priority
    is_active = Column(Boolean, default=True, index=True)

    # Match conditions JSON:
    # {
    #   "environment": "production",
    #   "service": "payment-api",
    #   "error_type": "DatabaseConnectionError",
    #   "phase": "deployment",
    #   "severity": "critical"
    # }
    conditions = Column(JSON, nullable=False, default=dict)

    # Routing target
    target_type = Column(String(50), default="user")  # "user", "team", "email"
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_team = Column(String(100), nullable=True)
    target_email = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="routing_rules")
    target_user = relationship("User", foreign_keys=[target_user_id])

