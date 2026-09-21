"""
Middleware للتحقق من الاشتراك الإجباري بالقنوات على كل تفاعل مع البوت
"""
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, TelegramObject

from bot import database as db
from bot.keyboards import force_sub_kb
from bot.admin_utils import is_admin_or_authorized

logger = logging.getLogger("force_sub")

# الأحداث المستثناة (مثلاً لأزرار التحقق من الاشتراك نفسها والدفع)
ALLOWED_CALLBACKS = {"check_subscription"}


def normalize_chat_ref(chat_id: str) -> Any:
    chat_id = str(chat_id).strip()
    if "t.me/" in chat_id:
        part = chat_id.split("t.me/")[-1].strip("/")
        if not part.startswith("+") and not part.startswith("joinchat/"):
            return f"@{part}"
    try:
        return int(chat_id)
    except (ValueError, TypeError):
        pass
    if not chat_id.startswith("@") and not chat_id.startswith("-"):
        return f"@{chat_id}"
    return chat_id


async def check_user_subscribed(bot: Bot, user_id: int) -> list:
    """كل شيء مجاني بالكامل - لا يوجد اشتراك إجباري"""
    return []


class ForceSubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        return await handler(event, data)

