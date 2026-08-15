from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
import os
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
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

    # Use the document primary key when available; fall back to a temp folder.
    doc_folder = f"doc_{instance.pk}" if instance.pk else "doc_temp"

    # CRITICAL FIX: The exported file is ALWAYS a DOCX document,
    # regardless of whether the original upload was raw_text (.txt) or docx.
    ext = ".docx"

    # Extract the base name of the original file safely, removing any old extension
    if instance.original_filename:
        original_base = os.path.splitext(instance.original_filename)[0]
    else:
        original_base = "document"

    # Ensure we don't end up with an empty base name
    if not original_base.strip():
        original_base = "document"

    new_filename = f"{original_base}{ext}"

    return os.path.join(
        "documents", "export", doc_folder, version_folder, new_filename
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

        

    # Core Identifiers
    title = models.CharField(max_length=255, blank=True)
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.DOCX,
        db_index=True,
    )

    # DOCX Source Fields (Optional to support raw text)
    original_file = models.FileField(
        upload_to="documents/originals/",
        null=True,
        blank=True,
    )
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    # Raw Text Source Fields
    raw_text = models.TextField(
        null=True,
        blank=True,
    )

    # Metadata & Statistics
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.BigIntegerField(default=0)
    file_sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    source_metadata = models.JSONField(default=dict, blank=True)

    # Lifecycle & Pipeline Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
        db_index=True,
    )
    processing_error = models.TextField(blank=True)

    # Export Metadata
    exported_docx = models.FileField(
        upload_to=get_dynamic_export_path,
        blank=True,
        null=True,
    )
    exported_docx_created_at = models.DateTimeField(blank=True, null=True)
    exported_docx_version = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "source_type"]),
        ]

    def clean(self):
        super().clean()
        
        has_file = bool(self.original_file)
        has_text = bool(self.raw_text and self.raw_text.strip())

        # Enforce mutual exclusivity at validation level
        if has_file and has_text:
            raise ValidationError(
                "Provide either original_file or raw_text, not both."
            )
        if not has_file and not has_text:
            raise ValidationError(
                "Either original_file or raw_text is required."
            )

        # Sync source_type based on the input
        expected_type = self.SourceType.DOCX if has_file else self.SourceType.RAW_TEXT
        if self.source_type != expected_type:
            raise ValidationError(
                f"Source type mismatch. Expected '{expected_type}', but got '{self.source_type}'."
            )

    def save(self, *args, **kwargs):
        # Auto-detect and populate fields before saving
        if self.original_file:
            self.source_type = self.SourceType.DOCX
        elif self.raw_text:
            self.source_type = self.SourceType.RAW_TEXT
            self.mime_type = "text/plain"

            # Auto-generate a title from the first line of raw text if empty
            if not self.title:
                first_line = self.raw_text.splitlines()[0] if self.raw_text else ""
                self.title = first_line[:50].strip() or "Raw Text Document"

            # Auto-generate a filename if missing
            if not self.original_filename:
                timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                self.original_filename = f"raw_text_{timestamp}.txt"

            # Calculate size for telemetry/reporting
            if not self.file_size:
                self.file_size = len(self.raw_text.encode("utf-8"))

        super().save(*args, **kwargs)

    def save_exported_file(self, file_bytes: bytes):
        """
        Increment the export version and store the generated DOCX file.
        """
        self.exported_docx_version += 1
        self.exported_docx_created_at = timezone.now()

        temp_filename = self.original_filename or "export.docx"

        # Save the file without triggering save() recursively immediately
        self.exported_docx.save(
            temp_filename,
            ContentFile(file_bytes),
            save=False,
        )
        self.save()

    exported_docx = models.FileField(
        upload_to=get_dynamic_export_path,
        blank=True,
        null=True,
    )
    exported_docx_created_at = models.DateTimeField(blank=True, null=True)
    exported_docx_version = models.PositiveIntegerField(default=0)

    def save_exported_file(self, file_bytes: bytes):
        """
        Increment the export version and store the generated DOCX file.
        """
        self.exported_docx_version += 1
        self.exported_docx_created_at = timezone.now()

        temp_filename = self.original_filename or "export.docx"

        self.exported_docx.save(
            temp_filename,
            ContentFile(file_bytes),
            save=False,
        )
        self.save()

    def __str__(self):
        return self.title or self.original_filename or f"Document #{self.id}"




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

    model_name = models.CharField(max_length=100, blank=True)
    prompt_version = models.CharField(max_length=50, blank=True)

    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    # Stores the exact payload sent to the LLM service.
    request_payload = models.JSONField(default=dict, blank=True)

    # Stores the raw response received from the LLM service.
    response_payload = models.JSONField(default=dict, blank=True)

    # Stores the execution or parsing error when the review fails.
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"ReviewJob<{self.id}> doc={self.document_id}"


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

    # Self-referencing Foreign Key to link child blocks to their parent heading
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
    
    # Stores the heading level (e.g., 1 for H1, 2 for H2, etc.). Null for regular paragraphs/tables.
    heading_level = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        db_index=True
    )
    
    order_index = models.PositiveIntegerField(db_index=True)

    raw_text = models.TextField(blank=True)
    normalized_text = models.TextField(blank=True)

    style_name = models.CharField(max_length=120, blank=True)
    is_rtl = models.BooleanField(default=False)
    alignment = models.CharField(max_length=20, blank=True)

    paragraph_index = models.PositiveIntegerField(blank=True, null=True)
    table_index = models.PositiveIntegerField(blank=True, null=True)
    row_index = models.PositiveIntegerField(blank=True, null=True)
    cell_index = models.PositiveIntegerField(blank=True, null=True)
    cell_paragraph_index = models.PositiveIntegerField(blank=True, null=True)

    source_path = models.CharField(max_length=255, blank=True, db_index=True)
    format_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["order_index"]
        indexes = [
            models.Index(fields=["document", "order_index"]),
            models.Index(fields=["document", "block_type"]),
            models.Index(fields=["document", "source_path"]),
            models.Index(fields=["document", "parent_heading"]),
            models.Index(fields=["document", "heading_level"]),
        ]

    @property
    def is_heading(self) -> bool:
        """Utility property to quickly check if the block is a heading."""
        return self.block_type == self.BlockType.HEADING

    @property
    def has_children(self) -> bool:
        """Checks if there are any child blocks pointing to this heading."""
        return self.child_blocks.exists()

    def __str__(self):
        level_str = f" L{self.heading_level}" if self.heading_level else ""
        return f"Block<{self.id}> ({self.block_type}{level_str}) doc={self.document_id} order={self.order_index}"


class BlockIssue(models.Model):
    """
    Represents an editorial or formatting issue detected within a specific document block.
    Issues can range from spelling and grammar errors to style and punctuation adjustments.
    """
    
    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    class IssueCode(models.TextChoices):
        SPELLING = "spelling", "Spelling Error"
        GRAMMAR = "grammar", "Grammar and Syntax"
        STYLE = "style", "Writing Style and Tone"
        PUNCTUATION = "punctuation", "Punctuation and Spacing"
        OPTIMIZATION = "optimization", "Readability and Optimization"

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

    # Identifies the category/code of the issue (e.g., spelling, punctuation)
    issue_code = models.CharField(
        max_length=100, 
        choices=IssueCode.choices,
        default=IssueCode.OPTIMIZATION,
        db_index=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.WARNING,
        db_index=True,
    )

    # Offsets are calculated based on the normalized_text of the target DocumentBlock
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()

    suggestion_text = models.TextField(blank=True)

    # Stores structured metadata or extra contextual values from the analysis engine
    extra_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["document", "severity"]),
            models.Index(fields=["block", "start_offset"]),
            models.Index(fields=["review_job"]),
        ]

    def __str__(self):
        return f"Issue<{self.id}> block={self.block_id} [{self.start_offset}, {self.end_offset})"


class BlockDifference(TimeStampedModel):
    """
    ذخیره تفاوت‌های ساختاری و متنی بین raw_text و normalized_text
    """
    class DifferenceType(models.TextChoices):
        WORD_CHANGE = "word_change", "Word Change"
        WHITESPACE_CHANGE = "whitespace_change", "Whitespace Change"

    class ChangeKind(models.TextChoices):
        REPLACEMENT = "replacement", "Replacement"
        INSERTION = "insertion", "Insertion"
        DELETION = "deletion", "Deletion"
        WORD_AND_WHITESPACE_CHANGE = (
            "word_and_whitespace_change",
            "Word and Whitespace Change",
        )
        SPACE_TO_HALF_SPACE = "space_to_half_space", "Space to Half-space"
        HALF_SPACE_TO_SPACE = "half_space_to_space", "Half-space to Space"
        EXTRA_WHITESPACE_REMOVED = (
            "extra_whitespace_removed",
            "Extra Whitespace Removed",
        )
        WHITESPACE_INSERTED = "whitespace_inserted", "Whitespace Inserted"
        WHITESPACE_REPLACED = "whitespace_replaced", "Whitespace Replaced"

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="differences"
    )
    block = models.ForeignKey(
        DocumentBlock, on_delete=models.CASCADE, related_name="differences"
    )
    review_job = models.ForeignKey(
        ReviewJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="differences",
    )

    difference_type = models.CharField(
        max_length=30, choices=DifferenceType.choices, db_index=True
    )
    change_kind = models.CharField(
        max_length=50, choices=ChangeKind.choices, db_index=True
    )

    raw_phrase = models.TextField(blank=True)
    normalized_phrase = models.TextField(blank=True)

    raw_start_offset = models.PositiveIntegerField()
    raw_end_offset = models.PositiveIntegerField()

    normalized_start_offset = models.PositiveIntegerField()
    normalized_end_offset = models.PositiveIntegerField()

    context_data = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["raw_start_offset", "id"]
        indexes = [
            models.Index(fields=["document", "block", "raw_start_offset"]),
            models.Index(fields=["block", "difference_type"]),
            models.Index(fields=["block", "change_kind"]),
            models.Index(fields=["review_job"]),
        ]

    def __str__(self):
        return f"Difference<{self.id}> block={self.block_id} [{self.raw_start_offset}, {self.raw_end_offset})"
