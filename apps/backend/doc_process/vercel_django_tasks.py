from django.tasks import task


@task(queue_name="default")
def run_document_parsing_task(document_id: int):
    from doc_process.tasks import (
        run_document_parsing_task as impl,
    )

    return impl(document_id)


@task(queue_name="default")
def run_document_review_job_task(review_job_id: int):
    from doc_process.tasks import (
        run_document_review_job_task as impl,
    )

    return impl(review_job_id)


@task(queue_name="default")
def run_block_difference_task(*args, **kwargs):
    from doc_process.tasks import (
        run_block_difference_task as impl,
    )

    return impl(*args, **kwargs)


@task(queue_name="default")
def run_ai_review_task(*args, **kwargs):
    from doc_process.tasks import (
        run_ai_review_task as impl,
    )

    return impl(*args, **kwargs)