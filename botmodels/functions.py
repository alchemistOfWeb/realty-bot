from django.db.models import Q, Case, When, IntegerField
from .models import TgSetting
from typing import List, Optional
from asgiref.sync import sync_to_async

async def get_setting_by_chat_id(bot_chat_id) -> Optional[TgSetting]:
    setting:TgSetting = await sync_to_async(TgSetting.objects\
        .filter(Q(user_profile__isnull=True) | Q(user_profile__chat_id=int(bot_chat_id)))\
        .annotate(
            priority=Case(
                When(user_profile__chat_id=bot_chat_id, then=0),
                When(user_profile__isnull=True, then=1),
                default=2,
                output_field=IntegerField(),
            )
        )
        .order_by("priority")\
        .first)()

    return setting

async def get_setting_by_user_id(user_id) -> Optional[TgSetting]:
    setting:TgSetting = await sync_to_async(TgSetting.objects\
        .filter(Q(user_profile__isnull=True) | Q(user_profile__id=int(user_id)))\
        .annotate(
            priority=Case(
                When(user_profile__id=user_id, then=0),
                When(user_profile__isnull=True, then=1),
                default=2,
                output_field=IntegerField(),
            )
        )
        .order_by("priority")\
        .first)()

    return setting
