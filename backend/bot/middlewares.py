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
    """يعيد قائمة القنوات التي لم يشترك بها المستخدم"""
    channels = await db.list_forced_channels()
    if not channels:
        return []
    not_subscribed = []
    for ch in channels:
        chat_id = ch["chat_id"]
        chat_ref = normalize_chat_ref(chat_id)
        try:
            member = await bot.get_chat_member(chat_ref, user_id)
            status = getattr(member, "status", None)
            if status in ("member", "administrator", "creator", "owner"):
                continue
            elif status in ("left", "kicked"):
                not_subscribed.append(ch)
            elif status == "restricted":
                is_member = getattr(member, "is_member", True)
                if is_member:
                    continue
                else:
                    not_subscribed.append(ch)
            else:
                not_subscribed.append(ch)
        except Exception as e:
            err_msg = str(e).lower()
            logger.warning(f"Error checking membership for user {user_id} in {chat_ref}: {e}")
            not_subscribed.append(ch)
    return not_subscribed


class ForceSubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            # اسمح لزر التحقق من الاشتراك دائماً
            if event.data in ALLOWED_CALLBACKS:
                return await handler(event, data)
        else:
            return await handler(event, data)

        if not user:
            return await handler(event, data)

        # تجاوز الأدمن
        if await is_admin_or_authorized(user.id, user.username or ""):
            return await handler(event, data)

        bot: Bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        not_subscribed = await check_user_subscribed(bot, user.id)
        if not not_subscribed:
            return await handler(event, data)

        # يجب الاشتراك أولاً
        text = (
            "⛔ <b>يجب الاشتراك في القنوات التالية للاستمرار</b>\n\n"
            "اشترك ثم اضغط زر «تحققت من الاشتراك» 👇"
        )
        kb = force_sub_kb(not_subscribed)
        try:
            if isinstance(event, Message):
                from aiogram.types import ReplyKeyboardRemove
                # Send a temporary message to hide the reply keyboard if active on the user's client
                hide_msg = await event.answer("⏳ جاري التحقق من الاشتراك...", reply_markup=ReplyKeyboardRemove())
                try:
                    await hide_msg.delete()
                except Exception:
                    pass
                await event.answer(text, reply_markup=kb)
            else:  # CallbackQuery
                await event.answer("اشترك بالقنوات أولاً", show_alert=True)
                try:
                    await event.message.answer(text, reply_markup=kb)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Failed to send force-sub message: {e}")
        return  # منع تشغيل الهاندلر الأصلي
