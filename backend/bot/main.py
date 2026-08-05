"""
تهيئة البوت (Bot + Dispatcher) وتشغيل الـ Polling
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot import database as db
from bot.handlers import user_handlers, payment_handlers, admin_handlers

logger = logging.getLogger("bot")


def build_bot() -> Bot:
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    # ترتيب الروترز مهم: الأدمن أولاً حتى لا يتم التقاط رسائل FSM الخاصة به من قِبل روتر المستخدم
    dp.include_router(admin_handlers.router)
    dp.include_router(payment_handlers.router)
    dp.include_router(user_handlers.router)
    return dp


async def run_bot_polling() -> None:
    """تشغيل الـ polling للبوت (يعمل داخل حلقة asyncio الخاصة بـ FastAPI)"""
    await db.init_db()
    bot = build_bot()
    dp = build_dispatcher()
    # حذف أي webhook قديم قبل تشغيل الـ polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f"delete_webhook failed: {e}")

    logger.info("🤖 Bot polling started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("🤖 Bot polling stopped")
