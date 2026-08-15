# Team Responsibilities

## Product Owner and Product Designer — Amirhossein Amin Moghaddam

Primary responsibilities:

- Product scope
- User flow
- UX research
- Homepage design
- Design review
- Acceptance criteria
- Demo storyline
- Final product acceptance

Primary Phase 1 branch:

```text
feat/home-page
```

Primary ownership:

```text
apps/frontend/src/pages/HomePage.tsx
apps/frontend/src/components/home/
apps/frontend/src/components/layout/
apps/frontend/src/assets/home/
apps/frontend/src/styles/
docs/product/
```

## Frontend and Database — Alireza Bagherzadeh

Primary responsibilities:

- Frontend architecture
- Editor UI
- API integration
- UI state management
- Initial database modeling support

Primary Phase 1 branches:

```text
feat/editor-shell
feat/frontend-api-integration
feat/document-data-models
```

Primary ownership:

```text
apps/frontend/src/features/editor/
apps/frontend/src/pages/EditorPage.tsx
apps/frontend/src/services/
apps/frontend/src/types/
apps/backend/editor/models.py
apps/backend/editor/migrations/
```

## Backend Lead — Nima Jamal-Doust

Primary responsibilities:

- Django architecture
- DRF API
- Validation
- Backend service layer
- Error handling
- Backend tests
- Deployment support

Primary Phase 1 branch:

```text
feat/editor-analysis-api
```

Primary ownership:

```text
apps/backend/config/
apps/backend/core/
apps/backend/editor/api/
apps/backend/editor/services/
```

## AI Lead — Mostafa Ahmadi

Primary responsibilities:

- AI input/output definition
- Adapter implementation
- Prompt design
- Rule-based and AI evaluation
- Demo fallback dataset
- Future fine-tuning plan

Primary Phase 1 branch:

```text
feat/ai-demo-adapter
```

Primary ownership:

```text
apps/backend/editor/ai/
apps/backend/editor/services/suggestion_service.py
docs/architecture/api-contract.md
AI evaluation fixtures
```

## Visual and AI Asset Support — Mr. Shahi

Primary responsibilities:

- Product visual identity
- Illustrations
- Image-generation support
- Presentation assets
- Visual consistency review

Primary Phase 1 branch when assets are committed:

```text
feat/home-visual-assets
```

Primary ownership:

```text
apps/frontend/src/assets/
Presentation assets
```

## Coordination Rules

- One accountable owner per Trello card.
- Cross-module changes require coordination before coding.
- API contract changes require frontend and backend approval.
- Visual changes require product design review.
- AI-generated code and assets require human review.
- Blockers must be reported on the same working day.
