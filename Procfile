web: poetry run python manage.py migrate && poetry run python bot.py
worker: poetry run celery -A config worker -l INFO