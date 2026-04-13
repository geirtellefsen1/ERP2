"""
Background task package.

Every submodule here defines Celery tasks bound to `celery_app`.
Add new task modules to `TASK_MODULES` in app/celery_app.py.
"""
from app.celery_app import celery_app

__all__ = ["celery_app"]
