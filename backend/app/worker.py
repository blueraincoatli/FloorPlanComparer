"""Celery application instance used for background processing."""

from __future__ import annotations

from celery import Celery

from app.core.settings import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery(
        "floorplan_backend",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.tasks.jobs", "app.tasks.enhanced_jobs", "app.tasks.converter_tasks"],
    )
    app.conf.update(
        task_always_eager=settings.celery_task_always_eager,
        task_eager_propagates=settings.celery_task_eager_propagates,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
    return app


celery_app = create_celery_app()
