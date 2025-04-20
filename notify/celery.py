import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transactions.settings')

app = Celery('notify')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    worker_concurrency=8,
)

app.autodiscover_tasks(['notify'])