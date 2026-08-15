import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


from config.celery import app

# Register Vercel/Celery task wrappers.
import doc_process.vercel_tasks  # noqa: F401

__all__ = ["app"]