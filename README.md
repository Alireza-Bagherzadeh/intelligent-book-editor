# AI Book Text and Page Editor

An intelligent platform for **Persian book editing, proofreading, text normalization, document review, and assisted page-editing workflows**.

The project combines a modern RTL web interface with a Django-based document-processing backend and asynchronous AI-assisted review pipeline.

---

## Overview

AI Book Text and Page Editor is designed to help editors, authors, publishers, and content teams review Persian documents more efficiently.

The platform processes uploaded documents or raw text, converts them into structured document blocks, performs Persian text normalization and proofreading, detects editorial issues, highlights differences, and prepares corrected content for review and export.

The current implementation includes both deterministic Persian text-processing logic and an AI-assisted review workflow.

---

## Key Features

### Persian Document Processing

* Upload and process DOCX documents
* Submit raw Persian text directly to the backend
* Convert documents into structured blocks
* Preserve paragraphs and headings during processing
* Normalize Persian characters and typography
* Handle Persian RTL content and alignment

### Editing and Proofreading

* Persian text normalization
* Spelling issue detection
* Grammar issue support
* Punctuation correction
* Half-space and Persian typography normalization
* Style and optimization suggestions
* Block-level issue tracking
* Original and corrected text comparison

### Issue Highlighting

* Detect differences between original and processed text
* Store block-level differences
* Highlight detected issues inside the editor
* Toggle issue highlighting on and off
* Use normalized offsets with fallback handling for original text offsets

### AI-Assisted Review

The backend currently supports an AI review pipeline using Gemini.

The AI review workflow can identify:

* Spelling issues
* Grammar issues
* Style issues
* Punctuation issues
* Text optimization opportunities

AI review is processed asynchronously through Django Q so long-running review operations do not block normal API requests.

### Background Processing

Django Q is used for asynchronous operations such as:

* Document parsing
* Document review
* Difference generation
* AI-assisted review

### Document Export

Processed documents can be exported back to DOCX format after the editing and review workflow.

### Responsive RTL Interface

The frontend provides:

* Persian-first RTL layout
* Responsive desktop and mobile experience
* Light and dark themes
* Document editor workspace
* Issue visualization
* Review controls
* Document upload and raw-text workflows

---

## System Architecture

The current application follows this general architecture:

```text
User
  │
  ▼
React / Vite Frontend
  │
  │ HTTP / REST API
  ▼
Django Backend
  │
  ├── Document Upload API
  ├── Raw Text API
  ├── Document Processing Pipeline
  ├── Review API
  ├── Differences API
  └── DOCX Export
  │
  ▼
Django Q
  │
  ├── Document Parsing Tasks
  ├── Normal Review Tasks
  ├── Difference Generation
  └── AI Review Tasks
  │
  ▼
Text Processing / Gemini AI Review
  │
  ▼
Database
```

SQLite is currently used for local development.

The SQLite configuration includes an increased lock timeout and immediate transaction mode to improve behavior when Django and Django Q access the development database concurrently.

---

## Repository Structure

```text
intelligent-book-editor/
│
├── apps/
│   ├── backend/
│   │   ├── config/
│   │   ├── doc_process/
│   │   ├── documents/
│   │   ├── editor/
│   │   └── manage.py
│   │
│   └── frontend/
│       ├── src/
│       ├── public/
│       └── package.json
│
├── ai/
│   └── AI-related services, experiments, and integrations
│
├── docs/
│   └── Product, UX, architecture, and technical documentation
│
├── prototypes/
│   └── Experimental implementations and proof-of-concepts
│
└── README.md
```

---

## Technology Stack

### Frontend

* React
* TypeScript
* Vite
* Modern responsive RTL UI

### Backend

* Python
* Django
* Django REST-based APIs
* Django Q / Django Q2
* SQLite for local development

### AI and Text Processing

* Persian text normalization
* Rule-based editorial preprocessing
* Gemini API integration
* Structured AI responses using Pydantic

### Document Processing

* DOCX parsing
* Block-based document representation
* Difference detection
* DOCX export

---

# Local Development

## Prerequisites

Install the following before running the project:

* Git
* Python
* Node.js
* npm

A Gemini API key is also required for the current AI review functionality.

---

## 1. Clone the Repository

```bash
git clone https://github.com/AIRAC-Devteam/intelligent-book-editor.git
cd intelligent-book-editor
```

For active development:

```bash
git switch develop
```

---

# Backend Setup

## 2. Create a Python Virtual Environment

From the repository root:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Then enter the backend directory:

```powershell
cd apps\backend
```

Install the backend dependencies using the dependency file provided by the project.

For example, when using `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create the local `.env` file used by the backend configuration.

The Gemini integration requires:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Never commit real API keys, passwords, tokens, or other secrets to Git.

---

## 4. Apply Database Migrations

From:

```text
apps/backend
```

run:

```powershell
python manage.py migrate
```

Verify the Django configuration:

```powershell
python manage.py check
```

You can inspect the document-processing migrations using:

```powershell
python manage.py showmigrations doc_process
```

---

# Running the Application

The application currently requires three development processes:

1. Django backend
2. Django Q worker
3. React frontend

These should normally be run in separate terminal windows.

---

## 5. Run the Django Backend

From:

```text
apps/backend
```

run:

```powershell
python manage.py runserver
```

The development API is normally available at:

```text
http://127.0.0.1:8000/
```

---

## 6. Run Django Q

Open another terminal, activate the same Python virtual environment, and run:

```powershell
cd apps\backend
python manage.py qcluster
```

A successful startup should indicate that the Q Cluster is running and workers are ready for tasks.

The Q Cluster must remain running for asynchronous document-processing and review jobs.

---

# Frontend Setup

## 7. Install Frontend Dependencies

Open another terminal and enter:

```powershell
cd apps\frontend
```

Install dependencies:

```powershell
npm install
```

---

## 8. Run the Frontend

```powershell
npm run dev
```

Vite normally serves the development application at:

```text
http://localhost:5173/
```

Open this address in the browser.

---

# Recommended Development Startup

During normal local development, keep these three terminals running:

### Terminal 1 — Backend

```powershell
cd apps\backend
python manage.py runserver
```

### Terminal 2 — Background Worker

```powershell
cd apps\backend
python manage.py qcluster
```

### Terminal 3 — Frontend

```powershell
cd apps\frontend
npm run dev
```

The resulting development flow is:

```text
Browser
   │
   ▼
localhost:5173
   │
   ▼
Django API
127.0.0.1:8000
   │
   ├── synchronous requests
   │
   └── asynchronous jobs
              │
              ▼
          Django Q
```

---

# Development Checks

## Backend

Run:

```powershell
python -m compileall .
python manage.py check
python manage.py makemigrations --check --dry-run
```

Before testing a new database migration:

```powershell
python manage.py migrate
```

---

## Frontend

From `apps/frontend`:

```powershell
npx tsc -p tsconfig.app.json --noEmit
npm run lint
npm run build
```

These checks should pass before merging significant frontend changes.

---

# Main Application Workflow

A typical document workflow is:

```text
Upload DOCX / Submit Raw Text
              │
              ▼
        Document Created
              │
              ▼
       Background Parsing
              │
              ▼
      Structured Blocks
              │
              ▼
      Normal Text Review
              │
              ▼
        Issue Detection
              │
              ▼
       AI-Assisted Review
              │
              ▼
    Difference Generation
              │
              ▼
     Editor Highlighting
              │
              ▼
        User Review
              │
              ▼
         DOCX Export
```

---

# Raw Text Processing

In addition to DOCX files, the backend supports documents created directly from raw text.

The backend stores the input source type and routes the document to the appropriate parsing pipeline.

This allows the same editing and review infrastructure to work with both:

```text
DOCX
```

and:

```text
Raw Text
```

---

# AI Review

The current AI-assisted review implementation uses the Gemini API.

Document blocks are processed in batches and AI output is mapped to structured issue records.

The AI layer can produce issue types such as:

```text
spelling
grammar
style
punctuation
optimization
```

AI processing is executed in the background through Django Q.

A valid `GEMINI_API_KEY` is required for this functionality.

---

# Database Notes

SQLite is currently used for local development.

The development configuration uses:

```python
"OPTIONS": {
    "timeout": 30,
    "transaction_mode": "IMMEDIATE",
}
```

This helps reduce database locking problems during concurrent Django and Django Q operations.

SQLite is suitable for the current development workflow, but production deployment should use an appropriate production-grade database architecture.

---

# Git Workflow

The repository follows a branch-based development workflow.

## `main`

Stable release branch.

Code should reach `main` through reviewed Pull Requests.

## `develop`

Primary integration branch.

Completed backend, frontend, AI, and integration work is merged into `develop` before release.

## Feature Branches

New work should normally be created from the latest `develop` branch.

Examples:

```text
feat/...
fix/...
docs/...
chore/...
integration/...
```

A typical workflow is:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feat/example-feature
```

After development and validation, open a Pull Request back into `develop`.

Release synchronization should be performed through a Pull Request from:

```text
develop → main
```

---

# Commit Convention

Use Conventional Commits for new commits.

Examples:

```text
feat(frontend): add document issue highlighting
fix(backend): improve SQLite transaction handling
docs: update local development guide
refactor(backend): simplify document processing pipeline
chore: update project dependencies
```

---

# Security

Do not commit:

* `.env` files
* API keys
* access tokens
* passwords
* private credentials
* local database secrets
* production configuration secrets

Environment-specific values must be provided through environment variables or secure deployment configuration.

---

# Current Status

The project has moved beyond the initial prototype phase and currently includes an integrated frontend and backend application with:

* Persian document processing
* DOCX support
* Raw text support
* Asynchronous processing
* Issue detection
* Difference tracking
* Editor highlighting
* AI-assisted review
* DOCX export
* Responsive RTL user interface

Development continues on the `develop` branch, while `main` is used as the stable release branch.

---

## Project

**AI Book Text and Page Editor**

Developed as part of the AI research and development activities of the AIRAC team.
