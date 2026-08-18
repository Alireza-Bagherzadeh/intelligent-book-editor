from __future__ import annotations

import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Document, DocumentBlock, ReviewJob
from .services.document_pipeline import DocumentPipelineService
from .services.normal_review_service import MockAiReview
from .services.text_diff_service import process_and_save_block_differences
from .task_queue import enqueue_task

logger = logging.getLogger(__name__)


def run_document_parsing_task(document_id: int):
    """Parse one uploaded source into DocumentBlock records."""
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.warning("Document %s was not found for parsing.", document_id)
        return f"Document {document_id} not found."

    try:
        pipeline = DocumentPipelineService()
        created_count = pipeline.parse_document(document)
        return f"Document {document_id} parsed successfully ({created_count} blocks)."
    except Exception:
        # DocumentPipelineService persists FAILED + processing_error.
        logger.exception("Error parsing document %s.", document_id)
        raise


def run_document_review_job_task(review_job_id: int):
    """Run the deterministic/local review, then queue block differences."""
    try:
        review_job = ReviewJob.objects.select_related("document").get(
            id=review_job_id
        )
    except ReviewJob.DoesNotExist:
        logger.warning("ReviewJob %s was not found.", review_job_id)
        return f"ReviewJob {review_job_id} not found."

    document = review_job.document

    review_job.status = ReviewJob.Status.RUNNING
    review_job.started_at = timezone.now()
    review_job.model_name = "local-normalization-v1"
    review_job.error_message = ""
    review_job.save(
        update_fields=[
            "status",
            "started_at",
            "model_name",
            "error_message",
        ]
    )

    document.status = Document.Status.REVIEWING
    document.processing_error = ""
    document.save(update_fields=["status", "processing_error"])

    try:
        summary = MockAiReview().review_document(document, review_job)

        enqueue_task(
            "doc_process.tasks.run_block_difference_task",
            review_job.id,
            task_name=f"BlockDiff-{review_job.id}",
        )

        logger.info(
            "Review phase completed for ReviewJob %s; difference task queued.",
            review_job_id,
        )
        return f"Review phase completed: {summary}"

    except Exception as exc:
        error_message = f"Failed executing review job: {exc}"
        logger.exception(error_message)

        review_job.status = ReviewJob.Status.FAILED
        review_job.finished_at = timezone.now()
        review_job.error_message = error_message
        review_job.save(
            update_fields=["status", "finished_at", "error_message"]
        )

        document.status = Document.Status.FAILED
        document.processing_error = error_message
        document.save(update_fields=["status", "processing_error"])
        raise


def run_block_difference_task(review_job_id: int):
    """Persist raw-vs-normalized differences and finalize local review."""
    review_job: ReviewJob | None = None
    document: Document | None = None

    try:
        review_job = ReviewJob.objects.select_related("document").get(
            id=review_job_id
        )
        document = review_job.document

        with transaction.atomic():
            blocks = (
                DocumentBlock.objects
                .filter(document=document)
                .order_by("order_index")
            )

            for block in blocks:
                process_and_save_block_differences(
                    block=block,
                    review_job=review_job,
                )

            document.status = Document.Status.REVIEWED
            document.processing_error = ""
            document.save(update_fields=["status", "processing_error"])

            review_job.status = ReviewJob.Status.SUCCEEDED
            review_job.finished_at = timezone.now()
            review_job.error_message = ""
            review_job.save(
                update_fields=[
                    "status",
                    "finished_at",
                    "error_message",
                ]
            )

        # AI review is optional. Do not make parsing/local review depend on the
        # provider being configured.
        if settings.GEMINI_API_KEY and settings.GEMINI_MODEL:
            enqueue_task(
                "doc_process.tasks.run_ai_review_task",
                document.id,
                task_name=f"AiReview-{document.id}",
            )

        logger.info(
            "Differences completed for ReviewJob %s / Document %s.",
            review_job_id,
            document.id,
        )
        return f"Differences calculated for ReviewJob {review_job_id}."

    except ReviewJob.DoesNotExist:
        logger.warning(
            "ReviewJob %s was not found for difference processing.",
            review_job_id,
        )
        return f"ReviewJob {review_job_id} not found."

    except Exception as exc:
        error_message = f"Block difference processing failed: {exc}"
        logger.exception(error_message)

        if review_job is not None:
            review_job.status = ReviewJob.Status.FAILED
            review_job.finished_at = timezone.now()
            review_job.error_message = error_message
            review_job.save(
                update_fields=["status", "finished_at", "error_message"]
            )

        if document is not None:
            document.status = Document.Status.FAILED
            document.processing_error = error_message
            document.save(update_fields=["status", "processing_error"])

        raise


def run_ai_review_task(document_id: int):
    """Run optional Gemini review after the deterministic review succeeds."""
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    if not settings.GEMINI_MODEL:
        raise RuntimeError("GEMINI_MODEL is not configured.")

    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.warning("Document %s was not found for AI review.", document_id)
        return f"Document {document_id} not found."

    review_job: ReviewJob | None = None

    try:
        document.status = Document.Status.AI_REVIEWING
        document.processing_error = ""
        document.save(update_fields=["status", "processing_error"])

        review_job = ReviewJob.objects.create(
            document=document,
            status=ReviewJob.Status.RUNNING,
            model_name=settings.GEMINI_MODEL,
            started_at=timezone.now(),
        )

        # Lazy import keeps upload/parsing independent from the Gemini SDK.
        from .services.ai_review_service import GeminiReviewService

        summary = GeminiReviewService.process_document(
            document_id,
            review_job.id,
        )

        document.status = Document.Status.AI_REVIEWED
        document.processing_error = ""
        document.save(update_fields=["status", "processing_error"])

        return (
            f"AI ReviewJob {review_job.id} completed for document "
            f"{document_id}: {summary}"
        )

    except Exception as exc:
        logger.exception("AI review failed for document %s.", document_id)

        if review_job is not None and review_job.status != ReviewJob.Status.FAILED:
            review_job.status = ReviewJob.Status.FAILED
            review_job.finished_at = timezone.now()
            review_job.error_message = str(exc)
            review_job.save(
                update_fields=["status", "finished_at", "error_message"]
            )

        # Keep the usable deterministic review available even if the optional
        # AI provider fails. The queue still receives the exception and can retry.
        document.status = Document.Status.REVIEWED
        document.processing_error = f"AI review failed: {exc}"
        document.save(update_fields=["status", "processing_error"])
        raise
