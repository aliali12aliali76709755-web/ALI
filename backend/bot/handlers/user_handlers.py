"""
هاندلرات المستخدم العادي (النسخة المحسّنة):
- /start مع معالجة روابط الإحالة
- إنشاء / تعديل الصفحة (FSM محسّن يخفي الكيبورد الرئيسي)
- تصحيح تلقائي للروابط (إضافة https:// عند الحاجة)
- دعم إدخال الرابط بصيغة "اسم | رابط" أو خطوتين منفصلتين
- رفع الصورة الشخصية (VIP)
- شرح كامل لميزات VIP
- إحصائيات جغرافية
- القوالب المدفوعة (شراء بالنجوم)
- كود QR (رابط الويب فقط)
- نظام الإحالات (مكافأة شهر)
"""
import io
import re
import os
import shutil
import logging
import qrcode

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, BufferedInputFile, PhotoSize,
    LabeledPrice,
)

from bot.config import settings
from bot.states import PageCreationStates, AvatarStates, LinkEditStates, CustomizationStates, SubPageStates
from bot.keyboards import (
    main_menu_kb, hide_kb, webapp_preview_kb, links_progress_kb,
    themes_kb, cancel_kb, skip_or_cancel_kb, referral_kb,
    subscription_kb, avatar_menu_kb, buy_theme_kb, THEMES,
    customize_menu_kb, accent_colors_kb, button_styles_kb,
    bg_effects_kb, badge_types_kb, music_menu_kb, whatsapp_btn_kb,
    reviews_manager_kb, review_detail_kb, fonts_kb, marquee_menu_kb,
    countdown_menu_kb, custom_domain_menu_kb, pixels_menu_kb, social_icons_menu_kb,
    fsm_cancel_kb, fsm_skip_bio_kb, fsm_links_progress_kb, fsm_cancel_link_kb,
    manage_links_kb, edit_link_options_kb, fsm_cancel_edit_kb, sponsor_channels_kb,
    support_kb,
)
from bot import database as db
from bot.middlewares import check_user_subscribed

logger = logging.getLogger("user")
router = Router(name="user")


EXPIRED_VIP_BLOCK_MSG = (
    "⚠️ <b>انتهى اشتراك VIP الخاص بك!</b>\n\n"
    "صفحتك الشخصية والروابط والقوالب التي اخترتها <b>لا تزال تعمل ونشطة بالكامل أمام زوارك ولن تختفي أبداً!</b>\n\n"
    "ولكن لتتمكن من تعديل الصفحة، إضافة أو تعديل روابطك، أو مراجعة إحصائيات زوارك، يرجى تجديد اشتراك VIP الخاص بك 💎"
)


async def check_vip_expired_blocking(user_id: int) -> bool:
    return False


WELCOME_TEXT = (
    "👋 <b>أهلاً بك في بوت ProLink! ⚡</b>\n\n"
    "🔗 المنصة المتكاملة لإنشاء صفحة بروفايلك وتنظيم روابطك وتوثيق حسابك مجاناً بالكامل!\n\n"
    "🎉 <b>مفاجأة سارة:</b> جميع القوالب الفاخرة، الصفحات المتعددة، التخصيص المتقدم، وشارات التوثيق <b>مفتوحة ومجانية 100% لجميع المستخدمين!</b>\n\n"
    "استخدم الأزرار بالأسفل للبدء في تصميم وإدارة صفحتك 👇"
)


VIP_FEATURES_TEXT = (
    "🎉 <b>جميع الميزات مفتوحة ومجانية بالكامل 100%!</b>\n\n"
    "استفد من كل هذه الإمكانيات القوية مجاناً وبدون أي اشتراك:\n\n"
    "🗂️ <b>صفحات مجمّعة وهبوط غير محدودة</b>: أنشئ صفحات فرعية بروابط خاصة.\n\n"
    "🚫 <b>بدون حقوق صنع</b>: صفحاتك نظيفة وخالية من أي إعلانات أو حقوق للبوت.\n\n"
    "🎨 <b>جميع القوالب مفتوحة</b>: اختر من بين 23 قالباً فاخراً مجاناً.\n\n"
    "⚙️ <b>لوحة التخصيص المتقدم</b>: تحكم كامل بالألوان وأشكال الأزرار والخطوط.\n\n"
    "🏆 <b>شارات التوثيق المتنوعة</b>: اختر شارة التوثيق التي تناسبك.\n\n"
    "🖼 <b>الصورة الشخصية (Avatar)</b>: ارفع صورتك الخاصة لبروفايلك.\n\n"
    "📊 <b>إحصائيات متقدمة</b>: تتبع الزيارات والنقرات والدول.\n\n"
    "📷 <b>كود QR مخصص</b>: كود سريع لمشاركة صفحتك.\n\n"
    "💬 <b>التعليقات والتقييمات</b>: تلقي وإدارة تقييمات زوارك بحرية."
)


# ─────────────────────────────── /start ───────────────────────────────

@router.message(CommandStart(deep_link=True))
async def cmd_start_with_ref(message: Message, command: CommandObject, state: FSMContext, bot: Bot):
    await state.clear()
    user = message.from_user
    is_new_user = (await db.get_user(user.id)) is None
    await db.get_or_create_user(user.id, user.username or "", user.full_name or "")

    args = (command.args or "").strip()
    if args.startswith("ref_") and is_new_user:
        try:
            referrer_id = int(args[4:])
            added = await db.add_pending_referral(referrer_id, user.id)
            if added:
                text = (
                    "🛡️ <b>نظام التحقق ومكافحة الحسابات الوهمية والسبام</b>\n\n"
                    "أهلاً بك في <b>ProLink</b>! ⚡\n\n"
                    "لتفعيل البوت وحماية حساب من دعاك من الرشق، يرجى إثبات أنك مستخدم حقيقي بالضغط على زر التحقق أدناه:\n\n"
                    "⚠️ <b>شروط القبول:</b> يجب أن يحتوي حسابك على <u>اسم مستخدم (Username)</u> أو <u>صورة شخصية</u> كحد أدنى ليتم تأكيد دعوتك بنجاح."
                )
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ اضغط هنا للتحقق وتفعيل البوت", callback_data="verify_ref_human")]
                ])
                await message.answer(text, reply_markup=kb, parse_mode="HTML")
                return
        except Exception as e:
            logger.warning(f"referral parse failed: {e}")

    is_vip = await db.is_user_vip(user.id)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(is_vip))


@router.callback_query(F.data == "verify_ref_human")
async def cb_verify_ref_human(cq: CallbackQuery, bot: Bot):
    user = cq.from_user
    
    # Check anti-fraud criteria:
    has_username = bool(user.username)
    
    has_avatar = False
    try:
        photos = await bot.get_user_profile_photos(user.id, limit=1)
        if photos and photos.photos:
            has_avatar = True
    except Exception as e:
        logger.warning(f"Failed to fetch profile photos for anti-fraud: {e}")
        
    if not has_username and not has_avatar:
        await cq.answer(
            "❌ فشل التحقق! يجب وضع يوزرنيم أو صورة شخصية لحسابك.",
            show_alert=True
        )
        await cq.message.edit_text(
            "❌ <b>فشل التحقق التلقائي!</b>\n\n"
            "لضمان أمان البوت ومكافحة الحسابات الوهمية (الرشق)، <b>يجب وضع صورة شخصية لحسابك أو إنشاء اسم مستخدم (Username) أولاً</b> في إعدادات تليجرام.\n\n"
            "بعد إعداد حسابك، اضغط على زر التحقق أدناه للمحاولة مجدداً 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 إعادة محاولة التحقق", callback_data="verify_ref_human")]
            ])
        )
        return

    # Check if there is a pending referral
    referrer_id = await db.get_pending_referral(user.id)
    if referrer_id:
        recorded = await db.record_referral(referrer_id, user.id)
        await db.delete_pending_referral(user.id)
        
        if recorded:
            count = await db.get_referral_count(referrer_id)
            target = settings.REFERRAL_TARGET
            
            try:
                if count >= target:
                    await db.set_vip_status(referrer_id, True, days=settings.REFERRAL_REWARD_DAYS)
                    await db.reset_referral_progress(referrer_id)
                    motivational_vip_msg = (
                        f"🎉 <b>يا لك من بطل رائع! مبروووك!</b> 🥳\n\n"
                        f"لقد نجحت في دعوة <b>{target}</b> صديقاً حقيقياً إلى البوت!\n"
                        f"💥 <b>جائزتك الكبرى جاهزة:</b> تم تفعيل اشتراك <b>VIP مجاني بالكامل لمدة 30 يوم!</b> 💎\n\n"
                        f"صفحتك أصبحت الآن خارقة ومميزة بكل الميزات الاحترافية. استمر في مشاركة رابطك مع الآخرين للحصول على المزيد من الأشهر المجانية! 🚀"
                    )
                    await bot.send_message(
                        referrer_id,
                        motivational_vip_msg,
                        reply_markup=main_menu_kb(is_vip=True),
                        parse_mode="HTML"
                    )
                else:
                    motivational_progress_msg = (
                        f"🎁 <b>صديق جديد انضم إليك بعد التحقق! إحالة مؤكدة!</b> 🔥\n\n"
                        f"لقد دعوت صديقاً حقيقياً بنجاح! عدادك الحالي: <b>{count}</b> / {target}\n"
                        f"💡 تبقت لك <b>{target - count}</b> دعوات فقط لتحصل على <b>شهر VIP مجاني!</b>\n\n"
                        f"شارك رابطك الآن في المجموعات ومع أصدقائك، فالتميز بانتظارك! 🌟"
                    )
                    await bot.send_message(
                        referrer_id,
                        motivational_progress_msg,
                        parse_mode="HTML"
                    )
            except Exception as e:
                logger.warning(f"Could not notify referrer: {e}")
                
    is_vip = await db.is_user_vip(user.id)
    await cq.message.edit_text(
        "✅ <b>تم التحقق من حسابك وتفعيله بنجاح!</b>\n\n"
        "أهلاً بك في <b>ProLink</b> ⚡ - المنصة الأقوى لإنشاء صفحتك الشخصية وتنظيم روابطك وتوثيق حسابك بشكل احترافي ✨\n\n"
        "اضغط على القائمة بالأسفل للبدء في تصميم صفحتك ولينك تري الخاص بك!",
        parse_mode="HTML"
    )
    await cq.message.answer(
        "👋 ابدأ الآن في تخصيص صفحتك من الأزرار بالأسفل:",
        reply_markup=main_menu_kb(is_vip)
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await db.get_or_create_user(user.id, user.username or "", user.full_name or "")
    is_vip = await db.is_user_vip(user.id)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(is_vip))


# ─────────────────────────────── التحقق من الاشتراك ───────────────────────────────

@router.callback_query(F.data == "check_subscription")
async def cb_check_sub(cq: CallbackQuery, bot: Bot):
    not_sub = await check_user_subscribed(bot, cq.from_user.id)
    if not not_sub:
        await cq.answer("✅ تم التحقق!", show_alert=True)
        is_vip = await db.is_user_vip(cq.from_user.id)
        try:
            await cq.message.delete()
        except Exception:
            pass
        await cq.message.answer("✅ تم قبولك. استخدم القائمة بالأسفل 👇",
                                reply_markup=main_menu_kb(is_vip))
    else:
        titles = ", ".join([c["title"] or "قناة" for c in not_sub])
        await cq.answer(f"❌ لم تشترك بعد في: {titles}", show_alert=True)


# ─────────────────────── معاينة الصفحة ───────────────────────

@router.message(F.text == "🌐 معاينة صفحتي")
async def preview_page(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user or not user.get("page_title"):
        await message.answer("لم تُنشئ صفحتك بعد. اضغط على «➕ إنشاء / تعديل صفحتي» للبدء.")
        return
    await message.answer("🌐 اضغط على الزر لفتح صفحتك:", reply_markup=webapp_preview_kb(user_id))


# ─────────────────────── FSM: إنشاء / تعديل الصفحة ───────────────────────

@router.message(F.text == "➕ إنشاء / تعديل صفحتي")
async def start_page_creation(message: Message, state: FSMContext):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    text = (
        "🗂️ <b>إدارة صفحات الهبوط والروابط</b>\n\n"
        "يمكنك إنشاء وإدارة عدد غير محدود من صفحات الهبوط والروابط المجمّعة مجاناً بالكامل!\n\n"
        "اختر ماذا تريد أن تفعل أدناه 👇"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ تعديل الصفحة الرئيسية", callback_data="edit_main_page")],
        [InlineKeyboardButton(text="📁 إدارة صفحاتي الفرعية", callback_data="manage_sub_pages")],
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("cancel"))
@router.message(F.text == "❌ إلغاء الإنشاء")
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        return
    await state.clear()
    is_vip = await db.is_user_vip(message.from_user.id)
    await message.answer("❌ تم إلغاء العملية.", reply_markup=main_menu_kb(is_vip))


@router.message(PageCreationStates.waiting_title, F.text)
async def receive_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if title == "❌ إلغاء الإنشاء":
        await cmd_cancel(message, state)
        return
    if title.startswith("/"):
        return  # تجاهل الأوامر
    if len(title) < 2 or len(title) > 60:
        await message.answer("⚠️ يجب أن يكون العنوان بين 2 و 60 حرف. حاول مرة أخرى.")
        return
    await state.update_data(page_title=title, links=[])
    await state.set_state(PageCreationStates.waiting_bio)
    await message.answer(
        "✏️ <b>الخطوة 2 من 3: نبذة مختصرة</b>\n\n"
        "أرسل الآن <b>نبذة عنك</b> (اختياري، حد أقصى 200 حرف):\n"
        "<i>أو اضغط زر «⏭ تخطي» لعدم إضافة نبذة.</i>",
        reply_markup=fsm_skip_bio_kb(),
    )


@router.callback_query(PageCreationStates.waiting_bio, F.data == "skip_bio")
async def cb_skip_bio(cq: CallbackQuery, state: FSMContext):
    await state.update_data(page_bio="")
    await state.set_state(PageCreationStates.waiting_link_title)
    await cq.message.edit_reply_markup(reply_markup=None)
    await _prompt_link_title(cq.message, state)
    await cq.answer("تم التخطي")


@router.message(PageCreationStates.waiting_bio, F.text)
async def receive_bio(message: Message, state: FSMContext):
    bio = message.text.strip()
    if bio == "❌ إلغاء الإنشاء":
        await cmd_cancel(message, state)
        return
    if bio == "⏭ تخطي (بدون نبذة)" or bio == "-":
        bio = ""
    elif len(bio) > 200:
        await message.answer("⚠️ النبذة يجب ألا تتجاوز 200 حرف. أعد الإرسال أو اضغط «تخطي».")
        return
    await state.update_data(page_bio=bio)
    await state.set_state(PageCreationStates.waiting_link_title)
    await _prompt_link_title(message, state)


async def _prompt_link_title(message: Message, state: FSMContext):
    data = await state.get_data()
    count = len(data.get("links", []))
    if count == 0:
        text = (
            "🔗 <b>الخطوة 3 من 3: إضافة الروابط</b>\n\n"
            "الآن سنضيف روابطك واحداً واحداً.\n\n"
            "أرسل <b>اسم الرابط الأول</b> (مثال: <code>انستقرام</code>، <code>يوتيوب</code>، <code>موقعي</code>...):\n\n"
            "💡 <b>طريقة سريعة:</b> يمكنك إرسال الاسم والرابط معاً بهذه الصيغة:\n"
            "<code>انستقرام | https://instagram.com/user</code>"
        )
        reply_markup = fsm_cancel_kb()
    else:
        text = (
            f"✅ تم إضافة الرابط بنجاح! عندك الآن <b>{count}</b> رابط محفوظ.\n\n"
            "أرسل <b>اسم الرابط التالي</b>، أو إذا انتهيت اضغط على زر <b>حفظ الروابط</b> بالأسفل 👇\n\n"
            "💡 <b>سريع:</b> <code>اسم | رابط</code> في رسالة واحدة"
        )
        reply_markup = fsm_links_progress_kb(count)
    await message.answer(text, reply_markup=reply_markup)


URL_ONLY_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
DOMAIN_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-]*(\.[a-zA-Z0-9\-]+)+(\/\S*)?$")


def normalize_url(text: str) -> str:
    """يحوّل النص إلى URL صحيح (يضيف https:// عند الحاجة)"""
    text = text.strip()
    if not text:
        return ""
    if text.startswith(("http://", "https://")):
        return text
    # إذا يبدو كنطاق (مثلاً instagram.com/x)
    if DOMAIN_RE.match(text):
        return "https://" + text
    return ""  # ليس رابطاً


def guess_platform_name(url: str) -> str:
    """يحدد اسم المنصة من الرابط"""
    low = url.lower()
    for key, name in {
        "youtube.com": "يوتيوب", "youtu.be": "يوتيوب",
        "instagram.com": "انستقرام",
        "twitter.com": "تويتر", "x.com": "تويتر",
        "tiktok.com": "تيك توك",
        "facebook.com": "فيسبوك", "fb.com": "فيسبوك",
        "t.me": "تليجرام", "telegram.me": "تليجرام",
        "whatsapp.com": "واتساب", "wa.me": "واتساب",
        "linkedin.com": "لينكدإن",
        "github.com": "جيت هب",
        "spotify.com": "سبوتيفاي",
        "snapchat.com": "سناب شات",
        "twitch.tv": "تويتش",
        "discord.gg": "ديسكورد", "discord.com": "ديسكورد",
        "pinterest.com": "بينترست",
    }.items():
        if key in low:
            return name
    return "رابط"


@router.message(PageCreationStates.waiting_link_title, F.text)
async def receive_link_title(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "❌ إلغاء الإنشاء":
        await cmd_cancel(message, state)
        return
    if text.startswith("✅ حفظ الروابط"):
        await _finalize_page(message, state)
        return
    if text.startswith("/"):
        return

    # 1) صيغة الأنبوب: "اسم | رابط"
    if "|" in text:
        parts = [p.strip() for p in text.split("|", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            title, url_raw = parts
            url = normalize_url(url_raw)
            if not url:
                await message.answer("⚠️ الرابط بعد الـ | غير صحيح. أعد الإرسال.")
                return
            if len(title) > 40:
                await message.answer("⚠️ اسم الرابط يجب ألا يتجاوز 40 حرف.")
                return
            await _add_link_and_continue(message, state, title, url)
            return

    # 2) المستخدم أرسل رابطاً كاملاً بدلاً من الاسم -> نخمّن الاسم
    if text.startswith(("http://", "https://")) or DOMAIN_RE.match(text):
        url = normalize_url(text)
        if url:
            guessed = guess_platform_name(url)
            await _add_link_and_continue(message, state, guessed, url)
            return

    # 3) الحالة الطبيعية: اسم الرابط، ثم نطلب URL في الخطوة التالية
    if len(text) < 1 or len(text) > 40:
        await message.answer("⚠️ اسم الرابط يجب أن يكون بين 1 و 40 حرف.")
        return
    await state.update_data(current_link_title=text)
    await state.set_state(PageCreationStates.waiting_link_url)
    await message.answer(
        f"🌐 الآن أرسل <b>الرابط (URL)</b> الخاص بـ <b>{text}</b>:\n\n"
        "<i>مثال: instagram.com/myname</i>",
        reply_markup=fsm_cancel_link_kb(),
    )


@router.message(PageCreationStates.waiting_link_url, F.text)
async def receive_link_url(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "🔙 إلغاء الرابط الحالي":
        await state.set_state(PageCreationStates.waiting_link_title)
        await _prompt_link_title(message, state)
        return
    if text.startswith("/"):
        return
    url = normalize_url(text)
    if not url:
        await message.answer(
            "⚠️ الرابط غير صحيح. مثال صحيح:\n<code>instagram.com/user</code>\n\nأعد إرسال الرابط:"
        )
        return
    data = await state.get_data()
    title = data.get("current_link_title", "رابط")
    await _add_link_and_continue(message, state, title, url)


async def _add_link_and_continue(message: Message, state: FSMContext, title: str, url: str):
    data = await state.get_data()
    links = data.get("links", [])
    links.append({"title": title, "url": url})
    await state.update_data(links=links)

    is_vip = await db.is_user_vip(message.from_user.id)
    if not is_vip and len(links) >= settings.FREE_LINKS_LIMIT:
        await _finalize_page(message, state, notice_limit=True)
        return

    await state.set_state(PageCreationStates.waiting_link_title)
    await _prompt_link_title(message, state)


@router.callback_query(F.data == "finish_page")
async def cb_finish_page(cq: CallbackQuery, state: FSMContext):
    try:
        await cq.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await _finalize_page(cq.message, state, from_user_id=cq.from_user.id)
    await cq.answer()


@router.callback_query(F.data == "cancel_fsm")
async def cb_cancel_fsm(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await cq.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    is_vip = await db.is_user_vip(cq.from_user.id)
    await cq.message.answer("❌ تم الإلغاء.", reply_markup=main_menu_kb(is_vip))
    await cq.answer()


async def _finalize_page(message: Message, state: FSMContext,
                         notice_limit: bool = False, from_user_id: int = None):
    user_id = from_user_id or message.from_user.id
    data = await state.get_data()
    links = data.get("links", [])
    if not links:
        await state.clear()
        is_vip = await db.is_user_vip(user_id)
        await message.answer("⚠️ لم تضف أي رابط بعد. تم الإلغاء.", reply_markup=main_menu_kb(is_vip))
        return

    await db.update_user_page(user_id, data.get("page_title", ""), data.get("page_bio", ""))
    await db.delete_user_links(user_id)
    for link in links:
        await db.add_link(user_id, link["title"], link["url"])

    await state.clear()

    is_vip = await db.is_user_vip(user_id)
    await message.answer(
        f"🎉 <b>تم حفظ صفحتك بنجاح!</b>\nعدد الروابط: <b>{len(links)}</b>",
        reply_markup=main_menu_kb(is_vip),
    )
    await message.answer("🌐 اضغط لفتح صفحتك:", reply_markup=webapp_preview_kb(user_id))


# ─────────────────────── القوالب ───────────────────────

VIP_ONLY_MSG = "🎉 <b>جميع الميزات مفتوحة ومتاحة لك مجاناً بالكامل 100%!</b>"



@router.message(F.text == "🎨 القوالب")
@router.message(F.text == "🎨 تغيير التصميم")
async def show_themes(message: Message):
    await _render_themes(message, message.from_user.id)


show_themes_legacy = show_themes


@router.callback_query(F.data == "show_themes")
async def cb_show_themes(cq: CallbackQuery):
    await _render_themes(cq.message, cq.from_user.id, edit=True)
    await cq.answer()


async def _render_themes(message: Message, user_id: int, edit: bool = False):
    user = await db.get_user(user_id)
    text = (
        "🎨 <b>اختر قالب صفحتك:</b>\n\n"
        "✨ جميع القوالب الـ 23 مفتوحة ومجانية بالكامل!\n"
        "اضغط على أي قالب لتطبيقه على صفحتك فوراً 👇"
    )
    kb = themes_kb(user["theme"] or 0 if user else 0, is_vip=True)
    if edit:
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("set_theme:"))
async def cb_set_theme(cq: CallbackQuery):
    theme_id = int(cq.data.split(":")[1])
    theme_def = next((t for t in THEMES if t[0] == theme_id), None)
    if not theme_def:
        await cq.answer("قالب غير صالح.", show_alert=True)
        return
    _, name, _ = theme_def
    await db.update_user_theme(cq.from_user.id, theme_id)
    await _render_themes(cq.message, cq.from_user.id, edit=True)
    await cq.answer(f"✅ تم تفعيل القالب: {name}")


@router.callback_query(F.data.startswith("buy_theme:"))
@router.callback_query(F.data.startswith("pay_theme:"))
async def cb_buy_theme(cq: CallbackQuery):
    theme_id = int(cq.data.split(":")[1])
    theme_def = next((t for t in THEMES if t[0] == theme_id), None)
    if theme_def:
        await db.update_user_theme(cq.from_user.id, theme_id)
        await _render_themes(cq.message, cq.from_user.id, edit=True)
        await cq.answer(f"✅ القالب مجاني! تم تفعيل: {theme_def[1]}", show_alert=True)
    else:
        await cq.answer()


# ─────────────────────── الإحصائيات (متاحة للجميع) ───────────────────────

@router.message(F.text == "📊 إحصائياتي")
async def user_stats(message: Message):
    stats = await db.get_user_stats(message.from_user.id)

    # Advanced statistics for VIP users
    lines = [
        "📊 <b>إحصائيات صفحتك المتقدمة (VIP 💎):</b>\n",
        f"👁️ إجمالي الزيارات: <b>{stats['visits']}</b>",
        f"🖱️ إجمالي نقرات الروابط: <b>{stats['total_clicks']}</b>\n",
        "🔗 <b>نقرات الروابط الفردية:</b>",
    ]
    if stats["links"]:
        for link in stats["links"]:
            lines.append(f"• {link['title']}: <b>{link['clicks']}</b> نقرة")
    else:
        lines.append("<i>لم تضف أي روابط بعد.</i>")

    # مصادر الزيارات (Referrers)
    if stats.get("referrers"):
        lines.append("\n📈 <b>مصادر حركة المرور (Traffic Sources):</b>")
        for r in stats["referrers"]:
            lines.append(f"• {r['referrer']}: <b>{r['c']}</b> زيارة")

    # أنظمة التشغيل (OS)
    if stats.get("os_list"):
        lines.append("\n📱 <b>أنظمة تشغيل الأجهزة (OS):</b>")
        for o in stats["os_list"]:
            lines.append(f"• {o['os']}: <b>{o['c']}</b> زيارة")

    # المتصفحات (Browsers)
    if stats.get("browsers"):
        lines.append("\n🌐 <b>المتصفحات المستخدمة:</b>")
        for b in stats["browsers"]:
            lines.append(f"• {b['browser']}: <b>{b['c']}</b> زيارة")

    # الإحصائيات الجغرافية
    if stats.get("countries"):
        lines.append("\n🌍 <b>الدول الأكثر زيارة:</b>")
        for c in stats["countries"]:
            lines.append(f"• {c['country']}: <b>{c['c']}</b> زيارة")

    # توزيع الجنس
    genders = stats.get("genders", {}) or {}
    male = genders.get("male", 0)
    female = genders.get("female", 0)
    unknown = genders.get("unknown", 0)
    total_known = male + female
    if total_known > 0 or unknown > 0:
        lines.append("\n👥 <b>توزيع الجنس للزوار:</b>")
        if total_known > 0:
            male_pct = round((male / total_known) * 100) if total_known else 0
            female_pct = round((female / total_known) * 100) if total_known else 0
            lines.append(f"• 👨 ذكور: <b>{male}</b> ({male_pct}%)")
            lines.append(f"• 👩 إناث: <b>{female}</b> ({female_pct}%)")
        if unknown:
            lines.append(f"• ❓ غير معروف: <b>{unknown}</b>")
            
    # ذروة أوقات التفاعل (Peak Activity Hours)
    peak_hours = await db.get_peak_activity_hours(message.from_user.id)
    if peak_hours:
        lines.append("\n⏰ <b>ذروة أوقات التفاعل الأكثر نشاطاً:</b>")
        for p in peak_hours:
            hour_num = int(p["hour"])
            period = "مساءً" if hour_num >= 12 else "صباحاً"
            h_display = hour_num if hour_num <= 12 else hour_num - 12
            if h_display == 0:
                h_display = 12
            lines.append(f"• الساعة <b>{h_display}:00 {period}</b> — <b>{p['count']}</b> تفاعل")

    await message.answer("\n".join(lines))


# ─────────────────────── كود QR (VIP) - رابط الويب فقط ───────────────────────

@router.message(F.text == "📷 كود QR")
@router.message(F.text == "📷 كود QR الخاص بي")  # توافق
async def user_qr(message: Message):
    user_id = message.from_user.id
    share_url = f"{settings.WEBAPP_BASE_URL}/api/page/{user_id}"

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
        f"🔗 {share_url}\n\n"
        "امسح الكود لفتح الصفحة مباشرة، أو شارك الرابط مع متابعيك!"
    )
    await message.answer_photo(photo, caption=caption)


# ─────────────────────── صورة الأفاتار (متاحة للجميع) ───────────────────────

@router.message(F.text == "🖼 صورتي الشخصية")
async def avatar_menu(message: Message):
    user = await db.get_user(message.from_user.id)
    has_avatar = bool(user and user.get("avatar_path"))
    text = (
        "🖼 <b>الصورة الشخصية</b>\n\n"
        "ارفع صورة أفاتار احترافية لتظهر بدل حرف الاسم على صفحتك.\n"
        + ("✅ يوجد لديك صورة مرفوعة حالياً." if has_avatar else "❌ لا يوجد صورة حالياً.")
    )
    await message.answer(text, reply_markup=avatar_menu_kb(has_avatar))


@router.callback_query(F.data == "upload_avatar")
async def cb_upload_avatar(cq: CallbackQuery, state: FSMContext):
    await state.set_state(AvatarStates.waiting_photo)
    await cq.message.edit_text(
        "📤 أرسل الآن <b>الصورة</b> التي تريدها كصورة شخصية.\n\n"
        "💡 نصائح للحصول على أفضل نتيجة:\n"
        "• صورة مربعة (نسبة 1:1)\n"
        "• واضحة وعالية الجودة\n"
        "• ملف حجمه أقل من 5 ميجابايت\n\n"
        "أرسل /cancel للإلغاء.",
    )
    await cq.answer()


@router.message(AvatarStates.waiting_photo, F.photo)
async def receive_avatar_photo(message: Message, state: FSMContext, bot: Bot):
    # أكبر مقاس متاح
    photo: PhotoSize = message.photo[-1]
    os.makedirs(settings.AVATARS_DIR, exist_ok=True)
    file_path = os.path.join(settings.AVATARS_DIR, f"{message.from_user.id}.jpg")
    try:
        await bot.download(photo, destination=file_path)
    except Exception as e:
        await message.answer(f"❌ فشل تنزيل الصورة: {e}")
        return
    await db.update_user_avatar(message.from_user.id, file_path)
    await state.clear()
    await message.answer(
        "✅ <b>تم حفظ صورتك الشخصية!</b>\n"
        "ستظهر الآن على صفحتك بدل الحرف الأول.",
        reply_markup=main_menu_kb(True),
    )


@router.message(AvatarStates.waiting_photo)
async def avatar_wrong_type(message: Message):
    await message.answer("⚠️ الرجاء إرسال <b>صورة</b> فقط (كصورة وليست ملف). أو /cancel للإلغاء.")


@router.callback_query(F.data == "delete_avatar")
async def cb_delete_avatar(cq: CallbackQuery):
    is_vip = await db.is_user_vip(cq.from_user.id)
    if not is_vip:
        await cq.answer("VIP فقط", show_alert=True)
        return
    user = await db.get_user(cq.from_user.id)
    if user and user.get("avatar_path"):
        try:
            os.remove(user["avatar_path"])
        except Exception:
            pass
    await db.update_user_avatar(cq.from_user.id, None)
    await cq.message.edit_text("🗑 تم حذف الصورة الشخصية.")
    await cq.answer("تم الحذف")


# ─────────────────────── نظام الإحالة (User side) ───────────────────────

@router.message(F.text.in_({"🎁 دعوة أصدقاء", "🎁 دعوة اصدقاء", "دعوة أصدقاء", "دعوة اصدقاء", "🎁 دعوة أصدقاء (VIP مجاني)"}))
async def user_referral(message: Message):
    await _show_referral(message)


@router.callback_query(F.data == "show_referral")
async def cb_show_referral(cq: CallbackQuery):
    await _show_referral(cq.message, override_user_id=cq.from_user.id)
    await cq.answer()


async def _show_referral(message: Message, override_user_id: int = None):
    user_id = override_user_id or message.from_user.id
    count = await db.get_referral_count(user_id)
    share_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{user_id}"
    
    text = (
        "🌟 <b>ادعُ أصدقاءك وانشر الفائدة للجميع!</b> 🚀\n\n"
        "💡 <b>الدال على الخير كفاعله:</b>\n"
        "دلّ أصدقاءك، زملاءك، وأصحاب المشاريع وصناع المحتوى على البوت لكي يستفيدوا من <b>إنشاء بروفايل احترافي وتنظيم كل روابطهم وحساباتهم مجاناً بالكامل 100%!</b> ✨\n\n"
        "🎁 <b>لماذا ينصح بمشاركة البوت مع أصدقائك؟</b>\n"
        "• <b>مجاني بالكامل للجميع:</b> لا يوجد أي اشتراك أو دفع، كل الميزات مفتوحة فوراً!\n"
        "• <b>23 ثيم وقالب فاخر:</b> تصاميم عصرية تناسب كل التخصصات والأذواق.\n"
        "• <b>روابط وصفحات غير محدودة:</b> تجميع كل وسائل التواصل في صفحة واحدة أنيقة وسريعة.\n"
        "• <b>شارات توثيق مميزة:</b> شارات احترافية كشارات انستغرام والشارة الملكية.\n"
        "• <b>إحصائيات دقيقة:</b> تتبع عدد الزيارات ونقرات الروابط والدول.\n\n"
        "👥 <b>إحصائيات مشاركاتك:</b>\n"
        f"• عدد الأصدقاء الذين استفادوا وانضموا عبرك: <b>{count}</b> صديق 🎉\n\n"
        f"🔗 <b>رابط الدعوة والمشاركة الخاص بك:</b>\n"
        f"<code>{share_link}</code>\n\n"
        "📲 <b>انشر رابطك الآن</b> في مجموعاتك وقنواتك وشاركه مع أصدقائك لتعم الفائدة بالضغط على الزر أدناه 👇"
    )
    await message.answer(text, reply_markup=referral_kb(share_link))


# ─────────────────────── حسابي ───────────────────────

@router.message(F.text == "ℹ️ حسابي")
async def my_account(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("لم يتم العثور على حسابك. أرسل /start")
        return
    ref_count = user.get("referral_count") or 0
    unlocked = await db.get_unlocked_themes(message.from_user.id)
    text = (
        "ℹ️ <b>معلومات حسابي</b>\n\n"
        f"👤 الاسم: <b>{user.get('full_name') or '-'}</b>\n"
        f"🆔 الآيدي: <code>{user['user_id']}</code>\n"
        f"🔖 اليوزر: {('@' + user['username']) if user.get('username') else '-'}\n"
        "✨ حالة الحساب: <b>مفعّل بجميع الميزات مجاناً 100% 🌟</b>\n"
        f"👥 عدد الأصدقاء المستفيدين عبرك: <b>{ref_count}</b> صديق 🎉\n"
        f"🎨 رقم القالب الحالي: <b>{user.get('theme') or 0}</b>\n"
        f"🖼 الصورة الشخصية: {'مفعّلة ✅' if user.get('avatar_path') else 'غير محددة'}\n"
    )
    await message.answer(text)


# ─────────────────────── الميزات المتاحة (شرح كامل) ───────────────────────

@router.message(F.text.in_({"⭐ الميزات", "⭐ ميزات البوت", "⭐ ميزات VIP", "الميزات"}))
async def show_vip_features(message: Message):
    header = "✨ <b>جميع ميزات المنصة مفتوحة ومتاحة لك مجاناً بالكامل 100%!</b>\n\n"
    await message.answer(header + VIP_FEATURES_TEXT)


@router.callback_query(F.data == "cmd_vip_cb")
async def cb_cmd_vip_from_gate(cq: CallbackQuery):
    header = "✨ <b>جميع ميزات المنصة مفتوحة ومتاحة لك مجاناً بالكامل 100%!</b>\n\n"
    await cq.message.answer(header + VIP_FEATURES_TEXT)
    await cq.answer()


@router.callback_query(F.data == "cmd_ref_cb")
async def cb_cmd_ref_from_gate(cq: CallbackQuery):
    await _show_referral(cq.message, override_user_id=cq.from_user.id)
    await cq.answer()



# ─────────────────────── الدعم الفني والتواصل ───────────────────────

@router.message(F.text.in_({"🛠️ الدعم الفني", "الدعم الفني", "🛠 الدعم الفني", "الدعم", "📞 تواصل مع المطور", "تواصل مع المطور", "الدعم والمساعدة"}))
@router.message(Command("support"))
@router.message(Command("contact"))
@router.callback_query(F.data == "support")
async def contact_developer(event: Message | CallbackQuery):
    dev = settings.DEVELOPER_USERNAME or "d91ik"
    support_id = 6641619062
    text = (
        "🛠️ <b>قسم الدعم الفني والمساعدة</b>\n\n"
        "مرحباً بك! إذا واجهتك أي مشكلة، أو كان لديك أي استفسار حول البوت، إنشاء وتعديل صفحاتك، أو اشتراك VIP، يمكنك التواصل مع الدعم الفني مباشرة:\n\n"
        f"👤 <b>حساب الدعم:</b> @{dev}\n"
        f"🆔 <b>آيدي الدعم (ID):</b> <code>{support_id}</code>\n\n"
        "اضغط على الزر بالأسفل لفتح المحادثة ومراسلة الدعم فوراً 👇"
    )
    kb = support_kb()
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=kb, disable_web_page_preview=True)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, disable_web_page_preview=True)

contact_support = contact_developer


# ─────────────────────── /help ───────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "❓ <b>مساعدة</b>\n\n"
        "<b>الأوامر الرئيسية:</b>\n"
        "• /start - بدء الاستخدام\n"
        "• /support - الدعم الفني والمساعدة\n"
        "• /help - عرض المساعدة\n"
        "• /cancel - إلغاء العملية الحالية\n"
        "• /edit - إنشاء / تعديل صفحتي\n"
        "• /page - معاينة صفحتي\n"
        "• /qr - كود QR لصفحتي\n"
        "• /features - استعراض ميزات المنصة\n"
        "• /invite - دعوة الأصدقاء ونشر الفائدة\n"
        "• /stats - إحصائيات الزيارات\n"
        "• /themes - القوالب والتصاميم\n"
        "• /avatar - الصورة الشخصية\n"
        "• /account - معلومات حسابي\n"
        "• /contact - تواصل مع الدعم الفني\n"
    )
    await message.answer(text)


# ─────────────────────── أوامر إضافية (Slash Commands) ───────────────────────

@router.message(Command("edit"))
async def cmd_edit(message: Message, state: FSMContext):
    await start_page_creation(message, state)


@router.message(Command("page"))
async def cmd_page(message: Message):
    await preview_page(message)


@router.message(Command("qr"))
async def cmd_qr(message: Message):
    await user_qr(message)


@router.message(Command("vip"))
async def cmd_vip(message: Message):
    from bot.handlers.payment_handlers import show_subscription
    await show_subscription(message)


@router.message(Command("features"))
async def cmd_features(message: Message):
    await show_vip_features(message)


@router.message(Command("invite"))
async def cmd_invite(message: Message):
    await user_referral(message)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    await user_stats(message)


@router.message(Command("themes"))
async def cmd_themes(message: Message):
    await show_themes(message)


@router.message(Command("avatar"))
async def cmd_avatar(message: Message):
    await avatar_menu(message)


@router.message(Command("account"))
async def cmd_account(message: Message):
    await my_account(message)


@router.message(Command("contact"))
async def cmd_contact(message: Message):
    await contact_developer(message)


# ─────────────────────────── التخصيص المتقدم (VIP) ───────────────────────────

@router.message(F.text.in_({"🎯 تخصيص متقدم والقوالب", "🎯 تخصيص متقدم"}))
async def show_customization_menu(message: Message):
    user = await db.get_user(message.from_user.id)
    show_badge = user.get("show_badge") if (user and user.get("show_badge") is not None) else 1
    await message.answer(
        "⚙️ <b>لوحة التخصيص المتقدم والتصاميم</b>\n\n"
        "جميع أدوات التخصيص مفتوحة ومجانية بالكامل!\n"
        "اختر أحد الخيارات أدناه لتعديل مظهر صفحتك الشخصية:",
        reply_markup=customize_menu_kb(bool(show_badge))
    )


@router.callback_query(F.data == "customize_color")
async def cb_customize_color(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    current_color = user.get("accent_color") if user else None
    await cq.message.edit_text(
        "🎨 <b>اختر لوناً مميزاً (Accent Color) لصفحتك:</b>\n\n"
        "سيتم تطبيق هذا اللون على الأيقونات، الخطوط، والتفاصيل الهامة في صفحتك الخاصة.",
        reply_markup=accent_colors_kb(current_color)
    )
    await cq.answer()


@router.callback_query(F.data.startswith("set_color:"))
async def cb_set_color(cq: CallbackQuery):
    color = cq.data.split(":")[1]
    await db.update_accent_color(cq.from_user.id, color)
    await cq.message.edit_reply_markup(reply_markup=accent_colors_kb(color))
    await cq.answer(f"✅ تم حفظ اللون الجديد بنجاح!")


@router.callback_query(F.data == "reset_color")
async def cb_reset_color(cq: CallbackQuery):
    await db.update_accent_color(cq.from_user.id, None)
    await cq.message.edit_reply_markup(reply_markup=accent_colors_kb(None))
    await cq.answer("🔄 تم استعادة اللون الافتراضي للقالب.")


@router.callback_query(F.data == "customize_style")
async def cb_customize_style(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    current_style = user.get("button_style") or "rounded" if user else "rounded"
    await cq.message.edit_text(
        "🔘 <b>اختر شكل أزرار الروابط لصفحتك:</b>\n\n"
        "سيتم تطبيق هذا الشكل على كافة أزرار الروابط في صفحة المعاينة الخاصة بك.",
        reply_markup=button_styles_kb(current_style)
    )
    await cq.answer()


@router.callback_query(F.data.startswith("set_style:"))
async def cb_set_style(cq: CallbackQuery):
    style = cq.data.split(":")[1]
    await db.update_button_style(cq.from_user.id, style)
    await cq.message.edit_reply_markup(reply_markup=button_styles_kb(style))
    await cq.answer("✅ تم تحديث شكل الأزرار بنجاح!")


@router.callback_query(F.data == "customize_avatar")
async def cb_customize_avatar(cq: CallbackQuery):
    await cq.message.delete()
    await avatar_menu(cq.message)
    await cq.answer()


@router.callback_query(F.data == "customize_back")
async def cb_customize_back(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(cq.from_user.id)
    show_badge = user.get("show_badge") if (user and user.get("show_badge") is not None) else 1
    await cq.message.edit_text(
        "⚙️ <b>لوحة التخصيص المتقدم والتصاميم</b>\n\n"
        "جميع أدوات التخصيص مفتوحة ومجانية بالكامل!\n"
        "اختر أحد الخيارات أدناه لتعديل مظهر صفحتك الشخصية:",
        reply_markup=customize_menu_kb(bool(show_badge))
    )
    await cq.answer()


@router.callback_query(F.data == "toggle_badge")
async def cb_toggle_badge(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    current = user.get("show_badge") if (user and user.get("show_badge") is not None) else 1
    new_val = 0 if current else 1
    await db.update_show_badge(cq.from_user.id, new_val)
    await cq.message.edit_reply_markup(reply_markup=customize_menu_kb(bool(new_val)))
    await cq.answer(f"✅ تم {'تفعيل' if new_val else 'تعطيل'} شارة التوثيق بنجاح!")


# ─────────────────────────── الخطوط العربية الفاخرة (VIP) ───────────────────────────

@router.callback_query(F.data == "customize_font")
async def cb_customize_font(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    current_font = user.get("font_family") or "Tajawal" if user else "Tajawal"
    await cq.message.edit_text(
        "🔤 <b>اختر نوع الخط العربي لصفحتك:</b>\n\n"
        "تم انتقاء باقة من أرقى الخطوط العربية العالمية لتعطي صفحتك مظهراً فائق الاحترافية والأناقة 🌟",
        reply_markup=fonts_kb(current_font)
    )
    await cq.answer()


@router.callback_query(F.data.startswith("set_font:"))
async def cb_set_font(cq: CallbackQuery):
    font_id = cq.data.split(":")[1]
    await db.update_font(cq.from_user.id, font_id)
    await cq.message.edit_reply_markup(reply_markup=fonts_kb(font_id))
    await cq.answer(f"✅ تم تطبيق خط {font_id} بنجاح!")


# ─────────────────────────── شريط الإعلانات العاجل المتحرك (VIP) ───────────────────────────

@router.callback_query(F.data == "customize_marquee")
async def cb_customize_marquee(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    has_marquee = bool(user and user.get("marquee_text"))
    text = (
        "📢 <b>شريط الإعلانات العاجل المتحرك + رابط (Marquee News Bar)</b>\n\n"
        "شريط شريطي احترافي يظهر في أعلى صفحتك للإعلان عن خصم، فيديو جديد، إطلاق منتج، أو خبر عاجل، مع إمكانية ربطه برابط يفتح عند النقر! 🚀\n\n"
    )
    if has_marquee:
        text += f"• النص الحالي: <i>\"{user['marquee_text']}\"</i>\n"
        if user.get("marquee_url"):
            text += f"• الرابط المرتبط: <code>{user['marquee_url']}</code>\n"
        else:
            text += "• الرابط: <i>بدون رابط (نص فقط)</i>\n"
    else:
        text += "• الحالة: <i>غير مفعّل</i>\n"
    await cq.message.edit_text(text, reply_markup=marquee_menu_kb(has_marquee))
    await cq.answer()


@router.callback_query(F.data == "set_marquee_txt")
async def cb_set_marquee_txt(cq: CallbackQuery, state: FSMContext):
    await state.set_state(CustomizationStates.waiting_marquee_text)
    await cq.message.edit_text(
        "📢 <b>كتابة نص الإعلان المتحرك</b>\n\n"
        "أرسل الآن نص الإعلان أو الخبر الذي تريده أن يظهر في الشريط المتحرك أعلى صفحتك:\n\n"
        "💡 <i>(مثال: 🔥 خصم 50% لفترة محدودة على جميع الاستشارات | اضغط هنا 👇)</i>\n\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=None
    )
    await cq.answer()


@router.message(CustomizationStates.waiting_marquee_text)
async def do_set_marquee_text(message: Message, state: FSMContext):
    txt = (message.text or "").strip()[:150]
    if not txt:
        await message.answer("⚠️ الرجاء كتابة نص للإعلان.")
        return
    await state.update_data(marquee_text=txt)
    await state.set_state(CustomizationStates.waiting_marquee_url)
    await message.answer(
        f"✅ تم حفظ النص: \"{txt}\"\n\n"
        "🔗 <b>هل ترغب بربط الإعلان برابط يفتح عند النقر عليه؟</b>\n\n"
        "• أرسل الرابط الآن (مثال: <code>https://t.me/mychannel</code> أو <code>https://mysite.com</code>)\n"
        "• أو أرسل /skip لتثبيت الإعلان كنص فقط بدون رابط.",
        reply_markup=None
    )


@router.message(CustomizationStates.waiting_marquee_url)
async def do_set_marquee_url(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    data = await state.get_data()
    marquee_text = data.get("marquee_text", "")
    
    url = None
    if txt and txt != "/skip":
        if not (txt.startswith("http://") or txt.startswith("https://")):
            txt = "https://" + txt
        url = txt

    await db.update_marquee(message.from_user.id, marquee_text, url)
    await state.clear()
    
    res = f"✅ <b>تم تفعيل شريط الإعلانات بنجاح!</b>\n\n• النص: \"{marquee_text}\"\n"
    if url:
        res += f"• الرابط: <code>{url}</code> (قابل للنقر 🔗)\n\n"
    else:
        res += "• الرابط: بدون رابط\n\n"
    res += "افتح صفحتك الآن لتشاهد الشريط المتحرك في الأعلى ✨"
    await message.answer(res, reply_markup=main_menu_kb(True))


@router.callback_query(F.data == "delete_marquee_txt")
async def cb_delete_marquee_txt(cq: CallbackQuery):
    await db.update_marquee(cq.from_user.id, None, None)
    await cq.message.edit_text("🗑 تم حذف شريط الإعلانات من صفحتك.", reply_markup=marquee_menu_kb(False))
    await cq.answer("تم الحذف")


# ─────────────────────────── العداد التنازلي للعروض (VIP) ───────────────────────────

@router.callback_query(F.data == "customize_countdown")
async def cb_customize_countdown(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    has_cd = bool(user and user.get("countdown_target"))
    text = (
        "⏳ <b>العداد التنازلي للأحداث والعروض (Countdown Timer)</b>\n\n"
        "ودجت زجاجي تفاعلي لحساب الوقت المتبقي (أيام : ساعات : دقائق : ثواني) لخلق حافز الشراء والترقب لدى زوارك فور دخولهم! 🔥\n\n"
    )
    if has_cd:
        text += f"• عنوان العداد: <i>\"{user.get('countdown_title') or 'ينتهي العرض خلال:'}\"</i>\n"
        text += f"• الموعد المستهدف: <code>{user.get('countdown_target')}</code>\n"
    else:
        text += "• الحالة: <i>غير مفعّل</i>\n"
    await cq.message.edit_text(text, reply_markup=countdown_menu_kb(has_cd))
    await cq.answer()


@router.callback_query(F.data == "set_countdown")
async def cb_set_countdown(cq: CallbackQuery, state: FSMContext):
    await state.set_state(CustomizationStates.waiting_countdown_title)
    await cq.message.edit_text(
        "⏳ <b>إعداد العداد التنازلي (الخطوة 1 من 2)</b>\n\n"
        "أرسل الآن عنوان الحدث أو العرض الذي سيظهر فوق العداد التنازلي:\n\n"
        "💡 <i>(أمثلة: 🔥 ينتهي الخصم الخاص خلال: / 🚀 باقي على إطلاق الدورة: / ⏰ عرض اليوم الوطني ينتهي في:)</i>\n\n"
        "أرسل /skip لاستخدام العنوان الافتراضي، أو /cancel للإلغاء.",
        reply_markup=None
    )
    await cq.answer()


@router.message(CustomizationStates.waiting_countdown_title)
async def do_set_countdown_title(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    title = "ينتهي العرض الخاص خلال:" if txt == "/skip" else txt[:80]
    await state.update_data(countdown_title=title)
    await state.set_state(CustomizationStates.waiting_countdown_target)
    
    import datetime
    example_dt = (datetime.datetime.now() + datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
    await message.answer(
        f"⏳ <b>تحديد تاريخ ووقت انتهاء العداد (الخطوة 2 من 2)</b>\n\n"
        f"أرسل الآن تاريخ ووقت الانتهاء بالصيغة: <code>YYYY-MM-DD HH:MM</code>\n"
        f"• مثال: <code>{example_dt}</code>\n"
        f"• أو يمكنك كتابة عدد الأيام مباشرة (مثلاً: <code>3</code> لتحديد 3 أيام من الآن).\n\n"
        "أرسل /cancel للإلغاء."
    )


@router.message(CustomizationStates.waiting_countdown_target)
async def do_set_countdown_target(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    import datetime
    target_iso = None

    # Check if number of days
    if txt.isdigit():
        days = int(txt)
        dt = datetime.datetime.now() + datetime.timedelta(days=days)
        target_iso = dt.strftime("%Y-%m-%dT%H:%M:00")
    else:
        # Try parsing YYYY-MM-DD HH:MM or YYYY-MM-DD
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M", "%Y/%m/%d"):
            try:
                dt = datetime.datetime.strptime(txt, fmt)
                target_iso = dt.strftime("%Y-%m-%dT%H:%M:00")
                break
            except ValueError:
                pass

    if not target_iso:
        await message.answer("⚠️ صيغة التاريخ غير صحيحة. الرجاء إرسالها بصيغة <code>YYYY-MM-DD HH:MM</code> أو كتابة عدد الأيام كرقم (مثال: <code>3</code>).")
        return

    data = await state.get_data()
    title = data.get("countdown_title", "ينتهي العرض الخاص خلال:")
    await db.update_countdown(message.from_user.id, title, target_iso)
    await state.clear()

    await message.answer(
        f"✅ <b>تم تفعيل العداد التنازلي بنجاح! ⏳</b>\n\n"
        f"• العنوان: \"{title}\"\n"
        f"• ينتهي في: <code>{target_iso}</code>\n\n"
        "افتح صفحتك الآن لتشاهد العداد التنازلي التفاعلي المباشر!",
        reply_markup=main_menu_kb(True)
    )


@router.callback_query(F.data == "delete_countdown")
async def cb_delete_countdown(cq: CallbackQuery):
    await db.update_countdown(cq.from_user.id, None, None)
    await cq.message.edit_text("🗑 تم حذف العداد التنازلي من صفحتك.", reply_markup=countdown_menu_kb(False))
    await cq.answer("تم الحذف")


# ─────────────────────────── الدومين المخصص CNAME (VIP) ───────────────────────────

@router.callback_query(F.data == "customize_domain")
async def cb_customize_domain(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    current_domain = user.get("custom_domain") if user else None
    text = (
        "🌐 <b>ربط النطاقات المخصصة (Custom Domain - CNAME)</b>\n\n"
        "اربط نطاقك الخاص (مثل: <code>bio.mybrand.com</code> أو <code>links.name.me</code>) ليفتح صفحتك مباشرة بدون روابط خارجية!\n\n"
        "📌 <b>طريقة الربط:</b>\n"
        "1. ادخل إلى لوحة تحكم نطاقك (Cloudflare / GoDaddy / Namecheap).\n"
        "2. أضف سجل <b>CNAME</b> للنطاق الفرعي ووجهه إلى سيرفر البوت.\n"
        "3. اكتب اسم النطاق هنا لتفعيله فوراً.\n\n"
    )
    if current_domain:
        text += f"• النطاق المرتبط حالياً: <code>{current_domain}</code> ✅\n"
    else:
        text += "• الحالة: <i>لم يتم ربط نطاق بعد</i>\n"
    await cq.message.edit_text(text, reply_markup=custom_domain_menu_kb(bool(current_domain)))
    await cq.answer()


@router.callback_query(F.data == "set_custom_domain")
async def cb_set_custom_domain(cq: CallbackQuery, state: FSMContext):
    await state.set_state(CustomizationStates.waiting_custom_domain)
    await cq.message.edit_text(
        "🌐 <b>إدخال الدومين المخصص</b>\n\n"
        "أرسل الآن اسم النطاق الذي ترغب بربطه (مثال: <code>bio.mybrand.com</code> أو <code>links.ahmed.me</code>):\n\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=None
    )
    await cq.answer()


@router.message(CustomizationStates.waiting_custom_domain)
async def do_set_custom_domain(message: Message, state: FSMContext):
    domain = (message.text or "").strip().lower().lstrip("http://").lstrip("https://").rstrip("/")
    import re
    if not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", domain):
        await message.answer("⚠️ اسم النطاق غير صالح. الرجاء إرسال اسم نطاق صحيح (مثال: <code>bio.mybrand.com</code>).")
        return

    # Check if domain taken by another user
    existing = await db.get_user_by_custom_domain(domain)
    if existing and int(existing["user_id"]) != message.from_user.id:
        await message.answer("❌ هذا النطاق مرتبط بحساب مستخدم آخر بالفعل!")
        return

    await db.update_custom_domain(message.from_user.id, domain)
    await state.clear()
    await message.answer(
        f"✅ <b>تم ربط النطاق بنجاح! 🌐</b>\n\n"
        f"• النطاق: <code>{domain}</code>\n\n"
        f"بمجرد اكتمال توجيه CNAME في مزود النطاق، سيفتح رابط <code>http://{domain}</code> صفحتك مباشرة!",
        reply_markup=main_menu_kb(True)
    )


@router.callback_query(F.data == "delete_custom_domain")
async def cb_delete_custom_domain(cq: CallbackQuery):
    await db.update_custom_domain(cq.from_user.id, None)
    await cq.message.edit_text("🗑 تم فك ربط النطاق المخصص من صفحتك.", reply_markup=custom_domain_menu_kb(False))
    await cq.answer("تم الحذف")


# ─────────────────────────── بكسل التتبع الإعلاني (VIP) ───────────────────────────

@router.callback_query(F.data == "customize_pixels")
async def cb_customize_pixels(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    meta = user.get("meta_pixel") if user else None
    tiktok = user.get("tiktok_pixel") if user else None
    ga = user.get("ga_pixel") if user else None
    
    text = (
        "🔮 <b>بكسل التتبع الإعلاني والحملات الممولة (Tracking Pixels)</b>\n\n"
        "أضف أكواد التتبع لبناء جماهير مخصصة (Custom Audiences) وإعادة استهداف زوار صفحتك (Retargeting) عبر إعلانات فيسبوك، انستغرام، وتيك توك، وتتبع دقيق عبر Google Analytics! 📈\n\n"
    )
    text += f"• Meta / Facebook Pixel: <code>{meta or 'غير مفعّل'}</code>\n"
    text += f"• TikTok Pixel: <code>{tiktok or 'غير مفعّل'}</code>\n"
    text += f"• Google Analytics (GA4): <code>{ga or 'غير مفعّل'}</code>\n"
    
    await cq.message.edit_text(text, reply_markup=pixels_menu_kb(bool(meta), bool(tiktok), bool(ga)))
    await cq.answer()


@router.callback_query(F.data == "set_pixel_meta")
async def cb_set_pixel_meta(cq: CallbackQuery, state: FSMContext):
    await state.set_state(CustomizationStates.waiting_meta_pixel)
    await cq.message.edit_text(
        "🔵 <b>إعداد Meta / Facebook Pixel</b>\n\n"
        "أرسل الآن الـ <b>Pixel ID</b> الخاص بحسابك الإعلاني في Meta (أرقام فقط، مثال: <code>123456789012345</code>):\n\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=None
    )
    await cq.answer()


@router.message(CustomizationStates.waiting_meta_pixel)
async def do_set_pixel_meta(message: Message, state: FSMContext):
    pid = (message.text or "").strip()
    if not pid:
        await message.answer("⚠️ الرجاء إرسال معرف البكسل.")
        return
    user = await db.get_user(message.from_user.id)
    await db.update_pixels(
        message.from_user.id,
        meta=pid,
        tiktok=user.get("tiktok_pixel") if user else None,
        ga=user.get("ga_pixel") if user else None
    )
    await state.clear()
    await message.answer(f"✅ تم حفظ Meta Pixel ID: <code>{pid}</code> بنجاح!", reply_markup=main_menu_kb(True))


@router.callback_query(F.data == "set_pixel_tiktok")
async def cb_set_pixel_tiktok(cq: CallbackQuery, state: FSMContext):
    await state.set_state(CustomizationStates.waiting_tiktok_pixel)
    await cq.message.edit_text(
        "🎵 <b>إعداد TikTok Pixel</b>\n\n"
        "أرسل الآن الـ <b>TikTok Pixel ID</b> من مدير إعلانات تيك توك (مثال: <code>C1234567890ABCDEFGH</code>):\n\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=None
    )
    await cq.answer()


@router.message(CustomizationStates.waiting_tiktok_pixel)
async def do_set_pixel_tiktok(message: Message, state: FSMContext):
    pid = (message.text or "").strip()
    if not pid:
        await message.answer("⚠️ الرجاء إرسال معرف البكسل.")
        return
    user = await db.get_user(message.from_user.id)
    await db.update_pixels(
        message.from_user.id,
        meta=user.get("meta_pixel") if user else None,
        tiktok=pid,
        ga=user.get("ga_pixel") if user else None
    )
    await state.clear()
    await message.answer(f"✅ تم حفظ TikTok Pixel ID: <code>{pid}</code> بنجاح!", reply_markup=main_menu_kb(True))


@router.callback_query(F.data == "set_pixel_ga")
async def cb_set_pixel_ga(cq: CallbackQuery, state: FSMContext):
    await state.set_state(CustomizationStates.waiting_ga_pixel)
    await cq.message.edit_text(
        "📊 <b>إعداد Google Analytics (GA4)</b>\n\n"
        "أرسل الآن معرف القياس <b>Measurement ID</b> من Google Analytics (مثال: <code>G-XXXXXXXXXX</code>):\n\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=None
    )
    await cq.answer()


@router.message(CustomizationStates.waiting_ga_pixel)
async def do_set_pixel_ga(message: Message, state: FSMContext):
    pid = (message.text or "").strip()
    if not pid:
        await message.answer("⚠️ الرجاء إرسال معرف القياس.")
        return
    user = await db.get_user(message.from_user.id)
    await db.update_pixels(
        message.from_user.id,
        meta=user.get("meta_pixel") if user else None,
        tiktok=user.get("tiktok_pixel") if user else None,
        ga=pid
    )
    await state.clear()
    await message.answer(f"✅ تم حفظ Google Analytics Measurement ID: <code>{pid}</code> بنجاح!", reply_markup=main_menu_kb(True))


@router.callback_query(F.data == "delete_pixels")
async def cb_delete_pixels(cq: CallbackQuery):
    await db.update_pixels(cq.from_user.id, None, None, None)
    await cq.message.edit_text("🗑 تم حذف جميع أكواد التتبع الإعلاني من صفحتك.", reply_markup=pixels_menu_kb())
    await cq.answer("تم الحذف")


# ─────────────────────────── الخلفيات الحية (VIP) ───────────────────────────

@router.callback_query(F.data == "customize_bg_effects")
async def cb_customize_bg_effects(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    current = user.get("bg_effect") or "none" if user else "none"
    await cq.message.edit_text(
        "🎬 <b>الخلفيات التفاعلية الحية (Live Canvas Effects):</b>\n\n"
        "اختر أحد المؤثرات الحية المتحركة لتظهر في خلفية صفحتك الشخصية بجاذبية فائقة ✨",
        reply_markup=bg_effects_kb(current)
    )
    await cq.answer()


@router.callback_query(F.data.startswith("set_bgeff:"))
async def cb_set_bgeff(cq: CallbackQuery):
    eff_id = cq.data.split(":")[1]
    await db.update_bg_effect(cq.from_user.id, eff_id)
    await cq.message.edit_reply_markup(reply_markup=bg_effects_kb(eff_id))
    await cq.answer("✅ تم تحديث الخلفية الحية لصفحتك بنجاح!")


# ─────────────────────────── شارات التوثيق (VIP) ───────────────────────────

@router.callback_query(F.data == "customize_badge_type")
async def cb_customize_badge_type(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    current = user.get("badge_type") or "blue" if user else "blue"
    await cq.message.edit_text(
        "🏆 <b>اختر نوع شارة التوثيق لصفحتك:</b>\n\n"
        "• 🔵 <b>رسمي موثق:</b> الشارة الكلاسيكية الزرقاء المعتمدة.\n"
        "• 👑 <b>ملكي ذهبي (VIP):</b> تاج ملكي ذهبي مضيء ولامع.\n"
        "• 💎 <b>ألماسي نخبوي:</b> ماسة نادرة بتأثيرات بريق متحركة.\n"
        "• 🎬 <b>صانع محتوى:</b> شارة النجوم الخاصة بالمشاهير والمؤثرين.",
        reply_markup=badge_types_kb(current)
    )
    await cq.answer()


@router.callback_query(F.data.startswith("set_badgetype:"))
async def cb_set_badgetype(cq: CallbackQuery):
    b_id = cq.data.split(":")[1]
    await db.update_badge_type(cq.from_user.id, b_id)
    await cq.message.edit_reply_markup(reply_markup=badge_types_kb(b_id))
    await cq.answer("✅ تم تغيير نوع شارة التوثيق بنجاح!")


# ─────────────────────────── مشغل الصوتيات (VIP) ───────────────────────────

@router.callback_query(F.data == "customize_music")
async def cb_customize_music(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    has_music = bool(user and user.get("music_url"))
    curr_title = user.get("music_title") or "بدون عنوان"
    text = (
        "🎵 <b>مشغل الصوتيات والبودكاست المدمج (Audio Player)</b>\n\n"
        "يتيح لك وضع مقطع صوتي، تلاوة قرآنية، بودكاست، أو نغمة ترحيبية تعمل في صفحتك بمشغل عائم أنيق مع موجات صوتية متفاعلة 🎧\n\n"
    )
    if has_music:
        text += f"• المقطع الحالي: <b>{curr_title}</b>\n• الرابط: <code>{user['music_url']}</code>\n"
    else:
        text += "• الحالة: <i>لم يتم تعيين مقطع صوتي بعد.</i>\n"
        
    await cq.message.edit_text(text, reply_markup=music_menu_kb(has_music))
    await cq.answer()


@router.callback_query(F.data == "set_music_url")
async def cb_set_music_url(cq: CallbackQuery, state: FSMContext):
    await state.set_state(CustomizationStates.waiting_music_url)
    await cq.message.edit_text(
        "🎵 <b>إضافة مقطع صوتي لصفحتك</b>\n\n"
        "أرسل رابط مباشر للمقطع الصوتي (ينتهي بـ <code>.mp3</code> أو رابط مباشر صوتي).\n\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=None
    )
    await cq.answer()


@router.message(CustomizationStates.waiting_music_url)
async def do_set_music_url(message: Message, state: FSMContext):
    url = (message.text or "").strip()
    if not url.startswith("http"):
        await message.answer("⚠️ الرجاء إرسال رابط صوتي يبدأ بـ https://")
        return
    await state.update_data(music_url=url)
    await state.set_state(CustomizationStates.waiting_music_title)
    await message.answer(
        "✏️ أرسل الآن <b>عنوان أو اسم المقطع الصوتي</b> ليظهر في المشغل (مثال: سورة الرحمن بصوت القارئ، أو نغمة ترحيبية):"
    )


@router.message(CustomizationStates.waiting_music_title)
async def do_set_music_title(message: Message, state: FSMContext):
    title = (message.text or "مقطع صوتي").strip()[:60]
    data = await state.get_data()
    url = data.get("music_url")
    await db.update_music(message.from_user.id, url, title)
    await state.clear()
    await message.answer(
        f"✅ <b>تم تفعيل مشغل الصوتيات بنجاح!</b>\n\n• العنوان: <b>{title}</b>\n• الرابط: <code>{url}</code>\n\nافتح صفحتك الآن لتستمتع بالمشغل!",
        reply_markup=main_menu_kb(True)
    )


@router.callback_query(F.data == "delete_music_url")
async def cb_delete_music_url(cq: CallbackQuery):
    await db.update_music(cq.from_user.id, None, None)
    await cq.message.edit_text("🗑 تم حذف المقطع الصوتي من صفحتك.", reply_markup=music_menu_kb(False))
    await cq.answer("تم الحذف")


# ─────────────────────────── زر محادثة واتساب المباشر ───────────────────────────

@router.callback_query(F.data == "customize_whatsapp")
async def cb_customize_whatsapp(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    has_wa = bool(user and user.get("whatsapp_btn"))
    text = (
        "💬 <b>زر محادثة واتساب المباشر (Click-to-Chat)</b>\n\n"
        "زر بارز ومميز في صفحتك ينقل الزائر فوراً لمحادثتك على واتساب مع رسالة ترحيبية جاهزة يرسلها بنقرة واحدة! 🚀\n\n"
    )
    if has_wa:
        text += "• الحالة: <b>مفعّل في صفحتك ✅</b>\n"
    else:
        text += "• الحالة: <i>غير مفعّل</i>\n"
    await cq.message.edit_text(text, reply_markup=whatsapp_btn_kb(has_wa))
    await cq.answer()


@router.callback_query(F.data == "set_wa_btn")
async def cb_set_wa_btn(cq: CallbackQuery, state: FSMContext):
    await state.set_state(CustomizationStates.waiting_wa_phone)
    await cq.message.edit_text(
        "💬 <b>إعداد زر محادثة واتساب</b>\n\n"
        "أرسل <b>رقم هاتفك مع رمز الدولة</b> (مثال: <code>9647700000000</code> أو <code>966500000000</code> بدون علامة + وبدون مسافات):\n\n"
        "أرسل /cancel للإلغاء.",
        reply_markup=None
    )
    await cq.answer()


@router.message(CustomizationStates.waiting_wa_phone)
async def do_set_wa_phone(message: Message, state: FSMContext):
    phone = re.sub(r"[^\d]", "", message.text or "")
    if len(phone) < 8 or len(phone) > 15:
        await message.answer("⚠️ رقم غير صالح. يرجى كتابة الرقم مع رمز الدولة (مثال: 9647701234567).")
        return
    await state.update_data(wa_phone=phone)
    await state.set_state(CustomizationStates.waiting_wa_msg)
    await message.answer(
        "✍️ أرسل الآن <b>الرسالة الجاهزة</b> التي تريد أن تظهر للزائر في حقل الكتابة عند فتح واتساب:\n"
        "(مثال: <i>مرحباً، أود الاستفسار عن خدماتك</i> أو <i>السلام عليكم، كيف حالك؟</i>):"
    )


@router.message(CustomizationStates.waiting_wa_msg)
async def do_set_wa_msg(message: Message, state: FSMContext):
    msg = (message.text or "").strip()[:200]
    data = await state.get_data()
    phone = data.get("wa_phone")
    import json
    wa_data = json.dumps({"phone": phone, "msg": msg})
    await db.update_whatsapp_btn(message.from_user.id, wa_data)
    await state.clear()
    await message.answer(
        f"✅ <b>تم تفعيل زر واتساب بنجاح!</b>\n\n• الرقم: <code>{phone}</code>\n• الرسالة الجاهزة: \"{msg}\"\n\nسيظهر زر المحادثة في صفحتك فوراً!",
        reply_markup=main_menu_kb(True)
    )


@router.callback_query(F.data == "delete_wa_btn")
async def cb_delete_wa_btn(cq: CallbackQuery):
    await db.update_whatsapp_btn(cq.from_user.id, None)
    await cq.message.edit_text("🗑 تم حذف زر واتساب من صفحتك.", reply_markup=whatsapp_btn_kb(False))
    await cq.answer("تم الحذف")


# ─────────────────────────── مراجعة وقبول تقييمات الزوار ───────────────────────────

@router.callback_query(F.data.startswith("approve_rev:"))
async def cb_approve_rev(cq: CallbackQuery):
    rev_id = int(cq.data.split(":")[1])
    await db.approve_review(rev_id, True)
    await cq.message.edit_text(
        cq.message.text + "\n\n✅ <b>تمت الموافقة على التقييم بنجاح وسيظهر في صفحتك الآن! ⭐</b>",
        reply_markup=None
    )
    await cq.answer("تمت الموافقة بنجاح!")


@router.callback_query(F.data.startswith("delete_rev:"))
async def cb_delete_rev(cq: CallbackQuery):
    rev_id = int(cq.data.split(":")[1])
    await db.delete_review(rev_id)
    await cq.message.edit_text(
        cq.message.text + "\n\n🗑 <b>تم حذف هذا التقييم ولن يظهر في صفحتك.</b>",
        reply_markup=None
    )
    await cq.answer("تم حذف التقييم")


# ─────────────────────────── قسم التعليقات والتقييمات ───────────────────────────

@router.message(F.text.in_({"💬 التعليقات والتقييمات", "💬 إدارة التعليقات", "⭐ التقييمات والآراء", "التعليقات والتقييمات"}))
@router.message(Command("reviews"))
async def show_reviews_manager_cmd(message: Message):
    if await check_vip_expired_blocking(message.from_user.id):
        await message.answer(EXPIRED_VIP_BLOCK_MSG)
        return
    await _render_reviews_manager(message, message.from_user.id)


@router.callback_query(F.data == "reviews_list")
@router.callback_query(F.data == "reviews_refresh")
async def cb_reviews_list(cq: CallbackQuery):
    await _render_reviews_manager(cq.message, cq.from_user.id, edit=True)
    await cq.answer()


async def _render_reviews_manager(message: Message, user_id: int, edit: bool = False):
    reviews = await db.get_reviews(user_id, approved_only=False)
    approved_count = sum(1 for r in reviews if r.get("is_approved"))
    pending_count = len(reviews) - approved_count
    
    avg_score = 0.0
    if reviews:
        avg_score = sum(r.get("rating", 5) for r in reviews) / len(reviews)
    
    user = await db.get_user(user_id)
    show_reviews = user.get("show_reviews") if (user and user.get("show_reviews") is not None) else 1
    show_reviews_status = "🟢 مفعل ويظهر للزوار" if show_reviews else "🔴 معطل ومخفي بالكامل"
    
    text = (
        "💬 <b>قسم التعليقات والتقييمات (Reviews & Testimonials)</b>\n\n"
        f"• حالة القسم بالصفحة: <b>{show_reviews_status}</b>\n"
        f"• إجمالي التقييمات: <b>{len(reviews)}</b>\n"
        f"• التقييمات المعتمدة الظاهرة بالصفحة: <b>{approved_count} ✅</b>\n"
        f"• التقييمات قيد المراجعة (المخفية): <b>{pending_count} ⏳</b>\n"
        f"• متوسط التقييم العام: <b>⭐ {avg_score:.1f} / 5.0</b>\n\n"
    )
    if not reviews:
        text += "<i>لم تتلقى أي تعليقات أو تقييمات حتى الآن. سيظهر هنا أي تقييم يتركه زوار صفحتك!</i>"
    else:
        text += "اضغط على أي تقييم أدناه لعرض تفاصيله الكاملة، والموافقة عليه أو إخفائه أو حذفه 👇"
        
    kb = reviews_manager_kb(reviews, show_reviews=bool(show_reviews))
    if edit:
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "toggle_reviews_section")
async def cb_toggle_reviews_section(cq: CallbackQuery):
    user_id = cq.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return
    current = user.get("show_reviews") if user.get("show_reviews") is not None else 1
    new_val = 0 if current else 1
    await db.update_show_reviews(user_id, new_val)
    await cq.answer(f"✅ تم {'تفعيل' if new_val else 'تعطيل'} قسم التعليقات بنجاح!")
    await _render_reviews_manager(cq.message, user_id, edit=True)


@router.callback_query(F.data.startswith("rev_view:"))
async def cb_rev_view(cq: CallbackQuery):
    rev_id = int(cq.data.split(":")[1])
    rev = await db.get_review(rev_id)
    if not rev:
        await cq.answer("هذا التقييم لم يعد موجوداً.", show_alert=True)
        return
    status = "معتمد ويظهر في صفحتك ✅" if rev.get("is_approved") else "قيد الانتظار (مخفي من الصفحة) ⏳"
    stars = "⭐" * (rev.get("rating") or 5)
    created = str(rev.get("created_at") or "")[:16]
    text = (
        f"⭐ <b>تفاصيل التقييم #{rev_id}</b>\n\n"
        f"👤 صاحب التقييم: <b>{rev.get('reviewer_name') or 'زائر'}</b>\n"
        f"⭐️ التقييم: <b>{stars} ({rev.get('rating')}/5)</b>\n"
        f"📅 التاريخ: <code>{created}</code>\n"
        f"📌 الحالة: <b>{status}</b>\n\n"
        f"💬 نص التعليق:\n<i>\"{rev.get('comment')}\"</i>\n\n"
        "اختر الإجراء المناسب أدناه:"
    )
    await cq.message.edit_text(text, reply_markup=review_detail_kb(rev))
    await cq.answer()


@router.callback_query(F.data.startswith("rev_approve:"))
async def cb_rev_approve(cq: CallbackQuery):
    rev_id = int(cq.data.split(":")[1])
    await db.approve_review(rev_id, True)
    rev = await db.get_review(rev_id)
    if rev:
        await cq.message.edit_reply_markup(reply_markup=review_detail_kb(rev))
    await cq.answer("✅ تم قبول التقييم وسيظهر في صفحتك فوراً!", show_alert=True)


@router.callback_query(F.data.startswith("rev_unapprove:"))
async def cb_rev_unapprove(cq: CallbackQuery):
    rev_id = int(cq.data.split(":")[1])
    await db.approve_review(rev_id, False)
    rev = await db.get_review(rev_id)
    if rev:
        await cq.message.edit_reply_markup(reply_markup=review_detail_kb(rev))
    await cq.answer("⏸ تم إخفاء التقييم من صفحتك.", show_alert=True)


@router.callback_query(F.data.startswith("rev_delete:"))
async def cb_rev_delete_manager(cq: CallbackQuery):
    rev_id = int(cq.data.split(":")[1])
    await db.delete_review(rev_id)
    await cq.answer("🗑 تم حذف التقييم نهائياً.", show_alert=True)
    await _render_reviews_manager(cq.message, cq.from_user.id, edit=True)


# ─────────────────────────── شريط أيقونات التواصل الاجتماعي ───────────────────────────

@router.callback_query(F.data == "customize_socials")
async def cb_customize_socials(cq: CallbackQuery):
    user = await db.get_user(cq.from_user.id)
    soc_raw = user.get("social_links") if user else None
    import json
    try:
        soc_dict = json.loads(soc_raw) if isinstance(soc_raw, str) else (soc_raw or {})
    except Exception:
        soc_dict = {}
    
    text = (
        "🌐 <b>شريط أيقونات التواصل الاجتماعي (Social Icons Bar)</b> 📲\n\n"
        "أيقونات دائرية أنيقة ومباشرة تظهر تحت النبذة مباشرة لأهم منصاتك وتسمح للزوار بالوصول إليك فوراً!\n\n"
        "اختر المنصة التي تريد ربطها أو تعديلها أدناه 👇"
    )
    await cq.message.edit_text(text, reply_markup=social_icons_menu_kb(soc_dict))
    await cq.answer()


@router.callback_query(F.data.startswith("soc_set:"))
async def cb_soc_set(cq: CallbackQuery, state: FSMContext):
    platform = cq.data.split(":", 1)[1]
    await state.set_state(CustomizationStates.waiting_social_url)
    await state.update_data(soc_platform=platform)
    
    platform_names = {
        "instagram": "انستغرام (Instagram)",
        "tiktok": "تيك توك (TikTok)",
        "youtube": "يوتيوب (YouTube)",
        "x": "منصة X (Twitter)",
        "snapchat": "سناب شات (Snapchat)",
        "telegram": "تليجرام (Telegram)",
        "facebook": "فيسبوك (Facebook)",
        "whatsapp": "واتساب (WhatsApp)",
        "linkedin": "لينكد إن (LinkedIn)",
        "discord": "ديسكورد (Discord)",
    }
    name = platform_names.get(platform, platform)
    
    await cq.message.edit_text(
        f"🌐 <b>ربط منصة {name}</b>\n\n"
        f"أرسل الآن <b>رابط حسابك</b> أو <b>اليوزرنيم</b> الخاص بك على {name}:\n"
        f"(مثال: <code>https://instagram.com/myusername</code> أو <code>@myusername</code>)\n\n"
        f"💡 لحذف هذه المنصة من الشريط أرسل كلمة: <code>حذف</code>\n"
        f"أرسل /cancel للإلغاء.",
        reply_markup=None
    )
    await cq.answer()


@router.message(CustomizationStates.waiting_social_url)
async def do_set_social_url(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    data = await state.get_data()
    platform = data.get("soc_platform")
    if not platform:
        await state.clear()
        return

    import json
    user = await db.get_user(message.from_user.id)
    soc_raw = user.get("social_links") if user else None
    try:
        soc_dict = json.loads(soc_raw) if isinstance(soc_raw, str) else (soc_raw or {})
    except Exception:
        soc_dict = {}

    if text in ["حذف", "delete", "remove", "مسح"]:
        soc_dict.pop(platform, None)
        await db.update_social_links(message.from_user.id, soc_dict)
        await state.clear()
        is_vip = await db.is_user_vip(message.from_user.id)
        await message.answer(f"🗑 تم حذف منصة <b>{platform}</b> من شريط التواصل بنجاح!", reply_markup=main_menu_kb(is_vip))
        return

    # Normalize url/username
    if platform == "telegram" and not text.startswith("http"):
        url = f"https://t.me/{text.lstrip('@')}"
    elif platform == "instagram" and not text.startswith("http"):
        url = f"https://instagram.com/{text.lstrip('@')}"
    elif platform == "tiktok" and not text.startswith("http"):
        url = f"https://tiktok.com/@{text.lstrip('@')}"
    elif platform == "x" and not text.startswith("http"):
        url = f"https://x.com/{text.lstrip('@')}"
    elif platform == "snapchat" and not text.startswith("http"):
        url = f"https://snapchat.com/add/{text.lstrip('@')}"
    elif platform == "youtube" and not text.startswith("http"):
        url = f"https://youtube.com/@{text.lstrip('@')}"
    elif platform == "whatsapp" and not text.startswith("http"):
        digits = re.sub(r"[^\d]", "", text)
        url = f"https://wa.me/{digits}"
    else:
        url = normalize_url(text) or text

    soc_dict[platform] = url
    await db.update_social_links(message.from_user.id, soc_dict)
    await state.clear()
    is_vip = await db.is_user_vip(message.from_user.id)
    await message.answer(
        f"✅ <b>تم ربط منصة {platform} بنجاح!</b>\n\n"
        f"🔗 الرابط: <code>{url}</code>\n"
        f"ستظهر الأيقونة فوراً تحت النبذة في صفحتك 🚀",
        reply_markup=main_menu_kb(is_vip)
    )


@router.callback_query(F.data == "soc_delete_all")
async def cb_soc_delete_all(cq: CallbackQuery):
    await db.update_social_links(cq.from_user.id, {})
    await cq.message.edit_text("🗑 تم مسح جميع أيقونات التواصل من صفحتك بنجاح.", reply_markup=social_icons_menu_kb({}))
    await cq.answer("تم المسح")


# ─────────────────────────── مدير الروابط (تعديل فردي ومتقدم) ───────────────────────────

async def _show_links_manager(message: Message, state: FSMContext, user_id: int = None, text_prefix: str = ""):
    await state.clear()
    uid = user_id or message.from_user.id
    links = await db.get_user_links(uid)
    is_vip = await db.is_user_vip(uid)
    text = text_prefix + (
        "🔗 <b>مدير روابط الصفحة الشخصية والتخصيص</b>\n\n"
        "يمكنك هنا إضافة روابط غير محدودة 🚀 والضغط على أي رابط لتخصيص:\n"
        "• 📝 <b>وصف فرعي (Subtitle)</b> مثل: <i>@username • 27K followers</i>\n"
        "• 🏷 <b>قسم وتصنيف فاصل</b> مثل: <i>دوراتي وكورساتي</i>\n"
        "• 🖼 <b>صورة مصغرة أو غلاف بنر عريض</b> للمنتج أو الدورة\n"
        "• ✨ <b>توهج ذهبي نبضي (Glow)</b> للرابط الأكثر أهمية!\n\n"
        f"عدد الروابط الحالية: <b>{len(links)}</b>"
    )
    
    await message.answer(text, reply_markup=manage_links_kb(links, is_vip))


@router.message(F.text == "🔗 تعديل الروابط")
async def cmd_manage_links(message: Message, state: FSMContext):
    if await check_vip_expired_blocking(message.from_user.id):
        await message.answer(EXPIRED_VIP_BLOCK_MSG)
        return
        
    await _show_links_manager(message, state)


@router.callback_query(F.data == "ln_back_manager")
async def cb_back_manager(cq: CallbackQuery, state: FSMContext):
    await cq.message.delete()
    await _show_links_manager(cq.message, state, user_id=cq.from_user.id)
    await cq.answer()


@router.callback_query(F.data == "ln_back_main")
async def cb_back_main(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    is_vip = await db.is_user_vip(cq.from_user.id)
    await cq.message.answer("🎛️ القائمة الرئيسية:", reply_markup=main_menu_kb(is_vip))
    await cq.message.delete()
    await cq.answer()


@router.callback_query(F.data.startswith("ln_edit:"))
async def cb_ln_edit(cq: CallbackQuery):
    link_id = int(cq.data.split(":")[1])
    link = await db.get_link_by_id(link_id) or await db.get_link(link_id)
    if not link:
        await cq.answer("الرابط غير موجود.", show_alert=True)
        return
    
    sub = link.get("subtitle") or "<i>لا يوجد</i>"
    sec = link.get("section_header") or "<i>لا يوجد</i>"
    thumb = "بنر عريض 🖼" if link.get("is_banner") else ("صورة مصغرة 🖼" if link.get("thumbnail_url") else "<i>لا يوجد</i>")
    glow = "مفعّل بتوهج ذهبي ✨" if link.get("is_featured") else "معطل"
    
    text = (
        f"📝 <b>تخصيص وتعديل الرابط #{link_id}</b>\n\n"
        f"• العنوان: <b>{link['title']}</b>\n"
        f"• الرابط: <code>{link['url']}</code>\n"
        f"• الوصف الفرعي: <b>{sub}</b>\n"
        f"• القسم الفاصل: <b>{sec}</b>\n"
        f"• الصورة / الغلاف: <b>{thumb}</b>\n"
        f"• التوهج النبضي: <b>{glow}</b>\n\n"
        "اختر ما تريد تعديله من الخيارات أدناه 👇"
    )
    await cq.message.edit_text(text, reply_markup=edit_link_options_kb(link_id, link))
    await cq.answer()


@router.callback_query(F.data.startswith("le_sub:"))
async def cb_le_sub(cq: CallbackQuery, state: FSMContext):
    link_id = int(cq.data.split(":")[1])
    await state.set_state(LinkEditStates.waiting_link_subtitle)
    await state.update_data(edit_link_id=link_id)
    await cq.message.delete()
    await cq.message.answer(
        "📝 <b>إضافة / تعديل الوصف الفرعي للرابط</b>\n\n"
        "أرسل النص التوضيحي الصغير الذي تريده أن يظهر تحت عنوان الرابط:\n"
        "(مثال: <code>@k41zen_1 • 27.1K followers</code> أو <code>خصم 50% لفترة محدودة 🔥</code>)\n\n"
        "💡 لحذف الوصف الفرعي أرسل كلمة: <code>حذف</code>",
        reply_markup=fsm_cancel_edit_kb()
    )
    await cq.answer()


@router.message(LinkEditStates.waiting_link_subtitle, F.text)
async def fsm_receive_link_subtitle(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    link_id = data.get("edit_link_id")
    if text == "🔙 إلغاء التعديل":
        await state.clear()
        await _show_links_manager(message, state)
        return

    val = None if text in ["حذف", "delete", "none", "مسح"] else text[:100]
    link = await db.get_link_by_id(link_id) or await db.get_link(link_id)
    if link:
        await db.update_link_extra(
            link_id,
            subtitle=val,
            thumbnail_url=link.get("thumbnail_url"),
            is_banner=link.get("is_banner") or 0,
            section_header=link.get("section_header"),
            is_featured=link.get("is_featured") or 0,
        )
    await state.clear()
    is_vip = await db.is_user_vip(message.from_user.id)
    await message.answer("✅ تم تحديث الوصف الفرعي للرابط بنجاح!", reply_markup=main_menu_kb(is_vip))
    await _show_links_manager(message, state)


@router.callback_query(F.data.startswith("le_sec:"))
async def cb_le_sec(cq: CallbackQuery, state: FSMContext):
    link_id = int(cq.data.split(":")[1])
    await state.set_state(LinkEditStates.waiting_link_section)
    await state.update_data(edit_link_id=link_id)
    await cq.message.delete()
    await cq.message.answer(
        "🏷 <b>إضافة / تعديل القسم الفاصل (Section Header)</b>\n\n"
        "أرسل عنوان التصنيف أو القسم الذي يسبق هذا الرابط:\n"
        "(مثال: <code>🎓 دوراتي وكورساتي</code> أو <code>📦 منتجاتي المفضلة</code> أو <code>📱 حساباتي في التواصل</code>)\n\n"
        "💡 لحذف القسم الفاصل أرسل كلمة: <code>حذف</code>",
        reply_markup=fsm_cancel_edit_kb()
    )
    await cq.answer()


@router.message(LinkEditStates.waiting_link_section, F.text)
async def fsm_receive_link_section(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    link_id = data.get("edit_link_id")
    if text == "🔙 إلغاء التعديل":
        await state.clear()
        await _show_links_manager(message, state)
        return

    val = None if text in ["حذف", "delete", "none", "مسح"] else text[:60]
    link = await db.get_link_by_id(link_id) or await db.get_link(link_id)
    if link:
        await db.update_link_extra(
            link_id,
            subtitle=link.get("subtitle"),
            thumbnail_url=link.get("thumbnail_url"),
            is_banner=link.get("is_banner") or 0,
            section_header=val,
            is_featured=link.get("is_featured") or 0,
        )
    await state.clear()
    is_vip = await db.is_user_vip(message.from_user.id)
    await message.answer("✅ تم تحديث القسم الفاصل بنجاح!", reply_markup=main_menu_kb(is_vip))
    await _show_links_manager(message, state)


@router.callback_query(F.data.startswith("le_thumb:"))
async def cb_le_thumb(cq: CallbackQuery, state: FSMContext):
    link_id = int(cq.data.split(":")[1])
    await state.set_state(LinkEditStates.waiting_link_thumbnail)
    await state.update_data(edit_link_id=link_id)
    await cq.message.delete()
    await cq.message.answer(
        "🖼 <b>إضافة صورة مصغرة أو غلاف للرابط</b>\n\n"
        "أرسل <b>رابط الصورة المباشر (Direct Image URL)</b>:\n"
        "(مثال: <code>https://i.imgur.com/example.png</code> أو أي رابط صورة ينتهي بـ .jpg/.png/.webp)\n\n"
        "💡 لحذف الصورة من الرابط أرسل كلمة: <code>حذف</code>",
        reply_markup=fsm_cancel_edit_kb()
    )
    await cq.answer()


@router.message(LinkEditStates.waiting_link_thumbnail, F.text)
async def fsm_receive_link_thumbnail(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    link_id = data.get("edit_link_id")
    if text == "🔙 إلغاء التعديل":
        await state.clear()
        await _show_links_manager(message, state)
        return

    val = None if text in ["حذف", "delete", "none", "مسح"] else text
    link = await db.get_link_by_id(link_id) or await db.get_link(link_id)
    if link:
        await db.update_link_extra(
            link_id,
            subtitle=link.get("subtitle"),
            thumbnail_url=val,
            is_banner=link.get("is_banner") or 0,
            section_header=link.get("section_header"),
            is_featured=link.get("is_featured") or 0,
        )
    await state.clear()
    is_vip = await db.is_user_vip(message.from_user.id)
    await message.answer("✅ تم تحديث صورة الرابط بنجاح!", reply_markup=main_menu_kb(is_vip))
    await _show_links_manager(message, state)


@router.callback_query(F.data.startswith("le_toggle_banner:"))
async def cb_le_toggle_banner(cq: CallbackQuery):
    link_id = int(cq.data.split(":")[1])
    link = await db.get_link_by_id(link_id) or await db.get_link(link_id)
    if link:
        new_banner = 0 if link.get("is_banner") else 1
        await db.update_link_extra(
            link_id,
            subtitle=link.get("subtitle"),
            thumbnail_url=link.get("thumbnail_url"),
            is_banner=new_banner,
            section_header=link.get("section_header"),
            is_featured=link.get("is_featured") or 0,
        )
        updated_link = await db.get_link_by_id(link_id)
        msg_text = "🖼 تم التبديل إلى نمط: بنر عريض!" if new_banner else "🖼 تم التبديل إلى نمط: صورة مصغرة دائرية/مربعة!"
        await cq.answer(msg_text, show_alert=True)
        await cq.message.edit_reply_markup(reply_markup=edit_link_options_kb(link_id, updated_link))


@router.callback_query(F.data.startswith("le_toggle_feat:"))
async def cb_le_toggle_feat(cq: CallbackQuery):
    link_id = int(cq.data.split(":")[1])
    link = await db.get_link_by_id(link_id) or await db.get_link(link_id)
    if link:
        new_feat = 0 if link.get("is_featured") else 1
        await db.update_link_extra(
            link_id,
            subtitle=link.get("subtitle"),
            thumbnail_url=link.get("thumbnail_url"),
            is_banner=link.get("is_banner") or 0,
            section_header=link.get("section_header"),
            is_featured=new_feat,
        )
        updated_link = await db.get_link_by_id(link_id)
        msg_text = "✨ تم تفعيل التوهج الذهبي النبضي للرابط!" if new_feat else "⭐ تم إلغاء التوهج."
        await cq.answer(msg_text, show_alert=True)
        await cq.message.edit_reply_markup(reply_markup=edit_link_options_kb(link_id, updated_link))


@router.callback_query(F.data.startswith("ln_del:"))
async def cb_ln_del(cq: CallbackQuery, state: FSMContext):
    link_id = int(cq.data.split(":")[1])
    link = await db.get_link(link_id)
    if link:
        await db.delete_link(link_id)
        await cq.answer("✅ تم حذف الرابط بنجاح!", show_alert=True)
    else:
        await cq.answer("الرابط غير موجود.", show_alert=True)
    
    await cq.message.delete()
    await _show_links_manager(cq.message, state, user_id=cq.from_user.id)


@router.callback_query(F.data == "ln_add_new")
async def cb_ln_add_new(cq: CallbackQuery, state: FSMContext):
    await state.set_state(LinkEditStates.waiting_new_title)
    await cq.message.delete()
    await cq.message.answer(
        "➕ <b>إضافة رابط جديد</b>\n\n"
        "أرسل الآن <b>اسم الرابط</b> (مثال: <code>قناتي على تليجرام</code>):\n\n"
        "💡 أو أرسل الاسم والرابط معاً تفصل بينهما علامة <b>|</b>:\n"
        "<code>قناتي | t.me/mychannel</code>",
        reply_markup=fsm_cancel_edit_kb()
    )
    await cq.answer()


@router.callback_query(F.data.startswith("le_title:"))
async def cb_le_title(cq: CallbackQuery, state: FSMContext):
    link_id = int(cq.data.split(":")[1])
    await state.set_state(LinkEditStates.waiting_edit_title)
    await state.update_data(edit_link_id=link_id)
    await cq.message.delete()
    await cq.message.answer(
        "✏️ <b>تعديل اسم الرابط</b>\n\n"
        "أرسل الآن <b>الاسم الجديد</b> للرابط:",
        reply_markup=fsm_cancel_edit_kb()
    )
    await cq.answer()


@router.callback_query(F.data.startswith("le_url:"))
async def cb_le_url(cq: CallbackQuery, state: FSMContext):
    link_id = int(cq.data.split(":")[1])
    await state.set_state(LinkEditStates.waiting_edit_url)
    await state.update_data(edit_link_id=link_id)
    await cq.message.delete()
    await cq.message.answer(
        "🌐 <b>تعديل رابط الـ URL</b>\n\n"
        "أرسل الآن <b>الرابط الجديد</b> للـ URL:",
        reply_markup=fsm_cancel_edit_kb()
    )
    await cq.answer()


# ─────────────────── رسائل FSM تعديل الروابط ───────────────────

@router.message(LinkEditStates.waiting_edit_title, F.text)
async def fsm_receive_edit_title(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    link_id = data.get("edit_link_id")
    
    if text == "🔙 إلغاء التعديل":
        await state.clear()
        if link_id:
            link = await db.get_link(link_id)
            if link:
                is_vip = await db.is_user_vip(message.from_user.id)
                await message.answer("🔙 تم إلغاء تعديل الاسم.", reply_markup=main_menu_kb(is_vip))
                await message.answer(
                    f"📝 <b>تعديل الرابط</b>\n\n"
                    f"الاسم الحالي: <b>{link['title']}</b>\n"
                    f"الرابط الحالي: <code>{link['url']}</code>\n\n"
                    f"اختر ما تريد تعديله:",
                    reply_markup=edit_link_options_kb(link_id)
                )
                return
        await _show_links_manager(message, state)
        return

    if len(text) < 1 or len(text) > 40:
        await message.answer("⚠️ اسم الرابط يجب أن يكون بين 1 و 40 حرف.")
        return
    
    await db.update_link_title(link_id, text)
    await state.clear()
    
    is_vip = await db.is_user_vip(message.from_user.id)
    await message.answer("✅ تم تحديث اسم الرابط بنجاح!", reply_markup=main_menu_kb(is_vip))
    
    link = await db.get_link(link_id)
    await message.answer(
        f"📝 <b>تعديل الرابط</b>\n\n"
        f"الاسم الحالي: <b>{link['title']}</b>\n"
        f"الرابط الحالي: <code>{link['url']}</code>\n\n"
        f"اختر ما تريد تعديله:",
        reply_markup=edit_link_options_kb(link_id)
    )


@router.message(LinkEditStates.waiting_edit_url, F.text)
async def fsm_receive_edit_url(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    link_id = data.get("edit_link_id")
    
    if text == "🔙 إلغاء التعديل":
        await state.clear()
        if link_id:
            link = await db.get_link(link_id)
            if link:
                is_vip = await db.is_user_vip(message.from_user.id)
                await message.answer("🔙 تم إلغاء تعديل الرابط.", reply_markup=main_menu_kb(is_vip))
                await message.answer(
                    f"📝 <b>تعديل الرابط</b>\n\n"
                    f"الاسم الحالي: <b>{link['title']}</b>\n"
                    f"الرابط الحالي: <code>{link['url']}</code>\n\n"
                    f"اختر ما تريد تعديله:",
                    reply_markup=edit_link_options_kb(link_id)
                )
                return
        await _show_links_manager(message, state)
        return

    url = normalize_url(text)
    if not url:
        await message.answer("⚠️ الرابط غير صحيح. أعد إرساله بشكل صحيح:")
        return
        
    await db.update_link_url(link_id, url)
    await state.clear()
    
    is_vip = await db.is_user_vip(message.from_user.id)
    await message.answer("✅ تم تحديث الرابط (URL) بنجاح!", reply_markup=main_menu_kb(is_vip))
    
    link = await db.get_link(link_id)
    await message.answer(
        f"📝 <b>تعديل الرابط</b>\n\n"
        f"الاسم الحالي: <b>{link['title']}</b>\n"
        f"الرابط الحالي: <code>{link['url']}</code>\n\n"
        f"اختر ما تريد تعديله:",
        reply_markup=edit_link_options_kb(link_id)
    )


@router.message(LinkEditStates.waiting_new_title, F.text)
async def fsm_receive_new_title(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "🔙 إلغاء التعديل":
        await state.clear()
        await _show_links_manager(message, state, text_prefix="🔙 تم إلغاء إضافة الرابط الجديد.\n\n")
        return

    if "|" in text:
        parts = [p.strip() for p in text.split("|", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            title, url_raw = parts
            url = normalize_url(url_raw)
            if not url:
                await message.answer("⚠️ الرابط بعد الـ | غير صحيح. أعد الإرسال.")
                return
            if len(title) > 40:
                await message.answer("⚠️ اسم الرابط يجب ألا يتجاوز 40 حرف.")
                return
            await db.add_link(message.from_user.id, title, url)
            await state.clear()
            is_vip = await db.is_user_vip(message.from_user.id)
            await message.answer("✅ تم إضافة الرابط الجديد بنجاح!", reply_markup=main_menu_kb(is_vip))
            await _show_links_manager(message, state)
            return

    if len(text) < 1 or len(text) > 40:
        await message.answer("⚠️ اسم الرابط يجب أن يكون بين 1 و 40 حرف.")
        return
        
    await state.update_data(new_link_title=text)
    await state.set_state(LinkEditStates.waiting_new_url)
    await message.answer(
        f"🌐 الآن أرسل <b>الرابط (URL)</b> الخاص بـ <b>{text}</b>:",
        reply_markup=fsm_cancel_edit_kb()
    )


@router.message(LinkEditStates.waiting_new_url, F.text)
async def fsm_receive_new_url(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "🔙 إلغاء التعديل":
        await state.clear()
        await _show_links_manager(message, state, text_prefix="🔙 تم إلغاء إضافة الرابط الجديد.\n\n")
        return

    url = normalize_url(text)
    if not url:
        await message.answer("⚠️ الرابط غير صحيح. أعد إرساله بشكل صحيح:")
        return
        
    data = await state.get_data()
    title = data.get("new_link_title", "رابط")
    
    await db.add_link(message.from_user.id, title, url)
    await state.clear()
    
    is_vip = await db.is_user_vip(message.from_user.id)
    await message.answer("✅ تم إضافة الرابط الجديد بنجاح!", reply_markup=main_menu_kb(is_vip))
    await _show_links_manager(message, state)


# ─────────────────────────────── إدارة الصفحات الفرعية (VIP Sub-Pages) ───────────────────────────────

@router.callback_query(F.data == "edit_main_page")
async def cb_edit_main_page(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(PageCreationStates.waiting_title)
    try:
        await cq.message.delete()
    except Exception:
        pass
    await cq.message.answer(
        "✏️ <b>تعديل الصفحة الرئيسية - الخطوة 1 من 3: عنوان الصفحة</b>\n\n"
        "أرسل الآن <b>عنوان صفحتك</b> (اسمك أو اسم صفحتك، من 2 إلى 60 حرف):",
        reply_markup=fsm_cancel_kb(),
    )
    await cq.answer()


@router.callback_query(F.data == "manage_sub_pages")
@router.callback_query(F.data == "back_to_pages_menu")
async def cb_manage_sub_pages(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    sub_pages = await db.list_user_sub_pages(user_id)
    text = (
        "📁 <b>إدارة صفحات الهبوط الفرعية (Sub-Pages)</b>\n\n"
        f"عدد صفحاتك الفرعية الحالية: <b>{len(sub_pages)}</b>\n\n"
        "اختر أحد خيارات الصفحات لإدارتها، أو أنشئ صفحة جديدة:"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows = []
    for sp in sub_pages:
        slug = sp["slug"]
        title = sp["page_title"] or "صفحة فرعية"
        rows.append([InlineKeyboardButton(text=f"📄 {title} ({slug})", callback_data=f"manage_sp:{slug}")])
        
    rows.append([InlineKeyboardButton(text="➕ إنشاء صفحة فرعية جديدة", callback_data="create_sub_page")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع للقائمة الرئيسية", callback_data="customize_back")])
    
    await cq.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")
    await cq.answer()


@router.callback_query(F.data == "create_sub_page")
async def cb_create_sub_page(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(SubPageStates.waiting_slug)
    try:
        await cq.message.delete()
    except Exception:
        pass
    await cq.message.answer(
        "📝 <b>إنشاء صفحة فرعية جديدة - الخطوة 1 من 3</b>\n\n"
        "أرسل الآن <b>المعرّف الإنجليزي القصير (Slug)</b> للصفحة الجديدة (سيُستخدم في الرابط مثل: mypage):\n"
        "⚠️ يجب أن يحتوي على حروف إنجليزية وأرقام فقط وبدون مسافات.",
        reply_markup=fsm_cancel_kb(),
    )
    await cq.answer()


@router.message(SubPageStates.waiting_slug)
async def do_create_sub_page_slug(message: Message, state: FSMContext):
    slug = (message.text or "").strip().lower()
    if not slug or not re.match(r"^[a-z0-9_-]+$", slug):
        await message.answer("⚠️ معرّف غير صالح. يجب أن يحتوي على حروف إنجليزية صغيرة، أرقام، أو شرطات فقط.")
        return
    if slug.isdigit():
        await message.answer("⚠️ عذراً، لا يمكن للمعرّف أن يكون أرقاماً فقط.")
        return
        
    existing = await db.get_sub_page(slug)
    if existing:
        await message.answer("⚠️ هذا المعرّف محجوز بالفعل! يرجى اختيار معرّف آخر:")
        return
        
    await state.update_data(sp_slug=slug)
    await state.set_state(SubPageStates.waiting_title)
    await message.answer(
        "✏️ <b>الخطوة 2 من 3: عنوان الصفحة</b>\n\n"
        "أرسل الآن <b>عنوان صفحتك الفرعية</b> (مثال: متجري الخاص أو أعمالي الفنية، من 2 إلى 60 حرف):",
        reply_markup=fsm_cancel_kb(),
    )


@router.message(SubPageStates.waiting_title)
async def do_create_sub_page_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    if len(title) < 2 or len(title) > 60:
        await message.answer("⚠️ عنوان الصفحة يجب أن يكون بين 2 و 60 حرفاً:")
        return
        
    await state.update_data(sp_title=title)
    await state.set_state(SubPageStates.waiting_bio)
    await message.answer(
        "✏️ <b>الخطوة 3 من 3: الوصف/النبذة التعريفية</b>\n\n"
        "أرسل الآن <b>الوصف الصغير</b> لصفحتك الفرعية (نبذة تظهر تحت العنوان):\n"
        "أو أرسل /skip لتجاوز الوصف.",
        reply_markup=fsm_skip_bio_kb(),
    )


@router.message(SubPageStates.waiting_bio)
async def do_create_sub_page_bio(message: Message, state: FSMContext):
    bio = (message.text or "").strip()
    if bio == "/skip" or bio == "⏭️ تجاوز الخطوة":
        bio = ""
        
    data = await state.get_data()
    slug = data.get("sp_slug")
    title = data.get("sp_title")
    user_id = message.from_user.id
    
    success = await db.create_sub_page(user_id, slug, title)
    if success:
        if bio:
            await db.update_sub_page_fields(user_id, slug, {"page_bio": bio})
        
        await state.clear()
        share_url = f"{settings.WEBAPP_BASE_URL}/api/page/{slug}"
        
        text = (
            f"🎉 <b>مبروك! تم إنشاء صفحتك الفرعية بنجاح!</b>\n\n"
            f"📄 العنوان: <b>{title}</b>\n"
            f"🔗 المعرّف: <code>{slug}</code>\n\n"
            f"🌐 رابط الصفحة الخاص بها:\n<code>{share_url}</code>"
        )
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ إدارة الروابط وتصميم الصفحة", callback_data=f"manage_sp:{slug}")],
            [InlineKeyboardButton(text="📁 العودة لقائمة الصفحات الفرعية", callback_data="manage_sub_pages")],
        ])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer("⚠️ حدث خطأ غير متوقع أثناء حفظ الصفحة. يرجى المحاولة لاحقاً.", reply_markup=main_menu_kb(True))
        await state.clear()


@router.callback_query(F.data.startswith("manage_sp:"))
async def cb_manage_sp(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    slug = cq.data.split(":")[1]
    sp = await db.get_sub_page(slug)
    if not sp:
        await cq.answer("هذه الصفحة غير موجودة.", show_alert=True)
        return
        
    user_id = cq.from_user.id
    links = await db.get_user_links(user_id, page_slug=slug)
    share_url = f"{settings.WEBAPP_BASE_URL}/api/page/{slug}"
    
    text = (
        f"📄 <b>إدارة الصفحة الفرعية: {sp['page_title']} ({slug})</b>\n\n"
        f"👁️ النبذة: <i>\"{sp['page_bio'] or 'لا يوجد وصف تعريفى'}\"</i>\n"
        f"🔗 عدد الروابط بالصفحة: <b>{len(links)}</b>\n\n"
        f"🌐 رابط الصفحة:\n<code>{share_url}</code>"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة رابط جديد لهذه الصفحة", callback_data=f"sp_addlink:{slug}")],
        [InlineKeyboardButton(text="🗑 حذف هذه الصفحة بالكامل", callback_data=f"sp_delete:{slug}")],
        [InlineKeyboardButton(text="📁 العودة لقائمة الصفحات الفرعية", callback_data="manage_sub_pages")],
    ])
    
    await cq.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cq.answer()


@router.callback_query(F.data.startswith("sp_addlink:"))
async def cb_sp_addlink(cq: CallbackQuery, state: FSMContext):
    slug = cq.data.split(":")[1]
    await state.clear()
    await state.update_data(sp_slug=slug)
    await state.set_state(SubPageStates.waiting_sp_new_link_title)
    
    try:
        await cq.message.delete()
    except Exception:
        pass
    await cq.message.answer(
        f"➕ <b>إضافة رابط لصفحة ({slug})</b>\n\n"
        "أرسل اسم الرابط الجديد (مثال: <code>قناتي الثانية</code>):",
        reply_markup=fsm_cancel_kb()
    )
    await cq.answer()


@router.message(SubPageStates.waiting_sp_new_link_title)
async def do_sp_add_link_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    if not title or len(title) > 40:
        await message.answer("⚠️ اسم الرابط يجب أن يكون بين 1 و 40 حرفاً:")
        return
        
    await state.update_data(sp_link_title=title)
    await state.set_state(SubPageStates.waiting_sp_new_link_url)
    await message.answer(
        f"🌐 أرسل الآن رابط الـ URL لـ <b>({title})</b>:"
    )


@router.message(SubPageStates.waiting_sp_new_link_url)
async def do_sp_add_link_url(message: Message, state: FSMContext):
    text = message.text.strip()
    url = normalize_url(text)
    if not url:
        await message.answer("⚠️ الرابط غير صحيح. أعد إرساله بشكل صحيح:")
        return
        
    data = await state.get_data()
    slug = data.get("sp_slug")
    title = data.get("sp_link_title")
    user_id = message.from_user.id
    
    await db.add_link(user_id, title, url, page_slug=slug)
    await state.clear()
    
    is_vip = await db.is_user_vip(user_id)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ العودة لإدارة الصفحة الفرعية", callback_data=f"manage_sp:{slug}")],
        [InlineKeyboardButton(text="📁 قائمة جميع الصفحات الفرعية", callback_data="manage_sub_pages")],
    ])
    await message.answer("✅ تم إضافة الرابط الجديد بنجاح!", reply_markup=main_menu_kb(is_vip))
    await message.answer(f"ماذا تريد أن تفعل الآن بالصفحة الفرعية ({slug})؟", reply_markup=kb)


@router.callback_query(F.data.startswith("sp_delete:"))
async def cb_sp_delete(cq: CallbackQuery):
    slug = cq.data.split(":")[1]
    user_id = cq.from_user.id
    
    deleted = await db.delete_sub_page(user_id, slug)
    if deleted:
        await cq.answer("✅ تم حذف الصفحة الفرعية والروابط والتقييمات التابعة لها بنجاح!", show_alert=True)
    else:
        await cq.answer("⚠️ لم نتمكن من حذف الصفحة الفرعية.", show_alert=True)
        
    sub_pages = await db.list_user_sub_pages(user_id)
    text = (
        "📁 <b>إدارة صفحات الهبوط الفرعية (Sub-Pages)</b>\n\n"
        f"عدد صفحاتك الفرعية الحالية: <b>{len(sub_pages)}</b>\n\n"
        "اختر أحد خيارات الصفحات لإدارتها، أو أنشئ صفحة جديدة:"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows = []
    for sp in sub_pages:
        sp_slug = sp["slug"]
        title = sp["page_title"] or "صفحة فرعية"
        rows.append([InlineKeyboardButton(text=f"📄 {title} ({sp_slug})", callback_data=f"manage_sp:{sp_slug}")])
        
    rows.append([InlineKeyboardButton(text="➕ إنشاء صفحة فرعية جديدة", callback_data="create_sub_page")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع للقائمة الرئيسية", callback_data="customize_back")])
    
    await cq.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")



