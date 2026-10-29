import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
from app.schemas.event import EventIngest, IngestResult
from app.api.deps import authenticate_api_key
from app.services.incident_service import process_event_ingestion

router = APIRouter()


@router.post("/jenkins", response_model=IngestResult, status_code=status.HTTP_201_CREATED)
async def jenkins_webhook(
    request: Request,
    payload: Dict[str, Any],
    project: Project = Depends(authenticate_api_key),
    db: Session = Depends(get_db)
):
    """
    Jenkins Pipeline / Webhook Integration.
    Captures job name, build number, repository, branch, commit ID,
    failed stage, build URL, timestamp, and sanitized log excerpt.
    """
    job_name = payload.get("job_name", "jenkins-job")
    build_num = payload.get("build_number", "0")
    failed_stage = payload.get("stage", payload.get("failed_stage", "build"))
    error_msg = payload.get("error_message", f"Jenkins build #{build_num} failed in stage '{failed_stage}'")
    build_url = payload.get("build_url", "")
    log_excerpt = payload.get("log_excerpt", "")
    branch = payload.get("branch", "main")
    commit_sha = payload.get("commit_sha", "")

    # Normalize to DevAlert Event
    event = EventIngest(
        project_id=project.id,
        event_id=f"jenkins-{job_name}-{build_num}-{failed_stage}",
        environment=payload.get("environment", "testing"),
        phase="Build" if "build" in failed_stage.lower() else ("Deployment" if "deploy" in failed_stage.lower() else "Testing"),
        service=job_name,
        source="jenkins",
        error_type=f"JenkinsBuildFailure[{failed_stage}]",
        message=error_msg,
        severity=payload.get("severity", "high"),
        stack_trace=log_excerpt,
        metadata={
            "job_name": job_name,
            "build_number": build_num,
            "stage": failed_stage,
            "branch": branch,
            "commit_sha": commit_sha,
            "build_url": build_url,
            "repository": payload.get("repository", "")
        }
    )

    return process_event_ingestion(db=db, project=project, event_in=event)


@router.post("/github", response_model=IngestResult, status_code=status.HTTP_201_CREATED)
async def github_actions_webhook(
    request: Request,
    payload: Dict[str, Any],
    project: Project = Depends(authenticate_api_key),
    db: Session = Depends(get_db)
):
    """
    GitHub Actions Integration.
    Captures repository, workflow name, run ID, failed step, branch, commit SHA, and failure details.
    """
    workflow = payload.get("workflow", "CI")
    run_id = str(payload.get("run_id", "0"))
    step = payload.get("failed_step", payload.get("job", "unknown-step"))
    error_msg = payload.get("message", f"GitHub Actions step '{step}' failed in workflow '{workflow}'")
    repo = payload.get("repository", "unknown-repo")
    branch = payload.get("branch", "main")
    commit_sha = payload.get("commit_sha", "")
    run_url = payload.get("run_url", f"https://github.com/{repo}/actions/runs/{run_id}")

    event = EventIngest(
        project_id=project.id,
        event_id=f"gh-{run_id}-{step}",
        environment=payload.get("environment", "testing"),
        phase="Testing" if "test" in step.lower() else ("Build" if "build" in step.lower() else "Deployment"),
        service=workflow,
        source="github-actions",
        error_type=f"WorkflowFailure[{step}]",
        message=error_msg,
        severity=payload.get("severity", "high"),
        stack_trace=payload.get("logs", ""),
        metadata={
            "workflow": workflow,
            "run_id": run_id,
            "step": step,
            "repository": repo,
            "branch": branch,
            "commit_sha": commit_sha,
            "run_url": run_url
        }
    )

    return process_event_ingestion(db=db, project=project, event_in=event)


@router.post("/generic", response_model=IngestResult, status_code=status.HTTP_201_CREATED)
async def generic_webhook(
    request: Request,
    payload: Dict[str, Any],
    project: Project = Depends(authenticate_api_key),
    db: Session = Depends(get_db)
):
    """
    Generic Webhook Integration for third-party monitoring or custom tools.
    """
    error_type = payload.get("error_type") or payload.get("event_type") or "GenericAlert"
    message = payload.get("message") or payload.get("summary") or payload.get("description") or "Unspecified error payload"
    service = payload.get("service") or payload.get("component") or "generic-service"
    severity = payload.get("severity", "medium")
    environment = payload.get("environment", "production")

    event = EventIngest(
        project_id=project.id,
        event_id=payload.get("id") or payload.get("event_id"),
        environment=environment,
        phase=payload.get("phase"),
        service=service,
        source="generic-webhook",
        error_type=str(error_type)[:150],
        message=str(message)[:5000],
        severity=severity,
        stack_trace=payload.get("stack_trace") or payload.get("trace"),
        metadata=payload.get("metadata", {})
    )

    return process_event_ingestion(db=db, project=project, event_in=event)

