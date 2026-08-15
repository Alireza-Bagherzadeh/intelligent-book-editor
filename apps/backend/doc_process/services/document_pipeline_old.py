from __future__ import annotations

import logging
from pathlib import Path
from django.db import transaction
from doc_process.models import Document, DocumentBlock
from doc_process.services.docx_parser import DocxParseService

logger = logging.getLogger(__name__)

class DocumentPipelineService:
    def __init__(self) -> None:
        # standardizing include_empty_blocks flag to False
        self.parser = DocxParseService(include_empty_blocks=False)

    def parse_document(self, document: Document) -> int:
        document.status = "parsing"
        document.processing_error = ""
        document.save(update_fields=["status", "processing_error", "updated_at"])

        try:
            file_path = Path(document.original_file.path)
            logger.info(f"[Pipeline] Starting to parse document ID: {document.id} at path: {file_path}")
            
            block_payloads = self.parser.extract_blocks(file_path)

            if not block_payloads:
                # Crucial step: Mark document as failed if parser yields 0 blocks
                document.status = "failed"
                document.processing_error = "Parser returned 0 blocks. File might be blank, corrupt, or unreadable."
                document.save(update_fields=["status", "processing_error", "updated_at"])
                logger.error(f"[Pipeline] Aborted. 0 blocks returned for Document ID: {document.id}")
                return 0

            with transaction.atomic():
                # Clean up existing blocks to prevent duplicates
                deleted_count, _ = document.blocks.all().delete()
                logger.info(f"[Pipeline] Cleaned up {deleted_count} old blocks for Document ID: {document.id}")

                db_blocks = [
                    DocumentBlock(
                        document=document,
                        block_type=item["block_type"],
                        heading_level=item.get("heading_level"),
                        order_index=item["order_index"],
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
                        source_path=item.get("source_path", str(file_path)),
                        format_metadata=item.get("format_metadata", {}),
                    )
                    for item in block_payloads
                ]

                created_blocks = DocumentBlock.objects.bulk_create(db_blocks, batch_size=500)
                logger.info(f"[Pipeline] Bulk created {len(created_blocks)} blocks in DB.")

                created_map = {block.order_index: block for block in created_blocks}
                updates = []

                for item in block_payloads:
                    current_order = item["order_index"]
                    parent_order = item.get("parent_heading_order_index")

                    if parent_order is None:
                        continue

                    current_block = created_map.get(current_order)
                    parent_block = created_map.get(parent_order)

                    if current_block and parent_block:
                        current_block.parent_heading_id = parent_block.id
                        updates.append(current_block)

                if updates:
                    updated_count = DocumentBlock.objects.bulk_update(
                        updates,
                        fields=["parent_heading"],
                        batch_size=500
                    )
                    logger.info(f"[Pipeline] Updated parent relations for {updated_count} blocks.")

                document.status = "parsed"
                document.processing_error = ""
                document.save(update_fields=["status", "processing_error", "updated_at"])

            logger.info(f"[Pipeline] Parsing pipeline finished successfully for Document ID: {document.id}")
            return len(created_blocks)

        except Exception as exc:
            logger.exception(f"[Pipeline] Global failure parsing Document ID: {document.id}")
            document.status = "failed"
            document.processing_error = str(exc)
            document.save(update_fields=["status", "processing_error", "updated_at"])
            raise
