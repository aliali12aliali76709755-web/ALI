"""
تهيئة البوت (Bot + Dispatcher) وتشغيل الـ Polling
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import settings
from bot import database as db
from bot.handlers import user_handlers, payment_handlers, admin_handlers
from bot.middlewares import ForceSubscriptionMiddleware

logger = logging.getLogger("bot")


BOT_COMMANDS = [
    BotCommand(command="start", description="🚀 تشغيل البوت"),
    BotCommand(command="vip", description="💎 اشتراك VIP"),
    BotCommand(command="contact", description="📞 تواصل مع الدعم الفني"),
]


from aiogram.client.session.aiohttp import AiohttpSession

def build_bot() -> Bot:
    session = AiohttpSession(timeout=45.0)
    return Bot(
        token=settings.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    force_sub = ForceSubscriptionMiddleware()
    dp.message.outer_middleware(force_sub)
    dp.callback_query.outer_middleware(force_sub)
    dp.include_router(admin_handlers.router)
    dp.include_router(payment_handlers.router)
    dp.include_router(user_handlers.router)
    return dp


async def run_bot_polling() -> None:
    await db.init_db()
    await db.grant_admin_session(settings.ADMIN_ID)

    bot = build_bot()
    dp = build_dispatcher()

    try:
        await bot.delete_webhook(drop_pending_updates=False)
    except Exception as e:
        logger.warning(f"delete_webhook failed: {e}")

    try:
        await bot.set_my_commands(BOT_COMMANDS)
        logger.info("Bot commands registered")
    except Exception as e:
        logger.warning(f"set_my_commands failed: {e}")

    logger.info("🤖 Bot polling started")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            polling_timeout=30,
            handle_signals=False,
            close_bot_session=True,
        )
    except Exception as e:
        logger.error(f"Error during polling: {e}", exc_info=True)
    finally:
        try:
            await bot.session.close()
        except Exception:
            pass
        logger.info("🤖 Bot polling stopped")
