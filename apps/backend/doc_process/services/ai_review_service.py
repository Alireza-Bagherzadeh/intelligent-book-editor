import json
from google import genai
from google.genai import types
from pydantic import BaseModel
from django.conf import settings
from django.utils import timezone
from ..models import Document, DocumentBlock, BlockIssue, ReviewJob

# Define the structured output schema mapping exactly to your BlockIssue model
class IssueSchema(BaseModel):
    issue_code: str  # Must match BlockIssue.IssueCode choices
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
    def process_document(document_id: int, review_job_id: int):
        """
        Fetches document blocks, batches them, and sends them to Gemini.
        Updates the ReviewJob status and creates BlockIssue instances.
        """
        doc = Document.objects.get(id=document_id)
        review_job = ReviewJob.objects.get(id=review_job_id)
        
        # Fetch only PARAGRAPH or HEADING blocks, ordered by order_index
        blocks = DocumentBlock.objects.filter(document=doc).order_by('order_index')
        
        batch_size = 10
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        all_request_payloads = []
        all_response_payloads = []

        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i + batch_size]
            
            # Prepare payload containing the raw_text of the blocks
            block_data = [{"block_id": b.id, "text": b.raw_text} for b in batch]
            all_request_payloads.append(block_data)
            
            prompt = (
                "Review the following texts. Find spelling, grammar, punctuation, and style errors. "
                "Only return output for the blocks that have been modified, and ignore the unchanged ones. "
                "For issue_code, you MUST strictly use one of these values: "
                "'spelling', 'grammar', 'style', 'punctuation', 'optimization'.\n"
                f"{json.dumps(block_data, ensure_ascii=False)}"
            )

            try:
                # Call Gemini API with Pydantic Structured Output
                response = client.models.generate_content(
                    model=review_job.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=GeminiReviewResponse,
                        temperature=0.1,
                    ),
                )
                
                result_data = json.loads(response.text)
                all_response_payloads.append(result_data)
                
                GeminiReviewService._save_results(result_data, doc, review_job)
                
            except Exception as e:
                review_job.error_message += f"\nBatch {i} Error: {str(e)}"
                review_job.save()

        # Finalize the ReviewJob
        review_job.status = ReviewJob.Status.SUCCEEDED if not review_job.error_message else ReviewJob.Status.FAILED
        review_job.request_payload = {"batches": all_request_payloads}
        review_job.response_payload = {"batches": all_response_payloads}
        review_job.finished_at = timezone.now()
        review_job.save()

    @staticmethod
    def _save_results(result_data: dict, doc: Document, review_job: ReviewJob):
        """
        Parses the JSON response and updates DocumentBlock and BlockIssue models.
        """
        modified_blocks = result_data.get('modified_blocks', [])
        
        for mod_block in modified_blocks:
            try:
                block = DocumentBlock.objects.get(id=mod_block['block_id'], document=doc)
                
                # Update the normalized_text (which acts as the corrected text)
                block.normalized_text = mod_block['normalized_text']
                block.save()

                # Save the identified issues mapped to the BlockIssue model
                for issue in mod_block.get('issues', []):
                    # Ensure issue_code is valid, fallback to OPTIMIZATION if LLM hallucinates
                    valid_codes = [choice[0] for choice in BlockIssue.IssueCode.choices]
                    issue_code = issue['issue_code'] if issue['issue_code'] in valid_codes else BlockIssue.IssueCode.OPTIMIZATION
                    
                    BlockIssue.objects.create(
                        document=doc,
                        block=block,
                        review_job=review_job,
                        issue_code=issue_code,
                        title=issue['title'],
                        description=issue['description'],
                        start_offset=issue['start_offset'],
                        end_offset=issue['end_offset'],
                        suggestion_text=issue['suggestion_text'],
                        severity=BlockIssue.Severity.WARNING # Default severity
                    )
                
            except DocumentBlock.DoesNotExist:
                continue