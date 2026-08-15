# Initial API Contract

## 1. Health Check

```http
GET /api/v1/health/
```

Response:

```json
{
  "status": "ok",
  "service": "intelligent-book-editor-api",
  "message": "Backend is running successfully."
}
```

## 2. Analyze Text

```http
POST /api/v1/editor/analyze/
Content-Type: application/json
```

Request:

```json
{
  "text": "این نرم افزار می تواند کتاب ها را سریع تر ویرایش کند .",
  "mode": "standard"
}
```

Validation Rules:

- `text` is required
- `text` must not contain only whitespace
- `mode` must be one of `light`, `standard`, or `advanced`
- Phase 1 may impose a temporary maximum text length

Success Response:

```json
{
  "analysis_id": "demo-analysis-001",
  "source": "rule_based",
  "original_text": "این نرم افزار می تواند کتاب ها را سریع تر ویرایش کند .",
  "cleaned_text": "این نرم‌افزار می‌تواند کتاب‌ها را سریع‌تر ویرایش کند.",
  "stats": {
    "total_suggestions": 5,
    "spacing": 4,
    "spelling": 0,
    "punctuation": 1,
    "style": 0
  },
  "suggestions": [
    {
      "id": "suggestion-001",
      "type": "spacing",
      "original": "نرم افزار",
      "replacement": "نرم‌افزار",
      "reason": "اصلاح نیم‌فاصله",
      "severity": "recommended",
      "start": 4,
      "end": 13
    }
  ],
  "preview": {
    "title": "پیش‌نمایش متن",
    "blocks": [
      {
        "type": "paragraph",
        "content": "این نرم‌افزار می‌تواند کتاب‌ها را سریع‌تر ویرایش کند."
      }
    ]
  }
}
```

Validation Error:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "fields": {
      "text": ["This field may not be blank."]
    }
  }
}
```

Server Error:

```json
{
  "error": {
    "code": "analysis_failed",
    "message": "Text analysis could not be completed."
  }
}
```

## 3. Contract Rules

- Fields already consumed by the frontend must not be renamed without team review.
- New optional fields may be added without breaking the contract.
- The `source` field identifies `mock`, `rule_based`, `external_llm`, or `fine_tuned_model`.
- Suggestion IDs must remain stable while the analysis result is displayed.
- Frontend types must mirror this contract.
