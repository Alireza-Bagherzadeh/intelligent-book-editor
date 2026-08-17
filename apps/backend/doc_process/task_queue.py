import os


def enqueue_task(
    task_path: str,
    *args,
    task_name: str | None = None,
):
    backend = os.getenv(
        "TASK_BACKEND",
        "django_q",
    ).lower()

    # Production / Vercel
    if backend == "vercel":
        from doc_process import vercel_django_tasks

        task_map = {
            "doc_process.tasks.run_document_parsing_task":
                vercel_django_tasks.run_document_parsing_task,

            "doc_process.tasks.run_document_review_job_task":
                vercel_django_tasks.run_document_review_job_task,

            "doc_process.tasks.run_block_difference_task":
                vercel_django_tasks.run_block_difference_task,

            "doc_process.tasks.run_ai_review_task":
                vercel_django_tasks.run_ai_review_task,
        }

        task = task_map.get(task_path)

        if task is None:
            raise ValueError(
                f"Unknown Vercel task: {task_path}"
            )

        return task.enqueue(*args)

    # Local
    from django_q.tasks import async_task

    kwargs = {}

    if task_name:
        kwargs["task_name"] = task_name

    return async_task(
        task_path,
        *args,
        **kwargs,
    )