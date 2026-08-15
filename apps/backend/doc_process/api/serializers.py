from rest_framework import serializers
from ..models import Document, BlockDifference
from rest_framework import serializers
from doc_process.models import BlockIssue, DocumentBlock


class DocumentUploadSerializer(serializers.ModelSerializer):
    # Backward-compatible upload field expected by the frontend
    file = serializers.FileField(
        source="original_file",
        write_only=True,
        required=False,
        allow_null=True,
    )

    # Backward-compatible response field expected by the frontend
    file_name = serializers.CharField(
        source="original_filename",
        read_only=True,
    )

    # New raw text input field
    raw_text = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "file",
            "file_name",
            "raw_text",
            "source_type",
            "mime_type",
            "file_size",
            "file_sha256",
            "status",
            "processing_error",
            "source_metadata",
            "exported_docx",
            "exported_docx_created_at",
            "exported_docx_version",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "file_name",
            "source_type",
            "mime_type",
            "file_size",
            "file_sha256",
            "status",
            "processing_error",
            "exported_docx",
            "exported_docx_created_at",
            "exported_docx_version",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data):
        from django.conf import settings

        uploaded_file = validated_data.pop(
            "original_file",
            None,
        )

        # Raw text - no special file handling required
        if uploaded_file is None:
            return Document.objects.create(**validated_data)

        validated_data["original_filename"] = (
            uploaded_file.name
        )
        validated_data["mime_type"] = (
            getattr(uploaded_file, "content_type", "")
            or
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        validated_data["file_size"] = uploaded_file.size
        validated_data["source_type"] = Document.SourceType.DOCX

        # Production / Vercel
        if settings.FILE_STORAGE_BACKEND == "database":
            uploaded_file.seek(0)
            file_bytes = uploaded_file.read()

            return Document.objects.create(
                original_file=None,
                original_file_data=file_bytes,
                **validated_data,
            )

        # Local - EXACT old behaviour
        return Document.objects.create(
            original_file=uploaded_file,
            **validated_data,
        )


class DocumentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "original_filename",
            "source_type",
            "mime_type",
            "file_size",
            "file_sha256",
            "status",
            "processing_error",
            "source_metadata",
            "exported_docx",
            "exported_docx_created_at",
            "exported_docx_version",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

# class DocumentUploadSerializer(serializers.ModelSerializer):
#     # The API accepts the file via 'file' parameter (write-only)
#     file = serializers.FileField(write_only=True)
#     file_name = serializers.CharField(source="original_filename", read_only=True)

#     class Meta:
#         model = Document
#         # We expose 'file' for uploads, but read status/metadata from the instance
#         fields = ("id", "file", "status", "file_name", "created_at")
#         read_only_fields = ("id", "status", "file_name", "created_at")

#     def validate_file(self, value):
#         # Validate that the uploaded file has a .docx extension
#         if not value.name.lower().endswith(".docx"):
#             raise serializers.ValidationError("Only .docx files are allowed.")
#         return value

#     def create(self, validated_data):
#         uploaded_file = validated_data.pop("file")

#         # Map 'file' from request to 'original_file' in the Document model
#         return Document.objects.create(
#             original_file=uploaded_file,
#             original_filename=uploaded_file.name,
#             mime_type=getattr(uploaded_file, "content_type", "") or "",
#             file_size=uploaded_file.size,
#             status=Document.Status.UPLOADED,
#         )





class BlockIssueSerializer(serializers.ModelSerializer):
    issue_code_display = serializers.CharField(
        source="get_issue_code_display",
        read_only=True,
    )
    severity_display = serializers.CharField(
        source="get_severity_display",
        read_only=True,
    )
    original_text = serializers.SerializerMethodField()

    class Meta:
        model = BlockIssue
        fields = [
            "id",
            "review_job",
            "issue_code",
            "issue_code_display",
            "title",
            "description",
            "severity",
            "severity_display",
            "start_offset",
            "end_offset",
            "original_text",
            "suggestion_text",
            "extra_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_original_text(self, issue: BlockIssue) -> str:
        """
        Extract the problematic segment from the block's normalized text.

        BlockIssue offsets are defined relative to normalized_text.
        """
        block = issue.block
        text = block.normalized_text or ""

        start = issue.start_offset
        end = issue.end_offset

        if start < 0 or end < start or start >= len(text):
            return ""

        return text[start:min(end, len(text))]


class DocumentBlockWithIssuesSerializer(serializers.ModelSerializer):
    issues = serializers.SerializerMethodField()
    issues_count = serializers.SerializerMethodField()

    is_heading = serializers.BooleanField(read_only=True)
    has_children = serializers.BooleanField(read_only=True)

    class Meta:
        model = DocumentBlock
        fields = [
            "id",
            "document",
            "parent_heading",
            "block_type",
            "heading_level",
            "order_index",
            "raw_text",
            "normalized_text",
            "style_name",
            "is_rtl",
            "alignment",
            "paragraph_index",
            "table_index",
            "row_index",
            "cell_index",
            "cell_paragraph_index",
            "source_path",
            "format_metadata",
            "is_heading",
            "has_children",
            "issues_count",
            "issues",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_issues(self, block: DocumentBlock) -> list[dict]:
        """
        Uses the issues prefetched by the view.

        Falls back to block.issues.all() if the serializer is used
        somewhere without the optimized prefetch.
        """
        issues = getattr(block, "prefetched_issues", None)

        if issues is None:
            issues = block.issues.select_related("review_job").all()

        return BlockIssueSerializer(
            issues,
            many=True,
            context=self.context,
        ).data

    def get_issues_count(self, block: DocumentBlock) -> int:
        issues = getattr(block, "prefetched_issues", None)

        if issues is not None:
            return len(issues)

        return block.issues.count()


class DocumentBlockWithIssuesSerializer(serializers.ModelSerializer):
    issues = serializers.SerializerMethodField()
    issues_count = serializers.SerializerMethodField()

    is_heading = serializers.BooleanField(read_only=True)
    has_children = serializers.BooleanField(read_only=True)

    class Meta:
        model = DocumentBlock
        fields = [
            "id",
            "document",
            "parent_heading",
            "block_type",
            "heading_level",
            "order_index",
            "raw_text",
            "normalized_text",
            "style_name",
            "is_rtl",
            "alignment",
            "paragraph_index",
            "table_index",
            "row_index",
            "cell_index",
            "cell_paragraph_index",
            "source_path",
            "format_metadata",
            "is_heading",
            "has_children",
            "issues_count",
            "issues",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_issues(self, block: DocumentBlock) -> list[dict]:
        """
        Uses the issues prefetched by the view.

        Falls back to block.issues.all() if the serializer is used
        somewhere without the optimized prefetch.
        """
        issues = getattr(block, "prefetched_issues", None)

        if issues is None:
            issues = block.issues.select_related("review_job").all()

        return BlockIssueSerializer(
            issues,
            many=True,
            context=self.context,
        ).data

    def get_issues_count(self, block: DocumentBlock) -> int:
        issues = getattr(block, "prefetched_issues", None)

        if issues is not None:
            return len(issues)

        return block.issues.count()


class BlockDifferenceSerializer(serializers.ModelSerializer):
    block_id = serializers.IntegerField(source="block.id", read_only=True)
    document_id = serializers.IntegerField(source="document.id", read_only=True)

    class Meta:
        model = BlockDifference
        fields = [
            "id",
            "document_id",
            "block_id",
            "review_job",
            "difference_type",
            "change_kind",
            "raw_phrase",
            "normalized_phrase",
            "raw_start_offset",
            "raw_end_offset",
            "normalized_start_offset",
            "normalized_end_offset",
            "context_data",
            "metadata",
            "created_at",
        ]