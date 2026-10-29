import time
from datetime import datetime, timezone
from typing import Generator, Optional, Callable
from collections import defaultdict
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token, hash_api_key
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.project import Project, ApiKey

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

# Simple in-memory sliding window rate limiter for API key requests
_rate_limits = defaultdict(list)


def check_rate_limit(project_id: str, max_requests: int = 120, window_seconds: int = 60):
    now = time.time()
    cutoff = now - window_seconds
    timestamps = [t for t in _rate_limits[project_id] if t > cutoff]
    if len(timestamps) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: maximum {max_requests} requests per minute."
        )
    timestamps.append(now)
    _rate_limits[project_id] = timestamps


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_current_org_id(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id")
) -> Optional[int]:
    if x_organization_id and x_organization_id.isdigit():
        return int(x_organization_id)
    return None


def get_current_membership(
    org_id: Optional[int] = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrganizationMember:
    query = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id)
    if org_id:
        membership = query.filter(OrganizationMember.organization_id == org_id).first()
    else:
        membership = query.first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization"
        )
    return membership


def require_role(allowed_roles: list[str]) -> Callable:
    def role_checker(membership: OrganizationMember = Depends(get_current_membership)) -> OrganizationMember:
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of roles: {', '.join(allowed_roles)}. Current role: {membership.role}"
            )
        return membership
    return role_checker


def authenticate_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Project:
    api_key_val = x_api_key
    # Also check Authorization header with Bearer or Api-Key prefix
    if not api_key_val:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() in ["bearer", "api-key", "token"]:
                api_key_val = parts[1]

    if not api_key_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide via 'X-API-Key' header or 'Authorization: Bearer <key>'"
        )

    hashed = hash_api_key(api_key_val.strip())
    api_key_record = db.query(ApiKey).filter(
        ApiKey.key_hash == hashed,
        ApiKey.is_active == True
    ).first()

    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key"
        )

    project = db.query(Project).filter(Project.id == api_key_record.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project associated with this API key not found"
        )

    # Check project rate limits
    max_rate = project.settings.get("rate_limit_per_minute", 120) if project.settings else 120
    check_rate_limit(project.id, max_requests=max_rate)

    # Update last used timestamp
    api_key_record.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return project
