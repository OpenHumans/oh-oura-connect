import os
from dotenv import load_dotenv, find_dotenv
from celery import Celery

load_dotenv(dotenv_path=find_dotenv(), verbose=True)

app = Celery('oura')

CELERY_BROKER_URL = os.getenv('REDIS_URL')
app.conf.update({
    'BROKER_URL': CELERY_BROKER_URL,
    # Recommended settings. See: https://www.cloudamqp.com/docs/celery.html
    'BROKER_POOL_LIMIT': None,
    'BROKER_HEARTBEAT': None,
    'BROKER_CONNECTION_TIMEOUT': 30,
    'CELERY_RESULT_BACKEND': CELERY_BROKER_URL,
    'CELERY_SEND_EVENTS': False,
    'CELERY_EVENT_QUEUE_EXPIRES': 60,
})
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
