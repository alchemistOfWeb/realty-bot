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
from botmodels.tasks import send_message_to_groups
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
    await message.answer(f"Здравствуйте, {html.bold(message.from_user.full_name)}!")


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

@dp.message(lambda message: message.forward_date is not None)
async def forward_message_handler(message: Message):
    # photo_ids = list()
    # unique_photos = {}
    # if message.photo:
    #     for photo in message.photo:
    #         # Получаем первые 50 символов file_id
    #         file_id_prefix = photo.file_id[:50]

    #         # Проверяем, если у нас уже есть изображение с таким префиксом
    #         if file_id_prefix not in unique_photos:
    #             unique_photos[file_id_prefix] = photo  # Сохраняем новое изображение
    #         else:
    #             # Сравниваем размеры
    #             existing_photo = unique_photos[file_id_prefix]
    #             # Сравниваем по `width` и `height`
    #             if (photo.width * photo.height) > (existing_photo.width * existing_photo.height):
    #                 unique_photos[file_id_prefix] = photo  # Сохраняем большее изображение

    #     # Получаем уникальные изображения с наибольшим размером
    #     photo_ids = [photo.file_id for photo in unique_photos.values()]
    #     print(f"Уникальные пересланные фото с наибольшим размером: {photo_ids}")

    send_message_to_groups.delay(from_chat_id=message.chat.id, message_id=message.message_id)
    # await message.answer(f"Get another forwarded message")


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
