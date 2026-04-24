import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "servio.settings")

app = Celery("servio")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
    "send-upcoming-work-reminders-daily": {
        "task": "notifications.tasks.send_upcoming_work_reminders",
        "schedule": crontab(hour=8, minute=0),
    }
}

app.autodiscover_tasks()
