"""Celery 任务模块。"""

from app.tasks.jobs import process_job_task

__all__ = ["process_job_task"]
