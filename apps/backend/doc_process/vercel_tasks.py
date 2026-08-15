from config.celery import app

from . import tasks as core_tasks


@app.task(
    name="doc_process.tasks.run_document_parsing_task"
)
def run_document_parsing_task(document_id: int):
    return core_tasks.run_document_parsing_task(document_id)


@app.task(
    name="doc_process.tasks.run_document_review_job_task"
)
def run_document_review_job_task(review_job_id: int):
    return core_tasks.run_document_review_job_task(review_job_id)


@app.task(
    name="doc_process.tasks.run_block_difference_task"
)
def run_block_difference_task(review_job_id: int):
    return core_tasks.run_block_difference_task(review_job_id)


@app.task(
    name="doc_process.tasks.run_ai_review_task"
)
def run_ai_review_task(document_id: int):
    return core_tasks.run_ai_review_task(document_id)