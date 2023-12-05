import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aos_tools.settings")

app = Celery("aos_tools")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
