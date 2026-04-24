import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "servio.settings")

app = Celery("servio")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
