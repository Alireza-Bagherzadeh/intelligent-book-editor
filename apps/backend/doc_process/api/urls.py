from django.urls import path

from .views import DocumentUploadView, trigger_document_review, get_review_status , DocumentBlocksWithIssuesAPIView, ExportDocumentDocxAPIView, DocumentDifferencesAPIView

urlpatterns = [
    path("documents/upload/", DocumentUploadView.as_view(), name="document-upload"),
    path(
        "documents/<int:document_id>/review/",
        trigger_document_review,
        name="trigger-document-review",
    ),
    path(
        "review-jobs/<int:review_job_id>/status/",
        get_review_status,
        name="review-job-status",
    ),
    path(
        "documents/<int:document_id>/blocks-with-issues/",
        DocumentBlocksWithIssuesAPIView.as_view(),
        name="document-blocks-with-issues",
    ),
    
    path(
        "documents/<int:document_id>/export-docx/",
        ExportDocumentDocxAPIView.as_view(),
        name="export_document_docx",
    ),
    path(
    "documents/<int:document_id>/differences/",
    DocumentDifferencesAPIView.as_view(),
    name="document-differences",
    )
]