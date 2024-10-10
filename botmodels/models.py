from django.db import models


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
