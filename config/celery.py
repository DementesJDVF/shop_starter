import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

app = Celery('shop_starter')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

from celery.schedules import crontab

app.conf.beat_schedule = {
    'reap-zombie-tasks-every-5-minutes': {
        'task': 'apps.products.tasks.reap_zombie_ai_tasks',
        'schedule': crontab(minute='*/5'),
    },
}
