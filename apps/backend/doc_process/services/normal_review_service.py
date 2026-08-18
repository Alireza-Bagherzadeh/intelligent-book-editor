# services.py
import re
import logging
import difflib
from django.db import transaction

from doc_process.models import Document, BlockIssue, ReviewJob

logger = logging.getLogger(__name__)


class MockAiReview:
    """
    Local normalizer service replacing the LLM.
    It normalizes Persian text, enforces RTL layout, and creates precise BlockIssue records.
    """

    ZWNJ = "\u200c"
    PERSIAN_LETTERS = "اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"

    ARABIC_TO_PERSIAN_MAP = {
        "ي": "ی", "ى": "ی", "ك": "ک", "ۀ": "هٔ", "ة": "ه",
        "ؤ": "و", "إ": "ا", "أ": "ا",
    }
    ARABIC_TO_PERSIAN = str.maketrans(ARABIC_TO_PERSIAN_MAP)
    EN_TO_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

    def _normalize_letters(self, text: str) -> str:
        text = text.translate(self.ARABIC_TO_PERSIAN)
        text = text.replace("ـ", "")  # Remove kashida
        text = text.replace("\u200f", "").replace("\u200e", "")  # Remove directional marks
        text = text.replace("\ufeff", "").replace("\u00a0", " ")
        return text

    def _fix_half_spaces(self, text: str) -> str:
        text = re.sub(rf"\s*{self.ZWNJ}\s*", self.ZWNJ, text)
        text = re.sub(
            rf"(?<![{self.PERSIAN_LETTERS}])(ن?می)\s+([{self.PERSIAN_LETTERS}])",
            rf"\1{self.ZWNJ}\2",
            text,
        )
        text = re.sub(
            rf"([{self.PERSIAN_LETTERS}])\s+(ها|های|هایی|تر|ترین|ای)(?![{self.PERSIAN_LETTERS}])",
            rf"\1{self.ZWNJ}\2",
            text,
        )

        replacements = {
            "هم چنین": "همچنین",
            "می بایست": f"می{self.ZWNJ}بایست",
            "می باشد": f"می{self.ZWNJ}باشد",
            "می شوند": f"می{self.ZWNJ}شوند",
            "می شود": f"می{self.ZWNJ}شود",
            "نرم افزار": f"نرم{self.ZWNJ}افزار",
            "سخت افزار": f"سخت{self.ZWNJ}افزار",
            "داده ها": f"داده{self.ZWNJ}ها",
            "وب سایت": f"وب{self.ZWNJ}سایت",
            "صفحه بندی": f"صفحه{self.ZWNJ}بندی",
            "استایل بندی": f"استایل{self.ZWNJ}بندی",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _fix_punctuation(self, text: str) -> str:
        text = re.sub(r"[ \t]+([،؛؟!,:])", r"\1", text)
        text = re.sub(r"([،؛؟!:])(?=[^\s\n\r،؛؟!,:])", r"\1 ", text)
        text = re.sub(r"\.\s+", ". ", text)
        text = re.sub(r"\(\s+", "(", text)
        text = re.sub(r"\s+\)", ")", text)
        text = re.sub(r"\s+([»”])", r"\1", text)
        text = re.sub(r"([«“])\s+", r"\1", text)
        text = re.sub(r" {2,}", " ", text)
        return text

    def normalize_text(self, text: str) -> str:
        """
        Run the normalization pipeline.
        """
        if not text:
            return ""
        result = self._normalize_letters(text)
        result = self._fix_half_spaces(result)
        result = self._fix_punctuation(result)
        result = result.translate(self.EN_TO_FA_DIGITS)
        return result

    def _build_issue_from_diff(self, original: str, normalized: str):
        """
        Convert character-level diff into precise issue payloads.

        This keeps offsets aligned with the original text.
        """
        issues = []
        matcher = difflib.SequenceMatcher(a=original, b=normalized)

        for tag, a0, a1, b0, b1 in matcher.get_opcodes():
            if tag == "equal":
                continue

            original_segment = original[a0:a1]
            suggestion_text = normalized[b0:b1]

            # Skip empty noise
            if not original_segment and not suggestion_text:
                continue

            issue_code = BlockIssue.IssueCode.OPTIMIZATION
            severity = BlockIssue.Severity.INFO
            title = "اصلاح خودکار نگارش"
            description = "متن به صورت خودکار اصلاح شد."

            # Heuristics for better categorization
            if any(ch in original_segment for ch in ["ي", "ى", "ك", "ۀ", "ة", "ؤ", "إ", "أ", "ـ"]):
                issue_code = BlockIssue.IssueCode.SPELLING
                severity = BlockIssue.Severity.WARNING
                title = "اصلاح نویسه‌های غیر استاندارد"
                description = "نویسه‌های عربی یا کشیده به معادل استاندارد فارسی تبدیل شدند."
            elif self.ZWNJ in suggestion_text or " " in original_segment:
                issue_code = BlockIssue.IssueCode.PUNCTUATION
                severity = BlockIssue.Severity.WARNING
                title = "اصلاح نیم‌فاصله"
                description = "فاصله‌های نامناسب به نیم‌فاصله یا ساختار صحیح تبدیل شدند."
            elif any(ch in original_segment for ch in ["،", "؛", "؟", "!", ":", ",", "."]):
                issue_code = BlockIssue.IssueCode.PUNCTUATION
                severity = BlockIssue.Severity.WARNING
                title = "اصلاح علائم نگارشی"
                description = "فاصله‌گذاری یا جای‌گذاری علائم نگارشی اصلاح شد."

            issues.append({
                "issue_code": issue_code,
                "title": title,
                "description": description,
                "severity": severity,
                "start_offset": a0,
                "end_offset": a1,
                "original_segment": original_segment,
                "suggestion_text": suggestion_text,
            })

        return issues

    def review_document(self, document: Document, review_job: ReviewJob) -> dict:
        """Normalize blocks and create local issues; orchestration lives in tasks.py."""
        blocks = document.blocks.all().order_by("order_index")
        total_issues_created = 0

        try:
            with transaction.atomic():
                BlockIssue.objects.filter(document=document).delete()

                for block in blocks:
                    original = (block.raw_text or "").strip()
                    if not original:
                        continue

                    normalized = self.normalize_text(original)

                    block.is_rtl = True
                    block.alignment = "right"
                    block.normalized_text = normalized
                    block.save(
                        update_fields=["normalized_text", "is_rtl", "alignment"]
                    )

                    issue_payloads = self._build_issue_from_diff(
                        original, normalized
                    )
                    if not issue_payloads:
                        continue

                    issues = [
                        BlockIssue(
                            document=document,
                            block=block,
                            review_job=review_job,
                            issue_code=item["issue_code"],
                            title=item["title"],
                            description=item["description"],
                            severity=item["severity"],
                            start_offset=item["start_offset"],
                            end_offset=item["end_offset"],
                            suggestion_text=item["suggestion_text"],
                            extra_data={
                                "original_segment": item["original_segment"]
                            },
                        )
                        for item in issue_payloads
                    ]
                    BlockIssue.objects.bulk_create(issues)
                    total_issues_created += len(issues)

            summary = {
                "status": "success",
                "processed_blocks": blocks.count(),
                "issues_count": total_issues_created,
            }
            review_job.response_payload = summary
            review_job.save(update_fields=["response_payload"])
            return summary

        except Exception:
            logger.exception("Error in local review service.")
            raise
