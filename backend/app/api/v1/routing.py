from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.organization import OrganizationMember, OrgRole
from app.models.project import Project
from app.models.routing import RoutingRule
from app.schemas.routing import (
    RoutingRuleCreate, RoutingRuleUpdate, RoutingRuleResponse,
    RoutingTestRequest, RoutingTestResponse
)
from app.api.deps import get_current_user, get_current_membership
from app.services.routing_engine import evaluate_routing
from app.services.audit_service import log_action

router = APIRouter()


@router.get("/projects/{project_id}/rules", response_model=List[RoutingRuleResponse])
def list_routing_rules(
    project_id: str,
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    rules = (
        db.query(RoutingRule)
        .filter(RoutingRule.project_id == project_id)
        .order_by(RoutingRule.priority.asc())
        .all()
    )
    return rules


@router.post("/projects/{project_id}/rules", response_model=RoutingRuleResponse, status_code=status.HTTP_201_CREATED)
def create_routing_rule(
    project_id: str,
    rule_in: RoutingRuleCreate,
    membership: OrganizationMember = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if membership.role not in [OrgRole.ADMIN.value, OrgRole.PROJECT_MANAGER.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to manage routing rules.")

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    rule = RoutingRule(
        project_id=project.id,
        name=rule_in.name,
        description=rule_in.description,
        priority=rule_in.priority,
        conditions=rule_in.conditions,
        target_type=rule_in.target_type,
        target_user_id=rule_in.target_user_id,
        target_team=rule_in.target_team,
        target_email=rule_in.target_email,
        is_active=True
    )
    db.add(rule)

    log_action(
        db=db,
        organization_id=membership.organization_id,
        action="routing_rule.create",
        resource_type="routing_rule",
        resource_id=rule.name,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"project_id": project.id, "priority": rule.priority}
    )

    db.commit()
    db.refresh(rule)
    return rule


@router.put("/projects/{project_id}/rules/{rule_id}", response_model=RoutingRuleResponse)
def update_routing_rule(
    project_id: str,
    rule_id: int,
    rule_in: RoutingRuleUpdate,
    membership: OrganizationMember = Depends(get_current_membership),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if membership.role not in [OrgRole.ADMIN.value, OrgRole.PROJECT_MANAGER.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to manage routing rules.")

    rule = (
        db.query(RoutingRule)
        .join(Project, RoutingRule.project_id == Project.id)
        .filter(
            RoutingRule.id == rule_id,
            RoutingRule.project_id == project_id,
            Project.organization_id == membership.organization_id
        )
        .first()
    )
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routing rule not found")

    if rule_in.name is not None:
        rule.name = rule_in.name
    if rule_in.description is not None:
        rule.description = rule_in.description
    if rule_in.priority is not None:
        rule.priority = rule_in.priority
    if rule_in.conditions is not None:
        rule.conditions = rule_in.conditions
    if rule_in.target_type is not None:
        rule.target_type = rule_in.target_type
    if rule_in.target_user_id is not None:
        rule.target_user_id = rule_in.target_user_id
    if rule_in.target_team is not None:
        rule.target_team = rule_in.target_team
    if rule_in.target_email is not None:
        rule.target_email = rule_in.target_email
    if rule_in.is_active is not None:
        rule.is_active = rule_in.is_active

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/projects/{project_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routing_rule(
    project_id: str,
    rule_id: int,
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    if membership.role not in [OrgRole.ADMIN.value, OrgRole.PROJECT_MANAGER.value]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to delete routing rules.")

    rule = (
        db.query(RoutingRule)
        .join(Project, RoutingRule.project_id == Project.id)
        .filter(
            RoutingRule.id == rule_id,
            RoutingRule.project_id == project_id,
            Project.organization_id == membership.organization_id
        )
        .first()
    )
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routing rule not found")

    db.delete(rule)
    db.commit()
    return None


@router.post("/projects/{project_id}/test", response_model=RoutingTestResponse)
def test_routing(
    project_id: str,
    test_in: RoutingTestRequest,
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    res = evaluate_routing(
        db=db,
        project=project,
        environment=test_in.environment,
        service=test_in.service,
        error_type=test_in.error_type,
        phase=test_in.phase or "development",
        severity=test_in.severity
    )

    target_val = res.assigned_email or res.assigned_team or "Default Project Owner"
    return RoutingTestResponse(
        matched_rule_id=res.matched_rule_id,
        matched_rule_name=res.matched_rule_name,
        target_type="user" if res.assigned_email else "team",
        target=target_val,
        reason=res.reason
    )

