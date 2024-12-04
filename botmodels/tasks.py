# thrid party
from celery import shared_task
from celery.utils.log import get_task_logger

# built-in python
import asyncio
import time
import datetime
import pytz
from typing import List
from asgiref.sync import sync_to_async

# django
from django.conf import settings

# handmade
from botmodels.models import GroupProfile, BotSetting

# aiogram
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InputMediaPhoto, InputMedia
from aiogram.utils.media_group import MediaGroupBuilder

# BotSetting().get("do_sending")
logger = get_task_logger(__name__)
LAST_TASK_CACHE_KEY = 'last_task_eta'

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

    bot:Bot = Bot(token=settings.BOT_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    groups:List[GroupProfile] = \
        await sync_to_async(list)(GroupProfile.objects.filter(deleted=False, active=True))
    
    for group in groups:
        try:
            media_group = MediaGroupBuilder(caption=caption)

            for media in media_list:
                media_group.add_photo(media)

            await bot.send_media_group(chat_id=group.chat_id, media=media_group.build())

        except Exception as e:
            print(f"Error of sending message to the group {group.chat_id}: {e}")

    if bot_chat_id and message_ids:
        await bot.delete_messages(bot_chat_id, message_ids)


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


def get_next_task_eta():
    now:datetime.datetime = datetime.datetime.now(pytz.timezone('Asia/Yerevan'))  # TODO: Incapsulate getting hours/minutes
    
    hour, minute = BotSetting()\
        .get("start_sending_time", settings.BOT_START_SENDING_TIME).split(':')

    start_time = now.replace(hour=int(hour), minute=int(minute), second=0)

    hour, minute = BotSetting()\
        .get("end_sending_time", settings.BOT_END_SENDING_TIME).split(':')

    end_time = now.replace(hour=int(hour), minute=int(minute), second=0)

    last_task_eta = BotSetting().get(LAST_TASK_CACHE_KEY)

    if not last_task_eta:
        last_task_eta = start_time if now < start_time else now
    else:
        last_task_eta:datetime.datetime = datetime.datetime.fromisoformat(last_task_eta)
        minutes, seconds = BotSetting()\
            .get("period_sending_time", settings.BOT_DEFAULT_COUNTDOWN).split(':')
        
        if last_task_eta < now:
            last_task_eta = now

        next_eta = last_task_eta + datetime.timedelta(minutes=int(minutes), seconds=int(seconds))

        if next_eta >= end_time:
            next_eta = start_time + datetime.timedelta(days=1)

        last_task_eta = next_eta
    
    BotSetting().set(LAST_TASK_CACHE_KEY, last_task_eta.isoformat())

    return last_task_eta


def add_task_to_queue(media_list: list, caption: str, bot_chat_id: str = None, message_ids: list = None):
    """
    Dinamically add tasks to the queue.
    """
    
    next_eta = get_next_task_eta()
    send_message_to_groups.apply_async(
        args=[media_list, caption, bot_chat_id, message_ids],
        eta=next_eta 
    )
    logger.info(f"Задача добавлена в очередь. Следующий запуск в {next_eta}")
