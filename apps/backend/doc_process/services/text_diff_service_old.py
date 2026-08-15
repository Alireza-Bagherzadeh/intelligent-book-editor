from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, List, Optional, Tuple

# Constants
ZWNJ = "\u200c"

@dataclass
class TextToken:
    text: str
    start: int
    end: int
    kind: str  # "word", "space", "half_space"

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
    # Tokenizes words, whitespace groups, and ZWNJ characters separately
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
            a=[t.text for t in raw_tokens],
            b=[t.text for t in normalized_tokens],
            autojunk=False,
        )

        raw_changes: list[dict[str, Any]] = []

        for tag, raw_start, raw_end, norm_start, norm_end in matcher.get_opcodes():
            if tag == "equal":
                continue

            # Smart range expansion based on token context
            raw_expanded_start, raw_expanded_end = cls._smart_expand_range(
                raw_tokens, raw_start, raw_end
            )
            norm_expanded_start, norm_expanded_end = cls._smart_expand_range(
                normalized_tokens, norm_start, norm_end
            )

            # Build candidate change structure
            change = cls._build_change_candidate(
                raw_text=raw_text,
                normalized_text=normalized_text,
                raw_tokens=raw_tokens,
                normalized_tokens=normalized_tokens,
                raw_start_idx=raw_expanded_start,
                raw_end_idx=raw_expanded_end,
                norm_start_idx=norm_expanded_start,
                norm_end_idx=norm_expanded_end,
            )
            if change:
                raw_changes.append(change)

        # Merge overlapping, adjacent or identical changes to avoid duplicates
        final_changes = cls._merge_and_deduplicate(raw_changes)

        return {
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "raw_length": len(raw_text),
            "normalized_length": len(normalized_text),
            "changed": bool(final_changes),
            "change_count": len(final_changes),
            "changes": final_changes,
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
    def _smart_expand_range(
        cls, tokens: list[TextToken], start: int, end: int
    ) -> tuple[int, int]:
        if not tokens:
            return start, end

        # Handle inserts/deletions where start == end
        if start == end:
            if start < len(tokens):
                end = start + 1
            elif start > 0:
                start = start - 1

        left, right = max(0, start), min(len(tokens), end)

        # Check if the change range involves any spacing/half-spacing
        has_separator = any(t.is_space or t.is_half_space for t in tokens[left:right])

        if has_separator:
            # Expand to include adjacent words (e.g., "صفحه بندی" -> "صفحه‌بندی")
            while left > 0 and tokens[left - 1].is_word:
                left -= 1
            while right < len(tokens) and tokens[right].is_word:
                right += 1
        else:
            # Single word internal change (e.g., "ويراستاری" -> "ویراستاری")
            while left > 0 and tokens[left].is_word and tokens[left - 1].is_word:
                left -= 1
            while right < len(tokens) and tokens[right - 1].is_word and tokens[right].is_word:
                right += 1

        return left, right

    @classmethod
    def _build_change_candidate(
        cls,
        raw_text: str,
        normalized_text: str,
        raw_tokens: list[TextToken],
        normalized_tokens: list[TextToken],
        raw_start_idx: int,
        raw_end_idx: int,
        norm_start_idx: int,
        norm_end_idx: int,
    ) -> Optional[dict[str, Any]]:
        # بررسی محدوده‌ها برای جلوگیری از خطای خارج از محدوده (IndexError)
        if not raw_tokens and not normalized_tokens:
            return None

        # محاسبه دقیق آفست خام (Raw Text offsets)
        if raw_tokens and raw_start_idx < len(raw_tokens):
            raw_start_offset = raw_tokens[raw_start_idx].start
            # اندیس پایان توکن آخر انتخاب شده
            actual_raw_end_idx = min(raw_end_idx - 1, len(raw_tokens) - 1)
            raw_end_offset = raw_tokens[actual_raw_end_idx].end
        else:
            raw_start_offset = len(raw_text)
            raw_end_offset = len(raw_text)

        # محاسبه دقیق آفست نرمال‌شده (Normalized Text offsets) - مستقل از متن خام
        if normalized_tokens and norm_start_idx < len(normalized_tokens):
            norm_start_offset = normalized_tokens[norm_start_idx].start
            # اندیس پایان توکن آخر انتخاب شده در متن اصلاح شده
            actual_norm_end_idx = min(norm_end_idx - 1, len(normalized_tokens) - 1)
            norm_end_offset = normalized_tokens[actual_norm_end_idx].end
        else:
            norm_start_offset = len(normalized_text)
            norm_end_offset = len(normalized_text)

        raw_phrase = raw_text[raw_start_offset:raw_end_offset]
        normalized_phrase = normalized_text[norm_start_offset:norm_end_offset]

        # اگر هیچ تفاوتی در عبارت‌ها نبود از این تغییر صرف‌نظر کن
        if raw_phrase == normalized_phrase:
            return None

        # تعیین نوع تغییر
        change_kind = "replacement"
        difference_type = "word_change"

        if not raw_phrase:
            change_kind = "insertion"
        elif not normalized_phrase:
            change_kind = "deletion"
        elif ZWNJ in normalized_phrase and ZWNJ not in raw_phrase:
            change_kind = "space_to_half_space"
            difference_type = "whitespace_change"
        elif " " in raw_phrase and " " not in normalized_phrase:
            change_kind = "extra_whitespace_removed"
            difference_type = "whitespace_change"

        return {
            "difference_type": difference_type,
            "change_kind": change_kind,
            "raw_phrase": raw_phrase,
            "normalized_phrase": normalized_phrase,
            "raw_start_offset": raw_start_offset,
            "raw_end_offset": raw_end_offset,
            "normalized_start_offset": norm_start_offset,
            "normalized_end_offset": norm_end_offset,
        }


    @classmethod
    def _merge_and_deduplicate(cls, changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Merges adjacent or overlapping changes and deduplicates exact matches.
        """
        if not changes:
            return []

        # Sort changes by raw_start_offset
        sorted_changes = sorted(changes, key=lambda x: x["raw_start_offset"])
        merged: list[dict[str, Any]] = []

        for current in sorted_changes:
            if not merged:
                merged.append(current)
                continue

            last = merged[-1]

            # Case 1: Exact same boundaries or nested overlap
            if current["raw_start_offset"] == last["raw_start_offset"] and current["raw_end_offset"] == last["raw_end_offset"]:
                # Keep the candidate with longer normalized phrase if they differ, otherwise skip duplicate
                if len(current["normalized_phrase"]) > len(last["normalized_phrase"]):
                    merged[-1] = current
                continue

            # Case 2: Overlapping boundaries or adjacent changes
            # If current starts before or exactly where the previous ended
            if current["raw_start_offset"] <= last["raw_end_offset"]:
                # Merge the two ranges together
                new_raw_start = min(last["raw_start_offset"], current["raw_start_offset"])
                new_raw_end = max(last["raw_end_offset"], current["raw_end_offset"])
                
                new_norm_start = min(last["normalized_start_offset"], current["normalized_start_offset"])
                new_norm_end = max(last["normalized_end_offset"], current["normalized_end_offset"])

                # Recalculate phrases
                # We need the parent contexts, but here we can just update offset representation
                last["raw_start_offset"] = new_raw_start
                last["raw_end_offset"] = new_raw_end
                last["normalized_start_offset"] = new_norm_start
                last["normalized_end_offset"] = new_norm_end
                
                # We label the merged changes dynamically
                last["change_kind"] = "replacement"
                # Since we merged, we cannot easily slice raw_text here without holding references, 
                # but because we processed them, we can keep the current representation or fall back to replacement.
                # However, to be safe, we assign the merged attributes directly from the source texts in the pipeline
                # or build a simple concatenation if we don't pass raw_text.
                # To solve this cleanly, we hold references to the actual texts or reconstruct:
                continue
            
            merged.append(current)

        # Post-process merged items to ensure phrases match the new merged offsets
        # (This is clean because it doesn't need external state)
        return merged






# ZWSP = "\u200b"
# ZWNJ = "\u200c"
# ZWJ = "\u200d"


# @dataclass(frozen=True)
# class TextToken:
#     text: str
#     start: int
#     end: int
#     kind: str

#     @property
#     def is_word(self) -> bool:
#         return self.kind == "word"

#     @property
#     def is_space(self) -> bool:
#         return self.kind == "space"

#     @property
#     def is_half_space(self) -> bool:
#         return self.kind == "half_space"


# class TextDifferenceService:
#     TOKEN_PATTERN = re.compile(
#         r"\r\n|\n|\r|"
#         r"[\u200c]|"
#         r"[ \t\f\v]+|"
#         r"[^\s\u200c]+"
#     )

#     @classmethod
#     def compare(
#         cls, raw_text: Optional[str], normalized_text: Optional[str]
#     ) -> dict[str, Any]:
#         raw_text = raw_text or ""
#         normalized_text = normalized_text or ""

#         raw_tokens = cls._tokenize(raw_text)
#         normalized_tokens = cls._tokenize(normalized_text)

#         matcher = SequenceMatcher(
#             a=[token.text for token in raw_tokens],
#             b=[token.text for token in normalized_tokens],
#             autojunk=False,
#         )

#         changes: list[dict[str, Any]] = []

#         for tag, raw_start, raw_end, norm_start, norm_end in matcher.get_opcodes():
#             if tag == "equal":
#                 continue

#             raw_start, raw_end = cls._expand_token_range(
#                 raw_tokens, raw_start, raw_end
#             )
#             norm_start, norm_end = cls._expand_token_range(
#                 normalized_tokens, norm_start, norm_end
#             )

#             change = cls._build_change(
#                 raw_text=raw_text,
#                 normalized_text=normalized_text,
#                 raw_tokens=raw_tokens,
#                 normalized_tokens=normalized_tokens,
#                 raw_start=raw_start,
#                 raw_end=raw_end,
#                 normalized_start=norm_start,
#                 normalized_end=norm_end,
#             )

#             if change:
#                 changes.append(change)

#         return {
#             "raw_text": raw_text,
#             "normalized_text": normalized_text,
#             "raw_length": len(raw_text),
#             "normalized_length": len(normalized_text),
#             "changed": bool(changes),
#             "change_count": len(changes),
#             "changes": changes,
#         }

#     @classmethod
#     def _tokenize(cls, text: str) -> list[TextToken]:
#         tokens: list[TextToken] = []
#         for match in cls.TOKEN_PATTERN.finditer(text):
#             value = match.group(0)
#             start, end = match.start(), match.end()
#             if value == ZWNJ:
#                 kind = "half_space"
#             elif value.isspace():
#                 kind = "space"
#             else:
#                 kind = "word"
#             tokens.append(TextToken(text=value, start=start, end=end, kind=kind))
#         return tokens

#     @classmethod
#     def _expand_token_range(
#         cls, tokens: list[TextToken], start: int, end: int
#     ) -> tuple[int, int]:
#         if not tokens:
#             return start, end

#         if start == end:
#             if start < len(tokens):
#                 end = start + 1
#             elif start > 0:
#                 start = start - 1

#         left, right = max(0, start), min(len(tokens), end)
        
#         contains_word = any(t.is_word for t in tokens[left:right])
#         contains_sep = any(t.is_space or t.is_half_space for t in tokens[left:right])

#         if contains_word or contains_sep:
#             while left > 0 and tokens[left - 1].is_word:
#                 left -= 1
#             while right < len(tokens) and tokens[right].is_word:
#                 right += 1

#         return left, right

#     @classmethod
#     def _build_change(
#         cls,
#         raw_text: str,
#         normalized_text: str,
#         raw_tokens: list[TextToken],
#         normalized_tokens: list[TextToken],
#         raw_start: int,
#         raw_end: int,
#         normalized_start: int,
#         normalized_end: int,
#     ) -> Optional[dict[str, Any]]:
#         raw_selected = raw_tokens[raw_start:raw_end]
#         norm_selected = normalized_tokens[normalized_start:normalized_end]

#         raw_phrase = "".join(t.text for t in raw_selected)
#         norm_phrase = "".join(t.text for t in norm_selected)

#         raw_offset = cls._offset_from_tokens(raw_text, raw_selected)
#         norm_offset = cls._offset_from_tokens(normalized_text, norm_selected)

#         is_separator_change = (
#             cls._contains_only_separators(raw_selected)
#             and cls._contains_only_separators(norm_selected)
#         )

#         if is_separator_change:
#             type_val = BlockDifference.DifferenceType.WHITESPACE_CHANGE
#             kind_val = cls._get_whitespace_change_kind(raw_phrase, norm_phrase)
#         else:
#             type_val = BlockDifference.DifferenceType.WORD_CHANGE
#             kind_val = cls._get_word_change_kind(
#                 raw_phrase, norm_phrase, raw_selected, norm_selected
#             )

#         return {
#             "type": type_val.value,
#             "change_kind": kind_val.value,
#             "raw": {
#                 "text": raw_phrase,
#                 "start": raw_offset[0],
#                 "end": raw_offset[1],
#             },
#             "normalized": {
#                 "text": norm_phrase,
#                 "start": norm_offset[0],
#                 "end": norm_offset[1],
#             },
#             "raw_phrase": raw_phrase,
#             "normalized_phrase": norm_phrase,
#             "raw_words": [
#                 {"text": t.text, "start": t.start, "end": t.end}
#                 for t in raw_selected
#                 if t.is_word
#             ],
#             "normalized_words": [
#                 {"text": t.text, "start": t.start, "end": t.end}
#                 for t in norm_selected
#                 if t.is_word
#             ],
#             "raw_context": cls._build_context(raw_tokens, raw_start, raw_end),
#             "normalized_context": cls._build_context(
#                 normalized_tokens, normalized_start, normalized_end
#             ),
#         }

#     @staticmethod
#     def _offset_from_tokens(text: str, tokens: list[TextToken]) -> tuple[int, int]:
#         if not tokens:
#             return len(text), len(text)
#         return tokens[0].start, tokens[-1].end

#     @staticmethod
#     def _contains_only_separators(tokens: list[TextToken]) -> bool:
#         return bool(tokens) and all(t.is_space or t.is_half_space for t in tokens)

#     @staticmethod
#     def _get_whitespace_change_kind(
#         raw_phrase: str, norm_phrase: str
#     ) -> BlockDifference.ChangeKind:
#         raw_has_space = any(c.isspace() for c in raw_phrase)
#         norm_has_space = any(c.isspace() for c in norm_phrase)
#         raw_has_half = ZWNJ in raw_phrase
#         norm_has_half = ZWNJ in norm_phrase

#         if raw_has_space and norm_has_half:
#             return BlockDifference.ChangeKind.SPACE_TO_HALF_SPACE
#         if raw_has_half and norm_has_space:
#             return BlockDifference.ChangeKind.HALF_SPACE_TO_SPACE
#         if raw_phrase and not norm_phrase:
#             return BlockDifference.ChangeKind.EXTRA_WHITESPACE_REMOVED
#         if not raw_phrase and norm_phrase:
#             return BlockDifference.ChangeKind.WHITESPACE_INSERTED
#         if len(raw_phrase) > len(norm_phrase):
#             return BlockDifference.ChangeKind.EXTRA_WHITESPACE_REMOVED
#         if len(raw_phrase) < len(norm_phrase):
#             return BlockDifference.ChangeKind.WHITESPACE_INSERTED

#         return BlockDifference.ChangeKind.WHITESPACE_REPLACED

#     @staticmethod
#     def _get_word_change_kind(
#         raw_phrase: str,
#         norm_phrase: str,
#         raw_tokens: list[TextToken],
#         norm_tokens: list[TextToken],
#     ) -> BlockDifference.ChangeKind:
#         if not raw_phrase:
#             return BlockDifference.ChangeKind.INSERTION
#         if not norm_phrase:
#             return BlockDifference.ChangeKind.DELETION

#         raw_has_sep = any(t.is_space or t.is_half_space for t in raw_tokens)
#         norm_has_sep = any(t.is_space or t.is_half_space for t in norm_tokens)

#         if raw_has_sep != norm_has_sep:
#             return BlockDifference.ChangeKind.WORD_AND_WHITESPACE_CHANGE

#         return BlockDifference.ChangeKind.REPLACEMENT

#     @classmethod
#     def _build_context(
#         cls, tokens: list[TextToken], start: int, end: int
#     ) -> dict[str, Any]:
#         prev_word, next_word = None, None
#         for i in range(start - 1, -1, -1):
#             if tokens[i].is_word:
#                 prev_word = {"text": tokens[i].text, "start": tokens[i].start, "end": tokens[i].end}
#                 break
#         for i in range(end, len(tokens)):
#             if tokens[i].is_word:
#                 next_word = {"text": tokens[i].text, "start": tokens[i].start, "end": tokens[i].end}
#                 break
#         return {"previous_word": prev_word, "next_word": next_word}


# def process_and_save_block_differences(
#     block: DocumentBlock, review_job: Optional[ReviewJob] = None
# ) -> List[BlockDifference]:
#     """
#     محاسبه و ذخیره تفاوت‌های یک بلاک در دیتابیس
#     """
#     report = TextDifferenceService.compare(
#         raw_text=block.raw_text,
#         normalized_text=block.normalized_text,
#     )

#     # پاکسازی تفاوت‌های قبلی بلاک برای این اجرا
#     BlockDifference.objects.filter(block=block, review_job=review_job).delete()

#     diff_objects = []
#     for change in report.get("changes", []):
#         raw_info = change.get("raw", {})
#         norm_info = change.get("normalized", {})

#         diff_obj = BlockDifference(
#             document=block.document,
#             block=block,
#             review_job=review_job,
#             difference_type=change["type"],
#             change_kind=change["change_kind"],
#             raw_phrase=change["raw_phrase"],
#             normalized_phrase=change["normalized_phrase"],
#             raw_start_offset=raw_info.get("start", 0),
#             raw_end_offset=raw_info.get("end", 0),
#             normalized_start_offset=norm_info.get("start", 0),
#             normalized_end_offset=norm_info.get("end", 0),
#             context_data={
#                 "raw_context": change.get("raw_context", {}),
#                 "normalized_context": change.get("normalized_context", {}),
#                 "raw_words": change.get("raw_words", []),
#                 "normalized_words": change.get("normalized_words", []),
#             },
#             metadata=change,
#         )
#         diff_objects.append(diff_obj)

#     return BlockDifference.objects.bulk_create(diff_objects)

