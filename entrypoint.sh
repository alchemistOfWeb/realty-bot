#!/bin/bash
# Запуск миграций и бота
poetry run python manage.py migrate
poetry run python bot.py &  # Запускаем бота в фоновом режиме

# Запуск Celery
poetry run celery -A config worker -l info --concurrency=2
