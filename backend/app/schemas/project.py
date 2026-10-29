from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr


class ApiKeyCreate(BaseModel):
    name: str = "Backend Service Key"


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    raw_key: str  # Only returned once upon creation!


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    default_owner_email: Optional[EmailStr] = None
    default_team: Optional[str] = "Engineering"
    environments: Optional[List[str]] = ["development", "testing", "staging", "production"]
    settings: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None
    default_owner_email: Optional[EmailStr] = None
    default_team: Optional[str] = None
    environments: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    id: str
    organization_id: int
    name: str
    slug: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    default_owner_id: Optional[int] = None
    default_owner_email: Optional[str] = None
    default_team: Optional[str] = None
    environments: List[str]
    integration_secret: Optional[str] = None
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    open_incidents_count: Optional[int] = 0
    total_events_count: Optional[int] = 0

    class Config:
        from_attributes = True

