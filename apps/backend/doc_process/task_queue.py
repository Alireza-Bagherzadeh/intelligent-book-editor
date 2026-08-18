from __future__ import annotations

import json
import os
from typing import Any


VERCEL_QUEUE_TOPIC = "default"


def enqueue_task(
    task_path: str,
    *args: Any,
    task_name: str | None = None,
):
    """Dispatch through Vercel Queues in production and Django-Q locally."""
    default_backend = "vercel" if os.getenv("VERCEL") else "django_q"
    backend = os.getenv("TASK_BACKEND", default_backend).lower()

    if backend == "vercel":
        from vercel.workers import send

        payload = {
            "task_path": task_path,
            "args": list(args),
            "task_name": task_name,
        }

        # Fail immediately with a useful error if a future caller passes an
        # argument that cannot be represented in a queue message.
        json.dumps(payload)
        return send(VERCEL_QUEUE_TOPIC, payload)

    if backend != "django_q":
        raise ValueError(
            "TASK_BACKEND must be either 'vercel' or 'django_q'."
        )

    from django_q.tasks import async_task

    kwargs: dict[str, Any] = {}
    if task_name:
        kwargs["task_name"] = task_name

    return async_task(task_path, *args, **kwargs)
