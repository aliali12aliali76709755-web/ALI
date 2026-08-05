"""
هاندلرات لوحة تحكم الأدمن (/admin)
"""
import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import settings
from bot.states import AdminStates
from bot.keyboards import admin_panel_kb, admin_back_kb, main_menu_kb
from bot import database as db

router = Router(name="admin")

ADMIN_ID = settings.ADMIN_ID


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ─────────────────────────── /admin ───────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return  # تجاهل - نفس رد المستخدم العادي
    await state.clear()
    await message.answer(
        "👑 <b>لوحة تحكم الأدمن</b>\n\nاختر إجراءً:",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "admin_back")
async def cb_admin_back(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id):
        await cq.answer()
        return
    await state.clear()
    await cq.message.edit_text(
        "👑 <b>لوحة تحكم الأدمن</b>\n\nاختر إجراءً:",
        reply_markup=admin_panel_kb(),
    )
    await cq.answer()


# ─────────────────────────── إحصائيات البوت ───────────────────────────

@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer()
        return
    s = await db.get_bot_stats()
    text = (
        "📊 <b>إحصائيات البوت</b>\n\n"
        f"👥 إجمالي المستخدمين: <b>{s['total_users']}</b>\n"
        f"💎 مشتركو VIP النشطون: <b>{s['vip_users']}</b>\n\n"
        f"💰 <b>إجمالي الأرباح:</b>\n"
        f"   ⭐ من Telegram Stars: <b>{s['total_stars']}</b>\n"
        f"   💵 من الدفع اليدوي (USD): <b>${s['total_usd']}</b>"
    )
    await cq.message.edit_text(text, reply_markup=admin_back_kb())
    await cq.answer()


# ─────────────────────────── الإذاعة (Broadcast) ───────────────────────────

@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id):
        await cq.answer()
        return
    await state.set_state(AdminStates.waiting_broadcast_message)
    await cq.message.edit_text(
        "📢 <b>الإذاعة العامة</b>\n\n"
        "أرسل الرسالة التي تريد إرسالها لجميع مستخدمي البوت.\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=admin_back_kb(),
    )
    await cq.answer()


@router.message(AdminStates.waiting_broadcast_message, Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم إلغاء الإذاعة.", reply_markup=admin_panel_kb())


@router.message(AdminStates.waiting_broadcast_message)
async def receive_broadcast(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    user_ids = await db.get_all_user_ids()
    await message.answer(f"⏳ جارٍ إرسال الرسالة إلى {len(user_ids)} مستخدم...")

    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
            sent += 1
            # تجنب Flood limit من تليجرام
            if sent % 25 == 0:
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await message.answer(
        f"✅ <b>تمت الإذاعة</b>\n\n"
        f"📤 نجح الإرسال: <b>{sent}</b>\n"
        f"❌ فشل الإرسال: <b>{failed}</b>",
        reply_markup=admin_panel_kb(),
    )


# ─────────────────────────── ترقية مستخدم إلى VIP ───────────────────────────

@router.callback_query(F.data == "admin_upgrade")
async def cb_admin_upgrade(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id):
        await cq.answer()
        return
    await state.set_state(AdminStates.waiting_upgrade_user_id)
    await cq.message.edit_text(
        "💎 <b>ترقية مستخدم إلى VIP</b>\n\n"
        "أرسل <b>آيدي</b> المستخدم (رقم) لترقيته يدوياً لمدة سنة.\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=admin_back_kb(),
    )
    await cq.answer()


@router.message(AdminStates.waiting_upgrade_user_id, Command("cancel"))
async def cancel_upgrade(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.", reply_markup=admin_panel_kb())


@router.message(AdminStates.waiting_upgrade_user_id)
async def do_upgrade(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("⚠️ أرسل آيدي رقمي صحيح.")
        return
    target_id = int(text)
    user = await db.get_user(target_id)
    if not user:
        await message.answer("⚠️ المستخدم غير مسجل في البوت.")
        return
    await db.set_vip_status(target_id, True, days=settings.VIP_DURATION_DAYS)
    await db.create_payment(
        user_id=target_id, amount=settings.VIP_USD_PRICE,
        currency="USD", status="completed", charge_id="manual_admin",
    )
    await state.clear()
    await message.answer(
        f"✅ تم ترقية المستخدم <code>{target_id}</code> إلى VIP لمدة سنة.",
        reply_markup=admin_panel_kb(),
    )
    # إشعار المستخدم
    try:
        await bot.send_message(
            target_id,
            "🎉 <b>تم تفعيل اشتراكك VIP بنجاح!</b>\n"
            f"⏳ صالح لمدة {settings.VIP_DURATION_DAYS} يوم.\n\n"
            "استمتع بجميع الميزات الحصرية ✨",
            reply_markup=main_menu_kb(is_vip=True),
        )
    except Exception:
        pass


# ─────────────────────────── إلغاء اشتراك VIP ───────────────────────────

@router.callback_query(F.data == "admin_downgrade")
async def cb_admin_downgrade(cq: CallbackQuery, state: FSMContext):
    if not is_admin(cq.from_user.id):
        await cq.answer()
        return
    await state.set_state(AdminStates.waiting_downgrade_user_id)
    await cq.message.edit_text(
        "❌ <b>إلغاء اشتراك VIP</b>\n\n"
        "أرسل <b>آيدي</b> المستخدم لإرجاعه إلى الخطة المجانية.\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=admin_back_kb(),
    )
    await cq.answer()


@router.message(AdminStates.waiting_downgrade_user_id, Command("cancel"))
async def cancel_downgrade(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.", reply_markup=admin_panel_kb())


@router.message(AdminStates.waiting_downgrade_user_id)
async def do_downgrade(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("⚠️ أرسل آيدي رقمي صحيح.")
        return
    target_id = int(text)
    user = await db.get_user(target_id)
    if not user:
        await message.answer("⚠️ المستخدم غير مسجل في البوت.")
        return
    await db.set_vip_status(target_id, False)
    await state.clear()
    await message.answer(
        f"✅ تم إلغاء VIP للمستخدم <code>{target_id}</code>.",
        reply_markup=admin_panel_kb(),
    )
    try:
        await bot.send_message(
            target_id,
            "ℹ️ تم إلغاء اشتراك VIP الخاص بك. تم إرجاع حسابك إلى الخطة المجانية.",
            reply_markup=main_menu_kb(is_vip=False),
        )
    except Exception:
        pass
