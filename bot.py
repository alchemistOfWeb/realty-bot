# django modules
import asyncio
import django

# python built-in modules
from datetime import datetime
import calendar
import logging
import sys
import os


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
# from botmodels.models import UserProfile
# import texts # mesage-templates


# ENV variables
config = dotenv_values('.env')
BOT_API_TOKEN = config.get('BOT_API_TOKEN')

# set dispatcher for tg bot handlers
dp = Dispatcher()


# Установите настройки Django для доступа к моделям
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# django.setup()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")

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



async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=BOT_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook()
    # And the run events dispatching
    await dp.start_polling(bot)
    print("start polling2")

if __name__ == "__main__":
    print("start polling")
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
