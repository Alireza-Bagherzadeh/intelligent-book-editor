from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

# ایمپورت کردن کدهای اصلی از دو فایل قبلی
from persian_text_pipeline import PersianTextPipeline, ProcessingResult, ChangeType, ChangeLogItemSchema
from llm_editor_agent import app as graph_app  # فرض بر این است که نام فایل گراف شما llm_editor_agent.py است

# ====================================================================
# ۱. تعریف مدل‌های ورودی (Request DTOs)
# ====================================================================
class InputBlock(BaseModel):
    id: int
    order_index: int
    raw_text: str
    normalized_text: Optional[str] = None
    block_type: Optional[str] = "paragraph"
    heading_level: Optional[int] = None
    parent_heading: Optional[Dict[str, Any]] = None

class DocumentReviewRequest(BaseModel):
    document_id: int
    review_job_id: int
    blocks: List[InputBlock]
    model_name: Optional[str] = "qwen2.5:latest"  # امکان تغییر مدل از طریق API
    batch_size: Optional[int] = 4

# ====================================================================
# ۲. تعریف مدل‌های خروجی (Response DTOs)
# ====================================================================
class IssueItem(BaseModel):
    issue_code: str
    title: str
    description: str
    severity: str
    start_offset: int
    end_offset: int
    suggestion_text: str

class BlockReviewResult(BaseModel):
    block_id: int
    suggested_text: str
    suggested_block_type: Optional[str] = "paragraph"
    suggested_heading_level: Optional[int] = None
    issues: List[IssueItem] = Field(default_factory=list)

class DocumentReviewResponse(BaseModel):
    document_id: int
    review_job_id: int
    results: List[BlockReviewResult] = Field(default_factory=list)

# ====================================================================
# ۳. راه‌اندازی FastAPI و متدهای کمکی
# ====================================================================
app = FastAPI(title="Persian AI Proofreader API")

# اجرای پایپ‌لاین در زمان لود شدن سرور (فقط یک بار انجام می‌شود تا سریع باشد)
pipeline = PersianTextPipeline()

def map_change_type_to_issue_code(change_type: Any) -> str:
    """تبدیل انواع خطای سیستم ما به کدهای استاندارد بک‌اند"""
    ctype_str = change_type.value if hasattr(change_type, 'value') else str(change_type)
    mapping = {
        "MECHANICAL_NORM": "formatting",
        "SUGGESTED_FIX": "half_space",
        "SUSPECT_TYPO": "spelling",
        "AMBIGUOUS": "ambiguity"
    }
    return mapping.get(ctype_str, "general")

def convert_log_to_issue(log: ChangeLogItemSchema) -> IssueItem:
    """تبدیل لاگ پایپ‌لاین به فرمت Issue استاندارد بک‌اند"""
    # استفاده از انتخاب LLM در صورت وجود، وگرنه استفاده از اصلاحیه مکانیکی
    chosen_fix = log.llm_choice if log.llm_choice is not None else log.modified_segment
    issue_code = map_change_type_to_issue_code(log.change_type)
    severity = "info" if log.change_type == ChangeType.MECHANICAL_NORM else "warning"

    return IssueItem(
        issue_code=issue_code,
        title=log.category_title,
        description=f"Change suggested: '{log.original_segment}' -> '{chosen_fix}'",
        severity=severity,
        start_offset=log.start_char,
        end_offset=log.end_char,
        suggestion_text=chosen_fix
    )

# ====================================================================
# ۴. اندپوینت اصلی پردازش (API Endpoint)
# ====================================================================
@app.post("/api/v1/review", response_model=DocumentReviewResponse)
async def review_document(request: DocumentReviewRequest):
    try:
        response_results: List[BlockReviewResult] = []

        # پردازش بلوک به بلوک
        for block in request.blocks:
            if not block.raw_text.strip():
                continue

            # الف) پردازش اولیه
            base_result: ProcessingResult = pipeline.process_text(block.raw_text)

            # ب) اجرای گراف LangGraph
            initial_state = {
                "pipeline_result": base_result,
                "pending_indices": [],
                "batch_size": request.batch_size,
                "model_name": request.model_name
            }

            # چون گراف را با ainvoke اجرا می‌کنیم، سرور بلاک نمی‌شود
            final_state = await graph_app.ainvoke(initial_state)
            processed_result: ProcessingResult = final_state["pipeline_result"]

            # ج) ساختن لیست Issues
            issues_list: List[IssueItem] = [
                convert_log_to_issue(log) for log in processed_result.change_logs
            ]

            # د) ساختن خروجی نهایی بلوک
            block_res = BlockReviewResult(
                block_id=block.id,
                suggested_text=processed_result.corrected_text,
                suggested_block_type=block.block_type,
                suggested_heading_level=block.heading_level,
                issues=issues_list
            )
            response_results.append(block_res)

        # بازگرداندن پاسخ نهایی به فرمت درخواستی شما
        return DocumentReviewResponse(
            document_id=request.document_id,
            review_job_id=request.review_job_id,
            results=response_results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Processing Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)