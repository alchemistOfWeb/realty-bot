from django.core.management.base import BaseCommand, CommandError
from botmodels.models import TgSetting
from django.conf import settings
from datetime import datetime, time


class Command(BaseCommand):
    help = "Creates some default objects if they doesn't exist"

    def handle(self, *args, **kwargs):
        if not TgSetting.objects.filter(user_profile=None).exists():
            TgSetting.objects.create(
                user_profile=None,
                end_sending_time=datetime.strptime(settings.BOT_START_SENDING_TIME, '%H:%M').time(),
                start_sending_time=datetime.strptime(settings.BOT_END_SENDING_TIME, '%H:%M').time(),
                period_sending_time=datetime.strptime(settings.BOT_DEFAULT_COUNTDOWN, '%M:%S').time(),
                do_sending=False
            )
            self.stdout.write(self.style.SUCCESS("TgSetting object created successfully!"))
        else:
            self.stdout.write(self.style.WARNING("TgSetting object already exists."))
