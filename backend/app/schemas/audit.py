from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    organization_id: int
    project_id: Optional[str] = None
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

