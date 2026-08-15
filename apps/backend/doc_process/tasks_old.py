# from doc_process.models import Document
# from doc_process.services.document_pipeline import DocumentPipelineService
# import logging
# from django.db import transaction
# from django.utils import timezone
# from .models import Document, DocumentBlock, ReviewJob, BlockIssue
# from .services.llm_review import LlmReviewService

# logger = logging.getLogger(__name__)

# def run_document_parsing_task(document_id: int):
#     print("starting the task")
#     # Fetch the document and process it in the background
#     try:
#         document = Document.objects.get(id=document_id)
#         document.status = Document.Status.REVIEWING
#         document.processing_error = ""
#         document.save(update_fields=["status", "processing_error"])

#         pipeline = DocumentPipelineService()
#         pipeline.parse_document(document)

#         document.status = Document.Status.PARSED
#         document.save(update_fields=["status"])

#         return f"Document {document_id} parsed successfully."

#     except Document.DoesNotExist:
#         return f"Document {document_id} does not exist."

#     except Exception as exc:
#         try:
#             document = Document.objects.get(id=document_id)
#             document.status = Document.Status.FAILED
#             document.processing_error = str(exc)
#             document.save(update_fields=["status", "processing_error"])
#         except Exception:
#             pass

#         raise


# def run_document_review_job_task(review_job_id: int):
#     """
#     تسک ناهمگام جهت پردازش و ارزیابی نگارشی سند با استفاده از مدل gpt-5.6-sol.
#     این تسک وضعیت‌های ReviewJob و Document را مدیریت می‌کند و رکوردها را به صورت فله‌ای ثبت می‌نماید.
#     """
#     try:
#         review_job = ReviewJob.objects.get(id=review_job_id)
#     except ReviewJob.DoesNotExist:
#         print(f"ReviewJob with ID {review_job_id} not found.")
#         return

#     document = review_job.document
    
#     # تغییر وضعیت به حالت در حال پردازش
#     review_job.status = ReviewJob.Status.RUNNING
#     review_job.started_at = timezone.now()
#     review_job.model_name = "gpt-5.6-sol"
#     review_job.save(update_fields=["status", "started_at", "model_name"])

#     document.status = Document.Status.REVIEWING
#     document.save(update_fields=["status"])

#     llm_service = LlmReviewService()
#     issues_to_create = []
    
#     # واکشی بلوک‌های پاراگراف و سربرگ (Heading) به ترتیب مشخص شده در فایل اصلی
#     blocks = DocumentBlock.objects.filter(
#         document=document,
#         block_type__in=[DocumentBlock.BlockType.PARAGRAPH, DocumentBlock.BlockType.HEADING]
#     ).order_by("order_index")

#     request_payload_log = []
#     response_payload_log = []

#     try:
#         for block in blocks:
#             # استفاده از متن نرمالایز شده (اولویت اول) یا متن خام بلوک
#             text_to_analyze = block.normalized_text if block.normalized_text else block.raw_text
#             if not text_to_analyze.strip():
#                 continue

#             # ذخیره‌سازی داده‌های ارسالی برای ثبت در تاریخچه Payload
#             request_payload_log.append({
#                 "block_id": block.id,
#                 "text": text_to_analyze
#             })

#             # ارسال به GapGPT
#             analysis_results = llm_service.analyze_block(text_to_analyze)

#             # ثبت پاسخ خام بازگشتی از مدل
#             response_payload_log.append({
#                 "block_id": block.id,
#                 "results": analysis_results
#             })

#             # تشکیل شیءهای مدل بدون ذخیره‌سازی تکی در دیتابیس
#             for result in analysis_results:
#                 issue = BlockIssue(
#                     document=document,
#                     block=block,
#                     review_job=review_job,
#                     issue_code=result["issue_code"],
#                     title=result["title"],
#                     description=result["description"],
#                     severity=result["severity"],
#                     start_offset=result["start_offset"],
#                     end_offset=result["end_offset"],
#                     suggestion_text=result["suggestion_text"],
#                     extra_data=result["extra_data"]
#                 )
#                 issues_to_create.append(issue)

#         # اجرای عملیات نهایی در بستر تراکنش اتمیک
#         with transaction.atomic():
#             # در صورت نیاز به حذف رکوردهای قبلی همین سند، خط زیر را فعال کنید:
#             # BlockIssue.objects.filter(document=document).delete()
            
#             # ذخیره‌سازی دسته‌ای همه‌ی ایرادات یافته شده در یک کوئری
#             if issues_to_create:
#                 BlockIssue.objects.bulk_create(issues_to_create)

#             # به‌روزرسانی اطلاعات نهایی جاب
#             review_job.status = ReviewJob.Status.SUCCEEDED
#             review_job.finished_at = timezone.now()
#             review_job.request_payload = {"blocks": request_payload_log}
#             review_job.response_payload = {"analysis": response_payload_log}
#             review_job.save(update_fields=["status", "finished_at", "request_payload", "response_payload"])

#             # به‌روزرسانی سند به وضعیت Reviewed
#             document.status = Document.Status.REVIEWED
#             document.save(update_fields=["status"])
            
#             logger.info(f"ReviewJob {review_job_id} successfully completed for Doc {document.id}")

#     except Exception as exc:
#         error_msg = f"Failed executing review job: {str(exc)}"
#         logger.error(error_msg, exc_info=True)
        
#         # ثبت خطای رخ داده در سیستم و تغییر وضعیت به FAILED
#         review_job.status = ReviewJob.Status.FAILED
#         review_job.finished_at = timezone.now()
#         review_job.error_message = error_msg
#         review_job.request_payload = {"blocks": request_payload_log}
#         review_job.save(update_fields=["status", "finished_at", "error_message", "request_payload"])

#         document.status = Document.Status.FAILED
#         document.processing_error = error_msg
#         document.save(update_fields=["status", "processing_error"])