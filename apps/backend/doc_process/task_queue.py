import os


def enqueue_task(
    task_path: str,
    *args,
    task_name: str | None = None,
):
    task_backend = os.getenv(
        "TASK_BACKEND",
        "django_q",
    ).lower()

    # Production on Vercel
    if task_backend == "vercel":
        from config.celery import app

        return app.send_task(
            task_path,
            args=list(args),
            queue="celery",
        )

    # Local development
    from django_q.tasks import async_task

    kwargs = {}

    if task_name:
        kwargs["task_name"] = task_name

    return async_task(
        task_path,
        *args,
        **kwargs,
    )