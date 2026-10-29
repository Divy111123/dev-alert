from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.project import Project
from app.schemas.organization import (
    OrgCreate, OrgUpdate, OrgResponse,
    OrgMemberCreate, OrgMemberUpdate, OrgMemberResponse
)
from app.api.deps import get_current_user, require_role, get_current_membership
from app.services.audit_service import log_action

router = APIRouter()


@router.get("", response_model=List[OrgResponse])
def list_organizations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).all()
    org_ids = [m.organization_id for m in memberships]
    orgs = db.query(Organization).filter(Organization.id.in_(org_ids)).all()

    result = []
    for org in orgs:
        resp = OrgResponse.model_validate(org)
        resp.members_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org.id).count()
        resp.projects_count = db.query(Project).filter(Project.organization_id == org.id).count()
        result.append(resp)
    return result


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_in: OrgCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    slug = org_in.name.lower().replace(" ", "-") + f"-{current_user.id}"
    org = Organization(
        name=org_in.name,
        slug=slug,
        description=org_in.description
    )
    db.add(org)
    db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=OrgRole.ADMIN.value
    )
    db.add(member)

    log_action(
        db=db,
        organization_id=org.id,
        action="organization.create",
        resource_type="organization",
        resource_id=str(org.id),
        user_id=current_user.id,
        user_email=current_user.email,
        details={"name": org.name}
    )

    db.commit()
    db.refresh(org)
    resp = OrgResponse.model_validate(org)
    resp.members_count = 1
    resp.projects_count = 0
    return resp


@router.get("/{org_id}/members", response_model=List[OrgMemberResponse])
def list_org_members(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify current user is a member of this org
    user_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == current_user.id
    ).first()
    if not user_mem:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this organization")

    members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).all()
    return members


@router.post("/{org_id}/members", response_model=OrgMemberResponse, status_code=status.HTTP_201_CREATED)
def add_org_member(
    org_id: int,
    member_in: OrgMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Ensure current user is Org Admin
    user_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role == OrgRole.ADMIN.value
    ).first()
    if not user_mem:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Organization Admins can add members.")

    # Find target user
    target_user = db.query(User).filter(User.email == member_in.email).first()
    if not target_user:
        # Create a stub user if not exists
        from app.core.security import get_password_hash
        target_user = User(
            email=member_in.email,
            full_name=member_in.email.split("@")[0].capitalize(),
            hashed_password=get_password_hash("DevAlertTempPass123!"),
            is_active=True
        )
        db.add(target_user)
        db.flush()

    # Check if already a member
    existing = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == target_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this organization.")

    new_member = OrganizationMember(
        organization_id=org_id,
        user_id=target_user.id,
        role=member_in.role
    )
    db.add(new_member)

    log_action(
        db=db,
        organization_id=org_id,
        action="member.add",
        resource_type="member",
        resource_id=str(target_user.id),
        user_id=current_user.id,
        user_email=current_user.email,
        details={"member_email": target_user.email, "role": member_in.role}
    )

    db.commit()
    db.refresh(new_member)
    return new_member


@router.put("/{org_id}/members/{user_id}", response_model=OrgMemberResponse)
def update_member_role(
    org_id: int,
    user_id: int,
    update_in: OrgMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    admin_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role == OrgRole.ADMIN.value
    ).first()
    if not admin_mem:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Organization Admins can update roles.")

    target_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == user_id
    ).first()
    if not target_mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    target_mem.role = update_in.role
    db.commit()
    db.refresh(target_mem)
    return target_mem


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    org_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    admin_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role == OrgRole.ADMIN.value
    ).first()
    if not admin_mem:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Organization Admins can remove members.")

    target_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == user_id
    ).first()
    if not target_mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    db.delete(target_mem)
    db.commit()
    return None

