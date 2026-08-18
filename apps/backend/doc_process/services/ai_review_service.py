from __future__ import annotations

import json

from django.conf import settings
from django.utils import timezone
from google import genai
from google.genai import types
from pydantic import BaseModel

from ..models import BlockIssue, Document, DocumentBlock, ReviewJob


class IssueSchema(BaseModel):
    issue_code: str
    title: str
    description: str
    start_offset: int
    end_offset: int
    suggestion_text: str


class ModifiedBlockSchema(BaseModel):
    block_id: int
    normalized_text: str
    issues: list[IssueSchema]


class GeminiReviewResponse(BaseModel):
    modified_blocks: list[ModifiedBlockSchema]


class GeminiReviewService:
    @staticmethod
    def process_document(document_id: int, review_job_id: int) -> dict:
        """Review document blocks with Gemini and persist structured results."""
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        document = Document.objects.get(id=document_id)
        review_job = ReviewJob.objects.get(id=review_job_id)
        blocks = list(
            DocumentBlock.objects
            .filter(document=document)
            .order_by("order_index")
        )

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        batch_size = 10
        request_batches: list[list[dict]] = []
        response_batches: list[dict] = []
        batch_errors: list[str] = []

        for offset in range(0, len(blocks), batch_size):
            batch = blocks[offset:offset + batch_size]
            block_data = [
                {"block_id": block.id, "text": block.raw_text}
                for block in batch
            ]
            request_batches.append(block_data)

            prompt = (
                "Review the following texts. Find spelling, grammar, "
                "punctuation, and style errors. Only return output for "
                "blocks that were modified. For issue_code, use exactly "
                "one of: spelling, grammar, style, punctuation, optimization.\n"
                f"{json.dumps(block_data, ensure_ascii=False)}"
            )

            try:
                response = client.models.generate_content(
                    model=review_job.model_name or settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=GeminiReviewResponse,
                        temperature=0.1,
                    ),
                )

                if not response.text:
                    raise RuntimeError("Gemini returned an empty response.")

                parsed = GeminiReviewResponse.model_validate_json(
                    response.text
                )
                result_data = parsed.model_dump()
                response_batches.append(result_data)
                GeminiReviewService._save_results(
                    result_data,
                    document,
                    review_job,
                )

            except Exception as exc:
                batch_errors.append(
                    f"Batch {offset // batch_size + 1}: {exc}"
                )

        review_job.request_payload = {"batches": request_batches}
        review_job.response_payload = {"batches": response_batches}
        review_job.finished_at = timezone.now()

        if batch_errors:
            review_job.status = ReviewJob.Status.FAILED
            review_job.error_message = "\n".join(batch_errors)
        else:
            review_job.status = ReviewJob.Status.SUCCEEDED
            review_job.error_message = ""

        review_job.save(
            update_fields=[
                "status",
                "request_payload",
                "response_payload",
                "finished_at",
                "error_message",
            ]
        )

        if batch_errors:
            raise RuntimeError(review_job.error_message)

        return {
            "processed_blocks": len(blocks),
            "response_batches": len(response_batches),
        }

    @staticmethod
    def _save_results(
        result_data: dict,
        document: Document,
        review_job: ReviewJob,
    ) -> None:
        valid_codes = {choice[0] for choice in BlockIssue.IssueCode.choices}

        for modified in result_data.get("modified_blocks", []):
            try:
                block = DocumentBlock.objects.get(
                    id=modified["block_id"],
                    document=document,
                )
            except DocumentBlock.DoesNotExist:
                continue

            block.normalized_text = modified["normalized_text"]
            block.save(update_fields=["normalized_text"])

            for issue in modified.get("issues", []):
                issue_code = issue["issue_code"]
                if issue_code not in valid_codes:
                    issue_code = BlockIssue.IssueCode.OPTIMIZATION

                BlockIssue.objects.create(
                    document=document,
                    block=block,
                    review_job=review_job,
                    issue_code=issue_code,
                    title=issue["title"],
                    description=issue["description"],
                    start_offset=max(0, issue["start_offset"]),
                    end_offset=max(0, issue["end_offset"]),
                    suggestion_text=issue["suggestion_text"],
                    severity=BlockIssue.Severity.WARNING,
                )
