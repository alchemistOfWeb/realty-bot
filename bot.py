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
from botmodels.models import BotSetting

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


BUTTON_ACTIONS = {
    "start": ButtonAction("start", inline=True, rus="Start", callback_name="start_handler"),
    "settings": ButtonAction("settings", inline=True, rus="Настройки", callback_name="go_to_settings"),
    "pause_sending": ButtonAction("pause_sending", inline=True, rus="⛔Остановить рассылку⛔", callback_name="pause_sending"),
    "start_sending": ButtonAction("start_sending", inline=True, rus="🟢Начать рассылку🟢", callback_name="start_sending"),
    "groups": ButtonAction("groups", inline=True, rus="👨‍👨‍👦‍👦Группы👨‍👨‍👦‍👦", callback_name="groups_handler"),
    "timings": ButtonAction("timings", inline=True, rus="⌚Тайминги⌚", callback_name="timings_handler"),
    "go_back": ButtonAction("go_back", inline=True, rus="🔙Назад🔙", callback_name="go_back_handler"),
    "start_sending_option": ButtonAction("start_sending_option", inline=True, rus="Начало отправки", callback_name="start_sending_option"),
    "end_sending_option": ButtonAction("end_sending_option", inline=True, rus="Конец отправки", callback_name="end_sending_option"),
    "period_option": ButtonAction("period_option", inline=True, rus="Промежуток", callback_name="period_option"),
}

async def update_actions_stack(state: FSMContext, action_name:str) -> None:
    data:dict = await state.get_data()
    if action_name not in BUTTON_ACTIONS: raise ValueError(f"There is no action with name {action_name}")
    actions_stack:list = data.get("actions_stack", [])
    actions_stack.append(action_name)
    state.update_data(actions_stack=actions_stack)

# BUTTON ACTIONS HANDLERS
# ---------------------------------------------------------------------------------

async def go_to_settings(callback_query: CallbackQuery, state: FSMContext):
    print("go_to_settings")
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["groups"].get_text(), callback_data="groups"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["timings"].get_text(), callback_data="timings"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["go_back"].get_text(), callback_data="go_back"),
    )
    await callback_query.message.edit_text(
        text="Настройки бота", 
        reply_markup=keyboard.as_markup()
    )
    await update_actions_stack(state, "settings")


async def pause_sending(callback_query: CallbackQuery, state: FSMContext):
    print("pause_sending")
    BotSetting().set("start_sending", False)
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text=BUTTON_ACTIONS["settings"].get_text(), callback_data="settings"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["start_sending"].get_text(), 
            callback_data="start_sending"
        )
    )
    await callback_query.message.edit_text(
        text="Состояние рассылки: выключена", 
        reply_markup=keyboard.as_markup()
    )


async def start_sending(callback_query: CallbackQuery, state: FSMContext):
    print("start_sending")
    BotSetting().set("start_sending", True)
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text=BUTTON_ACTIONS["settings"].get_text(), callback_data="settings"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["pause_sending"].get_text(), 
            callback_data="pause_sending"
        )
    )
    await callback_query.message.edit_text(
        text="Состояние рассылки: включена", 
        reply_markup=keyboard.as_markup()
    )


async def groups_handler(callback_query: CallbackQuery, state: FSMContext):
    # TODO: list of groups; pagination; next, back buttons
    print("groups_handler")
    return
    await update_actions_stack(state, "groups")


async def timings_handler(callback_query: CallbackQuery, state: FSMContext):
    print("timings handler")
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["start_sending_option"].get_text(), callback_data="start_sending_option"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["end_sending_option"].get_text(), callback_data="end_sending_option"),
    )
    keyboard.row(
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["period_option"].get_text(), callback_data="period_option"),
    )
    keyboard.row(
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["go_back"].get_text(), callback_data="go_back"),
    )
    await callback_query.message.edit_text(
        text="Настройка таймингов", 
        reply_markup=keyboard.as_markup()
    )
    await update_actions_stack(state, "timings")


async def start_sending_option(callback_query: CallbackQuery, state: FSMContext):
    print("start_sending_option")
    return
    await update_actions_stack(state, "start_sending_option")


async def end_sending_option(callback_query: CallbackQuery, state: FSMContext):
    print("end_sending_option")
    return
    await update_actions_stack(state, "end_sending_option")


async def period_option(callback_query: CallbackQuery, state: FSMContext):
    print("period_option")
    return
    await update_actions_stack(state, "period_option")


async def go_back_handler(callback_query: CallbackQuery, state: FSMContext):
    print("go_back_handler")
    data = await state.get_data()
    actions_stack = data.get("actions_stack")
    print('actions_stack: ', actions_stack)
    actions_stack.pop()
    await state.update_data(go_back_called=True)
    await BUTTON_ACTIONS[actions_stack.pop()].run(callback_query, state)


async def start_handler(message: Message|CallbackQuery, state: FSMContext):
    if isinstance(message, CallbackQuery):
        message:Message = message.message

    if message.chat.type != ChatType.PRIVATE:
        return

    pause_sending = BotSetting().get("start_sending", False)

    data = await state.get_data()
    go_back_called = data.get("go_back_called", False)
    await state.update_data(actions_stack=[])

    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text=BUTTON_ACTIONS["settings"].get_text(), callback_data="settings"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["pause_sending"].get_text(), 
            callback_data="pause_sending"
        ) if pause_sending \
            else InlineKeyboardButton(
                text=BUTTON_ACTIONS["start_sending"].get_text(), 
                callback_data="start_sending"
                )
    )
    if go_back_called:
        await message.edit_text(
            f"Здравствуйте, {html.bold(message.from_user.full_name)}!\n" +\
            f"Данный бот обрабатывает пересылаемые сообщения и рассылает их раз в {settings.BOT_DEFAULT_COUNTDOWN} минут",
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer(
            f"Здравствуйте, {html.bold(message.from_user.full_name)}!\n" +\
            f"Данный бот обрабатывает пересылаемые сообщения и рассылает их раз в {settings.BOT_DEFAULT_COUNTDOWN} минут",
            reply_markup=keyboard.as_markup()
        )

    await update_actions_stack(state, "start")

# ---------------------------------------------------------------------------------

@dp.callback_query(lambda callback_query: callback_query.data in BUTTON_ACTIONS.keys())
async def button_inline_actions_handler(callback_query: CallbackQuery, state: FSMContext):
    btn_action = BUTTON_ACTIONS[callback_query.data]
    await btn_action.run(callback_query, state)


BUTTON_ACTIONS_SEARCH_DICT = {
    btn_action.get_text():btn_action for btn_action in BUTTON_ACTIONS.values()
}

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
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    This handler receives messages with `/start` command
    TODO: must work only for admins in their individual chats
    """
    await start_handler(message, state)


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
