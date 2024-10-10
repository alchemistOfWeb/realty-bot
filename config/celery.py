import os
from celery import Celery

# Установка переменной окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создание экземпляра Celery
app = Celery('project')

# Загрузка настроек из файла settings.py с префиксом 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое нахождение и регистрация тасков в приложениях Django
app.autodiscover_tasks()