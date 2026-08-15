from config.celery import app

# Force Celery task registration when the Vercel worker starts.
import doc_process.vercel_tasks  # noqa: F401

__all__ = ["app"]