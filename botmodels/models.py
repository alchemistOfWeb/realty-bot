from django.db import models
from django.core.cache import cache
from threading import Lock
from aiogram.types import User as AiogramUser


class UserProfile(models.Model):
    user_id = models.BigIntegerField(null=True, blank=True)
    username = models.CharField(default="", null=False, max_length=255)
    chat_id = models.BigIntegerField(null=True, blank=True)
    is_admin = models.BooleanField(default=False, null=False, blank=False)

    def __str__(self):
        return self.username


class TgSetting(models.Model):
    end_sending_time = models.TimeField(null=True)
    start_sending_time = models.TimeField(null=True)
    period_sending_time = models.TimeField(null=True)
    do_sending = models.BooleanField(null=False, default=False)
    user_profile = models.OneToOneField(
        UserProfile, null=True, blank=True, related_name="bot_setting", on_delete=models.CASCADE)
    
    def __str__(self):
        return self.user_profile.username


class GroupProfile(models.Model):
    chat_id = models.BigIntegerField(unique=True, null=False, blank=False)
    group_name = models.CharField(default="", max_length=255, null=True, blank=True)
    active = models.BooleanField(default=False, null=False, blank=False)
    deleted = models.BooleanField(default=False, null=False, blank=False)

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

    # def set_start_sending_time(self):
    #     ...

    # def get_start_sending_time(self):
    #     ...

    # def set_end_sending_time(self):
    #     ...

    # def get_end_sending_time(self):
    #     ...

    # def set_period_sending_time(self):
    #     ...

    # def get_period_sending_time(self):
    #     ...

    # start_sending_time = property(set_start_sending_time, get_start_sending_time)
    # end_sending_time = property(set_end_sending_time, get_end_sending_time)
    # period_sending_time = property(set_period_sending_time, get_period_sending_time)
    

    def __init__(self, user:AiogramUser=None, prefix="bot_setting:"):
        self.prefix = prefix
        if user:
            self.tguser = user

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
