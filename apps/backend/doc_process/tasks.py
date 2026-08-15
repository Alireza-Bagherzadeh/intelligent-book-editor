# tasks.py

import logging
from django.db import transaction
from django.utils import timezone
from .models import Document, ReviewJob, DocumentBlock
from .services.normal_review_service import MockAiReview
from .services.document_pipeline import DocumentPipelineService
from django_q.tasks import async_task
from .services.text_diff_service import process_and_save_block_differences
from .services.ai_review_service import GeminiReviewService

logger = logging.getLogger(__name__)

def run_document_parsing_task(document_id: int):
    """
    Background task to parse the uploaded document (Docx to Blocks).
    """
    try:
        document = Document.objects.get(id=document_id)

        # Update status to indicate processing has started
        document.status = Document.Status.UPLOADED
        document.save(update_fields=["status"])

        # Use the pipeline service to handle heavy lifting of parsing
        pipeline = DocumentPipelineService()
        pipeline.parse_document(document)

        return f"Document {document_id} parsed successfully."

    except Document.DoesNotExist:
        return f"Document {document_id} not found."
    except Exception as exc:
        logger.error(f"Error parsing document {document_id}: {exc}", exc_info=True)
        # Error handling is partially managed inside parse_document,
        # but we re-raise to let the task runner know it failed.
        raise

def run_document_review_job_task(review_job_id: int):
    """
    Background task to process document text using MockAiReview.
    Handles text normalization, RTL enforcement, and issue identification.
    After successful review, enqueues block difference generation task.
    """
    try:
        review_job = ReviewJob.objects.select_related("document").get(id=review_job_id)
    except ReviewJob.DoesNotExist:
        logger.error(f"ReviewJob {review_job_id} not found.")
        return

    document = review_job.document

    # Initialize the review service
    llm_service = MockAiReview()

    # Update job status to RUNNING before starting the heavy process
    review_job.status = ReviewJob.Status.RUNNING
    review_job.started_at = timezone.now()
    review_job.model_name = "local-normalization-v1"
    review_job.error_message = ""
    review_job.save(update_fields=["status", "started_at", "model_name", "error_message"])

    # Update document status to REVIEWING
    document.status = Document.Status.REVIEWING
    document.processing_error = ""
    document.save(update_fields=["status", "processing_error"])

    try:
        # The service method handles:
        # 1. Iterating through all blocks
        # 2. Applying normalization
        # 3. Setting is_rtl=True
        # 4. Generating BlockIssue records
        # 5. Wrapping DB operations in a transaction
        summary = llm_service.review_document(document, review_job)

        # Enqueue next pipeline step: block differences
        async_task(
            "doc_process.tasks.run_block_difference_task",
            review_job.id,
            task_name=f"BlockDiff-{review_job.id}",
        )

        logger.info(
            f"ReviewJob {review_job_id} review phase completed successfully for Doc {document.id}. "
            f"Block difference task enqueued."
        )
        return f"Review completed and block difference task queued: {summary}"

    except Exception as exc:
        error_msg = f"Failed executing review job: {str(exc)}"
        logger.error(error_msg, exc_info=True)

        # Persist failure state
        review_job.status = ReviewJob.Status.FAILED
        review_job.finished_at = timezone.now()
        review_job.error_message = error_msg
        review_job.save(update_fields=["status", "finished_at", "error_message"])

        document.status = Document.Status.FAILED
        document.processing_error = error_msg
        document.save(update_fields=["status", "processing_error"])

        raise exc

# def run_document_review_job_task(review_job_id: int):
#     """
#     Background task to process document text using MockAiReview.
#     Handles text normalization, RTL enforcement, and issue identification.
#     """
#     try:
#         review_job = ReviewJob.objects.select_related('document').get(id=review_job_id)
#     except ReviewJob.DoesNotExist:
#         logger.error(f"ReviewJob {review_job_id} not found.")
#         return

#     document = review_job.document

#     # Initialize the review service (currently using local regex-based logic)
#     llm_service = MockAiReview()

#     # Update Job status to RUNNING before starting the heavy process
#     review_job.status = ReviewJob.Status.RUNNING
#     review_job.started_at = timezone.now()
#     review_job.model_name = "local-normalization-v1"  # Indicating the local processor version
#     review_job.save(update_fields=["status", "started_at", "model_name"])

#     # Update Document status to REVIEWING
#     document.status = Document.Status.REVIEWING
#     document.save(update_fields=["status"])

#     try:
#         # The service method handles:
#         # 1. Iterating through all blocks (Paragraphs/Headings)
#         # 2. Applying normalization (half-spaces, punctuation, etc.)
#         # 3. Setting is_rtl=True
#         # 4. Generating BlockIssue records for corrections
#         # 5. Wrapping DB operations in a transaction
#         summary = llm_service.review_document(document, review_job)

#         logger.info(f"ReviewJob {review_job_id} successfully completed for Doc {document.id}")
#         return f"Review completed: {summary}"

#     except Exception as exc:
#         error_msg = f"Failed executing review job: {str(exc)}"
#         logger.error(error_msg, exc_info=True)

#         # Ensure failure state is persisted if the service crashes
#         review_job.status = ReviewJob.Status.FAILED
#         review_job.finished_at = timezone.now()
#         review_job.error_message = error_msg
#         review_job.save(update_fields=["status", "finished_at", "error_message"])

#         document.status = Document.Status.FAILED
#         document.processing_error = error_msg
#         document.save(update_fields=["status", "processing_error"])

#         raise exc

# tasks.py (ادامه فایل شما)


def run_block_difference_task(review_job_id: int):
    """
    Background task that calculates and stores differences between
    raw_text and normalized_text for every document block.

    This is the final stage of the review pipeline:
    parse -> review -> block differences
    """
    review_job = None
    document = None

    try:
        # Load the review job and its related document in one query.
        review_job = ReviewJob.objects.select_related("document").get(
            id=review_job_id
        )
        document = review_job.document

        # The job should already be RUNNING from the review task.
        # Do not mark it as SUCCEEDED until all differences are saved.

        # Use one transaction so partial difference records are not persisted
        # if processing any block fails.
        with transaction.atomic():
            blocks = (
                DocumentBlock.objects
                .filter(document=document)
                .order_by("order_index")
            )

            # Process each block and save its technical normalization differences.
            for block in blocks:
                process_and_save_block_differences(
                    block=block,
                    review_job=review_job,
                )

            # Mark the document as reviewed only after the full pipeline succeeds.
            document.status = Document.Status.REVIEWED
            document.processing_error = ""
            document.save(update_fields=["status", "processing_error"])

            # Mark the review job as successful only after differences are stored.
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

        logger.info(
            "Block differences completed successfully for ReviewJob %s "
            "and Document %s was marked as REVIEWED.",
            review_job_id,
            document.id,
        )

        return (
            f"Differences calculated successfully for ReviewJob "
            f"{review_job_id}."
        )

    except ReviewJob.DoesNotExist:
        logger.error(
            "ReviewJob %s was not found for block difference processing.",
            review_job_id,
        )
        return f"ReviewJob {review_job_id} not found."

    except Exception as exc:
        error_message = f"Block difference processing failed: {exc}"

        logger.error(
            "Error calculating differences for ReviewJob %s: %s",
            review_job_id,
            exc,
            exc_info=True,
        )

        # Persist the failure state for the review job when it was loaded.
        if review_job is not None:
            review_job.status = ReviewJob.Status.FAILED
            review_job.finished_at = timezone.now()
            review_job.error_message = error_message
            review_job.save(
                update_fields=[
                    "status",
                    "finished_at",
                    "error_message",
                ]
            )

        # Persist the failure state for the document when it was loaded.
        if document is not None:
            document.status = Document.Status.FAILED
            document.processing_error = error_message
            document.save(update_fields=["status", "processing_error"])

        # Re-raise the exception so django-q2 marks the task as failed.
        raise

def run_ai_review_task(document_id: int):
    """
    Background task for Django-Q to process the document with Gemini.
    Manages Document and ReviewJob states.
    """
    try:
        doc = Document.objects.get(id=document_id)
        
        # Update Document status
        doc.status = Document.Status.REVIEWING
        doc.save()
        
        # Initialize a new ReviewJob for this run
        review_job = ReviewJob.objects.create(
            document=doc,
            status=ReviewJob.Status.RUNNING,
            model_name='gemini-3.5-flash',
            started_at=timezone.now()
        )
        
        # Execute the AI review service
        GeminiReviewService.process_document(document_id, review_job.id)
        
        # Mark the document as reviewed
        doc.status = Document.Status.REVIEWED
        doc.save()
        
        return f"ReviewJob {review_job.id} completed for document {document_id}"
        
    except Document.DoesNotExist:
        return f"Document {document_id} not found."
    except Exception as e:
        # Handle unhandled pipeline crashes
        if 'doc' in locals():
            doc.status = Document.Status.FAILED
            doc.processing_error = str(e)
            doc.save()
        return f"Failed processing document {document_id}: {str(e)}"