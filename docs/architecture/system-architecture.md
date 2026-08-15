# System Architecture

## 1. Purpose

This document defines the Phase 1 architecture of the Intelligent Book Editor.

The Phase 1 architecture is intentionally modular but lightweight. It must support fast demo development without locking the team into a prototype-only structure.

## 2. Architectural Goals

- Deliver a stable investor-facing demo within a 10-day sprint.
- Keep frontend, backend, and AI concerns clearly separated.
- Allow frontend and backend development to proceed in parallel.
- Preserve the ability to replace mock or rule-based analysis with an LLM/SLM later.
- Keep the primary demo flow functional when an external AI provider is unavailable.
- Avoid premature microservices and unnecessary infrastructure.

## 3. Repository Model

The project uses a monorepo:

```text
intelligent-book-editor/
├── apps/
│   ├── frontend/
│   └── backend/
├── docs/
├── .github/
├── .gitignore
└── README.md
```

## 4. High-Level Architecture

```text
┌──────────────────────────────────────────┐
│ React + TypeScript + Vite                │
│ Home / Editor / Suggestions / Preview    │
└────────────────────┬─────────────────────┘
                     │ HTTPS / JSON REST API
┌────────────────────▼─────────────────────┐
│ Django + Django REST Framework           │
│ Validation / Orchestration / API         │
└───────────────┬───────────────┬──────────┘
                │               │
┌───────────────▼───────┐ ┌─────▼─────────────────┐
│ Domain Services       │ │ Persistence Layer      │
│ Normalize / Analyze   │ │ SQLite local           │
│ Suggest / Preview     │ │ PostgreSQL staging     │
└───────────────┬───────┘ └───────────────────────┘
                │
┌───────────────▼───────────────────────────┐
│ AI Adapter Layer                          │
│ Mock / Rule Engine / External LLM / SLM   │
└───────────────────────────────────────────┘
```

## 5. Frontend Responsibilities

The frontend is responsible for:

- Product homepage
- Editor interface
- Input and result presentation
- Suggestion accept/reject interaction
- Loading, success, empty, and error states
- Book-page preview
- Client-side validation for usability
- API communication through a dedicated service layer

The frontend must not contain the authoritative text-processing rules.

## 6. Backend Responsibilities

The backend is responsible for:

- API validation
- Text-processing orchestration
- Rule-based normalization
- AI adapter execution
- Suggestion generation
- Stable response contracts
- Document and analysis persistence
- Logging and error handling
- Future authentication and permissions

## 7. AI Integration Strategy

AI integration must use an adapter boundary.

```text
Editor API
   ↓
Analysis Service
   ↓
AI Adapter Interface
   ├── MockAnalysisAdapter
   ├── RuleBasedAnalysisAdapter
   ├── ExternalLLMAdapter
   └── FineTunedModelAdapter
```

Phase 1 uses Mock and rule-based implementations first. The API response format must remain stable when the underlying implementation changes.

## 8. Data Strategy

### Local Development

- SQLite is acceptable for local development.
- Local database files must not be committed.

### Shared Demo or Staging

- PostgreSQL is the preferred shared database.
- Environment-specific credentials must be supplied through environment variables.

### Initial Domain Entities

- `Document`
- `Analysis`
- `Suggestion`
- `DocumentVersion` — optional for late Phase 1 or Phase 2

## 9. API Strategy

- Base path: `/api/v1/`
- JSON request and response bodies
- Explicit validation through DRF serializers
- Predictable error format
- No breaking changes inside `/api/v1/` without team approval
- Frontend must consume API types from a central TypeScript module

## 10. Reliability Strategy

The investor demo must not depend on a live external model.

Required fallback order:

1. Real AI adapter, when configured and healthy
2. Rule-based analysis
3. Deterministic mock response for the predefined demo text

## 11. Security Boundaries for Phase 1

- No API keys in source control
- No unpublished confidential book content in public AI services
- CORS restricted to known development and deployment origins
- Upload size limits must be defined before file upload is enabled
- Only TXT input is required initially; DOCX can be introduced after validation
- Authentication is outside the first demo scope unless explicitly approved

## 12. Deployment Model

### Frontend

- Static Vite build
- Deployable to a static hosting platform

### Backend

- Django ASGI or WSGI application
- Environment-based configuration
- Separate development and production settings before public deployment

### Required Environments

- Local
- Demo/Staging
- Production — outside the initial sprint unless required

## 13. Architecture Decision Rules

Create an Architecture Decision Record when a decision:

- Changes the API contract
- Adds a new framework or major dependency
- Introduces a new Django app
- Changes persistence technology
- Changes the AI integration boundary
- Affects deployment or security

## 14. Out of Scope for Phase 1

- Full multi-user collaboration
- Complex role-based access control
- Billing
- Fine-tuning pipeline inside the application
- High-volume asynchronous processing
- Complete PDF or InDesign support
- Full publishing workflow management
- Microservice decomposition
