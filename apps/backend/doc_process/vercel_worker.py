from __future__ import annotations

import os
from typing import Any

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from vercel.workers import MessageMetadata, subscribe

from doc_process import tasks as core_tasks


_TASKS = {
    "doc_process.tasks.run_document_parsing_task": (
        core_tasks.run_document_parsing_task
    ),
    "doc_process.tasks.run_document_review_job_task": (
        core_tasks.run_document_review_job_task
    ),
    "doc_process.tasks.run_block_difference_task": (
        core_tasks.run_block_difference_task
    ),
    "doc_process.tasks.run_ai_review_task": (
        core_tasks.run_ai_review_task
    ),
}


@subscribe(topic="default")
def process_message(
    message: Any,
    metadata: MessageMetadata,
) -> None:
    """Execute one serialized application task from Vercel Queues."""
    if not isinstance(message, dict):
        raise ValueError("Queue message must be a JSON object.")

    task_path = message.get("task_path")
    args = message.get("args", [])

    if not isinstance(task_path, str) or not task_path:
        raise ValueError("Queue message is missing task_path.")
    if not isinstance(args, list):
        raise ValueError("Queue message args must be a list.")

    task = _TASKS.get(task_path)
    if task is None:
        raise ValueError(f"Unknown queue task: {task_path}")

    print(
        "Vercel worker executing",
        task_path,
        "message_id=",
        metadata.get("messageId"),
    )
    task(*args)
    return None
