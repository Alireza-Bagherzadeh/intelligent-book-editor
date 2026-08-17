import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

# Fully initialize Django before the queue callback
# imports task definitions / ORM models.
from django.core.wsgi import get_wsgi_application

get_wsgi_application()

from vercel.workers.django import get_wsgi_app

app = get_wsgi_app(
    backend_alias="default",
)