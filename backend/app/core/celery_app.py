from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "devalert",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.email_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.CELERY_ALWAYS_EAGER,
    task_eager_propagates=True,
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
    }
)

