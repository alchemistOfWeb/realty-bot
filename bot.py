
# python built-in modules
from collections import defaultdict
from datetime import datetime
import calendar
import logging
import sys
import os

# django modules
import asyncio
import django
from django.db import IntegrityError
from django.core.cache import cache
from asgiref.sync import sync_to_async

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
    InlineKeyboardButton, CallbackQuery, InputMediaPhoto,
    ChatMemberUpdated
)

from aiogram.fsm.context import FSMContext
from magic_filter import F

# handmade modules
from botmodels.tasks import send_message_to_groups, send_message_async, add_task_to_queue
from botmodels.models import BotSetting, GroupProfile
import constants
# from botmodels.models import UserProfile
# import texts # mesage-templates


# ENV variables
# config = dotenv_values('.env')
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')

LANGUAGE = "ru"

# set dispatcher for tg bot handlers
dp = Dispatcher()

class ButtonAction():
    def __init__(
        self, title, inline=False, 
        eng=None, rus=None, callback_name=None, 
        takes_callback_query=False, *args, **kwargs):

        self.title = title
        self._eng = eng
        self._rus = rus
        self._inline = inline
        self._callback_name = callback_name
        self._takes_callback_query = takes_callback_query


    def get_text(self):
        if LANGUAGE == "ru":
            return self._rus
        else:
            return self._eng


    async def run(self, callback_query:CallbackQuery|Message, state:FSMContext, *args, **kwargs):
        callback = globals().get(self._callback_name)

        if callback and callable(callback):
            if self._takes_callback_query and isinstance(callback_query, CallbackQuery):
                await callback(callback_query, state, *args, **kwargs)
            else:
                if isinstance(callback_query, CallbackQuery):
                    await callback(callback_query.message, state, *args, **kwargs)
                else:
                    await callback(callback_query, state, *args, **kwargs)


class MessageAction():
    def __init__(self, title, callback_name=None, *args, **kwargs):
        self.title = title
        self._callback_name = callback_name


    async def run(self, *args, **kwargs):
        callback = globals().get(self._callback_name)

        if callback and callable(callback):
            await callback(*args, **kwargs)


BUTTON_ACTIONS = {
    "start": ButtonAction("start", inline=True, rus="Start", callback_name="start_handler"),
    "settings": ButtonAction("settings", inline=True, rus="⚙Настройки⚙", callback_name="go_to_settings"),
    "pause_sending": ButtonAction("pause_sending", inline=True, rus="⛔Остановить рассылку⛔", callback_name="pause_sending"),
    "start_sending": ButtonAction("start_sending", inline=True, rus="🟢Начать рассылку🟢", callback_name="start_sending"),
    "groups": ButtonAction("groups", inline=True, rus="👨‍👨‍👦‍👦Группы👨‍👨‍👦‍👦", callback_name="groups_handler"),
    "timings": ButtonAction("timings", inline=True, rus="⌚Тайминги⌚", callback_name="timings_handler"),
    "go_back": ButtonAction("go_back", inline=True, rus="🔙Назад🔙", callback_name="go_back_handler", takes_callback_query=True),
    "start_sending_option": ButtonAction("start_sending_option", inline=True, rus="Начало отправки", callback_name="start_sending_option"),
    "end_sending_option": ButtonAction("end_sending_option", inline=True, rus="Конец отправки", callback_name="end_sending_option"),
    "period_option": ButtonAction("period_option", inline=True, rus="Промежуток", callback_name="period_option"),
    "group_choice": ButtonAction("group_choice", inline=True, rus="Промежуток", callback_name="group_choice_handler"),
    "add_group": ButtonAction("add_group", inline=True, rus="Промежуток", callback_name="add_group_handler"),
}

# HELPER FUNCTIONS
async def update_actions_stack(state: FSMContext, action_name:str) -> None:
    data:dict = await state.get_data()
    if action_name not in BUTTON_ACTIONS: raise ValueError(f"There is no action with name {action_name}")
    actions_stack:list = data.get("actions_stack", [])
    actions_stack.append(action_name)
    await state.update_data(actions_stack=actions_stack)

async def set_input_action(state: FSMContext, action_name:str):
    await state.update_data(input_action=action_name)

async def pop_actions_stack(state: FSMContext) -> str|None:
    data:dict = await state.get_data()
    actions_stack:list = data.get("actions_stack", [])
    action_name:str = actions_stack.pop()
    await state.update_data(actions_stack=actions_stack)
    return action_name

# BUTTON ACTIONS HANDLERS
# ---------------------------------------------------------------------------------

async def go_to_settings(message: Message, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["groups"].get_text(), callback_data="groups"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["timings"].get_text(), callback_data="timings"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["go_back"].get_text(), callback_data="go_back"),
    )
    await message.edit_text(
        text="Настройки бота", 
        reply_markup=keyboard.as_markup()
    )
    await update_actions_stack(state, "settings")


async def pause_sending(message: Message, state: FSMContext):
    BotSetting().set("do_sending", False)
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text=BUTTON_ACTIONS["settings"].get_text(), callback_data="settings"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["start_sending"].get_text(), 
            callback_data="start_sending"
        )
    )
    await message.edit_text(
        text="Состояние рассылки: выключена", 
        reply_markup=keyboard.as_markup()
    )


async def start_sending(message: Message, state: FSMContext):
    BotSetting().set("do_sending", True)
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text=BUTTON_ACTIONS["settings"].get_text(), callback_data="settings"),
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["pause_sending"].get_text(), 
            callback_data="pause_sending"
        )
    )
    await message.edit_text(
        text="Состояние рассылки: включена", 
        reply_markup=keyboard.as_markup()
    )


async def groups_handler(message: Message, state: FSMContext):
    keyboard = InlineKeyboardBuilder()
    groups = await sync_to_async(list)(GroupProfile.objects.filter(deleted=False))
    
    for group in groups:
        status_symbol:str = '🟩' if group.active else '🟥'
        print("GROUPS_LIST")
        print(group.id, group.chat_id, group.group_name)
        keyboard.row(
            InlineKeyboardButton(
                text=f"{status_symbol}{group.group_name}", 
                callback_data=f"group_choice%{group.id}")
        )

    keyboard.row(
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["go_back"].get_text(), callback_data="go_back")
    )

    text:str = "🟩 - значит группа активна и в неё идет рассылка\n"+\
        "🟥- рассылка приостановлена\n\n"+\
        "Нажав на кнопку с названием группы вы изменяете данный статус"
    
    await message.edit_text(
        text=text,
        reply_markup=keyboard.as_markup()
    )
    await update_actions_stack(state, "groups")


async def group_choice_handler(message: Message, state: FSMContext, action_id:str):
    group = await sync_to_async(GroupProfile.objects.get)(id=int(action_id))
    group.active = not group.active
    await sync_to_async(group.save)()
    await BUTTON_ACTIONS[await pop_actions_stack(state)].run(message, state)



async def add_group_handler(message: Message, state: FSMContext):
    ... # I think we dont need it


async def timings_handler(message: Message, state: FSMContext, updated=False):
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
    start_sending_time = BotSetting().get('start_sending_time', settings.BOT_START_SENDING_TIME)
    end_sending_time = BotSetting().get('end_sending_time', settings.BOT_END_SENDING_TIME)
    period_sending_time = BotSetting().get('period_sending_time', settings.BOT_DEFAULT_COUNTDOWN)
    text = ("Настройка таймингов\n" if not updated else "Тайминги успешно обновлены!\n") +\
        f"Начало отправки: {start_sending_time}\n" +\
        f"Конец отправки: {end_sending_time}\n" +\
        f"Промежуток(пауза между отправками): {period_sending_time}\n"
    
    if not updated:
        await message.edit_text(
            text=text, 
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer(
            text=text, 
            reply_markup=keyboard.as_markup()
        )

    await update_actions_stack(state, "timings")


async def start_sending_option(message: Message, state: FSMContext, errors: list=None):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["go_back"].get_text(), callback_data="go_back")
    )
    
    errors_str = "\n".join([error["message"] for error in errors]) if errors else ""
    text=f"{errors_str}\nВведите время формата HH:ss " +\
        "(например, ввод `8:30` означает старт в 8 часов 30 минут)"
    
    if not errors:
        await message.edit_text(
            text=text, 
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer(
            text=text, 
            reply_markup=keyboard.as_markup()
        )
    await update_actions_stack(state, "start_sending_option")
    await set_input_action(state, "start_sending_time")


async def end_sending_option(message: Message, state: FSMContext, errors: list=None):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["go_back"].get_text(), callback_data="go_back")
    )

    errors_str = "\n".join([error["message"] for error in errors]) if errors else ""
    text = f"{errors_str}\nВведите время формата HH:ss "+\
        "(например, ввод `22:30` означает конец отправки в 22 часов 30 минут)"

    if not errors:
        await message.edit_text(
            text=text, 
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer(
            text=text, 
            reply_markup=keyboard.as_markup()
        )
    await update_actions_stack(state, "end_sending_option")
    await set_input_action(state, "end_sending_time")


async def period_option(message: Message, state: FSMContext, errors: list=None):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text=BUTTON_ACTIONS["go_back"].get_text(), callback_data="go_back")
    )

    errors_str = "\n".join([error["message"] for error in errors]) if errors else ""
    text=f"{errors_str}\nВведите время формата mm:ss " +\
        "(например, ввод `5:30` означает обновление раз в 5 минут 30 секунд)"

    if not errors:
        await message.edit_text(
            text=text, 
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer(
            text=text, 
            reply_markup=keyboard.as_markup()
        )

    await update_actions_stack(state, "period_option")
    await set_input_action(state, "period_time")


async def go_back_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    actions_stack = data.get("actions_stack")
    actions_stack.pop()
    await state.update_data(go_back_called=True)
    await state.update_data(input_action=None)
    await BUTTON_ACTIONS[actions_stack.pop()].run(callback_query, state)


async def start_handler(message: Message, state: FSMContext):
    pause_sending = BotSetting().get("do_sending", False)

    data = await state.get_data()
    go_back_called = data.get("go_back_called", False)
    await state.update_data(go_back_called=False)
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

    period:str = BotSetting().get("period_sending_time", settings.BOT_DEFAULT_COUNTDOWN)
    if go_back_called:
        await message.edit_text(
            f"Здравствуйте, {html.bold(message.from_user.full_name)}!\n" +\
            f"Данный бот обрабатывает пересылаемые сообщения и рассылает их раз в {period} минут",
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer(
            f"Здравствуйте, {html.bold(message.from_user.full_name)}!\n" +\
            f"Данный бот обрабатывает пересылаемые сообщения и рассылает их раз в {period} минут",
            reply_markup=keyboard.as_markup()
        )

    await update_actions_stack(state, "start")

# ---------------------------------------------------------------------------------

@dp.callback_query()
async def button_inline_actions_handler(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.message.chat.type != ChatType.PRIVATE: return
    data:list = callback_query.data.split('%')
    action_name:str = data[0]
    action_id:str = None
    if len(data) > 1:
        action_id = data[1]
    
    btn_action:ButtonAction = BUTTON_ACTIONS.get(action_name)
    if not btn_action: return

    if action_id:
        await btn_action.run(callback_query, state, action_id=action_id)
    else:
        await btn_action.run(callback_query, state)


BUTTON_ACTIONS_SEARCH_DICT = {
    btn_action.get_text():btn_action for btn_action in BUTTON_ACTIONS.values()
}

@dp.message(lambda message: message.text in BUTTON_ACTIONS_SEARCH_DICT.keys())
async def button_actions_handler(message: Message):
    if message.chat.type != ChatType.PRIVATE: return
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
    if message.chat.type != ChatType.PRIVATE: return
    await start_handler(message, state)


@dp.message(lambda message: message.forward_date is not None)
async def forward_message_handler(message: Message):
    # print(str(message) + "\n" + ("-"*80) + "\n")
    if message.chat.type != ChatType.PRIVATE: return

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


# MESSAGE ACTIONS HANDLERS
# ---------------------------------------------------------------------------------
MESSAGE_ACTIONS = {
    "start_sending_time": MessageAction("start_sending_time", "start_sending_input_handler"),
    "end_sending_time": MessageAction("start_sending_time", "end_sending_input_handler"),
    "period_time": MessageAction("start_sending_time", "period_input_handler"),
}

def is_valid_time(time_str: str) -> bool:
    try:
        hours, minutes = map(int, time_str.split(":"))
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except (ValueError, AttributeError):
        return False

def is_valid_period(time_str: str) -> bool:
    try:
        minutes, seconds = map(int, time_str.split(":"))
        return (0 <= minutes <= 59) and (0 <= seconds <= 59)
    except (ValueError, AttributeError):
        return False

async def start_sending_input_handler(message: Message, state: FSMContext):
    input_text = message.text.strip().replace(" ", "")
    
    if not is_valid_time(input_text):
        errors = [{message: "Некорректный формат ввода, попробуйте еще раз"}]
        return await BUTTON_ACTIONS[await pop_actions_stack(state)].run(message, state, errors)
    
    BotSetting().set("start_sending_time", input_text)

    await pop_actions_stack(state)
    await BUTTON_ACTIONS[await pop_actions_stack(state)]\
        .run(message, state, updated=True)


async def end_sending_input_handler(message: Message, state: FSMContext):
    input_text = message.text.strip().replace(" ", "")
    
    if not is_valid_time(input_text):
        errors = [{message: "Некорректный формат ввода, попробуйте еще раз"}]
        return await BUTTON_ACTIONS[await pop_actions_stack(state)].run(message, state, errors)
    
    BotSetting().set("end_sending_time", input_text)
    
    await pop_actions_stack(state)
    await BUTTON_ACTIONS[await pop_actions_stack(state)]\
        .run(message, state, updated=True)


async def period_input_handler(message: Message, state: FSMContext):
    input_text = message.text.strip().replace(" ", "")
    
    if not is_valid_period(input_text):
        errors = [{message: "Некорректный формат ввода, попробуйте еще раз"}]
        return await BUTTON_ACTIONS[await pop_actions_stack(state)].run(message, state, errors)
    
    BotSetting().set("period_sending_time", input_text)
    
    await pop_actions_stack(state)
    await BUTTON_ACTIONS[await pop_actions_stack(state)]\
        .run(message, state, updated=True)

# ---------------------------------------------------------------------------------


@dp.message()
async def message_main_handler(message: Message, state: FSMContext):
    print("MESSAGE_TYPE: ", message.chat.type)
    if message.chat.type in {"group", "supergroup"}:
        print("TRY TO CREATE NEW GROUP: ", message.chat)
        group_id = message.chat.id
        cached_groups:list = cache.get("bot_groups_ids", list())
        if group_id in cached_groups: return

        new_group, created = await GroupProfile.objects.aupdate_or_create(
            chat_id=group_id,
            defaults={
                "group_name": message.chat.title
            }
        )
        print("GROUP CREATED: ", created)
        cached_groups = cached_groups.append(new_group)
        
        cache.set("bot_groups_ids", cached_groups, timeout=constants.CACHE_TIMEOUT_DAY)
        return
    
    if message.chat.type != ChatType.PRIVATE: return

    data = await state.get_data()
    input_action:str = data.get("input_action")
    if not input_action: return
    await MESSAGE_ACTIONS[input_action].run(message, state)
    await state.update_data(input_action=None)
# ---------------------------------------------------------------------------------

@dp.chat_member(ChatMemberUpdated)
async def handle_bot_left_group(event: ChatMemberUpdated):
    if event.new_chat_member.status == "left" and event.new_chat_member.user.id == event.bot.id:
        group_id = event.chat.id
        try:
            group = GroupProfile.objects.get(chat_id=group_id)
            group.active = False
            group.deleted = True
            group.save()
        except GroupProfile.DoesNotExist:
            pass


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
