# django modules
import asyncio
import django

# python built-in modules
from datetime import datetime
import calendar
import logging
import sys
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

# third-party modules
from dotenv import dotenv_values

# aoigram modules
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

from aiogram.utils.keyboard import (
    InlineKeyboardBuilder, ReplyKeyboardBuilder, 
    KeyboardButton, ReplyKeyboardMarkup
)

from aiogram.types import (
    Message, InputFile, FSInputFile, InlineKeyboardMarkup, 
    InlineKeyboardButton, CallbackQuery, InputMediaPhoto
)

from aiogram.fsm.context import FSMContext
from magic_filter import F

# handmade modules
from botmodels.tasks import send_message_to_groups, send_message_async, add_task_to_queue

# from botmodels.models import UserProfile
# import texts # mesage-templates


# ENV variables
config = dotenv_values('.env')
BOT_API_TOKEN = config.get('BOT_API_TOKEN')

# set dispatcher for tg bot handlers
dp = Dispatcher()








# TMP BOT SETTINGS
groups_ids = [2320898941]

def send_messages():
    for group_id in groups_ids:
        ...


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    TODO: must work only for admins in their individual chats
    """
    await message.answer(
        f"Здравствуйте, {html.bold(message.from_user.full_name)}!\n" +\
        f"Данный бот обрабатывает пересылаемые сообщения и рассылает их раз в {settings.BOT_DEFAULT_COUNTDOWN} секунд")


    # kb = [
    #     [KeyboardButton(text="Получить расклад🎴")]
    # ]
    # mrkp = ReplyKeyboardMarkup(
    #     keyboard=kb, resize_keyboard=True
    # )
    
    # await message.bot.send_message()
    # await message.bot.send_photo(
    #     chat_id=message.from_user.id,
    #     photo=FSInputFile(image_path), 
    #     caption="hello i'm a bot", 
    #     reply_markup=mrkp,
    #     parse_mode=ParseMode.HTML
    # )

from collections import defaultdict

media_groups_cache = defaultdict(list)


# @dp.message(lambda message: message.forward_date is not None)
# @dp.message(lambda message: message.caption is not None)
@dp.message(lambda message: message.forward_date is not None)
async def forward_message_handler(message: Message):
    print(str(message) + "\n" + ("-"*80) + "\n")

    media_group_id = message.media_group_id
    media_groups_cache[media_group_id].append(message)

    if message.caption:
        await asyncio.sleep(1) # wait untill all media collected

        media_list = []
        message_ids = []
        caption = None

        for msg in media_groups_cache[media_group_id]:
            if msg.caption:
                caption = msg.caption
            
            if msg.photo:
                media_list.append(msg.photo[-1].file_id)

            message_ids.append(msg.message_id)
        
        del media_groups_cache[media_group_id]

        print("media_list: ", media_list)
        # await send_message_async(media_list, caption)
        add_task_to_queue(media_list, caption, message.chat.id, message_ids)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=BOT_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook()
    # And the run events dispatching
    print("start polling")
    await dp.start_polling(bot)
    # print("start polling2")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
