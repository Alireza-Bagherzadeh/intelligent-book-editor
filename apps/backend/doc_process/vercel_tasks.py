import os

from config.celery import app


def _ensure_django():
    """
    Ensure Django is initialized inside the actual
    Vercel Queue consumer invocation.
    """
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "config.settings",
    )

    from django.apps import apps

    if not apps.ready:
        import django
        django.setup()


@app.task(
    name="doc_process.tasks.run_document_parsing_task"
)
def run_document_parsing_task(document_id: int):
    _ensure_django()

    from doc_process.tasks import (
        run_document_parsing_task as task_impl,
    )

    return task_impl(document_id)


@app.task(
    name="doc_process.tasks.run_document_review_job_task"
)
def run_document_review_job_task(review_job_id: int):
    _ensure_django()

    from doc_process.tasks import (
        run_document_review_job_task as task_impl,
    )

    return task_impl(review_job_id)


@app.task(
    name="doc_process.tasks.run_block_difference_task"
)
def run_block_difference_task(*args, **kwargs):
    _ensure_django()

    from doc_process.tasks import (
        run_block_difference_task as task_impl,
    )

    return task_impl(*args, **kwargs)


@app.task(
    name="doc_process.tasks.run_ai_review_task"
)
def run_ai_review_task(*args, **kwargs):
    _ensure_django()

    from doc_process.tasks import (
        run_ai_review_task as task_impl,
    )

    return task_impl(*args, **kwargs)