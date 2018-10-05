release: python manage.py migrate
web: gunicorn wsgi --log-file -
worker: celery worker -A app --concurrency 1
