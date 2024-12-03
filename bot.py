# django modules
import asyncio
import django

# python built-in modules
from collections import defaultdict
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
from aiogram.enums import ParseMode, ChatType
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
# config = dotenv_values('.env')
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')

LANGUAGE = "ru"

# set dispatcher for tg bot handlers
dp = Dispatcher()

class ButtonAction():
    def __init__(self, title, inline=False, eng=None, rus=None, callback_name=None, *args, **kwargs):
        self.title = title
        self._eng = eng
        self._rus = rus
        self._inline = inline
        self._callback_name = callback_name

    def get_text(self):
        if LANGUAGE == "ru":
            return self._rus
        else:
            return self._eng

    async def run(self, *args, **kwargs):
        callback = globals().get(self._callback_name)

        if callback and callable(callback):
            await callback(*args, **kwargs)


# BUTTON ACTIONS HANDLERS
# ---------------------------------------------------------------------------------


BUTTON_ACTIONS = {
    "settings": ButtonAction("settings", inline=True, rus="Настройки", callback_name="go_to_settings"),
    "pause_sending": ButtonAction("pause_sending", inline=True, rus="⛔Остановить рассылку⛔", callback_name="pause_sending"),
    "start_sending": ButtonAction("start_sending", inline=True, rus="🟢Начать рассылку🟢", callback_name="start_sending"),
}


async def go_to_settings(message):
    print("go_to_settings")


async def pause_sending(message):
    print("pause_sending")


async def start_sending(message):
    print("start_sending")
    # message.

BUTTON_ACTIONS_SEARCH_DICT = {
    btn_action.get_text():btn_action for btn_action in BUTTON_ACTIONS.values()
}


# @dp.message(lambda message: message.text in BUTTON_ACTIONS.keys())
# async def button_inline_actions_handler(message: Message):
#     btn_action = BUTTON_ACTIONS[message.text]
#     await btn_action.run(message)
#     await message.delete()

@dp.message(lambda message: message.text in BUTTON_ACTIONS_SEARCH_DICT.keys())
async def button_actions_handler(message: Message):
    btn_action = BUTTON_ACTIONS_SEARCH_DICT[message.text]
    await btn_action.run(message)
    await message.delete()





# @dp.message(lambda message: message.forward_date is not None)
# @dp.message(lambda message: message.caption is not None)

# OTHER HANDLERS
# ---------------------------------------------------------------------------------
media_groups_cache = defaultdict(list)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    TODO: must work only for admins in their individual chats
    """
    message.edit_reply_markup()
    if message.chat.type != ChatType.PRIVATE:
        return

    pause_sending = True

    kb = [
        [KeyboardButton(text=BUTTON_ACTIONS["settings"].get_text())],
        [KeyboardButton(text=BUTTON_ACTIONS["pause_sending"].get_text())] if pause_sending \
            else [KeyboardButton(text=BUTTON_ACTIONS["start_sending"].get_text())]
    ]
    mrkp = ReplyKeyboardMarkup(
        keyboard=kb, resize_keyboard=True)

    await message.answer(
        f"Здравствуйте, {html.bold(message.from_user.full_name)}!\n" +\
        f"Данный бот обрабатывает пересылаемые сообщения и рассылает их раз в {settings.BOT_DEFAULT_COUNTDOWN} минут",
        reply_markup=mrkp
    )


@dp.message(lambda message: message.forward_date is not None)
async def forward_message_handler(message: Message):
    # print(str(message) + "\n" + ("-"*80) + "\n")
    if message.chat.type != ChatType.PRIVATE:
        return

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

        # print("media_list: ", media_list)
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
