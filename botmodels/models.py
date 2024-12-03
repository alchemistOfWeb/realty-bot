from django.db import models
from django.core.cache import cache
from threading import Lock


class UserProfile(models.Model):
    user_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return self.name


class GroupProfile(models.Model):
    chat_id = models.BigIntegerField(unique=True, null=False, blank=False)
    group_name = models.CharField(default="", max_length=255, null=True, blank=True)
    active = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return self.group_name

class SingletonMeta(type):
    """Metaclass implementing Singleton."""
    _instances = {}
    _lock = Lock()  # for thread safety

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class BotSetting(metaclass=SingletonMeta):
    default_timeout = None

    def __init__(self, prefix="bot_setting:"):
        self.prefix = prefix

    def _key(self, name):
        """incapsulating variables of the settings from other db vars"""
        return f"{self.prefix}{name}"

    def get(self, name, default=None):
        key = self._key(name)
        return cache.get(key, default)

    def set(self, name, value, timeout=None):
        key = self._key(name)
        cache.set(key, value, timeout or self.default_timeout)

    def delete(self, name):
        key = self._key(name)
        cache.delete(key)