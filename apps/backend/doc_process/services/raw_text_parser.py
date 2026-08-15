# doc_process/services/raw_text_parser.py
from __future__ import annotations

import re
from typing import Any

from doc_process.services.text_normalizer import TextNormalizationService


class RawTextParseService:
    # Common Persian heading/section words
    HEADING_WORDS = {
        "مقدمه",
        "چکیده",
        "نتیجه‌گیری",
        "نتیجه گیری",
        "جمع‌بندی",
        "جمع بندی",
        "پیشنهادها",
        "پیشنهادات",
        "بحث",
        "روش تحقیق",
        "یافته‌ها",
        "یافته ها",
        "منابع",
        "ضمائم",
        "پیوست",
    }

    def __init__(self, include_empty_blocks: bool = False) -> None:
        self.include_empty_blocks = include_empty_blocks
        self.normalizer = TextNormalizationService()

    def extract_blocks(
        self,
        text: str,
        source_identifier: str,
    ) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        active_headings: dict[int, int] = {}  # Map heading_level -> order_index

        for paragraph_index, raw_line in enumerate(text.splitlines()):
            raw_text = raw_line.strip()
            normalized_text = self.normalizer.normalize(raw_text)

            # Skip empty lines if configured
            if not self.include_empty_blocks and not normalized_text:
                continue

            block_type, heading_level = self._detect_heading(normalized_text)
            order_index = len(blocks)

            # Build the parent-child heading hierarchy
            parent_heading_order_index = self._resolve_parent_heading(
                block_type=block_type,
                heading_level=heading_level,
                order_index=order_index,
                active_headings=active_headings,
            )

            is_rtl = self._is_rtl(raw_text)

            # This dictionary matches the DocxParseService block contract
            blocks.append({
                "block_type": block_type,
                "heading_level": heading_level,
                "order_index": order_index,
                "parent_heading_order_index": parent_heading_order_index,
                "raw_text": raw_text,
                "normalized_text": normalized_text,
                "style_name": "",
                "is_rtl": is_rtl,
                "alignment": "right" if is_rtl else "left",
                "paragraph_index": paragraph_index,
                "table_index": None,
                "row_index": None,
                "cell_index": None,
                "cell_paragraph_index": None,
                "source_path": source_identifier,
                "format_metadata": {
                    "source_format": "raw_text",
                    "text_length": len(normalized_text),
                },
            })

        return blocks

    def _detect_heading(self, text: str) -> tuple[str, int | None]:
        if not text:
            return "paragraph", None

        # 1. Detect Markdown headings (e.g. # Intro, ## Section)
        markdown_match = re.match(r"^(#{1,6})\s+(.+)$", text)
        if markdown_match:
            return "heading", min(len(markdown_match.group(1)), 6)

        # 2. Detect common Persian single-word headings
        if text in self.HEADING_WORDS:
            return "heading", 1

        # 3. Detect numbered headings (e.g. 1.2 Introduction, 1-3 Section)
        numbered_match = re.match(
            r"^\d+(?:\.\d+){0,5}\s*[\)\-–—.:]?\s+.+$",
            text,
        )
        if numbered_match:
            prefix_match = re.match(r"^\d+(?:\.\d+)*", text)
            level = 1
            if prefix_match:
                level = prefix_match.group(0).count(".") + 1
            return "heading", min(level, 6)

        return "paragraph", None

    def _resolve_parent_heading(
        self,
        block_type: str,
        heading_level: int | None,
        order_index: int,
        active_headings: dict[int, int],
    ) -> int | None:
        if block_type == "heading" and heading_level is not None:
            parent_order_index = None

            # Find closest parent heading level above this one
            for level in range(heading_level - 1, 0, -1):
                if level in active_headings:
                    parent_order_index = active_headings[level]
                    break

            active_headings[heading_level] = order_index

            # Clear deeper nesting since we started a new higher level heading
            for level in list(active_headings.keys()):
                if level > heading_level:
                    del active_headings[level]

            return parent_order_index

        # For normal paragraphs, attach them to the current deepest active heading
        if active_headings:
            return active_headings[max(active_headings.keys())]

        return None

    def _is_rtl(self, text: str) -> bool:
        rtl_count = len(re.findall(r"[\u0590-\u08FF]", text))
        ltr_count = len(re.findall(r"[A-Za-z]", text))
        return rtl_count >= ltr_count
