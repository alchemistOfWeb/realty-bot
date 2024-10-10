# thrid party
from celery import shared_task

# built-in python
import asyncio

# django
from django.conf import settings

# handmade
from botmodels.models import GroupProfile

# aiogram
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


BOT_API_TOKEN = settings.BOT_API_TOKEN
SEND_TASKS_COUNTDOWN = 10


async def send_message_async(message_text: str) -> None:
    bot = Bot(token=BOT_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # groups = GroupProfile.objects.all()

    groups = [-1002320898941]
    
    for group in groups:
        try:
            await bot.send_message(chat_id=group, text=message_text)
        except Exception as e:
            print(f"Ошибка отправки сообщения в группу {group}: {e}")


@shared_task(bind=True)
def send_message_to_groups(self, message_text: str) -> None:
    """
    Task for sending messagesin into the groups by Celery
    """
    asyncio.run(send_message_async(message_text))
    self.apply_async((message_text,), countdown=SEND_TASKS_COUNTDOWN)
