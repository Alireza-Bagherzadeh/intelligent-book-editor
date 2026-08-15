from __future__ import annotations

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def get_dynamic_export_path(instance, filename):
    """
    Build the export path as:
    documents/export/doc_<id>/v<version>/<filename>

    Example:
    documents/export/doc_42/v2/my_document.docx
    """

    version = instance.exported_docx_version or 1
    version_folder = f"v{version}"

    # Use the document primary key when available;
    # fall back to a temp folder.
    doc_folder = (
        f"doc_{instance.pk}"
        if instance.pk
        else "doc_temp"
    )

    # Exported file is always DOCX.
    ext = ".docx"

    # Extract base name safely.
    if instance.original_filename:
        original_base = os.path.splitext(
            instance.original_filename
        )[0]
    else:
        original_base = "document"

    if not original_base.strip():
        original_base = "document"

    new_filename = f"{original_base}{ext}"

    return os.path.join(
        "documents",
        "export",
        doc_folder,
        version_folder,
        new_filename,
    )


class Document(TimeStampedModel):

    class SourceType(models.TextChoices):
        DOCX = "docx", "DOCX"
        RAW_TEXT = "raw_text", "Raw text"

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PARSING = "parsing", "Parsing"
        PARSED = "parsed", "Parsed"

        REVIEWING = "reviewing", "Reviewing"
        REVIEWED = "reviewed", "Reviewed"

        AI_REVIEWING = "ai_reviewing", "AI Reviewing"
        AI_REVIEWED = "ai_reviewed", "AI Reviewed"

        FAILED = "failed", "Failed"

    # ------------------------------------------------------------------
    # Core Identifiers
    # ------------------------------------------------------------------

    title = models.CharField(
        max_length=255,
        blank=True,
    )

    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.DOCX,
        db_index=True,
    )

    # ------------------------------------------------------------------
    # DOCX Source
    # ------------------------------------------------------------------

    # LOCAL:
    # Actual uploaded file is stored on filesystem.
    original_file = models.FileField(
        upload_to="documents/originals/",
        null=True,
        blank=True,
    )

    # PRODUCTION / VERCEL:
    # Actual uploaded DOCX bytes are temporarily stored
    # inside PostgreSQL.
    original_file_data = models.BinaryField(
        null=True,
        blank=True,
        editable=False,
    )

    original_filename = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    # ------------------------------------------------------------------
    # Raw Text Source
    # ------------------------------------------------------------------

    raw_text = models.TextField(
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # Metadata & Statistics
    # ------------------------------------------------------------------

    mime_type = models.CharField(
        max_length=100,
        blank=True,
    )

    file_size = models.BigIntegerField(
        default=0,
    )

    file_sha256 = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
    )

    source_metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    # ------------------------------------------------------------------
    # Lifecycle & Pipeline Status
    # ------------------------------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
        db_index=True,
    )

    processing_error = models.TextField(
        blank=True,
    )

    # ------------------------------------------------------------------
    # Export Metadata
    # ------------------------------------------------------------------

    # LOCAL:
    # Final generated DOCX is stored on filesystem.
    exported_docx = models.FileField(
        upload_to=get_dynamic_export_path,
        blank=True,
        null=True,
    )

    # PRODUCTION / VERCEL:
    # Final generated DOCX bytes are stored in PostgreSQL.
    exported_docx_data = models.BinaryField(
        null=True,
        blank=True,
        editable=False,
    )

    exported_docx_created_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    exported_docx_version = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=[
                    "status",
                    "source_type",
                ]
            ),
        ]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def clean(self):
        super().clean()

        has_file = bool(
            self.original_file
            or self.original_file_data
        )

        has_text = bool(
            self.raw_text
            and self.raw_text.strip()
        )

        # Do not allow DOCX + raw text simultaneously.
        if has_file and has_text:
            raise ValidationError(
                "Provide either original_file or raw_text, not both."
            )

        # One input source must exist.
        if not has_file and not has_text:
            raise ValidationError(
                "Either original_file or raw_text is required."
            )

        expected_type = (
            self.SourceType.DOCX
            if has_file
            else self.SourceType.RAW_TEXT
        )

        if self.source_type != expected_type:
            raise ValidationError(
                f"Source type mismatch. "
                f"Expected '{expected_type}', "
                f"but got '{self.source_type}'."
            )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, *args, **kwargs):
        """
        Automatically synchronize source_type and
        raw-text metadata.

        LOCAL:
            original_file -> DOCX

        PRODUCTION:
            original_file_data -> DOCX

        Raw text:
            raw_text -> RAW_TEXT
        """

        if (
            self.original_file
            or self.original_file_data
        ):
            self.source_type = self.SourceType.DOCX

        elif self.raw_text:
            self.source_type = self.SourceType.RAW_TEXT
            self.mime_type = "text/plain"

            # Generate title from first line when empty.
            if not self.title:
                first_line = (
                    self.raw_text.splitlines()[0]
                    if self.raw_text
                    else ""
                )

                self.title = (
                    first_line[:50].strip()
                    or "Raw Text Document"
                )

            # Generate a filename when missing.
            if not self.original_filename:
                timestamp = timezone.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                self.original_filename = (
                    f"raw_text_{timestamp}.txt"
                )

            # Calculate raw-text size.
            if not self.file_size:
                self.file_size = len(
                    self.raw_text.encode("utf-8")
                )

        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Export Storage
    # ------------------------------------------------------------------

    def save_exported_file(
        self,
        file_bytes: bytes,
    ):
        """
        Save generated DOCX.

        LOCAL:
            filesystem using exported_docx FileField

        PRODUCTION / VERCEL:
            PostgreSQL using exported_docx_data BinaryField
        """

        self.exported_docx_version += 1
        self.exported_docx_created_at = timezone.now()

        storage_backend = getattr(
            settings,
            "FILE_STORAGE_BACKEND",
            "local",
        ).lower()

        # --------------------------------------------------------------
        # Production / Vercel
        # --------------------------------------------------------------

        if storage_backend == "database":
            self.exported_docx_data = bytes(
                file_bytes
            )

            self.save(
                update_fields=[
                    "exported_docx_data",
                    "exported_docx_version",
                    "exported_docx_created_at",
                    "updated_at",
                ]
            )

            return

        # --------------------------------------------------------------
        # Local filesystem
        # --------------------------------------------------------------

        temp_filename = (
            self.original_filename
            or "export.docx"
        )

        self.exported_docx.save(
            temp_filename,
            ContentFile(file_bytes),
            save=False,
        )

        self.save()

    def __str__(self):
        return (
            self.title
            or self.original_filename
            or f"Document #{self.id}"
        )


class ReviewJob(TimeStampedModel):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="review_jobs",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    model_name = models.CharField(
        max_length=100,
        blank=True,
    )

    prompt_version = models.CharField(
        max_length=50,
        blank=True,
    )

    started_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    finished_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    # Stores the exact payload sent to the LLM service.
    request_payload = models.JSONField(
        default=dict,
        blank=True,
    )

    # Stores the raw response received from the LLM service.
    response_payload = models.JSONField(
        default=dict,
        blank=True,
    )

    # Stores execution/parsing errors.
    error_message = models.TextField(
        blank=True,
    )

    def __str__(self):
        return (
            f"ReviewJob<{self.id}> "
            f"doc={self.document_id}"
        )


class DocumentBlock(TimeStampedModel):

    class BlockType(models.TextChoices):
        HEADING = "heading", "Heading"
        PARAGRAPH = "paragraph", "Paragraph"
        TABLE_CELL = "table_cell", "Table Cell"

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="blocks",
    )

    # Self-reference for heading hierarchy.
    parent_heading = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_blocks",
    )

    block_type = models.CharField(
        max_length=20,
        choices=BlockType.choices,
        db_index=True,
    )

    # Heading level: H1, H2, ...
    heading_level = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
    )

    order_index = models.PositiveIntegerField(
        db_index=True,
    )

    raw_text = models.TextField(
        blank=True,
    )

    normalized_text = models.TextField(
        blank=True,
    )

    style_name = models.CharField(
        max_length=120,
        blank=True,
    )

    is_rtl = models.BooleanField(
        default=False,
    )

    alignment = models.CharField(
        max_length=20,
        blank=True,
    )

    paragraph_index = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    table_index = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    row_index = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    cell_index = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    cell_paragraph_index = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    source_path = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
    )

    format_metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = ["order_index"]

        indexes = [
            models.Index(
                fields=[
                    "document",
                    "order_index",
                ]
            ),
            models.Index(
                fields=[
                    "document",
                    "block_type",
                ]
            ),
            models.Index(
                fields=[
                    "document",
                    "source_path",
                ]
            ),
            models.Index(
                fields=[
                    "document",
                    "parent_heading",
                ]
            ),
            models.Index(
                fields=[
                    "document",
                    "heading_level",
                ]
            ),
        ]

    @property
    def is_heading(self) -> bool:
        """
        Quickly check whether the block
        represents a heading.
        """

        return (
            self.block_type
            == self.BlockType.HEADING
        )

    @property
    def has_children(self) -> bool:
        """
        Check whether this heading
        has child blocks.
        """

        return self.child_blocks.exists()

    def __str__(self):
        level_str = (
            f" L{self.heading_level}"
            if self.heading_level
            else ""
        )

        return (
            f"Block<{self.id}> "
            f"({self.block_type}{level_str}) "
            f"doc={self.document_id} "
            f"order={self.order_index}"
        )


class BlockIssue(models.Model):
    """
    Represents an editorial or formatting issue
    detected within a specific document block.

    Issues can include spelling, grammar,
    style, punctuation and optimization.
    """

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    class IssueCode(models.TextChoices):
        SPELLING = (
            "spelling",
            "Spelling Error",
        )

        GRAMMAR = (
            "grammar",
            "Grammar and Syntax",
        )

        STYLE = (
            "style",
            "Writing Style and Tone",
        )

        PUNCTUATION = (
            "punctuation",
            "Punctuation and Spacing",
        )

        OPTIMIZATION = (
            "optimization",
            "Readability and Optimization",
        )

    document = models.ForeignKey(
        "Document",
        on_delete=models.CASCADE,
        related_name="issues",
    )

    block = models.ForeignKey(
        "DocumentBlock",
        on_delete=models.CASCADE,
        related_name="issues",
    )

    review_job = models.ForeignKey(
        "ReviewJob",
        on_delete=models.CASCADE,
        related_name="issues",
    )

    issue_code = models.CharField(
        max_length=100,
        choices=IssueCode.choices,
        default=IssueCode.OPTIMIZATION,
        db_index=True,
    )

    title = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.WARNING,
        db_index=True,
    )

    # Offsets are based on normalized_text.
    start_offset = models.PositiveIntegerField()

    end_offset = models.PositiveIntegerField()

    suggestion_text = models.TextField(
        blank=True,
    )

    # Structured metadata from analysis engine.
    extra_data = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "document",
                    "severity",
                ]
            ),
            models.Index(
                fields=[
                    "block",
                    "start_offset",
                ]
            ),
            models.Index(
                fields=[
                    "review_job",
                ]
            ),
        ]

    def __str__(self):
        return (
            f"Issue<{self.id}> "
            f"block={self.block_id} "
            f"[{self.start_offset}, "
            f"{self.end_offset})"
        )


class BlockDifference(TimeStampedModel):
    """
    ذخیره تفاوت‌های ساختاری و متنی بین
    raw_text و normalized_text
    """

    class DifferenceType(models.TextChoices):
        WORD_CHANGE = (
            "word_change",
            "Word Change",
        )

        WHITESPACE_CHANGE = (
            "whitespace_change",
            "Whitespace Change",
        )

    class ChangeKind(models.TextChoices):
        REPLACEMENT = (
            "replacement",
            "Replacement",
        )

        INSERTION = (
            "insertion",
            "Insertion",
        )

        DELETION = (
            "deletion",
            "Deletion",
        )

        WORD_AND_WHITESPACE_CHANGE = (
            "word_and_whitespace_change",
            "Word and Whitespace Change",
        )

        SPACE_TO_HALF_SPACE = (
            "space_to_half_space",
            "Space to Half-space",
        )

        HALF_SPACE_TO_SPACE = (
            "half_space_to_space",
            "Half-space to Space",
        )

        EXTRA_WHITESPACE_REMOVED = (
            "extra_whitespace_removed",
            "Extra Whitespace Removed",
        )

        WHITESPACE_INSERTED = (
            "whitespace_inserted",
            "Whitespace Inserted",
        )

        WHITESPACE_REPLACED = (
            "whitespace_replaced",
            "Whitespace Replaced",
        )

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="differences",
    )

    block = models.ForeignKey(
        DocumentBlock,
        on_delete=models.CASCADE,
        related_name="differences",
    )

    review_job = models.ForeignKey(
        ReviewJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="differences",
    )

    difference_type = models.CharField(
        max_length=30,
        choices=DifferenceType.choices,
        db_index=True,
    )

    change_kind = models.CharField(
        max_length=50,
        choices=ChangeKind.choices,
        db_index=True,
    )

    raw_phrase = models.TextField(
        blank=True,
    )

    normalized_phrase = models.TextField(
        blank=True,
    )

    raw_start_offset = models.PositiveIntegerField()

    raw_end_offset = models.PositiveIntegerField()

    normalized_start_offset = models.PositiveIntegerField()

    normalized_end_offset = models.PositiveIntegerField()

    context_data = models.JSONField(
        default=dict,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = [
            "raw_start_offset",
            "id",
        ]

        indexes = [
            models.Index(
                fields=[
                    "document",
                    "block",
                    "raw_start_offset",
                ]
            ),
            models.Index(
                fields=[
                    "block",
                    "difference_type",
                ]
            ),
            models.Index(
                fields=[
                    "block",
                    "change_kind",
                ]
            ),
            models.Index(
                fields=[
                    "review_job",
                ]
            ),
        ]

    def __str__(self):
        return (
            f"Difference<{self.id}> "
            f"block={self.block_id} "
            f"[{self.raw_start_offset}, "
            f"{self.raw_end_offset})"
        )