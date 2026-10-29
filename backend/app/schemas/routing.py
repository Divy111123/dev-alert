from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr


class RoutingRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    priority: int = 10
    conditions: Dict[str, Any]  # e.g., {"service": "payment-api", "environment": "production", "error_type": "DatabaseError"}
    target_type: str = "user"  # "user", "team", "email"
    target_user_id: Optional[int] = None
    target_team: Optional[str] = None
    target_email: Optional[EmailStr] = None


class RoutingRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = None
    target_type: Optional[str] = None
    target_user_id: Optional[int] = None
    target_team: Optional[str] = None
    target_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class RoutingRuleResponse(BaseModel):
    id: int
    project_id: str
    name: str
    description: Optional[str] = None
    priority: int
    is_active: bool
    conditions: Dict[str, Any]
    target_type: str
    target_user_id: Optional[int] = None
    target_team: Optional[str] = None
    target_email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RoutingTestRequest(BaseModel):
    environment: str = "production"
    service: str = "payment-api"
    error_type: str = "DatabaseConnectionError"
    phase: Optional[str] = "deployment"
    severity: str = "high"


class RoutingTestResponse(BaseModel):
    matched_rule_id: Optional[int] = None
    matched_rule_name: Optional[str] = None
    target_type: str
    target: str
    reason: str

