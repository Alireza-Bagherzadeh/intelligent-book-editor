# اصلاح V2 - حذف Queue از Parsing اولیه

در این نسخه مرحله‌ی parsing اولیه‌ی فایل DOCX/متن خام دیگر به Vercel Queue وابسته نیست.

مسیر جدید:

Upload -> save Document -> DocumentPipelineService.parse_document() -> PARSED -> response 201

اگر parsing شکست بخورد، Pipeline وضعیت FAILED و processing_error را ذخیره می‌کند و endpoint پاسخ 422 می‌دهد.

Queue فقط برای مراحل بعدی review / block differences / AI باقی مانده است.

هدف این تغییر این است که UI دیگر به خاطر اجرا نشدن subscriber روی status=uploaded گیر نکند.
