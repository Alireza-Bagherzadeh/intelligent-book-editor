# Register your models here.
from django.contrib import admin

from .models import BlockIssue, Document, DocumentBlock, ReviewJob, BlockDifference


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "original_filename",
        "status",
        "file_size",
        "created_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("title", "original_filename", "file_sha256")
    readonly_fields = (
        "created_at",
        "updated_at",
        "file_sha256",
        "file_size",
        "mime_type",
        "processing_error",
        "source_metadata",
    )
    ordering = ("-created_at",)


@admin.register(ReviewJob)
class ReviewJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "status",
        "model_name",
        "prompt_version",
        "started_at",
        "finished_at",
        "created_at",
    )
    list_filter = ("status", "model_name", "prompt_version", "created_at")
    search_fields = ("document__title", "document__original_filename", "model_name")
    readonly_fields = (
        "created_at",
        "updated_at",
        "request_payload",
        "response_payload",
        "error_message",
    )
    ordering = ("-created_at",)


@admin.register(DocumentBlock)
class DocumentBlockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "block_type",
        "order_index",
        "style_name",
        "source_path",
        "created_at",
    )
    list_filter = ("block_type", "style_name", "is_rtl", "created_at")
    search_fields = (
        "document__title",
        "document__original_filename",
        "raw_text",
        "normalized_text",
        "source_path",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "format_metadata",
    )
    ordering = ("document", "order_index")


@admin.register(BlockIssue)
class BlockIssueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "block",
        "review_job",
        "issue_code",
        "severity",
        "start_offset",
        "end_offset",
        "created_at",
    )
    list_filter = ("severity", "issue_code", "created_at")
    search_fields = (
        "title",
        "description",
        "suggestion_text",
        "issue_code",
        "document__title",
        "document__original_filename",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "extra_data",
    )
    ordering = ("-created_at",)

@admin.register(BlockDifference)
class BlockDifferenceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "block",
        "review_job",
        "difference_type",
        "change_kind",
        "raw_phrase",
        "normalized_phrase",
        "raw_start_offset",
        "raw_end_offset",
        "created_at",
    )

    list_filter = (
        "difference_type",
        "change_kind",
        "review_job",
        "document",
    )

    search_fields = (
        "raw_phrase",
        "normalized_phrase",
        "block__raw_text",
        "block__normalized_text",
    )

    autocomplete_fields = (
        "document",
        "block",
        "review_job",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "document",
        "block__order_index",
        "raw_start_offset",
    )

    list_select_related = (
        "document",
        "block",
        "review_job",
    )

    fieldsets = (
        (
            "Relations",
            {
                "fields": (
                    "document",
                    "block",
                    "review_job",
                )
            },
        ),
        (
            "Difference",
            {
                "fields": (
                    "difference_type",
                    "change_kind",
                    "raw_phrase",
                    "normalized_phrase",
                )
            },
        ),
        (
            "Offsets",
            {
                "fields": (
                    "raw_start_offset",
                    "raw_end_offset",
                    "normalized_start_offset",
                    "normalized_end_offset",
                )
            },
        ),
        (
            "Additional Data",
            {
                "fields": (
                    "context_data",
                    "metadata",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
