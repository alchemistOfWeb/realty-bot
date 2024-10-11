# thrid party
from celery import shared_task
from celery.utils.log import get_task_logger

# built-in python
import asyncio
import time
import datetime
import pytz

# django
from django.conf import settings
from django.core.cache import cache

# handmade
from botmodels.models import GroupProfile

# aiogram
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InputMediaPhoto, InputMedia
from aiogram.utils.media_group import MediaGroupBuilder


logger = get_task_logger(__name__)
CACHE_KEY = 'last_task_eta'

async def send_message_async(
    media_list:list, caption:str, 
    bot_chat_id:str|None=None, 
    message_ids:list|None=None
    ) -> None:
    """
    media_list - list of strings with tg img ids or urls of images
    caption - some text under images
    bot_chat_id and message_ids - needs to delete message in bot chat 
    with user after sending post to groups
    """

    bot = Bot(token=settings.BOT_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # groups = GroupProfile.objects.all()

    groups = [-1002320898941]
    
    for group in groups:
        try:
            media_group = MediaGroupBuilder(caption=caption)

            for media in media_list:
                media_group.add_photo(media)

            await bot.send_media_group(chat_id=group, media=media_group.build())
            if bot_chat_id and message_ids:
                await bot.delete_messages(bot_chat_id, message_ids)

        except Exception as e:
            print(f"Error of sending message to the group {group}: {e}")


@shared_task(bind=True)
def send_message_to_groups(
    self, 
    media_list: list, caption: str,
    bot_chat_id:str|None=None, 
    message_ids:list|None=None
    ) -> None:
    """
    Task for sending messagesin into the groups by Celery
    """
    asyncio.run(send_message_async(media_list, caption, bot_chat_id, message_ids))
    # self.apply_async(
    #     (media_list, caption, bot_chat_id, message_ids),
    #     countdown=settings.BOT_DEFAULT_COUNTDOWN
    # )


def get_next_task_eta():
    now = datetime.datetime.now(pytz.timezone('Asia/Yerevan'))  
    start_time = now.replace(hour=int(settings.BOT_START_SENDING_HOUR), minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=int(settings.BOT_END_SENDING_HOUR), minute=55, second=0, microsecond=0)

    last_task_eta = cache.get(CACHE_KEY)
    if not last_task_eta:
        last_task_eta = start_time if now < start_time else now
    else:
        last_task_eta = datetime.datetime.fromisoformat(last_task_eta)
        next_eta = last_task_eta + datetime.timedelta(seconds=int(settings.BOT_DEFAULT_COUNTDOWN))

        if next_eta >= end_time:
            next_eta = start_time + datetime.timedelta(days=1)

        last_task_eta = next_eta
    
    cache.set(CACHE_KEY, last_task_eta.isoformat())

    # interval = datetime.timedelta(seconds=int(settings.BOT_DEFAULT_COUNTDOWN))
    # next_eta = eta + interval

    return last_task_eta


def add_task_to_queue(media_list: list, caption: str, bot_chat_id: str = None, message_ids: list = None):
    """
    Функция для динамического добавления задач в очередь.
    Запускает задачу каждые 20 минут в интервале с 8:00 до 20:00.
    """
    
    next_eta = get_next_task_eta()
    send_message_to_groups.apply_async(
        args=[media_list, caption, bot_chat_id, message_ids],
        eta=next_eta 
    )
    logger.info(f"Задача добавлена в очередь. Следующий запуск в {next_eta}")
