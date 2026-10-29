import threading
from app.core.celery_app import celery_app
from app.services.email_service import send_email_sync


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def send_email_notification_task(self, notification_id: int):
    """Celery background task to send an email notification."""
    success = send_email_sync(notification_id)
    if not success:
        # Check if we should retry
        try:
            self.retry(countdown=5 * (2 ** self.request.retries))
        except Exception:
            pass
    return success


def dispatch_notification_async(notification_id: int):
    """
    Dispatches the email notification asynchronously.
    Tries Celery first; if broker is unreachable or in development/test,
    uses a daemon thread to guarantee non-blocking delivery.
    """
    try:
        send_email_notification_task.delay(notification_id)
    except Exception:
        # Fallback to background thread execution so error ingestion API never blocks
        thread = threading.Thread(target=send_email_sync, args=(notification_id,), daemon=True)
        thread.start()

