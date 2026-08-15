# Module Structure

## 1. Frontend Structure

```text
apps/frontend/src/
├── app/
│   ├── App.tsx
│   └── routes.tsx
├── assets/
├── components/
│   ├── layout/
│   ├── home/
│   ├── editor/
│   └── ui/
├── features/
│   └── editor/
│       ├── api/
│       ├── components/
│       ├── hooks/
│       ├── types/
│       └── utils/
├── pages/
│   ├── HomePage.tsx
│   └── EditorPage.tsx
├── services/
│   └── httpClient.ts
├── styles/
├── types/
└── main.tsx
```

### Frontend Module Rules

- `pages` compose complete screens.
- `components/ui` contains generic reusable components.
- `components/home` contains homepage-specific sections.
- `features/editor` contains editor domain logic.
- `services` contains shared infrastructure such as the HTTP client.
- Components must not call `fetch` directly when a feature API module exists.
- Shared types must not be duplicated across files.
- UI text may be separated into data/content files when repeated.

## 2. Backend Structure

```text
apps/backend/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── core/
│   ├── api/
│   ├── services/
│   ├── urls.py
│   └── views.py
├── editor/
│   ├── api/
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── ai/
│   │   ├── adapters.py
│   │   └── prompts.py
│   ├── services/
│   │   ├── analysis_service.py
│   │   ├── text_normalizer.py
│   │   └── suggestion_service.py
│   ├── migrations/
│   ├── models.py
│   ├── admin.py
│   └── tests/
├── manage.py
└── requirements.txt
```

### Backend Module Rules

- API views handle HTTP concerns only.
- Serializers validate and transform request/response data.
- Business logic belongs in `services`.
- AI provider details belong in `editor/ai`.
- Models define persistence, not orchestration.
- URL definitions remain versioned under `/api/v1/`.
- Avoid importing Django request objects into pure domain services.

## 3. Initial Django Apps

### `core`

Responsibilities:

- Health checks
- Shared exceptions
- Common response utilities
- Cross-cutting configuration
- Shared infrastructure that does not belong to a product domain

### `editor`

Responsibilities:

- Documents
- Text analysis
- Suggestions
- Persian normalization
- AI adapter orchestration
- Preview-related structured output

Do not create more Django apps in Phase 1 unless a separate domain boundary is clear.

## 4. Dependency Direction

Allowed:

```text
API Layer → Services → Models / AI Adapters
```

Avoid:

```text
Models → API Views
AI Adapter → React-specific structures
Frontend UI → Django implementation details
```

## 5. Ownership Boundaries

- Homepage team: `components/home`, `pages/HomePage.tsx`, homepage assets
- Editor frontend team: `features/editor`, `pages/EditorPage.tsx`
- Backend API team: `editor/api`, root API routing
- Backend domain team: `editor/services`, `editor/models.py`
- AI team: `editor/ai`, prompts, evaluation fixtures
