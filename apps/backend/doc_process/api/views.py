from doc_process.task_queue import enqueue_task
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DocumentUploadSerializer, BlockDifferenceSerializer
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import get_object_or_404

from ..models import Document, ReviewJob, DocumentBlock, BlockDifference
from doc_process.services.document_export_service import DocumentExportService
from django.http import HttpResponse
from django.http import FileResponse
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
import os

from django.conf import settings
from django.urls import reverse


class DocumentUploadView(APIView):
    # Keep previous multipart support and add JSON support for raw_text uploads
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def post(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        enqueue_task(
            "doc_process.tasks.run_document_parsing_task",
            document.id,
            task_name=f"ParseDoc-{document.id}",
        )

        response_serializer = DocumentUploadSerializer(document)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )



@csrf_exempt
@require_POST
def trigger_document_review(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    # 1. Validation: Only PARSED documents can be reviewed
    if document.status != Document.Status.PARSED:
        return JsonResponse({
            "success": False,
            "error": f"Document status must be 'PARSED'. Current: {document.get_status_display()}"
        }, status=400)

    # 2. Validation: Ensure the document actually has blocks to process
    blocks_exist = DocumentBlock.objects.filter(document=document).exists()
    if not blocks_exist:
        return JsonResponse({
            "success": False,
            "error": "This document has no content blocks. Please parse the document again."
        }, status=422)  # 422 Unprocessable Entity

    # 3. Check for existing active jobs
    active_jobs = ReviewJob.objects.filter(
        document=document,
        status__in=[ReviewJob.Status.PENDING, ReviewJob.Status.RUNNING]
    ).exists()

    if active_jobs:
        return JsonResponse({
            "success": False,
            "error": "A review job is already in progress for this document."
        }, status=409)

    # 4. Create job
    review_job = ReviewJob.objects.create(
        document=document,
        status=ReviewJob.Status.PENDING,
    )

    try:
        async_task("doc_process.tasks.run_document_review_job_task", review_job.id)

        return JsonResponse({
            "success": True,
            "message": "Review process queued successfully.",
            "review_job_id": review_job.id,
            "status": review_job.status
        }, status=202)

    except Exception as e:
        review_job.delete()
        return JsonResponse({
            "success": False,
            "error": f"Could not queue the task: {str(e)}"
        }, status=500)


# @csrf_exempt
# @require_POST
# def trigger_document_review(request, document_id):
#     """
#     Start the asynchronous document review process.
#     This endpoint returns immediately and does not wait for the task to finish.
#     """
#     document = get_object_or_404(Document, id=document_id)

#     # Ensure the document has been fully parsed before starting AI review
#     if document.status != Document.Status.PARSED:
#         return JsonResponse({
#             "success": False,
#             "error": f"Document is not in a valid state for review. Current status: {document.get_status_display()}"
#         }, status=400)

#     # Create a new review job with initial PENDING status
#     review_job = ReviewJob.objects.create(
#         document=document,
#         status=ReviewJob.Status.PENDING,
#     )

#     # Dispatch the task asynchronously using a task runner such as Django Q or Celery
#     # Example with Django Q:
#     from django_q.tasks import async_task
#     async_task("doc_process.tasks.run_document_review_job_task", review_job.id)

#     # Important:
#     # If you execute the review task synchronously (without Celery/Django Q),
#     # polling will not be useful because this request will block until the whole review finishes.

#     return JsonResponse({
#         "success": True,
#         "message": "Review process started successfully.",
#         "review_job_id": review_job.id,
#         "status": review_job.status
#     }, status=202)  # 202 Accepted is appropriate for async operations


@require_GET
def get_review_status(request, review_job_id):
    """
    Return the current review job status and estimated progress.
    """
    review_job = get_object_or_404(ReviewJob, id=review_job_id)
    document = review_job.document

    # Count all relevant blocks that should be reviewed
    total_blocks = DocumentBlock.objects.filter(
        document=document,
        block_type__in=[DocumentBlock.BlockType.PARAGRAPH, DocumentBlock.BlockType.HEADING]
    ).count()

    # Count distinct blocks that already produced at least one issue for this review job
    # This is only an approximate progress indicator
    processed_blocks_count = DocumentBlock.objects.filter(
        document=document,
        blockissue__review_job=review_job
    ).distinct().count()

    # Calculate estimated progress percentage
    progress_percentage = 0
    if total_blocks > 0:
        progress_percentage = int((processed_blocks_count / total_blocks) * 100)

        # Force progress to 100% if the job has already completed successfully
        if review_job.status == ReviewJob.Status.SUCCEEDED:
            progress_percentage = 100

    return JsonResponse({
        "review_job_id": review_job.id,
        "status": review_job.status,  # e.g. PENDING, RUNNING, SUCCEEDED, FAILED
        "status_display": review_job.get_status_display(),
        "progress_percentage": progress_percentage,
        "error_message": review_job.error_message if review_job.status == ReviewJob.Status.FAILED else None,
        "issues_found": review_job.blockissue_set.count() if review_job.status == ReviewJob.Status.SUCCEEDED else 0
    })



from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from doc_process.models import (
    BlockIssue,
    Document,
    DocumentBlock,
    ReviewJob,
)
from .serializers import (
    DocumentBlockWithIssuesSerializer,
)

class DocumentBlocksWithIssuesAPIView(ListAPIView):
    """
    Returns every block belonging to a document, ordered by order_index.

    Blocks without issues are also included with:

        "issues_count": 0,
        "issues": []

    Optional query parameter:

        ?review_job_id=<id>

    When review_job_id is provided, only issues generated by that
    review job are included.
    """

    serializer_class = DocumentBlockWithIssuesSerializer
    pagination_class = None

    def get_document(self) -> Document:
        if not hasattr(self, "_document"):
            self._document = get_object_or_404(
                Document,
                pk=self.kwargs["document_id"],
            )
            self.validate_document_status(self._document)

        return self._document

    def validate_document_status(self, document: Document) -> None:
        """
        For now, blocks can be returned only if the document has been
        parsed at least once.

        Allowed statuses for now:
            - parsed
            - reviewing
            - reviewed
        """
        allowed_statuses = {
            Document.Status.PARSED,
            Document.Status.REVIEWING,
            Document.Status.REVIEWED,
        }

        if document.status not in allowed_statuses:
            raise ValidationError(
                {
                    "document": (
                        "Blocks are not available until the document "
                        "has been parsed."
                    ),
                    "status": document.status,
                }
            )

    def get_review_job(self) -> ReviewJob | None:
        review_job_id = self.request.query_params.get("review_job_id")

        if not review_job_id:
            return None

        try:
            review_job_id = int(review_job_id)
        except (TypeError, ValueError):
            raise ValidationError(
                {
                    "review_job_id": (
                        "review_job_id must be a valid integer."
                    )
                }
            )

        return get_object_or_404(
            ReviewJob,
            pk=review_job_id,
            document=self.get_document(),
        )

    def get_queryset(self):
        document = self.get_document()
        review_job = self.get_review_job()

        issues_queryset = (
            BlockIssue.objects
            .filter(document=document)
            .select_related("review_job", "block")
            .order_by("start_offset", "id")
        )

        if review_job is not None:
            issues_queryset = issues_queryset.filter(
                review_job=review_job,
            )

        return (
            DocumentBlock.objects
            .filter(document=document)
            .select_related(
                "document",
                "parent_heading",
            )
            .prefetch_related(
                Prefetch(
                    "issues",
                    queryset=issues_queryset,
                    to_attr="prefetched_issues",
                )
            )
            .order_by("order_index", "id")
        )

# class DocumentBlocksWithIssuesAPIView(ListAPIView):
#     """
#     Returns every block belonging to a document, ordered by order_index.

#     Blocks without issues are also included with:

#         "issues_count": 0,
#         "issues": []

#     Optional query parameter:

#         ?review_job_id=<id>

#     When review_job_id is provided, only issues generated by that
#     review job are included.
#     """

#     serializer_class = DocumentBlockWithIssuesSerializer

#     # This endpoint is expected to return all document blocks.
#     pagination_class = None

#     def get_document(self) -> Document:
#         if not hasattr(self, "_document"):
#             self._document = get_object_or_404(
#                 Document,
#                 pk=self.kwargs["document_id"],
#             )

#         return self._document

#     def get_review_job(self) -> ReviewJob | None:
#         review_job_id = self.request.query_params.get("review_job_id")

#         if not review_job_id:
#             return None

#         try:
#             review_job_id = int(review_job_id)
#         except (TypeError, ValueError):
#             raise ValidationError(
#                 {
#                     "review_job_id": (
#                         "review_job_id must be a valid integer."
#                     )
#                 }
#             )

#         return get_object_or_404(
#             ReviewJob,
#             pk=review_job_id,
#             document=self.get_document(),
#         )

#     def get_queryset(self):
#         document = self.get_document()
#         review_job = self.get_review_job()

#         issues_queryset = (
#             BlockIssue.objects
#             .filter(document=document)
#             .select_related("review_job", "block")
#             .order_by("start_offset", "id")
#         )

#         if review_job is not None:
#             issues_queryset = issues_queryset.filter(
#                 review_job=review_job,
#             )

#         return (
#             DocumentBlock.objects
#             .filter(document=document)
#             .select_related(
#                 "document",
#                 "parent_heading",
#             )
#             .prefetch_related(
#                 Prefetch(
#                     "issues",
#                     queryset=issues_queryset,
#                     to_attr="prefetched_issues",
#                 )
#             )
#             .order_by("order_index", "id")
#         )







class ExportDocumentDocxAPIView(APIView):
    """
    API endpoint to generate a DOCX export, save it in storage,
    and return the download URL.
    """

    def get(self, request, document_id, *args, **kwargs):
        document = get_object_or_404(Document, id=document_id)

        try:
            exporter = DocumentExportService(document)
            file_bytes = exporter.export_normalized_docx()

            document.save_exported_file(file_bytes)

            download_url = request.build_absolute_uri(
               reverse(
                "download_exported_docx",
                        kwargs={
                            "document_id": document.id,
                        },
                    )
                    )

            return Response(
                {
                    "message": "Export successful",
                    "document_id": document.id,
                    "version": document.exported_docx_version,
                    "download_url": download_url,
                    "created_at": document.exported_docx_created_at,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "error": "Failed to generate export file.",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class DownloadExportedDocxAPIView(APIView):

    def get(self, request, document_id, *args, **kwargs):
        document = get_object_or_404(
            Document,
            id=document_id,
        )

        filename = (
            os.path.splitext(
                document.original_filename or "document"
            )[0]
            + ".docx"
        )

        # Vercel / PostgreSQL
        if document.exported_docx_data:
            response = HttpResponse(
                bytes(document.exported_docx_data),
                content_type=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
            )

            response["Content-Disposition"] = (
                f'attachment; filename="{filename}"'
            )

            return response

        # Local / FileField
        if document.exported_docx:
            return FileResponse(
                document.exported_docx.open("rb"),
                as_attachment=True,
                filename=filename,
                content_type=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
            )

        return Response(
            {
                "error": "No exported DOCX is available."
            },
            status=status.HTTP_404_NOT_FOUND,
        )
class DocumentDifferencesAPIView(ListAPIView):
    serializer_class = BlockDifferenceSerializer
    # permission_classes = [AllowAny]

    def get_queryset(self):
        document_id = self.kwargs["document_id"]

        # دسترسی به تفاوت‌ها از طریق document
        queryset = BlockDifference.objects.filter(document_id=document_id)

        # فیلتر برای اینکه فقط آخرین job را نشان دهیم (اگر کاربر job خاصی را نفرستاد)
        job_id = self.request.query_params.get("review_job_id")
        if job_id:
            queryset = queryset.filter(review_job_id=job_id)
        else:
            # نمایش آخرین job موفق برای این سند
            last_job = ReviewJob.objects.filter(document_id=document_id).last()
            if last_job:
                queryset = queryset.filter(review_job_id=last_job.id)

        return queryset.order_by("block__order_index", "raw_start_offset")