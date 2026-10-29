from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.routing import RoutingRule
from app.models.user import User


class RoutingResult:
    def __init__(
        self,
        assigned_user_id: Optional[int] = None,
        assigned_team: Optional[str] = None,
        assigned_email: Optional[str] = None,
        reason: str = "",
        matched_rule_id: Optional[int] = None,
        matched_rule_name: Optional[str] = None
    ):
        self.assigned_user_id = assigned_user_id
        self.assigned_team = assigned_team
        self.assigned_email = assigned_email
        self.reason = reason
        self.matched_rule_id = matched_rule_id
        self.matched_rule_name = matched_rule_name


def evaluate_routing(
    db: Session,
    project: Project,
    environment: str,
    service: str,
    error_type: str,
    phase: str,
    severity: str,
    metadata: Optional[Dict[str, Any]] = None
) -> RoutingResult:
    """
    Evaluates project-configured routing rules in priority order.
    If no rule matches, falls back to the default project owner or default team.
    """
    metadata = metadata or {}
    rules = (
        db.query(RoutingRule)
        .filter(
            RoutingRule.project_id == project.id,
            RoutingRule.is_active == True
        )
        .order_by(RoutingRule.priority.asc(), RoutingRule.id.asc())
        .all()
    )

    env_norm = environment.lower().strip()
    srv_norm = service.lower().strip()
    err_norm = error_type.lower().strip()
    phase_norm = phase.lower().strip()
    sev_norm = severity.lower().strip()
    stage_val = str(metadata.get("stage", "")).lower().strip()

    for rule in rules:
        conds = rule.conditions or {}
        matches = True
        matched_fields = []

        # Check environment
        if "environment" in conds and conds["environment"]:
            expected_env = str(conds["environment"]).lower().strip()
            if expected_env != "*" and expected_env != env_norm:
                matches = False
            else:
                matched_fields.append(f"environment={expected_env}")

        # Check service/component
        if matches and "service" in conds and conds["service"]:
            expected_srv = str(conds["service"]).lower().strip()
            if expected_srv != "*" and expected_srv != srv_norm:
                matches = False
            else:
                matched_fields.append(f"service={expected_srv}")

        # Check error category / error type
        if matches and "error_type" in conds and conds["error_type"]:
            expected_err = str(conds["error_type"]).lower().strip()
            if expected_err != "*" and expected_err not in err_norm:
                matches = False
            else:
                matched_fields.append(f"error_type={expected_err}")

        # Check phase
        if matches and "phase" in conds and conds["phase"]:
            expected_phase = str(conds["phase"]).lower().strip()
            if expected_phase != "*" and expected_phase != phase_norm:
                matches = False
            else:
                matched_fields.append(f"phase={expected_phase}")

        # Check CI/CD stage
        if matches and "stage" in conds and conds["stage"]:
            expected_stage = str(conds["stage"]).lower().strip()
            if expected_stage != "*" and expected_stage not in stage_val:
                matches = False
            else:
                matched_fields.append(f"stage={expected_stage}")

        # Check severity
        if matches and "severity" in conds and conds["severity"]:
            expected_sev = str(conds["severity"]).lower().strip()
            if expected_sev != "*" and expected_sev != sev_norm:
                matches = False
            else:
                matched_fields.append(f"severity={expected_sev}")

        if matches and matched_fields:
            # Rule matched!
            target_email = rule.target_email
            target_user_id = rule.target_user_id

            # If user_id provided, look up email if not set
            if target_user_id and not target_email:
                user = db.query(User).filter(User.id == target_user_id).first()
                if user:
                    target_email = user.email

            reason = f"Matched Rule #{rule.priority} '{rule.name}' on ({', '.join(matched_fields)})"
            return RoutingResult(
                assigned_user_id=target_user_id,
                assigned_team=rule.target_team,
                assigned_email=target_email,
                reason=reason,
                matched_rule_id=rule.id,
                matched_rule_name=rule.name
            )

    # Fallback to project defaults
    fallback_email = project.default_owner_email
    fallback_user_id = project.default_owner_id
    fallback_team = project.default_team or "Engineering"

    if fallback_user_id and not fallback_email:
        user = db.query(User).filter(User.id == fallback_user_id).first()
        if user:
            fallback_email = user.email

    reason = "Fallback: No specific routing rule matched; routed to project default owner/team."
    return RoutingResult(
        assigned_user_id=fallback_user_id,
        assigned_team=fallback_team,
        assigned_email=fallback_email,
        reason=reason,
        matched_rule_id=None,
        matched_rule_name=None
    )

