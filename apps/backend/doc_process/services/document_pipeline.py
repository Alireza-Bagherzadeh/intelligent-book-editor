# doc_process/services/pipeline_service.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from django.db import transaction

from doc_process.models import Document, DocumentBlock
from doc_process.services.docx_parser import DocxParseService
from doc_process.services.raw_text_parser import RawTextParseService
from doc_process.services.file_materializer import (
    materialize_original_document,
)
logger = logging.getLogger(__name__)


class DocumentPipelineService:
    def __init__(self) -> None:
        # Instantiating both parsers
        self.docx_parser = DocxParseService(include_empty_blocks=False)
        self.raw_text_parser = RawTextParseService(include_empty_blocks=False)

    def parse_document(self, document: Document) -> int:
        self._mark_parsing(document)

        try:
            # 1. Select the correct parser adapter based on source_type
            block_payloads = self._extract_blocks(document)

            if not block_payloads:
                raise ValueError(
                    "Parser returned zero blocks. The input source may be empty."
                )

            # 2. Persist to DB using unified logic
            created_count = self._persist_blocks(
                document=document,
                block_payloads=block_payloads,
            )

            document.status = Document.Status.PARSED
            document.processing_error = ""
            from django.conf import settings

            if settings.FILE_STORAGE_BACKEND == "database":
                document.original_file_data = None

                document.save(
                    update_fields=[
                        "status",
                        "processing_error",
                        "original_file_data",
                        "updated_at",
                    ]
                )
            else:
                document.save(
                    update_fields=[
                        "status",
                        "processing_error",
                        "updated_at",
                    ]
                )

            logger.info(
                "Document %s parsed successfully. Total blocks: %s",
                document.id,
                created_count,
            )
            return created_count

        except Exception as exc:
            logger.exception("Document parsing failed for document %s.", document.id)
            self._mark_failed(document, str(exc))
            raise

    def _extract_blocks(self, document: Document) -> list[dict[str, Any]]:
        # Router logic based on source type
        if document.source_type == Document.SourceType.DOCX:
            with materialize_original_document(document) as file_path:
                return self.docx_parser.extract_blocks(file_path)
        if document.source_type == Document.SourceType.RAW_TEXT:
            if not document.raw_text or not document.raw_text.strip():
                raise ValueError("Raw text document source is empty.")
            
            # New raw text parser
            return self.raw_text_parser.extract_blocks(
                text=document.raw_text,
                source_identifier=f"raw_text://document/{document.id}",
            )

        raise ValueError(f"Unsupported source_type: {document.source_type}")

    def _persist_blocks(
        self,
        document: Document,
        block_payloads: list[dict[str, Any]],
    ) -> int:
        with transaction.atomic():
            # Delete old blocks first
            document.blocks.all().delete()

            # Create standard DocumentBlock objects
            db_blocks = [
                DocumentBlock(
                    document=document,
                    block_type=item["block_type"],
                    heading_level=item.get("heading_level"),
                    order_index=item["order_index"],
                    parent_heading_id=None,  # Will update in secondary pass below
                    raw_text=item["raw_text"],
                    normalized_text=item["normalized_text"],
                    style_name=item.get("style_name", ""),
                    is_rtl=item.get("is_rtl", False),
                    alignment=item.get("alignment", "unknown"),
                    paragraph_index=item.get("paragraph_index"),
                    table_index=item.get("table_index"),
                    row_index=item.get("row_index"),
                    cell_index=item.get("cell_index"),
                    cell_paragraph_index=item.get("cell_paragraph_index"),
                    source_path=item.get("source_path", ""),
                    format_metadata=item.get("format_metadata", {}),
                )
                for item in block_payloads
            ]

            # Fast bulk create
            created_blocks = DocumentBlock.objects.bulk_create(
                db_blocks,
                batch_size=500,
            )

            # Map order_index to saved database object IDs to map parent references
            created_by_order = {
                block.order_index: block
                for block in created_blocks
            }

            relation_updates = []
            for item in block_payloads:
                parent_order_index = item.get("parent_heading_order_index")
                if parent_order_index is None:
                    continue

                current_block = created_by_order.get(item["order_index"])
                parent_block = created_by_order.get(parent_order_index)

                if current_block and parent_block:
                    current_block.parent_heading_id = parent_block.id
                    relation_updates.append(current_block)

            # Update database parent references in bulk
            if relation_updates:
                DocumentBlock.objects.bulk_update(
                    relation_updates,
                    fields=["parent_heading"],
                    batch_size=500,
                )

            return len(created_blocks)

    def _mark_parsing(self, document: Document) -> None:
        document.status = Document.Status.PARSING
        document.processing_error = ""
        document.save(update_fields=["status", "processing_error", "updated_at"])

    def _mark_failed(self, document: Document, message: str) -> None:
        document.status = Document.Status.FAILED
        document.processing_error = message
        document.save(update_fields=["status", "processing_error", "updated_at"])
