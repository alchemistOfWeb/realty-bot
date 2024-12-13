from django.db.models import Q
from .models import TgSetting
from typing import List
from asgiref.sync import sync_to_async

async def get_setting_by_chat_id(bot_chat_id) -> TgSetting|None:
    usersetting_list:List[TgSetting] = await sync_to_async(list)(TgSetting.objects\
        .filter(Q(user_profile__isnull=True) | Q(user_profile__chat_id=int(bot_chat_id))))

    if len(usersetting_list) > 1:
        return usersetting_list[0] if usersetting_list[0].user_profile else usersetting_list[1]
    elif len(usersetting_list) == 1:
        return usersetting_list[0]
    else:
        return None
