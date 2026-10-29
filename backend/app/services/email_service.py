import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.notification import NotificationRecord

# Setup Jinja2 templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def render_email(template_name: str, context: dict) -> tuple[str, str]:
    """Renders HTML and plain-text fallback for email."""
    html_template = jinja_env.get_template(f"emails/{template_name}.html")
    html_content = html_template.render(**context)

    # Simple plain-text fallback generation
    text_content = f"{context.get('subject', 'DevAlert Notification')}\n"
    text_content += f"==============================================\n"
    if "incident" in context:
        inc = context["incident"]
        text_content += f"Incident ID: {inc.id}\n"
        text_content += f"Error Type: {inc.error_type}\n"
        text_content += f"Message: {inc.message}\n"
        text_content += f"Severity: {inc.severity}\n"
        text_content += f"Phase: {inc.phase}\n"
        text_content += f"Service: {inc.service}\n"
        text_content += f"Assigned: {context.get('assigned_to', 'Unassigned')}\n"
        text_content += f"Dashboard: {context.get('dashboard_url')}/incidents/{inc.id}\n"
    else:
        text_content += f"DevAlert Notification for {context.get('recipient_email')}\n"

    return html_content, text_content


def send_email_sync(
    notification_id: int,
    max_retries: int = 3,
    backoff_factor: float = 1.0
) -> bool:
    """
    Sends an email with exponential backoff retry.
    Records delivery status and errors in the NotificationRecord table.
    """
    db = SessionLocal()
    try:
        notif = db.query(NotificationRecord).filter(NotificationRecord.id == notification_id).first()
        if not notif:
            return False

        notif.attempts_count += 1
        notif.last_attempt_at = datetime.now(timezone.utc)
        db.commit()

        # Build context
        context = {
            "subject": notif.subject,
            "recipient_email": notif.recipient_email,
            "recipient_name": notif.recipient_name,
            "dashboard_url": settings.FRONTEND_URL,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        # Check incident details if available
        if notif.incident:
            inc = notif.incident
            proj = inc.project
            context.update({
                "incident": inc,
                "project": proj,
                "assigned_to": notif.recipient_name or notif.recipient_email,
                "stack_trace": inc.events[0].sanitized_stack_trace if inc.events else "",
                "ai_summary": inc.ai_summary,
            })

        html_body, text_body = render_email(notif.notification_type, context)

        # Handle different EMAIL_MODEs
        mode = settings.EMAIL_MODE.lower()

        if mode == "mock" or mode == "console":
            # Fast in-memory or stdout mode for testing
            print(f"\n[DEV-ALERT-EMAIL-MOCK] To: {notif.recipient_email} | Subject: {notif.subject}")
            print(f"Content excerpt: {text_body[:160]}...\n")
            notif.status = "sent"
            notif.sent_at = datetime.now(timezone.utc)
            notif.error_message = None
            db.commit()
            return True

        elif mode == "file":
            # Dump to directory for offline verification
            out_dir = Path(settings.EMAIL_FILE_PATH)
            out_dir.mkdir(parents=True, exist_ok=True)
            filename = out_dir / f"email_{notif.id}_{int(time.time())}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_body)
            notif.status = "sent"
            notif.sent_at = datetime.now(timezone.utc)
            notif.error_message = f"Saved to file: {filename}"
            db.commit()
            return True

        elif mode == "smtp":
            # Real SMTP delivery with exponential backoff
            last_err = None
            for attempt in range(1, max_retries + 1):
                try:
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = notif.subject
                    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
                    msg["To"] = notif.recipient_email

                    msg.attach(MIMEText(text_body, "plain"))
                    msg.attach(MIMEText(html_body, "html"))

                    if settings.SMTP_USE_SSL:
                        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
                    else:
                        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
                        if settings.SMTP_USE_TLS:
                            server.starttls()

                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                    server.sendmail(settings.SMTP_FROM_EMAIL, [notif.recipient_email], msg.as_string())
                    server.quit()

                    notif.status = "sent"
                    notif.sent_at = datetime.now(timezone.utc)
                    notif.error_message = None
                    db.commit()
                    return True
                except Exception as ex:
                    last_err = str(ex)
                    if attempt < max_retries:
                        time.sleep(backoff_factor * (2 ** (attempt - 1)))

            # If all retries failed
            notif.status = "failed"
            notif.error_message = f"SMTP delivery failed after {max_retries} attempts: {last_err}"
            db.commit()
            return False

        else:
            notif.status = "sent"
            notif.sent_at = datetime.now(timezone.utc)
            db.commit()
            return True

    except Exception as e:
        if 'notif' in locals() and notif:
            notif.status = "failed"
            notif.error_message = f"Unhandled delivery exception: {str(e)}"
            db.commit()
        return False
    finally:
        db.close()

