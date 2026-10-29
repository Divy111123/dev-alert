import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.incident import Incident
from app.models.event import ErrorEvent
from app.models.notification import NotificationRecord
from app.schemas.event import EventIngest, IngestResult
from app.services.fingerprint import sanitize_text, compute_fingerprint
from app.services.phase_detector import detect_phase
from app.services.routing_engine import evaluate_routing
from app.services.ai_analyzer import generate_heuristic_analysis
from app.tasks.email_tasks import dispatch_notification_async


SEVERITY_RANKS = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def process_event_ingestion(
    db: Session,
    project: Project,
    event_in: EventIngest
) -> IngestResult:
    """
    Core ingestion pipeline:
    1. Idempotency check
    2. Sanitization & Phase detection
    3. Fingerprinting & Incident deduplication
    4. Escalation & Cooldown evaluation
    5. Developer routing
    6. Non-blocking asynchronous notification dispatch
    """
    # 1. Idempotency check: if event_id is supplied and already recorded
    if event_in.event_id:
        existing_event = db.query(ErrorEvent).filter(
            ErrorEvent.project_id == project.id,
            ErrorEvent.event_id == event_in.event_id
        ).first()
        if existing_event:
            inc = existing_event.incident
            return IngestResult(
                status="idempotent_duplicate",
                incident_id=inc.id,
                event_id=existing_event.id,
                is_new_incident=False,
                occurrence_count=inc.occurrence_count,
                assigned_to=inc.assigned_email or inc.assigned_team,
                phase=inc.phase,
                severity=inc.severity
            )

    # 2. Sanitize and normalize
    clean_message = sanitize_text(event_in.message) or ""
    clean_stack = sanitize_text(event_in.stack_trace) if event_in.stack_trace else None
    
    # Detect Phase
    detected_phase, phase_reason = detect_phase(
        explicit_phase=event_in.phase,
        environment=event_in.environment,
        metadata=event_in.metadata,
        source=event_in.source
    )

    # 3. Compute Fingerprint
    fingerprint = compute_fingerprint(
        project_id=project.id,
        error_type=event_in.error_type,
        message=clean_message,
        service=event_in.service,
        stack_trace=clean_stack
    )

    now = datetime.now(timezone.utc)
    is_new = False
    should_notify = False
    notification_type = "new_incident"

    # 4. Check for existing incident
    incident = db.query(Incident).filter(
        Incident.project_id == project.id,
        Incident.fingerprint == fingerprint
    ).first()

    proj_settings = project.settings or {}
    cooldown_minutes = proj_settings.get("cooldown_minutes", 15)

    if incident:
        # Existing incident: duplicate error grouping
        incident.occurrence_count += 1
        incident.last_seen = now

        # Reopen if it was previously marked resolved
        if incident.status == "resolved":
            incident.status = "reopened"
            should_notify = True
            notification_type = "escalation"

        # Check severity escalation
        current_rank = SEVERITY_RANKS.get(incident.severity.lower(), 2)
        new_rank = SEVERITY_RANKS.get(event_in.severity.lower(), 2)
        if new_rank > current_rank:
            incident.severity = event_in.severity.lower()
            if proj_settings.get("notify_on_escalation", True):
                should_notify = True
                notification_type = "escalation"

        # Cooldown check for repeated notifications
        if not should_notify:
            if incident.last_notified_at:
                diff = now - incident.last_notified_at.replace(tzinfo=timezone.utc if incident.last_notified_at.tzinfo is None else incident.last_notified_at.tzinfo)
                if diff > timedelta(minutes=cooldown_minutes) and incident.occurrence_count % 10 == 0:
                    should_notify = True
                    notification_type = "summary"
            else:
                should_notify = True
                notification_type = "summary"

    else:
        # New Incident!
        is_new = True
        should_notify = proj_settings.get("notify_on_new", True)
        notification_type = "critical_incident" if event_in.severity.lower() == "critical" else "new_incident"

        # Route to developer or team
        routing = evaluate_routing(
            db=db,
            project=project,
            environment=event_in.environment,
            service=event_in.service,
            error_type=event_in.error_type,
            phase=detected_phase,
            severity=event_in.severity,
            metadata=event_in.metadata
        )

        # Generate initial AI heuristic analysis
        ai_summary, ai_steps = generate_heuristic_analysis(
            error_type=event_in.error_type,
            message=clean_message,
            service=event_in.service
        )

        title = f"{event_in.error_type} in {event_in.service}"
        incident = Incident(
            project_id=project.id,
            fingerprint=fingerprint,
            title=title,
            error_type=event_in.error_type,
            message=clean_message,
            severity=event_in.severity.lower(),
            status="open",
            environment=event_in.environment,
            phase=detected_phase,
            service=event_in.service,
            first_seen=now,
            last_seen=now,
            occurrence_count=1,
            assigned_user_id=routing.assigned_user_id,
            assigned_team=routing.assigned_team,
            assigned_email=routing.assigned_email,
            routing_reason=routing.reason,
            ai_summary=ai_summary,
            ai_suggested_fix=ai_steps,
        )
        db.add(incident)
        db.flush()

    # 5. Record the ErrorEvent
    event_record = ErrorEvent(
        incident_id=incident.id,
        project_id=project.id,
        event_id=event_in.event_id,
        environment=event_in.environment,
        phase=detected_phase,
        service=event_in.service,
        source=event_in.source,
        error_type=event_in.error_type,
        message=clean_message,
        severity=event_in.severity.lower(),
        timestamp=event_in.timestamp or now,
        stack_trace=clean_stack,
        sanitized_stack_trace=clean_stack,
        metadata_json=event_in.metadata or {},
        request_data=event_in.request_data or {},
        host=event_in.host,
        release=event_in.release,
    )
    db.add(event_record)

    # 6. Dispatch Notification if policy indicates
    recipient = incident.assigned_email or project.default_owner_email
    if should_notify and recipient:
        subject = f"[{incident.severity.upper()}] {project.name}: {incident.error_type} in {incident.service}"
        notif = NotificationRecord(
            incident_id=incident.id,
            project_id=project.id,
            notification_type=notification_type,
            recipient_email=recipient,
            recipient_name=incident.assigned_team or recipient,
            subject=subject,
            status="pending",
        )
        db.add(notif)
        db.flush()
        incident.last_notified_at = now
        incident.notification_count += 1

        # Dispatch in background worker without blocking ingestion
        dispatch_notification_async(notif.id)

    db.commit()

    return IngestResult(
        status="success",
        incident_id=incident.id,
        event_id=event_record.id,
        is_new_incident=is_new,
        occurrence_count=incident.occurrence_count,
        assigned_to=incident.assigned_email or incident.assigned_team or "Unassigned",
        phase=detected_phase,
        severity=incident.severity
    )

