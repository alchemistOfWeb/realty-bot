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
from django.core.cache import cache
from django.db.models import Q

# handmade
from botmodels.models import GroupProfile, UserProfile, TgSetting, BotSetting
from botmodels.functions import get_setting_by_chat_id

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
    # usersetting_list:List[TgSetting] = await sync_to_async(list)(TgSetting.objects\
    #     .filter(Q(user_profile__isnull=True) | Q(user_profile__chat_id=int(bot_chat_id))))

    # usersetting:TgSetting|None = None
    # if len(usersetting_list) > 1:
    #     usersetting = usersetting_list[0] if usersetting_list[0].user_profile else usersetting_list[1]
    # elif len(usersetting_list) == 1:
    #     usersetting = usersetting_list[0]
    # else:
    #     usersetting = None
    usersetting:TgSetting = await get_setting_by_chat_id(bot_chat_id)

    # if not BotSetting().get("do_sending", True): return
    if not (usersetting and usersetting.do_sending): return
    
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


async def get_next_task_eta(user_id:str|int):
    now:datetime.datetime = datetime.datetime.now(pytz.timezone(settings.TIME_ZONE))
    
    usersetting:TgSetting = await get_setting_by_chat_id(user_id)

    hour = usersetting.start_sending_time.hour
    minute = usersetting.start_sending_time.minute
    start_time = now.replace(hour=int(hour), minute=int(minute), second=0)

    hour = usersetting.end_sending_time.hour
    minute = usersetting.end_sending_time.minute
    end_time = now.replace(hour=int(hour), minute=int(minute), second=0)

    last_task_eta:datetime.datetime = usersetting.last_task_eta

    if not last_task_eta:
        last_task_eta = start_time if now < start_time else now
    else:
        minutes = usersetting.period_sending_time.minute
        seconds = usersetting.period_sending_time.second
        
        if last_task_eta < now:
            last_task_eta = now

        print(f"minutes: {minutes}\nseconds: {seconds}\n")
        next_eta = last_task_eta + datetime.timedelta(minutes=int(minutes), seconds=int(seconds))
        print(f"next_eta before update: {next_eta}")

        if next_eta >= end_time:
            next_eta = start_time + datetime.timedelta(days=1)

        print(f"next_eta after update: {next_eta}")
        last_task_eta = next_eta
    
    usersetting.last_task_eta = last_task_eta
    await sync_to_async(usersetting.save)()
    return last_task_eta


async def add_task_to_queue(media_list: list, caption: str, bot_chat_id: str = None, message_ids: list = None):
    """
    Dinamically add tasks to the queue.
    """
    
    next_eta = await get_next_task_eta(bot_chat_id)
    send_message_to_groups.apply_async(
        args=[media_list, caption, bot_chat_id, message_ids],
        eta=next_eta 
    )
    logger.info(f"Задача добавлена в очередь. Следующий запуск в {next_eta}")
