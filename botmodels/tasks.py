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
from aiogram.types import InputMediaPhoto, InputMedia
from aiogram.utils.media_group import MediaGroupBuilder


BOT_API_TOKEN = settings.BOT_API_TOKEN
SEND_TASKS_COUNTDOWN = 10


async def send_message_async(media_list:list, caption:str) -> None:
    bot = Bot(token=BOT_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # groups = GroupProfile.objects.all()

    groups = [-1002320898941]
    
    for group in groups:
        try:
            media_group = MediaGroupBuilder(caption=caption)
            media_group_list = list()

            for media in media_list:
                media_group.add_photo(media)

            for media in media_list:
                media_group_list.append(InputMediaPhoto(media=media))
            
            print("media_group_build: ", media_group)
            print("media_group_list: ", media_group_list)
            # await bot.send_media_group(chat_id=group, media=media_group.build())

            # ANOTHER METHOD:
            print("AAAAAAAAAAAAA")
            await bot.send_media_group(chat_id=group, media=media_group.build())
            
            # if caption:
            #     await bot.send_message(chat_id=group, text=caption)

            # await bot.send_photo(chat_id=group, photo=)
            # await bot.forward_message(chat_id=group, from_chat_id=from_chat_id, message_id=message_id)
            # await bot.send_message(chat_id=group, text=message_text)
        except Exception as e:
            print(f"Error of sending message to the group {group}: {e}")


@shared_task(bind=True)
def send_message_to_groups(self, media_list: list, caption: str) -> None:
    """
    Task for sending messagesin into the groups by Celery
    """
    asyncio.run(send_message_async(media_list, caption))
    # self.apply_async((message_text,), countdown=SEND_TASKS_COUNTDOWN)
