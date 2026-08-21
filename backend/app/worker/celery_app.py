import os
from celery import Celery
from app.config import settings

celery_app = Celery(
    "survey_sentinel_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="ping_task")
def ping_task():
    return {"status": "pong", "worker": "survey_sentinel_celery"}
