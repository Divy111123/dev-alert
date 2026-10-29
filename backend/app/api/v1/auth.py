from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.api.deps import get_current_user
from app.services.audit_service import log_action

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Create user
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=True
    )
    db.add(user)
    db.flush()

    # Create default Organization
    org_name = user_in.organization_name or f"{user_in.full_name or 'Default'}'s Team"
    slug = org_name.lower().replace(" ", "-").replace("'", "") + f"-{user.id}"
    org = Organization(
        name=org_name,
        slug=slug,
        description="Default organization"
    )
    db.add(org)
    db.flush()

    # Add user as Admin to this organization
    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.ADMIN.value
    )
    db.add(member)

    log_action(
        db=db,
        organization_id=org.id,
        action="user.register",
        resource_type="user",
        resource_id=str(user.id),
        user_id=user.id,
        user_email=user.email,
        details={"organization": org.name}
    )

    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "org_id": org.id})
    return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account."
        )

    # Get primary organization
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    org_id = membership.organization_id if membership else None

    token = create_access_token({"sub": str(user.id), "email": user.email, "org_id": org_id})
    return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

