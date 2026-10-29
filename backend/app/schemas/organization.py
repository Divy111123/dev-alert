from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.schemas.auth import UserResponse


class OrgMemberResponse(BaseModel):
    id: int
    user_id: int
    organization_id: int
    role: str
    created_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class OrgMemberCreate(BaseModel):
    email: EmailStr
    role: str = "developer"  # admin, project_manager, developer, viewer


class OrgMemberUpdate(BaseModel):
    role: str


class OrgCreate(BaseModel):
    name: str
    description: Optional[str] = None


class OrgUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class OrgResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime
    members_count: Optional[int] = 0
    projects_count: Optional[int] = 0

    class Config:
        from_attributes = True

