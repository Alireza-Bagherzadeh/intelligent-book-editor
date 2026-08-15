from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, List, Optional, Tuple
import logging
import requests
from django.conf import settings
from django.db import transaction
from doc_process.models import Document, DocumentBlock, ReviewJob, BlockDifference

ZWSP = "\u200b"
ZWNJ = "\u200c"
ZWJ = "\u200d"


@dataclass(frozen=True)
class TextToken:
    text: str
    start: int
    end: int
    kind: str

    @property
    def is_word(self) -> bool:
        return self.kind == "word"

    @property
    def is_space(self) -> bool:
        return self.kind == "space"

    @property
    def is_half_space(self) -> bool:
        return self.kind == "half_space"


class TextDifferenceService:
    TOKEN_PATTERN = re.compile(
        r"\r\n|\n|\r|"
        r"[\u200c]|"
        r"[ \t\f\v]+|"
        r"[^\s\u200c]+"
    )

    @classmethod
    def compare(
        cls, raw_text: Optional[str], normalized_text: Optional[str]
    ) -> dict[str, Any]:
        raw_text = raw_text or ""
        normalized_text = normalized_text or ""

        raw_tokens = cls._tokenize(raw_text)
        normalized_tokens = cls._tokenize(normalized_text)

        matcher = SequenceMatcher(
            a=[token.text for token in raw_tokens],
            b=[token.text for token in normalized_tokens],
            autojunk=False,
        )

        changes: list[dict[str, Any]] = []

        for tag, raw_start, raw_end, norm_start, norm_end in matcher.get_opcodes():
            if tag == "equal":
                continue

            raw_start, raw_end = cls._expand_token_range(
                raw_tokens, raw_start, raw_end
            )
            norm_start, norm_end = cls._expand_token_range(
                normalized_tokens, norm_start, norm_end
            )

            change = cls._build_change(
                raw_text=raw_text,
                normalized_text=normalized_text,
                raw_tokens=raw_tokens,
                normalized_tokens=normalized_tokens,
                raw_start=raw_start,
                raw_end=raw_end,
                normalized_start=norm_start,
                normalized_end=norm_end,
            )

            if change:
                changes.append(change)

        return {
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "raw_length": len(raw_text),
            "normalized_length": len(normalized_text),
            "changed": bool(changes),
            "change_count": len(changes),
            "changes": changes,
        }

    @classmethod
    def _tokenize(cls, text: str) -> list[TextToken]:
        tokens: list[TextToken] = []
        for match in cls.TOKEN_PATTERN.finditer(text):
            value = match.group(0)
            start, end = match.start(), match.end()
            if value == ZWNJ:
                kind = "half_space"
            elif value.isspace():
                kind = "space"
            else:
                kind = "word"
            tokens.append(TextToken(text=value, start=start, end=end, kind=kind))
        return tokens

    @classmethod
    def _expand_token_range(
        cls, tokens: list[TextToken], start: int, end: int
    ) -> tuple[int, int]:
        if not tokens:
            return start, end

        if start == end:
            if start < len(tokens):
                end = start + 1
            elif start > 0:
                start = start - 1

        left, right = max(0, start), min(len(tokens), end)
        contains_word = any(t.is_word for t in tokens[left:right])
        contains_sep = any(t.is_space or t.is_half_space for t in tokens[left:right])

        if contains_word or contains_sep:
            while left > 0 and tokens[left - 1].is_word:
                left -= 1
            while right < len(tokens) and tokens[right].is_word:
                right += 1

        return left, right

    @classmethod
    def _build_change(
        cls,
        raw_text: str,
        normalized_text: str,
        raw_tokens: list[TextToken],
        normalized_tokens: list[TextToken],
        raw_start: int,
        raw_end: int,
        normalized_start: int,
        normalized_end: int,
    ) -> Optional[dict[str, Any]]:
        raw_selected = raw_tokens[raw_start:raw_end]
        norm_selected = normalized_tokens[normalized_start:normalized_end]

        raw_phrase = "".join(t.text for t in raw_selected)
        norm_phrase = "".join(t.text for t in norm_selected)

        raw_offset = cls._offset_from_tokens(raw_text, raw_selected)
        norm_offset = cls._offset_from_tokens(normalized_text, norm_selected)

        is_separator_change = cls._is_whitespace_only_change(
            raw_selected,
            norm_selected,
        )

        if is_separator_change:
            type_val = BlockDifference.DifferenceType.WHITESPACE_CHANGE
            kind_val = cls._get_whitespace_change_kind(raw_phrase, norm_phrase)
        else:
            type_val = BlockDifference.DifferenceType.WORD_CHANGE
            kind_val = cls._get_word_change_kind(
                raw_phrase, norm_phrase, raw_selected, norm_selected
            )

        return {
            "type": type_val.value,
            "change_kind": kind_val.value,
            "raw": {
                "text": raw_phrase,
                "start": raw_offset[0],
                "end": raw_offset[1],
            },
            "normalized": {
                "text": norm_phrase,
                "start": norm_offset[0],
                "end": norm_offset[1],
            },
            "raw_phrase": raw_phrase,
            "normalized_phrase": norm_phrase,
            "raw_words": [
                {"text": t.text, "start": t.start, "end": t.end}
                for t in raw_selected
                if t.is_word
            ],
            "normalized_words": [
                {"text": t.text, "start": t.start, "end": t.end}
                for t in norm_selected
                if t.is_word
            ],
            "raw_context": cls._build_context(raw_tokens, raw_start, raw_end),
            "normalized_context": cls._build_context(
                normalized_tokens, normalized_start, normalized_end
            ),
        }

    @staticmethod
    def _offset_from_tokens(text: str, tokens: list[TextToken]) -> tuple[int, int]:
        if not tokens:
            return len(text), len(text)
        return tokens[0].start, tokens[-1].end

    @staticmethod
    def _contains_only_separators(tokens: list[TextToken]) -> bool:
        return bool(tokens) and all(t.is_space or t.is_half_space for t in tokens)

    @staticmethod
    def _get_whitespace_change_kind(
        raw_phrase: str, norm_phrase: str
    ) -> BlockDifference.ChangeKind:
        raw_has_space = any(c.isspace() for c in raw_phrase)
        norm_has_space = any(c.isspace() for c in norm_phrase)
        raw_has_half = ZWNJ in raw_phrase
        norm_has_half = ZWNJ in norm_phrase

        if raw_has_space and norm_has_half:
            return BlockDifference.ChangeKind.SPACE_TO_HALF_SPACE
        if raw_has_half and norm_has_space:
            return BlockDifference.ChangeKind.HALF_SPACE_TO_SPACE
        if raw_phrase and not norm_phrase:
            return BlockDifference.ChangeKind.EXTRA_WHITESPACE_REMOVED
        if not raw_phrase and norm_phrase:
            return BlockDifference.ChangeKind.WHITESPACE_INSERTED
        if len(raw_phrase) > len(norm_phrase):
            return BlockDifference.ChangeKind.EXTRA_WHITESPACE_REMOVED
        if len(raw_phrase) < len(norm_phrase):
            return BlockDifference.ChangeKind.WHITESPACE_INSERTED

        return BlockDifference.ChangeKind.WHITESPACE_REPLACED

    @staticmethod
    def _get_word_change_kind(
        raw_phrase: str,
        norm_phrase: str,
        raw_tokens: list[TextToken],
        norm_tokens: list[TextToken],
    ) -> BlockDifference.ChangeKind:
        if not raw_phrase:
            return BlockDifference.ChangeKind.INSERTION
        if not norm_phrase:
            return BlockDifference.ChangeKind.DELETION

        raw_has_sep = any(t.is_space or t.is_half_space for t in raw_tokens)
        norm_has_sep = any(t.is_space or t.is_half_space for t in norm_tokens)

        if raw_has_sep != norm_has_sep:
            return BlockDifference.ChangeKind.WORD_AND_WHITESPACE_CHANGE

        return BlockDifference.ChangeKind.REPLACEMENT

    @classmethod
    def _build_context(
        cls, tokens: list[TextToken], start: int, end: int
    ) -> dict[str, Any]:
        prev_word, next_word = None, None
        for i in range(start - 1, -1, -1):
            if tokens[i].is_word:
                prev_word = {"text": tokens[i].text, "start": tokens[i].start, "end": tokens[i].end}
                break
        for i in range(end, len(tokens)):
            if tokens[i].is_word:
                next_word = {"text": tokens[i].text, "start": tokens[i].start, "end": tokens[i].end}
                break
        return {"previous_word": prev_word, "next_word": next_word}

    @classmethod
    def _is_whitespace_only_change(
        cls,
        raw_tokens: list[TextToken],
        norm_tokens: list[TextToken],
    ) -> bool:
        """
        Detects changes where only spaces / half-spaces changed
        while actual words stayed identical.

        Examples:
            صفحه بندی -> صفحه‌بندی
            می شود -> می‌شود
            داده ها -> داده‌ها
        """

        raw_words = [t.text for t in raw_tokens if t.is_word]
        norm_words = [t.text for t in norm_tokens if t.is_word]

        # اگر خود کلمات فرق کرده باشند، دیگر whitespace-only نیست
        if raw_words != norm_words:
            return False

        raw_has_sep = any(t.is_space or t.is_half_space for t in raw_tokens)
        norm_has_sep = any(t.is_space or t.is_half_space for t in norm_tokens)

        return raw_has_sep or norm_has_sep


def process_and_save_block_differences(
    block: DocumentBlock, review_job: Optional[ReviewJob] = None
) -> List[BlockDifference]:
    """
    محاسبه و ذخیره تفاوت‌های یک بلاک در دیتابیس
    """
    report = TextDifferenceService.compare(
        raw_text=block.raw_text,
        normalized_text=block.normalized_text,
    )

    # پاکسازی تفاوت‌های قبلی بلاک برای این اجرا
    BlockDifference.objects.filter(block=block, review_job=review_job).delete()

    diff_objects = []
    for change in report.get("changes", []):
        raw_info = change.get("raw", {})
        norm_info = change.get("normalized", {})

        diff_obj = BlockDifference(
            document=block.document,
            block=block,
            review_job=review_job,
            difference_type=change["type"],
            change_kind=change["change_kind"],
            raw_phrase=change["raw_phrase"],
            normalized_phrase=change["normalized_phrase"],
            raw_start_offset=raw_info.get("start", 0),
            raw_end_offset=raw_info.get("end", 0),
            normalized_start_offset=norm_info.get("start", 0),
            normalized_end_offset=norm_info.get("end", 0),
            context_data={
                "raw_context": change.get("raw_context", {}),
                "normalized_context": change.get("normalized_context", {}),
                "raw_words": change.get("raw_words", []),
                "normalized_words": change.get("normalized_words", []),
            },
            metadata=change,
        )
        diff_objects.append(diff_obj)

    return BlockDifference.objects.bulk_create(diff_objects)
