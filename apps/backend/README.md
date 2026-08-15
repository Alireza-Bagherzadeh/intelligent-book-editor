# AI Publisher Backend

Django backend for uploading DOCX manuscripts, extracting ordered document blocks, normalizing Persian text, preserving source formatting metadata, building heading relationships, and running asynchronous review jobs.

---

# English Guide

## 1. Main workflow

```text
DOCX upload
   ↓
Document record (status: uploaded)
   ↓
DOCX parsing and block extraction
   ↓
Text normalization + block classification
   ↓
DocumentBlock records and heading hierarchy
   ↓
Document status: parsed
   ↓
ReviewJob queued in Django Q
   ↓
ReviewJob: pending → running → succeeded/failed
   ↓
BlockIssue records returned to the frontend
```

The parser preserves both the original text and the normalized text. It also classifies each extracted item as a `heading`, `paragraph`, or `table_cell` and connects blocks to their nearest parent heading.

## 2. Local setup

### Requirements

- Python 3.x
- The project database and required services configured in Django settings
- A Django Q broker configured for asynchronous jobs

### Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create the environment file expected by the project, for example `.env`, and set the database, Django secret key, allowed hosts, AI service credentials, and Django Q broker settings required by your local environment.

Do not commit real secrets to Git.

### Apply migrations

```bash
python manage.py migrate
```

If needed, create an admin user:

```bash
python manage.py createsuperuser
```

## 3. Run the project

Two terminals must normally remain open.

### Terminal 1 — Django API server

```bash
python manage.py runserver
```

Default development address:

```text
http://127.0.0.1:8000/
```

### Terminal 2 — Django Q worker

Activate the same virtual environment, move to the backend directory, and run:

```bash
python manage.py qcluster
```

The `qcluster` process executes queued background tasks such as document review. If only `runserver` is running, API requests can still create queued jobs, but asynchronous jobs may remain in `pending` and will not be processed.

> Keep both `runserver` and `qcluster` running while testing the complete pipeline.

## 4. Processing states

### Document status

| Status | Meaning |
|---|---|
| `uploaded` | The source file has been uploaded and the document record exists. |
| `parsed` | DOCX parsing completed and its blocks were stored successfully. |
| `reviewing` | The document is currently in the review stage. |
| `reviewed` | Review completed successfully. |
| `failed` | Parsing or review failed; inspect `processing_error`. |

The current model does **not** define a `parsing` status. Therefore, code should not save `"parsing"` unless that choice is deliberately added through a model change and migration. With the current choices, a document may remain `uploaded` while parsing is in progress and then become `parsed`.

### Review job status

| Status | Meaning |
|---|---|
| `pending` | The job has been created and is waiting for `qcluster`. |
| `running` | A worker is processing the job. |
| `succeeded` | The review completed successfully. |
| `failed` | The review failed; inspect `error_message`. |

`request_payload` preserves the data sent to the review service, while `response_payload` preserves its raw response.

## 5. Important `DocumentBlock` fields

A document is represented as an ordered list of blocks. The frontend should sort blocks by `order_index` and use the classification and hierarchy fields to render the manuscript.

### Fields required for frontend structure

| Field | Purpose |
|---|---|
| `id` | Unique block ID. It is also referenced by `parent_heading`. |
| `order_index` | Original logical order of the block. Always sort ascending by this field. |
| `block_type` | Current usable classification: `heading`, `paragraph`, or `table_cell`. |
| `heading_level` | Heading depth such as `1`, `2`, or `3`; normally `null` for non-heading blocks. |
| `parent_heading` | ID of the heading that owns the block; `null` means that the block is at the root level. |
| `normalized_text` | Cleaned text intended for display, review, issue offsets, and later processing. |
| `is_rtl` | Indicates right-to-left text rendering. |
| `alignment` | Source paragraph alignment information. |
| `issues` / `issues_count` | Review findings associated with the block. |

The three essential hierarchy fields are:

```text
block_type + heading_level + parent_heading
```

Example interpretation:

- Block `739`: `heading`, level `1`, no parent → a root H1 heading.
- Block `740`: `paragraph`, parent `739` → body text under heading 739.
- Block `741`: `heading`, level `1`, no parent → another root H1 heading.
- Block `742`: `paragraph`, parent `741` → body text under heading 741.

A simple frontend type can be defined as:

```ts
type DocumentBlock = {
  id: number;
  order_index: number;
  block_type: "heading" | "paragraph" | "table_cell";
  heading_level: number | null;
  parent_heading: number | null;
  raw_text: string;
  normalized_text: string;
  is_rtl: boolean;
  alignment: string;
  issues_count: number;
  issues: BlockIssue[];
};
```

Recommended rendering rules:

1. Sort all blocks by `order_index`.
2. Use `block_type` to select the component.
3. For headings, use `heading_level` to select the visual level.
4. Use `parent_heading` to create a tree, section grouping, indentation, or collapsible navigation.
5. Display `normalized_text` by default, while keeping `raw_text` available for comparison or debugging.
6. Use `id` as the React key—not `order_index`.

## 6. Original source data vs. processed data

### Original/source-oriented fields

These fields preserve text or location information obtained from the uploaded Word file:

- `raw_text`: original extracted text before normalization.
- `style_name`: Word paragraph style, such as `Normal` or `Heading 1`.
- `paragraph_index`: source paragraph position.
- `table_index`, `row_index`, `cell_index`, `cell_paragraph_index`: original table location.
- `source_path`: server-side path of the stored source file; it should normally not be displayed to end users.
- `format_metadata.raw_style_name`: original Word style name.
- `format_metadata.semantic_heading_level`: heading level inferred directly from Word style/outline semantics.
- `format_metadata.pagination`: source pagination properties such as `keep_together`, `keep_with_next`, and `widow_control`.

`source_path` is internal backend information and may expose server filesystem details. Prefer omitting it from public API serializers unless the frontend genuinely requires it.

### Processed/current usable fields

These fields represent the parser's current result and should be used by the application:

- `normalized_text`: normalized Persian text.
- `block_type`: current parser classification.
- `heading_level`: current usable heading level.
- `parent_heading`: computed hierarchy relationship.
- `order_index`: stable display order.
- `is_heading`: convenience value derived from `block_type`.
- `has_children`: indicates whether another block references this heading.
- `issues` and `issues_count`: review results.

### Current `format_metadata`

The current API response uses a flat metadata structure:

```json
{
  "bold_ratio": 1.0,
  "max_font_size": 22.0,
  "text_length": 35,
  "raw_style_name": "Normal",
  "semantic_heading_level": null,
  "was_reclassified": false,
  "pagination": {
    "keep_together": null,
    "keep_with_next": null,
    "widow_control": null
  }
}
```

Important values:

- `bold_ratio`: proportion of bold text used by classification heuristics.
- `max_font_size`: largest detected font size in the block.
- `text_length`: extracted text length.
- `raw_style_name`: style read from Word.
- `semantic_heading_level`: level detected from Word semantics, before heuristic correction.
- `was_reclassified`: whether parser heuristics changed the initial semantic classification.
- `pagination`: original Word paragraph pagination settings.

For example, a paragraph can have `style_name: "Heading 1"` and `semantic_heading_level: 1`, but the parser may identify it as long body text. In that case, its usable values become:

```json
{
  "block_type": "paragraph",
  "heading_level": null,
  "was_reclassified": true
}
```

The frontend must therefore use the top-level `block_type`, `heading_level`, and `parent_heading` fields—not `style_name` or `semantic_heading_level`—for the current document structure.

> The proposed nested provenance structure (`source_format`, `parser_classification`, `ai_classification`, and `current_classification`) is not active yet and is intentionally not assumed in the current frontend contract.

## 7. Text and issue behavior

- `raw_text` is retained for traceability.
- `normalized_text` is the operational text used after normalization.
- `BlockIssue.start_offset` and `end_offset` are based on `normalized_text`, not `raw_text`.
- The issue range uses the half-open convention `[start_offset, end_offset)`.
- Replacing the normalized text without recalculating issue offsets can make highlights incorrect.

## 8. Main database entities

- `Document`: uploaded file, document metadata, and overall processing state.
- `DocumentBlock`: ordered text/heading/table units extracted from the document.
- `ReviewJob`: asynchronous review execution and request/response audit data.
- `BlockIssue`: spelling, grammar, style, punctuation, or optimization issue attached to a block.

## 9. Common development checks

```bash
python manage.py check
python manage.py showmigrations
python manage.py test
```

If background jobs stay in `pending`:

1. Confirm that the second terminal is running `python manage.py qcluster`.
2. Check the Django Q broker configuration.
3. Check the `qcluster` terminal logs.
4. Inspect `ReviewJob.error_message` and Django logs.

---

# راهنمای فارسی

## ۱. روند اصلی سامانه

```text
آپلود فایل DOCX
   ↓
ساخت Document با وضعیت uploaded
   ↓
Parse فایل و استخراج بلاک‌ها
   ↓
نرمال‌سازی متن و تشخیص نوع بلاک
   ↓
ذخیره DocumentBlockها و رابطه عنوان‌ها
   ↓
تغییر وضعیت Document به parsed
   ↓
قرار گرفتن ReviewJob در صف Django Q
   ↓
pending → running → succeeded/failed
   ↓
ساخت BlockIssue و ارسال نتایج به فرانت‌اند
```

سامانه متن اصلی و متن نرمال‌شده را هم‌زمان نگه می‌دارد. Parser هر بخش را به یکی از انواع `heading`، `paragraph` یا `table_cell` تبدیل می‌کند و رابطه هر بلاک با عنوان والد را می‌سازد.

## ۲. راه‌اندازی محلی

ساخت و فعال‌کردن محیط مجازی در PowerShell ویندوز:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

نصب وابستگی‌ها و اجرای migrationها:

```bash
pip install -r requirements.txt
python manage.py migrate
```

متغیرهای محیطی پروژه، تنظیمات دیتابیس، کلیدهای سرویس AI و broker مربوط به Django Q را مطابق محیط توسعه تنظیم کنید. اطلاعات محرمانه را در Git قرار ندهید.

## ۳. اجرای پروژه در دو ترمینال

### ترمینال اول — سرور Django

```bash
python manage.py runserver
```

### ترمینال دوم — پردازشگر Django Q

در همان محیط مجازی و پوشه backend اجرا کنید:

```bash
python manage.py qcluster
```

وجود ترمینال دوم ضروری است. `qcluster` کارهای پس‌زمینه مانند Review را از صف دریافت می‌کند. اگر فقط `runserver` فعال باشد، ممکن است Job ساخته شود اما در وضعیت `pending` باقی بماند.

## ۴. وضعیت‌های پردازش

### وضعیت Document

| وضعیت | مفهوم |
|---|---|
| `uploaded` | فایل آپلود و رکورد سند ساخته شده است. |
| `parsed` | Parse فایل و ذخیره بلاک‌ها با موفقیت تمام شده است. |
| `reviewing` | سند در مرحله بررسی قرار دارد. |
| `reviewed` | بررسی سند کامل شده است. |
| `failed` | Parse یا Review شکست خورده است؛ `processing_error` بررسی شود. |

در مدل فعلی وضعیت `parsing` تعریف نشده است. بنابراین تا زمانی که این مقدار به مدل اضافه نشده و migration اجرا نشده، نباید `"parsing"` ذخیره شود. سند می‌تواند هنگام Parse همچنان `uploaded` باشد و پس از موفقیت به `parsed` تغییر کند.

### وضعیت ReviewJob

| وضعیت | مفهوم |
|---|---|
| `pending` | Job ساخته شده و منتظر `qcluster` است. |
| `running` | Worker در حال اجرای Job است. |
| `succeeded` | Review موفق بوده است. |
| `failed` | Review شکست خورده و `error_message` باید بررسی شود. |

## ۵. فیلدهای مهم برای فرانت‌اند

فرانت‌اند باید بلاک‌ها را با `order_index` مرتب کند. برای نمایش ساختار سند، سه فیلد اصلی عبارت‌اند از:

```text
block_type + heading_level + parent_heading
```

- `block_type`: نوع فعلی و قابل استفاده بلاک؛ یعنی `heading`، `paragraph` یا `table_cell`.
- `heading_level`: سطح عنوان؛ برای مثال 1 برای H1 و 2 برای H2. برای متن عادی معمولاً `null` است.
- `parent_heading`: شناسه عنوان والد. مقدار `null` یعنی بلاک در سطح ریشه قرار دارد.
- `order_index`: ترتیب نمایش بلاک در سند.
- `normalized_text`: متن مناسب نمایش و پردازش.
- `id`: شناسه بلاک و مقدار مناسب برای React key.
- `is_rtl`: برای تنظیم نمایش راست‌به‌چپ.
- `issues` و `issues_count`: خطاها و پیشنهادهای Review.

در نمونه پاسخ:

- بلاک `739` یک Heading سطح 1 و ریشه است.
- بلاک `740` یک Paragraph زیر عنوان `739` است.
- بلاک `741` یک Heading سطح 1 جدید و ریشه است.
- بلاک `742` یک Paragraph زیر عنوان `741` است.

قواعد پیشنهادی فرانت‌اند:

1. مرتب‌سازی صعودی با `order_index`.
2. انتخاب کامپوننت بر اساس `block_type`.
3. نمایش سطح عنوان بر اساس `heading_level`.
4. ساخت درخت، گروه‌بندی یا منوی جمع‌شونده با `parent_heading`.
5. نمایش پیش‌فرض `normalized_text` و نگهداری `raw_text` فقط برای مقایسه یا Debug.
6. استفاده از `id` به‌عنوان React key.

## ۶. داده اصلی Word و داده پردازش‌شده

### فیلدهای مربوط به فایل اصلی

- `raw_text`: متن استخراج‌شده پیش از نرمال‌سازی.
- `style_name`: استایل اصلی Word مانند `Normal` یا `Heading 1`.
- `paragraph_index`: موقعیت پاراگراف در فایل اصلی.
- `table_index`، `row_index`، `cell_index` و `cell_paragraph_index`: موقعیت در جدول.
- `source_path`: مسیر داخلی فایل روی سرور؛ بهتر است بدون نیاز واقعی به کاربر نهایی نمایش داده نشود.
- `format_metadata.raw_style_name`: استایل خام Word.
- `format_metadata.semantic_heading_level`: سطح عنوان تشخیص‌داده‌شده از semantics یا style فایل Word.
- `format_metadata.pagination`: تنظیمات صفحه‌بندی اصلی Word.

### فیلدهای فعلی و قابل استفاده

- `normalized_text`: متن پس از نرمال‌سازی.
- `block_type`: نتیجه فعلی Parser.
- `heading_level`: سطح فعلی و قابل استفاده عنوان.
- `parent_heading`: رابطه ساختاری محاسبه‌شده.
- `order_index`: ترتیب نمایش.
- `is_heading` و `has_children`: مقادیر کمکی برای UI.
- `issues` و `issues_count`: نتایج Review.

ممکن است یک پاراگراف در Word دارای استایل `Heading 1` باشد، اما Parser به‌دلیل طولانی و بدنه‌بودن متن آن را مجدداً به `paragraph` طبقه‌بندی کند. در این حالت:

```json
{
  "style_name": "Heading 1",
  "block_type": "paragraph",
  "heading_level": null,
  "format_metadata": {
    "semantic_heading_level": 1,
    "was_reclassified": true
  }
}
```

بنابراین فرانت‌اند برای ساختار فعلی باید از `block_type`، `heading_level` و `parent_heading` استفاده کند، نه از `style_name` یا `semantic_heading_level`.

ساختار توسعه‌یافته metadata شامل `source_format`، `parser_classification`، `ai_classification` و `current_classification` هنوز اعمال نشده است و فعلاً بخشی از قرارداد API نیست.

## ۷. نکات Review و Offsetها

- `raw_text` برای حفظ سابقه و مقایسه نگهداری می‌شود.
- `normalized_text` متن عملیاتی سیستم است.
- `start_offset` و `end_offset` در `BlockIssue` بر اساس `normalized_text` محاسبه می‌شوند.
- بازه خطا به‌صورت `[start_offset, end_offset)` است.
- اگر متن نرمال‌شده تغییر کند، offsetهای قبلی ممکن است دیگر معتبر نباشند.

## ۸. مدل‌های اصلی

- `Document`: فایل، metadata و وضعیت کلی پردازش.
- `DocumentBlock`: بخش‌های مرتب‌شده سند و سلسله‌مراتب عنوان‌ها.
- `ReviewJob`: اجرای غیرهم‌زمان Review و ثبت payloadهای درخواست و پاسخ.
- `BlockIssue`: خطاهای املایی، دستوری، نگارشی، سبکی یا بهینه‌سازی مربوط به هر بلاک.

## ۹. رفع مشکل Jobهای صف

اگر Job در `pending` باقی ماند:

1. بررسی کنید `python manage.py qcluster` در ترمینال دوم فعال باشد.
2. تنظیمات broker مربوط به Django Q را بررسی کنید.
3. لاگ ترمینال `qcluster` را ببینید.
4. `ReviewJob.error_message` و لاگ Django را بررسی کنید.
