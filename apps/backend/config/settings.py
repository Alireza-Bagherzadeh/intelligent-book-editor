"""Django settings for the intelligent book editor backend."""

from pathlib import Path
import os
from urllib.parse import urlsplit

from dotenv import load_dotenv


# ======================================================================
# Base
# ======================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))


# ======================================================================
# Security
# ======================================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-local-development-only-change-me",
)

DEBUG = os.getenv(
    "DEBUG",
    "False" if IS_VERCEL else "True",
).lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1",
    ).split(",")
    if host.strip()
]

if IS_VERCEL and ".vercel.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".vercel.app")


# ======================================================================
# External AI configuration
# ======================================================================

# Gemini is optional during application startup. It is validated only when
# the Gemini review task is actually executed, so upload/parsing can run
# independently from the AI provider.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")


# ======================================================================
# Installed apps / middleware
# ======================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_q",
    "corsheaders",
    "doc_process",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ======================================================================
# URLs / WSGI
# ======================================================================

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# ======================================================================
# Templates
# ======================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ======================================================================
# CORS
# ======================================================================

def _normalize_origin(value: str) -> str:
    """Return only scheme://host[:port], never a URL path."""
    value = value.strip()
    if not value:
        return ""

    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"

    return value.rstrip("/")


_raw_cors_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "https://intelligent-book-editor.vercel.app"
    ),
).split(",")

CORS_ALLOWED_ORIGINS = list(
    dict.fromkeys(
        origin
        for origin in (
            _normalize_origin(item)
            for item in _raw_cors_origins
        )
        if origin
    )
)


# ======================================================================
# Database
# ======================================================================

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("DATABASE_URL_POSTGRES_URL")
)

if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            "OPTIONS": {
                "timeout": 30,
                "transaction_mode": "IMMEDIATE",
            },
        }
    }


# ======================================================================
# File storage
# ======================================================================

# Local: FileField/filesystem.
# Vercel: BinaryField/PostgreSQL. The explicit environment variable wins,
# otherwise PostgreSQL presence selects database-backed file storage.
FILE_STORAGE_BACKEND = os.getenv(
    "FILE_STORAGE_BACKEND",
    "database" if DATABASE_URL else "local",
).lower()

if FILE_STORAGE_BACKEND not in {"local", "database"}:
    raise ValueError(
        "FILE_STORAGE_BACKEND must be either 'local' or 'database'."
    )


# ======================================================================
# Password validation
# ======================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ======================================================================
# Internationalization
# ======================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ======================================================================
# Static / media
# ======================================================================

STATIC_URL = "/static/"

# Keeping MEDIA_ROOT at BASE_DIR preserves the project's existing local paths:
# upload_to="documents/..." -> <backend>/documents/...
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ======================================================================
# Django-Q2 (local development only)
# ======================================================================

Q_CLUSTER = {
    "name": "DocProcessor",
    "workers": 1,
    "recycle": 500,
    "timeout": 120,
    "retry": 180,
    "compress": True,
    "save_limit": 250,
    "queue_limit": 100,
    "label": "Django Q",
    "orm": "default",
}


# ======================================================================
# GapGPT API configuration
# ======================================================================

GAPGPT_API_KEY = os.getenv("GAPGPT_API_KEY", "")
GAPGPT_BASE_URL = os.getenv("GAPGPT_BASE_URL", "https://api.gapgpt.app/v1")
GAPGPT_MODEL = os.getenv("GAPGPT_MODEL", "gpt-4o-mini")
GAPGPT_TIMEOUT = float(os.getenv("GAPGPT_TIMEOUT", "120"))
GAPGPT_MAX_RETRIES = int(os.getenv("GAPGPT_MAX_RETRIES", "3"))
GAPGPT_TEMPERATURE = float(os.getenv("GAPGPT_TEMPERATURE", "0.1"))
