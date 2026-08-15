# Coding Standards

## 1. General Principles

- Optimize for readability and maintainability.
- Keep functions focused on one responsibility.
- Avoid speculative abstractions.
- Do not merge generated code without human review.
- Do not commit secrets, local databases, dependency folders, or generated build output.
- Add or update documentation when behavior or architecture changes.

## 2. Git Workflow

### Protected Branch

- `main` is stable and must not receive direct pushes.

### Branch Naming

```text
feat/home-page
feat/editor-shell
feat/editor-analysis-api
feat/document-data-models
feat/ai-demo-adapter
fix/<short-description>
docs/<short-description>
refactor/<short-description>
chore/<short-description>
```

### Commit Messages

Use Conventional Commits:

```text
feat: implement product homepage
fix: handle empty editor input
docs: add phase one architecture
refactor: extract analysis service
test: add editor API tests
chore: update frontend dependencies
```

### Pull Requests

Each PR must include:

- Summary
- Changes
- Verification
- Screenshots for visible UI changes
- API example for API changes
- Known limitations
- Next steps

Each PR requires at least one review before merge.

## 3. Frontend Standards

- Use TypeScript for all new source files.
- Use functional React components.
- Define explicit prop types.
- Avoid `any`; justify it when unavoidable.
- Keep API calls in feature API modules or services.
- Build repeated UI from typed data arrays.
- Handle loading, empty, success, and error states.
- Use semantic HTML and accessible labels.
- Maintain RTL support and Persian typography.
- Keep components small enough to understand without excessive scrolling.
- Run lint and build before creating a PR.

Required checks:

```bash
npm run lint
npm run build
```

## 4. Backend Standards

- Follow PEP 8 naming conventions.
- Use type hints for service-layer public functions where practical.
- Keep views thin.
- Use DRF serializers for request validation.
- Put orchestration and business rules in services.
- Keep provider-specific AI code behind adapters.
- Use migrations for all model changes.
- Add tests for validation and critical service behavior.
- Return structured errors rather than raw exceptions.

Required checks:

```bash
python manage.py check
python manage.py test
```

## 5. API Standards

- Version API routes under `/api/v1/`.
- Use plural nouns for resource collections.
- Use consistent JSON field naming with `snake_case`.
- Validate all external input.
- Do not expose stack traces or secrets.
- Document request, response, and error examples.
- Maintain backward compatibility during Phase 1 unless the contract is explicitly revised.

## 6. Testing Expectations

### Frontend

Phase 1 minimum:

- Build succeeds
- Lint succeeds
- Golden path manually verified
- Responsive behavior checked
- No critical console errors

### Backend

Phase 1 minimum:

- Django system check succeeds
- API validation tests
- Health endpoint test
- Analyze endpoint success test
- Analyze endpoint invalid-input test
- Fallback behavior test

## 7. Definition of Done

A task is Done only when:

- Acceptance criteria are satisfied
- Code is reviewed
- Required checks pass
- Relevant documentation is updated
- No critical known bug blocks the demo
- The branch is merged into `main`
- The Trello card links to the PR
