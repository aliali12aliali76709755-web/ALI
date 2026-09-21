"""
هاندلرات لوحة تحكم الأدمن:
- الدخول عن طريق كلمة "صويري" + كلمة السر
- إدارة المستخدمين، الإذاعة، القنوات الإجبارية، الإحالات، الحظر، الرسائل الخاصة
"""
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import settings
from bot.states import AdminStates, AdminAuthStates
from bot.keyboards import (
    admin_panel_kb, admin_back_kb, main_menu_kb,
    admin_channels_kb, admin_referrals_kb, admin_vip_durations_kb,
)
from bot import database as db
from bot.admin_utils import is_admin_or_authorized
from bot.middlewares import normalize_chat_ref

logger = logging.getLogger("admin")
router = Router(name="admin")


# ─────────────────────────── بوابة كلمة السر (صويري + 76891796) ───────────────────────────

@router.message(F.text == settings.ADMIN_PANEL_TRIGGER_WORD)
async def trigger_admin_login(message: Message, state: FSMContext):
    """عند إرسال كلمة (صويري) - نطلب كلمة السر"""
    await state.clear()
    await state.set_state(AdminAuthStates.waiting_password)
    await message.answer(
        "🔐 <b>لوحة التحكم محمية</b>\n\n"
        "أدخل <b>كلمة السر</b> للدخول إلى لوحة التحكم:"
    )


@router.message(AdminAuthStates.waiting_password)
async def check_admin_password(message: Message, state: FSMContext):
    entered = (message.text or "").strip()
    if entered != settings.ADMIN_PANEL_PASSWORD:
        # لا تدخله نهائياً كما طلب المستخدم
        await state.clear()
        # نتجاهل بصمت (بدون رسالة كي لا نُلمّح بوجود لوحة تحكم)
        return
    await state.clear()
    # منح جلسة أدمن دائمة لهذا المستخدم
    await db.grant_admin_session(message.from_user.id)
    # حاول حذف رسالة كلمة السر لأمان أكثر
    try:
        await message.delete()
    except Exception:
        pass
    await message.answer(
        "✅ <b>تم قبولك في لوحة التحكم</b>\n\n"
        "👑 <b>لوحة تحكم الأدمن</b>\n\nاختر إجراءً من الأسفل:",
        reply_markup=admin_panel_kb(),
    )


# ─────────────────────────── حماية باقي الهاندلرات ───────────────────────────

async def _guard(cq: CallbackQuery) -> bool:
    """يرجع True إذا مسموح، ويردّ ذاتياً إذا لا"""
    if await is_admin_or_authorized(cq.from_user.id, cq.from_user.username or ""):
        return True
    await cq.answer("⛔ لا تملك صلاحية.", show_alert=True)
    return False


@router.callback_query(F.data == "admin_back")
async def cb_admin_back(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        return
    await state.clear()
    try:
        await cq.message.edit_text(
            "👑 <b>لوحة تحكم الأدمن</b>\n\nاختر إجراءً:",
            reply_markup=admin_panel_kb(),
        )
    except Exception:
        await cq.message.answer(
            "👑 <b>لوحة تحكم الأدمن</b>",
            reply_markup=admin_panel_kb(),
        )
    await cq.answer()


@router.callback_query(F.data == "admin_logout")
async def cb_admin_logout(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        return
    # لا نلغي جلسة الأدمن الأصلي بالـID
    if cq.from_user.id != settings.ADMIN_ID:
        await db.revoke_admin_session(cq.from_user.id)
    await state.clear()
    await cq.message.edit_text("🔒 تم تسجيل الخروج من لوحة التحكم.")
    await cq.answer()


# ─────────────────────────── إحصائيات البوت ───────────────────────────

@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(cq: CallbackQuery):
    if not await _guard(cq):
        return
    s = await db.get_bot_stats()
    text = (
        "📊 <b>إحصائيات البوت</b>\n\n"
        f"👥 إجمالي المستخدمين: <b>{s['total_users']}</b>\n"
        f"🟢 نشطون اليوم: <b>{s['active_today']}</b>\n"
        f"💎 مشتركو VIP النشطون: <b>{s['vip_users']}</b>\n"
        f"🚫 المحظورون: <b>{s['banned']}</b>\n\n"
        f"📢 قنوات الاشتراك الإجباري: <b>{s['total_channels']}</b>\n"
        f"🎁 إجمالي الإحالات: <b>{s['total_referrals']}</b>\n\n"
        f"💰 <b>الأرباح:</b>\n"
        f"   ⭐ Telegram Stars: <b>{s['total_stars']}</b>\n"
        f"   💵 Manual (USD): <b>${s['total_usd']}</b>"
    )
    await cq.message.edit_text(text, reply_markup=admin_back_kb())
    await cq.answer()


# ─────────────────────────── الإذاعة (Broadcast) ───────────────────────────

@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        return
    await state.set_state(AdminStates.waiting_broadcast_message)
    await cq.message.edit_text(
        "📢 <b>الإذاعة الجماعية</b>\n\n"
        "أرسل الآن الرسالة (نص/صورة/فيديو/ملصق) لإرسالها لجميع مستخدمي البوت.\n"
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
    if not await is_admin_or_authorized(message.from_user.id, message.from_user.username or ""):
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
    if not await _guard(cq):
        return
    await state.set_state(AdminStates.waiting_upgrade_user_id)
    await cq.message.edit_text(
        "💎 <b>إرسال / ترقية اشتراك VIP لمستخدم</b>\n\n"
        "أرسل <b>آيدي</b> المستخدم (أرقام) أو <b>يوزره</b> (@username).\n"
        "بعدها ستظهر لك لوحة لاختيار مدة الاشتراك المطلوبة (أسبوع، شهر، سنة، مدى الحياة...).\n\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=admin_back_kb(),
    )
    await cq.answer()


@router.message(AdminStates.waiting_upgrade_user_id, Command("cancel"))
async def cancel_upgrade(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.", reply_markup=admin_panel_kb())


async def _resolve_target_user(text: str):
    text = text.strip().lstrip("@")
    if text.isdigit():
        uid = int(text)
        user = await db.get_user(uid)
        if not user:
            # Create user placeholder in DB if valid telegram ID
            await db.get_or_create_user(uid, "", f"مستخدم {uid}")
            user = await db.get_user(uid)
        return user
    return await db.get_user_by_username(text)


@router.message(AdminStates.waiting_upgrade_user_id)
async def do_upgrade(message: Message, state: FSMContext):
    if not await is_admin_or_authorized(message.from_user.id, message.from_user.username or ""):
        return
    user = await _resolve_target_user(message.text or "")
    if not user:
        await message.answer("⚠️ لم يتم العثور على هذا المستخدم. تأكد من صحة اليوزر أو الآيدي.")
        return

    target_id = user["user_id"]
    is_vip = await db.is_user_vip(target_id)
    name = user.get("full_name") or f"مستخدم {target_id}"
    uname = f"@{user['username']}" if user.get("username") else "بدون يوزر"
    
    vip_info = "👑 مشترك VIP" if is_vip else "⚪ حساب مجاني"
    if is_vip and user.get("vip_expires"):
        exp = "مدى الحياة (دائم ✨)" if user["vip_expires"].startswith("9999-") else user["vip_expires"][:10]
        vip_info += f" (ينتهي: <code>{exp}</code>)"
    
    text = (
        "👤 <b>بطاقة المستخدم:</b>\n\n"
        f"• الاسم: <b>{name}</b>\n"
        f"• اليوزر: <b>{uname}</b>\n"
        f"• الآيدي: <code>{target_id}</code>\n"
        f"• الحالة الحالية: <b>{vip_info}</b>\n\n"
        "👇 <b>اختر مدة اشتراك VIP التي تريد منحها له:</b>"
    )
    await state.clear()
    await message.answer(text, reply_markup=admin_vip_durations_kb(target_id))


@router.callback_query(F.data.startswith("admin_set_vip:"))
async def cb_admin_set_vip(cq: CallbackQuery, bot: Bot):
    if not await _guard(cq):
        return
    
    parts = cq.data.split(":")
    if len(parts) != 3:
        await cq.answer("خطأ في البيانات.", show_alert=True)
        return
    
    target_id = int(parts[1])
    days = int(parts[2])
    
    user = await db.get_user(target_id)
    user_name = user.get("full_name") if user else f"مستخدم {target_id}"
    
    if days == 0:
        # إلغاء VIP
        await db.set_vip_status(target_id, False)
        await cq.message.edit_text(
            f"✅ <b>تم إلغاء اشتراك VIP بنجاح!</b>\n\n"
            f"👤 المستخدم: <b>{user_name}</b> (<code>{target_id}</code>)\n"
            f"الحساب الآن: <b>مجاني عادي</b>.",
            reply_markup=admin_panel_kb(),
        )
        await cq.answer("تم إلغاء الاشتراك بنجاح")
        try:
            await bot.send_message(
                target_id,
                "ℹ️ <b>تنبيه من الإدارة:</b> تم إلغاء اشتراك VIP الخاص بك وإرجاع حسابك إلى الخطة المجانية.",
                reply_markup=main_menu_kb(is_vip=False),
            )
        except Exception:
            pass
        return

    # تحديد اسم المدة
    duration_labels = {
        7: "أسبوع واحد (7 أيام)",
        30: "شهر واحد (30 يوم)",
        90: "3 أشهر (90 يوم)",
        180: "6 أشهر (180 يوم)",
        365: "سنة كاملة (365 يوم)",
        730: "سنتين (730 يوم)",
        99999: "مدى الحياة (اشتراك دائم للأبد ✨)",
    }
    label = duration_labels.get(days, f"{days} يوم")
    
    await db.set_vip_status(target_id, True, days=days)
    await db.create_payment(
        user_id=target_id, amount=0, currency="STARS",
        status="completed", charge_id="admin_gift", purpose=f"vip_gift_{days}d",
    )
    
    await cq.message.edit_text(
        f"🎉 <b>تم منح اشتراك VIP بنجاح!</b>\n\n"
        f"👤 المستخدم: <b>{user_name}</b> (<code>{target_id}</code>)\n"
        f"⏳ المدة المحددة: <b>{label}</b>\n\n"
        "تم إرسال إشعار ترحيبي للمستخدم وتفعيل الميزات له فوراً.",
        reply_markup=admin_panel_kb(),
    )
    await cq.answer("تم تفعيل VIP بنجاح!")
    
    try:
        await bot.send_message(
            target_id,
            f"🎉 <b>تهانينا الحارة!</b>\n\n"
            f"قام المشرف/المطور بمنحك <b>اشتراك VIP مجاناً!</b> 💎\n"
            f"⏳ مدة الاشتراك: <b>{label}</b>.\n\n"
            "استمتع بكافة الميزات الحصرية، القوالب البريميوم، وتخصيص صفحتك الشخصية الآن! ✨",
            reply_markup=main_menu_kb(is_vip=True),
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_id} of VIP grant: {e}")


# ─────────────────────────── إلغاء VIP (عبر إدخال المعرف المباشر) ───────────────────────────

@router.callback_query(F.data == "admin_downgrade")
async def cb_admin_downgrade(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        return
    await state.set_state(AdminStates.waiting_downgrade_user_id)
    await cq.message.edit_text(
        "❌ <b>إلغاء اشتراك VIP</b>\n\n"
        "أرسل <b>آيدي</b> أو <b>يوزر</b> المستخدم لإلغاء اشتراكه فوراً.\n"
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
    if not await is_admin_or_authorized(message.from_user.id, message.from_user.username or ""):
        return
    user = await _resolve_target_user(message.text or "")
    if not user:
        await message.answer("⚠️ المستخدم غير موجود.")
        return
    await db.set_vip_status(user["user_id"], False)
    await state.clear()
    await message.answer(
        f"✅ تم إلغاء VIP للمستخدم <code>{user['user_id']}</code>.",
        reply_markup=admin_panel_kb(),
    )
    try:
        await bot.send_message(
            user["user_id"],
            "ℹ️ تم إلغاء اشتراك VIP الخاص بك. تم إرجاع حسابك إلى الخطة المجانية.",
            reply_markup=main_menu_kb(is_vip=False),
        )
    except Exception:
        pass


# ─────────────────────────── القنوات الإجبارية ───────────────────────────

@router.callback_query(F.data == "admin_channels")
async def cb_admin_channels(cq: CallbackQuery):
    if not await _guard(cq):
        return
    channels = await db.list_forced_channels()
    if channels:
        lines = ["📢 <b>قنوات/قروبات الاشتراك الإجباري</b>\n"]
        for i, ch in enumerate(channels, 1):
            lines.append(f"{i}. <b>{ch['title'] or 'قناة'}</b>\n   ID: <code>{ch['chat_id']}</code>\n   🔗 {ch['invite_url']}")
        text = "\n".join(lines)
    else:
        text = "📢 <b>لا توجد قنوات مضافة حالياً.</b>\n\nأضف قناة أو قروب لجعل الاشتراك بها إجبارياً."
    await cq.message.edit_text(text, reply_markup=admin_channels_kb(bool(channels)))
    await cq.answer()


@router.callback_query(F.data == "admin_add_channel")
async def cb_add_channel(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        return
    await state.set_state(AdminStates.waiting_add_channel)
    await cq.message.edit_text(
        "➕ <b>إضافة قناة/قروب للاشتراك الإجباري</b>\n\n"
        "أرسل <b>يوزر القناة</b> (مثل: <code>@mychannel</code>) أو <b>رابطها</b> (مثل: <code>https://t.me/mychannel</code>) أو الآيدي (مثل: <code>-1001234567890</code>).\n\n"
        "أو أرسل النموذج الكامل للقنوات الخاصة:\n"
        "<code>chat_id | عنوان القناة | رابط الدعوة</code>\n\n"
        "⚠️ <b>مهم جداً:</b> تأكد من رفع البوت مشرفاً (Admin) في القناة/القروب بصلاحية دعوة المستخدمين حتى يستطيع فحص اشتراكهم بدقة.\n\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=admin_back_kb(),
    )
    await cq.answer()


@router.message(AdminStates.waiting_add_channel, Command("cancel"))
async def cancel_add_channel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.", reply_markup=admin_panel_kb())


@router.message(AdminStates.waiting_add_channel)
async def do_add_channel(message: Message, state: FSMContext, bot: Bot):
    if not await is_admin_or_authorized(message.from_user.id, message.from_user.username or ""):
        return
    raw_text = (message.text or "").strip()
    
    chat_id = ""
    title = ""
    invite_url = ""
    
    if "|" in raw_text:
        parts = [p.strip() for p in raw_text.split("|")]
        if len(parts) == 3:
            chat_id, title, invite_url = parts
        elif len(parts) == 2:
            chat_id, invite_url = parts
    else:
        chat_id = raw_text
        
    if not invite_url and "t.me/" in chat_id:
        invite_url = chat_id if chat_id.startswith("http") else f"https://{chat_id}"
        
    chat_ref = normalize_chat_ref(chat_id)
    is_bot_admin = False
    
    try:
        chat_info = await bot.get_chat(chat_ref)
        if not title:
            title = chat_info.title or chat_info.username or "قناة"
        if not invite_url:
            if chat_info.username:
                invite_url = f"https://t.me/{chat_info.username}"
            elif chat_info.invite_link:
                invite_url = chat_info.invite_link
        
        bot_member = await bot.get_chat_member(chat_ref, bot.id)
        is_bot_admin = bot_member.status in ("administrator", "creator")
    except Exception as e:
        logger.warning(f"Could not auto-fetch chat info for {chat_ref}: {e}")
        
    if not title:
        title = "قناة/جروب"
    if not invite_url:
        invite_url = f"https://t.me/{str(chat_id).lstrip('@')}" if not str(chat_id).startswith("-") else "https://t.me"
        
    ok = await db.add_forced_channel(chat_id, title, invite_url)
    await state.clear()
    
    if ok:
        res_text = (
            f"✅ <b>تمت إضافة القناة/الجروب للاشتراك الإجباري بنجاح!</b>\n\n"
            f"• العنوان: <b>{title}</b>\n"
            f"• المعرف: <code>{chat_id}</code>\n"
            f"• الرابط: {invite_url}\n\n"
        )
        if is_bot_admin:
            res_text += "🔒 <b>حالة الصلاحيات:</b> تم التحقق بنجاح (البوت مشرف ويملك صلاحيات فحص الأعضاء)."
        else:
            res_text += "⚠️ <b>تنبيه مهم:</b> البوت ليس مشرفاً في هذه القناة حالياً! يرجى رفع البوت مشرفاً (Admin) في القناة/الجروب لتفعيل التحقق ومنع الأعضاء غير المشتركين."
            
        await message.answer(res_text, reply_markup=admin_panel_kb())
    else:
        await message.answer("⚠️ هذه القناة مضافة مسبقاً في قائمة الاشتراك الإجباري.", reply_markup=admin_panel_kb())


@router.callback_query(F.data == "admin_test_channels")
async def cb_test_channels(cq: CallbackQuery, bot: Bot):
    if not await _guard(cq):
        return
    channels = await db.list_forced_channels()
    if not channels:
        await cq.answer("لا توجد قنوات لفحصها.", show_alert=True)
        return
        
    lines = ["🔍 <b>تقرير فحص صلاحيات البوت في القنوات:</b>\n"]
    for i, ch in enumerate(channels, 1):
        chat_id = ch["chat_id"]
        chat_ref = normalize_chat_ref(chat_id)
        status_text = "❌ خطأ غير معروف"
        try:
            member = await bot.get_chat_member(chat_ref, bot.id)
            if member.status in ("administrator", "creator"):
                status_text = "✅ البوت مشرف (صلاحيات كاملة)"
            else:
                status_text = "⚠️ البوت عضو عادي (يرجى ترقيته لمشرف)"
        except Exception as e:
            err = str(e).lower()
            if "chat not found" in err:
                status_text = "❌ القناة غير موجودة أو المعرف خاطئ"
            elif "bot was kicked" in err:
                status_text = "❌ تم طرد البوت من القناة"
            elif "not enough rights" in err or "admin" in err:
                status_text = "⚠️ البوت يحتاج رتبة مشرف"
            else:
                status_text = f"⚠️ خطأ: {e}"
        lines.append(f"{i}. <b>{ch['title'] or 'قناة'}</b>\n   ID: <code>{chat_id}</code>\n   الحالة: {status_text}\n")
        
    await cq.message.edit_text("\n".join(lines), reply_markup=admin_channels_kb(bool(channels)))
    await cq.answer()


@router.callback_query(F.data == "admin_remove_channel")
async def cb_remove_channel(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        return
    await state.set_state(AdminStates.waiting_remove_channel)
    await cq.message.edit_text(
        "🗑 <b>حذف قناة</b>\n\nأرسل <code>chat_id</code> القناة المراد حذفها.\nأرسل /cancel للإلغاء.",
        reply_markup=admin_back_kb(),
    )
    await cq.answer()


@router.message(AdminStates.waiting_remove_channel, Command("cancel"))
async def cancel_remove_channel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.", reply_markup=admin_panel_kb())


@router.message(AdminStates.waiting_remove_channel)
async def do_remove_channel(message: Message, state: FSMContext):
    if not await is_admin_or_authorized(message.from_user.id, message.from_user.username or ""):
        return
    chat_id = (message.text or "").strip()
    ok = await db.remove_forced_channel(chat_id)
    await state.clear()
    await message.answer(
        "✅ تم الحذف." if ok else "⚠️ القناة غير موجودة.",
        reply_markup=admin_panel_kb(),
    )


# ─────────────────────────── نظام الإحالات (إعدادات الأدمن) ───────────────────────────

@router.callback_query(F.data == "admin_referrals")
async def cb_admin_referrals(cq: CallbackQuery):
    if not await _guard(cq):
        return
    text = (
        "🎁 <b>إعدادات نظام الإحالات</b>\n\n"
        f"عدد الإحالات المطلوبة لتفعيل VIP مجاناً: <b>{settings.REFERRAL_TARGET}</b>\n"
    )
    await cq.message.edit_text(text, reply_markup=admin_referrals_kb())
    await cq.answer()


@router.callback_query(F.data == "admin_set_ref_target")
async def cb_set_ref_target(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        return
    await state.set_state(AdminStates.waiting_set_referral_target)
    await cq.message.edit_text(
        "⚙️ أرسل الآن العدد الجديد للإحالات المطلوبة (مثلاً: 10).\n/cancel للإلغاء.",
        reply_markup=admin_back_kb(),
    )
    await cq.answer()


@router.message(AdminStates.waiting_set_referral_target, Command("cancel"))
async def cancel_set_ref_target(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.", reply_markup=admin_panel_kb())


@router.message(AdminStates.waiting_set_referral_target)
async def do_set_ref_target(message: Message, state: FSMContext):
    if not await is_admin_or_authorized(message.from_user.id, message.from_user.username or ""):
        return
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) < 1:
        await message.answer("⚠️ رقم غير صالح.")
        return
    settings.REFERRAL_TARGET = int(text)
    await state.clear()
    await message.answer(
        f"✅ تم تعيين هدف الإحالات إلى: <b>{settings.REFERRAL_TARGET}</b>",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "admin_leaderboard")
async def cb_leaderboard(cq: CallbackQuery):
    if not await _guard(cq):
        return
    rows = await db.get_referral_leaderboard(20)
    if not rows:
        text = "🏆 <b>المتصدرون بالإحالات</b>\n\n<i>لا يوجد أي إحالات بعد.</i>"
    else:
        lines = ["🏆 <b>المتصدرون بالإحالات</b>\n"]
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(rows):
            m = medals[i] if i < 3 else f"#{i+1}"
            name = r.get("full_name") or r.get("username") or str(r["user_id"])
            uname = f"(@{r['username']})" if r.get("username") else ""
            lines.append(f"{m} <b>{name}</b> {uname} — <b>{r['referral_count']}</b> إحالة")
        text = "\n".join(lines)
    await cq.message.edit_text(text, reply_markup=admin_back_kb())
    await cq.answer()


# ─────────────────────────── حظر مستخدم ───────────────────────────

@router.callback_query(F.data == "admin_ban")
async def cb_ban(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        return
    await state.set_state(AdminStates.waiting_ban_input)
    await cq.message.edit_text(
        "🚫 <b>حظر/رفع حظر مستخدم</b>\n\n"
        "أرسل: <code>ban 123456</code> للحظر\n"
        "أرسل: <code>unban 123456</code> لرفع الحظر\n\n"
        "أو استخدم اليوزر: <code>ban @username</code>\n"
        "/cancel للإلغاء.",
        reply_markup=admin_back_kb(),
    )
    await cq.answer()


@router.message(AdminStates.waiting_ban_input, Command("cancel"))
async def cancel_ban(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.", reply_markup=admin_panel_kb())


@router.message(AdminStates.waiting_ban_input)
async def do_ban_flow(message: Message, state: FSMContext, bot: Bot):
    if not await is_admin_or_authorized(message.from_user.id, message.from_user.username or ""):
        return
    parts = (message.text or "").strip().split(maxsplit=1)
    if len(parts) != 2 or parts[0] not in ("ban", "unban"):
        await message.answer("⚠️ صيغة غير صحيحة. مثال: <code>ban 123456</code>")
        return
    action, target = parts
    user = await _resolve_target_user(target)
    if not user:
        await message.answer("⚠️ المستخدم غير موجود.")
        return
    banned = action == "ban"
    await db.ban_user(user["user_id"], banned)
    await state.clear()
    await message.answer(
        f"✅ تم {'حظر' if banned else 'رفع حظر'} المستخدم <code>{user['user_id']}</code>.",
        reply_markup=admin_panel_kb(),
    )


# ─────────────────────────── رسالة خاصة لمستخدم ───────────────────────────

@router.callback_query(F.data == "admin_dm")
async def cb_admin_dm(cq: CallbackQuery, state: FSMContext):
    if not await _guard(cq):
        return
    await state.set_state(AdminStates.waiting_admin_dm_user)
    await cq.message.edit_text(
        "✉️ <b>إرسال رسالة خاصة</b>\n\n"
        "أرسل الآن <b>آيدي</b> أو <b>يوزر</b> المستخدم المستهدف.\n/cancel للإلغاء.",
        reply_markup=admin_back_kb(),
    )
    await cq.answer()


@router.message(AdminStates.waiting_admin_dm_user, Command("cancel"))
async def cancel_dm(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.", reply_markup=admin_panel_kb())


@router.message(AdminStates.waiting_admin_dm_user)
async def receive_dm_target(message: Message, state: FSMContext):
    user = await _resolve_target_user(message.text or "")
    if not user:
        await message.answer("⚠️ لم يتم العثور على المستخدم. أعد الإرسال أو /cancel.")
        return
    await state.update_data(dm_target=user["user_id"])
    await state.set_state(AdminStates.waiting_admin_dm_text)
    await message.answer(
        f"✅ المستخدم: <code>{user['user_id']}</code>\n\nأرسل الآن الرسالة التي تريد إرسالها:"
    )


@router.message(AdminStates.waiting_admin_dm_text, Command("cancel"))
async def cancel_dm2(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.", reply_markup=admin_panel_kb())


@router.message(AdminStates.waiting_admin_dm_text)
async def send_dm(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target = data.get("dm_target")
    await state.clear()
    if not target:
        return
    try:
        await bot.copy_message(chat_id=target, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.answer("✅ تم إرسال الرسالة.", reply_markup=admin_panel_kb())
    except Exception as e:
        await message.answer(f"❌ فشل الإرسال: {e}", reply_markup=admin_panel_kb())
