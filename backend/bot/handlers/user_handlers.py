"""
هاندلرات المستخدم العادي:
- /start
- إنشاء / تعديل الصفحة (FSM)
- معاينة الصفحة
- تغيير التصميم (VIP)
- الإحصائيات (VIP)
- كود QR (VIP)
"""
import io
import re
import qrcode

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, BufferedInputFile,
)

from bot.config import settings
from bot.states import PageCreationStates
from bot.keyboards import (
    main_menu_kb, webapp_preview_kb, add_link_prompt_kb,
    themes_kb, cancel_kb,
)
from bot import database as db

router = Router(name="user")

# ─────────────────────────────── /start ───────────────────────────────

WELCOME_TEXT = (
    "👋 <b>أهلاً بك في بوت LinkTree المصغّر!</b>\n\n"
    "🔗 يمكنك إنشاء صفحة ويب مصغّرة تجمع كل روابطك الشخصية في مكان واحد "
    "لتشاركها مع متابعيك ✨\n\n"
    "استخدم الأزرار بالأسفل للبدء 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await db.get_or_create_user(
        user.id,
        user.username or "",
        user.full_name or "",
    )
    is_vip = await db.is_user_vip(user.id)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(is_vip))


# ─────────────────────── معاينة الصفحة ───────────────────────

@router.message(F.text == "🌐 معاينة صفحتي")
async def preview_page(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user or not user.get("page_title"):
        await message.answer(
            "لم تُنشئ صفحتك بعد. اضغط على «➕ إنشاء / تعديل صفحتي» للبدء."
        )
        return
    await message.answer(
        "🌐 اضغط على الزر لفتح صفحتك:",
        reply_markup=webapp_preview_kb(user_id),
    )


# ─────────────────────── FSM: إنشاء / تعديل الصفحة ───────────────────────

@router.message(F.text == "➕ إنشاء / تعديل صفحتي")
async def start_page_creation(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(PageCreationStates.waiting_title)
    await message.answer(
        "✏️ <b>الخطوة 1/3:</b>\nأرسل الآن <b>عنوان صفحتك</b> (اسم الصفحة أو اسمك):",
        reply_markup=cancel_kb(),
    )


@router.message(PageCreationStates.waiting_title, F.text)
async def receive_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 2 or len(title) > 60:
        await message.answer("⚠️ يجب أن يكون العنوان بين 2 و 60 حرف. حاول مرة أخرى.")
        return
    await state.update_data(page_title=title, links=[])
    await state.set_state(PageCreationStates.waiting_bio)
    await message.answer(
        "✏️ <b>الخطوة 2/3:</b>\nأرسل الآن <b>نبذة مختصرة</b> عنك (Bio):\n"
        "<i>أو أرسل - إذا لم ترغب بإضافة نبذة.</i>",
        reply_markup=cancel_kb(),
    )


@router.message(PageCreationStates.waiting_bio, F.text)
async def receive_bio(message: Message, state: FSMContext):
    bio = message.text.strip()
    if bio == "-":
        bio = ""
    if len(bio) > 200:
        await message.answer("⚠️ النبذة يجب ألا تتجاوز 200 حرف.")
        return
    await state.update_data(page_bio=bio)
    await state.set_state(PageCreationStates.waiting_link_title)
    await message.answer(
        "🔗 <b>الخطوة 3/3:</b>\n"
        "الآن سنضيف روابطك واحداً واحداً.\n\n"
        "أرسل <b>اسم الرابط الأول</b> (مثال: يوتيوب، انستقرام، موقعي...):",
        reply_markup=cancel_kb(),
    )


@router.message(PageCreationStates.waiting_link_title, F.text)
async def receive_link_title(message: Message, state: FSMContext):
    link_title = message.text.strip()
    if len(link_title) < 1 or len(link_title) > 40:
        await message.answer("⚠️ اسم الرابط يجب أن يكون بين 1 و 40 حرف.")
        return
    await state.update_data(current_link_title=link_title)
    await state.set_state(PageCreationStates.waiting_link_url)
    await message.answer(
        f"🌐 الآن أرسل <b>الرابط (URL)</b> الخاص بـ <b>{link_title}</b>:\n"
        "<i>مثال: https://youtube.com/@myname</i>",
        reply_markup=cancel_kb(),
    )


URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)


@router.message(PageCreationStates.waiting_link_url, F.text)
async def receive_link_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if not URL_RE.match(url):
        await message.answer(
            "⚠️ الرابط غير صحيح. يجب أن يبدأ بـ http:// أو https://\nأعد الإرسال:"
        )
        return

    data = await state.get_data()
    links = data.get("links", [])
    links.append({"title": data["current_link_title"], "url": url})
    await state.update_data(links=links)

    # التحقق من عضوية المستخدم
    is_vip = await db.is_user_vip(message.from_user.id)
    if not is_vip and len(links) >= settings.FREE_LINKS_LIMIT:
        # للمجاني: توقف بعد الرابط الثالث
        await _finalize_page(message, state, notice_limit=True)
        return

    # اسأله عن الرابط التالي أو الإنهاء
    await state.set_state(PageCreationStates.waiting_link_title)
    await message.answer(
        f"✅ تم إضافة الرابط ({len(links)}). ماذا تريد أن تفعل الآن؟",
        reply_markup=add_link_prompt_kb(),
    )


@router.callback_query(F.data == "add_new_link")
async def cb_add_new_link(cq: CallbackQuery, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await cq.answer("انتهت الجلسة، ابدأ من جديد.", show_alert=True)
        return
    await state.set_state(PageCreationStates.waiting_link_title)
    await cq.message.edit_reply_markup(reply_markup=None)
    await cq.message.answer("🔗 أرسل <b>اسم الرابط التالي</b>:", reply_markup=cancel_kb())
    await cq.answer()


@router.callback_query(F.data == "finish_page")
async def cb_finish_page(cq: CallbackQuery, state: FSMContext):
    await cq.message.edit_reply_markup(reply_markup=None)
    await _finalize_page(cq.message, state, from_user_id=cq.from_user.id)
    await cq.answer()


@router.callback_query(F.data == "cancel_fsm")
async def cb_cancel_fsm(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.message.edit_reply_markup(reply_markup=None)
    is_vip = await db.is_user_vip(cq.from_user.id)
    await cq.message.answer("❌ تم الإلغاء.", reply_markup=main_menu_kb(is_vip))
    await cq.answer()


async def _finalize_page(message: Message, state: FSMContext,
                         notice_limit: bool = False, from_user_id: int = None):
    """حفظ الصفحة النهائية في قاعدة البيانات"""
    user_id = from_user_id or message.from_user.id
    data = await state.get_data()
    links = data.get("links", [])
    if not links:
        await message.answer("⚠️ لم تضف أي رابط بعد. تم الإلغاء.")
        await state.clear()
        is_vip = await db.is_user_vip(user_id)
        await message.answer("القائمة الرئيسية:", reply_markup=main_menu_kb(is_vip))
        return

    await db.update_user_page(user_id, data.get("page_title", ""), data.get("page_bio", ""))
    # حذف الروابط القديمة وإعادة إدراجها (إعادة بناء الصفحة)
    await db.delete_user_links(user_id)
    for link in links:
        await db.add_link(user_id, link["title"], link["url"])

    await state.clear()

    if notice_limit:
        await message.answer(
            f"⚠️ لقد بلغت الحد الأقصى للعضوية المجانية "
            f"(<b>{settings.FREE_LINKS_LIMIT} روابط فقط</b>).\n\n"
            "💎 قم بالترقية إلى VIP للحصول على روابط غير محدودة وقوالب حصرية!"
        )

    is_vip = await db.is_user_vip(user_id)
    await message.answer(
        "🎉 <b>تم حفظ صفحتك بنجاح!</b>\nيمكنك الآن معاينتها:",
        reply_markup=main_menu_kb(is_vip),
    )
    await message.answer(
        "🌐 اضغط لفتح صفحتك:",
        reply_markup=webapp_preview_kb(user_id),
    )


# ─────────────────────── تغيير التصميم (VIP) ───────────────────────

VIP_ONLY_MSG = (
    "🔒 هذه الميزة متاحة لمستخدمي <b>VIP</b> فقط.\n\n"
    "💎 اضغط على «الاشتراك في VIP» للحصول على الميزات الحصرية:\n"
    "• روابط غير محدودة\n"
    "• قوالب وألوان حصرية\n"
    "• كود QR لصفحتك\n"
    "• إحصائيات زوار متقدمة"
)


@router.message(F.text == "🎨 تغيير التصميم")
async def change_theme(message: Message):
    is_vip = await db.is_user_vip(message.from_user.id)
    if not is_vip:
        await message.answer(VIP_ONLY_MSG)
        return
    user = await db.get_user(message.from_user.id)
    await message.answer(
        "🎨 <b>اختر قالب صفحتك:</b>",
        reply_markup=themes_kb(current_theme=user["theme"] or 0),
    )


@router.callback_query(F.data.startswith("set_theme:"))
async def cb_set_theme(cq: CallbackQuery):
    is_vip = await db.is_user_vip(cq.from_user.id)
    if not is_vip:
        await cq.answer("VIP فقط.", show_alert=True)
        return
    theme_id = int(cq.data.split(":")[1])
    if theme_id not in (1, 2, 3):
        await cq.answer("قالب غير صالح.", show_alert=True)
        return
    await db.update_user_theme(cq.from_user.id, theme_id)
    names = {1: "🌌 Dark Cyber", 2: "💖 Neon Glow", 3: "🪟 Glassmorphism"}
    await cq.message.edit_reply_markup(reply_markup=themes_kb(theme_id))
    await cq.answer(f"تم اختيار: {names[theme_id]}", show_alert=False)


# ─────────────────────── الإحصائيات (VIP) ───────────────────────

@router.message(F.text == "📊 إحصائياتي")
async def user_stats(message: Message):
    is_vip = await db.is_user_vip(message.from_user.id)
    if not is_vip:
        await message.answer(VIP_ONLY_MSG)
        return
    stats = await db.get_user_stats(message.from_user.id)
    lines = [
        "📊 <b>إحصائيات صفحتك:</b>\n",
        f"👁️ إجمالي الزيارات: <b>{stats['visits']}</b>",
        f"🖱️ إجمالي نقرات الروابط: <b>{stats['total_clicks']}</b>",
        "",
        "🔗 <b>نقرات كل رابط:</b>",
    ]
    if stats["links"]:
        for link in stats["links"]:
            lines.append(f"• {link['title']}: <b>{link['clicks']}</b> نقرة")
    else:
        lines.append("<i>لم تضف أي روابط بعد.</i>")
    await message.answer("\n".join(lines))


# ─────────────────────── كود QR (VIP) ───────────────────────

@router.message(F.text == "📷 كود QR الخاص بي")
async def user_qr(message: Message):
    is_vip = await db.is_user_vip(message.from_user.id)
    if not is_vip:
        await message.answer(VIP_ONLY_MSG)
        return

    user_id = message.from_user.id
    # رابط مشاركة قابل للفتح خارج تليجرام أيضاً
    share_url = f"{settings.WEBAPP_BASE_URL}/api/page/{user_id}"
    tg_url = f"https://t.me/{settings.BOT_USERNAME}?startapp=user_{user_id}"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(share_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    photo = BufferedInputFile(buf.getvalue(), filename="qr.png")

    caption = (
        "📷 <b>كود QR لصفحتك:</b>\n\n"
        f"🔗 رابط الويب: {share_url}\n"
        f"💬 رابط تليجرام: {tg_url}\n\n"
        "شاركه مع متابعيك للوصول السريع إلى صفحتك!"
    )
    await message.answer_photo(photo, caption=caption)
