release: python manage.py migrate
web: gunicorn wsgi --log-file -
worker: celery -A app worker --concurrency 1
