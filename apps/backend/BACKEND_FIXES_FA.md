# نسخه اصلاح‌شده Backend — Intelligent Book Editor

این بسته بر اساس Backend ارسالی شما اصلاح شده است. هدف اصلی این نسخه این است که:

- اجرای لوکال قبلی حفظ شود: **SQLite + FileField + Django-Q2**.
- اجرای Vercel از **PostgreSQL + BinaryField + Vercel Queues** استفاده کند.
- Celery و callbackهای قبلی که باعث `AppRegistryNotReady` و `Celery task not found` می‌شدند از runtime حذف شوند.

## معماری Queue نهایی

### Local

```text
APIView -> enqueue_task -> Django-Q2 -> qcluster -> doc_process.tasks.*
```

دستور اجرا:

```powershell
python manage.py runserver
```

در ترمینال دوم:

```powershell
python manage.py qcluster
```

### Vercel

```text
APIView
  -> enqueue_task
  -> vercel.workers.send("default", payload)
  -> Vercel Queue
  -> doc_process.vercel_worker.process_message
  -> doc_process.tasks.*
```

Subscriber در `pyproject.toml` تعریف شده و دیگر از Celery استفاده نمی‌شود.

> در Deployment جدید وجود یک Function با مسیر `_py_subscribers/...` طبیعی است؛ این بار subscriber عمومی Vercel Queue است، نه Celery worker قدیمی.

## فایل‌های Queue که باید وجود داشته باشند

```text
doc_process/task_queue.py
doc_process/vercel_worker.py
```

و این فایل‌های legacy عمداً حذف شده‌اند:

```text
worker.py
config/celery.py
doc_process/vercel_tasks.py
doc_process/vercel_django_tasks.py
api/queue/callback.py
```

## Environment Variables برای Vercel Production

حداقل:

```text
DATABASE_URL=<Neon/PostgreSQL connection URL>
DEBUG=False
SECRET_KEY=<strong production secret>
FILE_STORAGE_BACKEND=database
TASK_BACKEND=vercel
CORS_ALLOWED_ORIGINS=https://intelligent-book-editor.vercel.app
```

برای AI review نیز:

```text
GEMINI_API_KEY=<key>
GEMINI_MODEL=<model configured for your account>
```

اگر Gemini تنظیم نشده باشد، Upload، Parse، local normalization و block differences همچنان کار می‌کنند؛ فقط AI review خودکار enqueue نمی‌شود.

## قبل از Push

از `apps/backend`:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

سپس:

```powershell
git status
git add .
git commit -m "Fix Vercel queue and document processing pipeline"
git push
```

## بعد از Deploy

در Build Log باید migration بدون خطا اجرا شود.

در Deployment -> Functions باید:

- Django web function وجود داشته باشد.
- یک `_py_subscribers/...` مربوط به `doc_process.vercel_worker:process_message` وجود داشته باشد.
- subscriber قدیمی Celery (`worker:app` روی topic `celery`) دیگر وجود نداشته باشد.

بعد یک **Document جدید** آپلود کنید. اسناد قدیمی که task آن‌ها قبلاً fail شده خودکار دوباره enqueue نمی‌شوند.

## اصلاحات مهم دیگر

- تعریف تکراری `FILE_STORAGE_BACKEND` حذف شد.
- `DEBUG` روی Vercel به‌صورت پیش‌فرض False است.
- `GEMINI_API_KEY` دیگر startup کل Django را متوقف نمی‌کند.
- `MEDIA_ROOT` برای لوکال تعریف شد.
- `trigger_document_review` دیگر مستقیم `async_task()` صدا نمی‌زند.
- parsing task دیگر status را دوباره به `uploaded` برنمی‌گرداند.
- orchestration AI از `normal_review_service.py` خارج شد تا race condition ایجاد نشود.
- AI review بعد از پایان block differences اجرا می‌شود.
- statusهای `AI_REVIEWING` و `AI_REVIEWED` برای endpoint بلاک‌ها مجاز شدند.
- temporary DOCX در production با `tempfile` ساخته می‌شود و در Vercel به temp directory قابل‌نوشتن می‌رود.
- serializer تکراری حذف و validation ورودی DOCX/raw text اضافه شد.
- dependencyهای `vercel-workers` و `google-genai` اضافه شدند و Celery حذف شد.

## نکته درباره `.env`

فایل `.env` واقعی شما داخل ZIP قرار داده نشده تا secretها کپی/منتشر نشوند. فایل `.env.example` اضافه شده است. `.env` فعلی خودتان را نگه دارید.
