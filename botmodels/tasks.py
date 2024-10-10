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
from aiogram.types import InputMediaPhoto


BOT_API_TOKEN = settings.BOT_API_TOKEN
SEND_TASKS_COUNTDOWN = 10


async def send_message_async(from_chat_id: int, message_id: int) -> None:
    bot = Bot(token=BOT_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # groups = GroupProfile.objects.all()

    groups = [-1002320898941]
    
    for group in groups:
        try:
            # await bot.send_media_group(chat_id=group, media=media)
            await bot.forward_message(chat_id=group, from_chat_id=from_chat_id, message_id=message_id)
            # await bot.send_message(chat_id=group, text=message_text)
        except Exception as e:
            print(f"Ошибка отправки сообщения в группу {group}: {e}")


@shared_task(bind=True)
def send_message_to_groups(self, from_chat_id: int, message_id: int) -> None:
    """
    Task for sending messagesin into the groups by Celery
    """
    asyncio.run(send_message_async(from_chat_id, message_id))
    # self.apply_async((message_text,), countdown=SEND_TASKS_COUNTDOWN)
