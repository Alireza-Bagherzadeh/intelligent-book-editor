import os

from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

app = Celery(
    "intelligent_book_editor",
    broker=os.getenv(
        "CELERY_BROKER_URL",
        "vercel://",
    ),
    include=[
        "doc_process.vercel_tasks",
    ],
)

app.conf.update(
    task_default_queue="celery",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_ignore_result=True,
)