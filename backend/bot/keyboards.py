"""
لوحات المفاتيح (Keyboards)
"""
from typing import Optional
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, ReplyKeyboardRemove,
)
from bot.config import settings


# قائمة القوالب: (id, name, is_premium)
THEMES = [
    (1, "🌌 Dark Cyber", False),
    (2, "💖 Neon Glow", False),
    (3, "🪟 Glassmorphism", False),
    (4, "🌊 Ocean Wave", False),
    (5, "🔥 Sunset Vibes", False),
    (6, "🌿 Forest Green", False),
    (7, "👑 Royal Gold", False),
    (8, "🎮 Cyberpunk 2077", False),
    (9, "❄️ Crystal Ice", False),
    (10, "💜 Cosmic Nebula", False),
    (11, "🖤 Obsidian Gold", False),
    (12, "🍃 Emerald Aurora", False),
    (13, "☕ Vintage Espresso", False),
    (15, "👾 Cyber Synth", False),
    (16, "📦 Bento 3D Grid", False),
    (17, "🎬 Studio Minimalist", False),
    (18, "🗞️ Editorial Luxury", False),
    (19, "⚡ Titanium Stealth", False),
    (20, "🕊️ Studio Pure White", False),
    (21, "🔴 SuperProfile Crimson", False),
    (22, "⚪ Kaizen Minimal", False),
    (23, "🌊 Academy Soft Pastel", False),
]


# ─────────────────────────── لوحة المستخدم الرئيسية ───────────────────────────

def main_menu_kb(is_vip: bool = True) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="➕ إنشاء / تعديل صفحتي"),
         KeyboardButton(text="🔗 تعديل الروابط")],
        [KeyboardButton(text="🌐 معاينة صفحتي"),
         KeyboardButton(text="🖼 صورتي الشخصية")],
        [KeyboardButton(text="🎯 تخصيص متقدم والقوالب"),
         KeyboardButton(text="💬 التعليقات والتقييمات")],
        [KeyboardButton(text="📊 إحصائياتي"),
         KeyboardButton(text="📷 كود QR")],
        [KeyboardButton(text="ℹ️ حسابي"),
         KeyboardButton(text="🎁 دعوة أصدقاء")],
        [KeyboardButton(text="🛠️ الدعم الفني")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# قائمة ألوان مميزة للتخصيص
ACCENT_COLORS = [
    ("#7c3aed", "🟣 بنفسجي"),
    ("#ec4899", "🌸 وردي"),
    ("#ef4444", "🔴 أحمر"),
    ("#f97316", "🟠 برتقالي"),
    ("#eab308", "🟡 ذهبي"),
    ("#22c55e", "🟢 أخضر"),
    ("#06b6d4", "🩵 سماوي"),
    ("#3b82f6", "🔵 أزرق"),
    ("#ffffff", "⚪ أبيض"),
    ("#000000", "⚫ أسود"),
]


def accent_colors_kb(current: Optional[str] = None) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(ACCENT_COLORS), 2):
        row = []
        for hexc, name in ACCENT_COLORS[i:i+2]:
            prefix = "✅ " if hexc == current else ""
            row.append(InlineKeyboardButton(text=f"{prefix}{name}",
                                             callback_data=f"set_color:{hexc}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="🔄 استعادة اللون الافتراضي", callback_data="reset_color")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


BUTTON_STYLES = [
    ("rounded", "🟩 مستدير الحواف"),
    ("pill", "💊 كبسولة (Pill)"),
    ("square", "🟥 حواف حادة"),
    ("tab", "📑 مسطح (Tab)"),
]


def button_styles_kb(current: str = "rounded") -> InlineKeyboardMarkup:
    rows = []
    for sid, name in BUTTON_STYLES:
        prefix = "✅ " if sid == current else ""
        rows.append([InlineKeyboardButton(text=f"{prefix}{name}",
                                          callback_data=f"set_style:{sid}")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


BG_EFFECTS = [
    ("none", "🚫 بدون تأثير"),
    ("stars", "✨ نجوم الفضاء المتلألئة"),
    ("aurora", "🔮 تموجات أورورا الحية"),
    ("neon", "🌐 شبكة النيون المستقبلية"),
    ("bubbles", "🫧 فقاعات مضيئة طافية"),
]


def bg_effects_kb(current: str = "none") -> InlineKeyboardMarkup:
    rows = []
    for eff_id, name in BG_EFFECTS:
        prefix = "✅ " if eff_id == current else ""
        rows.append([InlineKeyboardButton(text=f"{prefix}{name}", callback_data=f"set_bgeff:{eff_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


BADGE_TYPES = [
    ("blue", "🔵 رسمي موثق (Blue)"),
    ("gold_vip", "👑 ملكي ذهبي (Gold VIP)"),
    ("diamond", "💎 ألماسي نخبوي (Diamond)"),
    ("creator", "🎬 صانع محتوى (Creator)"),
    ("star", "⭐ النجمة الذهبية (Star)"),
]


def badge_types_kb(current: str = "blue") -> InlineKeyboardMarkup:
    rows = []
    for b_id, name in BADGE_TYPES:
        prefix = "✅ " if b_id == current else ""
        rows.append([InlineKeyboardButton(text=f"{prefix}{name}", callback_data=f"set_badgetype:{b_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def music_menu_kb(has_music: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="🎵 إضافة / تغيير رابط المقطع الصوتي", callback_data="set_music_url")]]
    if has_music:
        rows.append([InlineKeyboardButton(text="🗑 حذف المقطع الصوتي", callback_data="delete_music_url")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def whatsapp_btn_kb(has_wa: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="💬 إعداد زر واتساب بنص ترحيبي", callback_data="set_wa_btn")]]
    if has_wa:
        rows.append([InlineKeyboardButton(text="🗑 حذف زر واتساب", callback_data="delete_wa_btn")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


FONTS = [
    ("Tajawal", "✨ Tajawal (عصري متوازن - افتراضي)"),
    ("Cairo", "🏢 Cairo (أنيق وعريض)"),
    ("Almarai", "🍏 Almarai (ناعم نمط Apple)"),
    ("Readex Pro", "🚀 Readex Pro (حديث وتقني)"),
    ("Amiri", "📜 Amiri (كلاسيكي فاخر)"),
    ("IBM Plex Sans Arabic", "💼 IBM Plex (احترافي عالمي)"),
]


def fonts_kb(current: str = "Tajawal") -> InlineKeyboardMarkup:
    rows = []
    for f_id, name in FONTS:
        prefix = "✅ " if f_id == current else ""
        rows.append([InlineKeyboardButton(text=f"{prefix}{name}", callback_data=f"set_font:{f_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def marquee_menu_kb(has_marquee: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="📢 كتابة / تعديل نص الإعلان المتحرك", callback_data="set_marquee_txt")]]
    if has_marquee:
        rows.append([InlineKeyboardButton(text="🗑 حذف شريط الإعلانات", callback_data="delete_marquee_txt")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def countdown_menu_kb(has_countdown: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="⏳ إعداد / تعديل العداد التنازلي", callback_data="set_countdown")]]
    if has_countdown:
        rows.append([InlineKeyboardButton(text="🗑 حذف العداد التنازلي", callback_data="delete_countdown")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def custom_domain_menu_kb(has_domain: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="🌐 ربط دومين مخصص (CNAME)", callback_data="set_custom_domain")]]
    if has_domain:
        rows.append([InlineKeyboardButton(text="🗑 إزالة الدومين المخصص", callback_data="delete_custom_domain")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def social_icons_menu_kb(current_socials: dict) -> InlineKeyboardMarkup:
    platforms = [
        ("instagram", "📸 انستغرام"),
        ("tiktok", "🎵 تيك توك"),
        ("youtube", "▶️ يوتيوب"),
        ("x", "🐦 منصة X"),
        ("snapchat", "👻 سناب شات"),
        ("telegram", "✈️ تليجرام"),
        ("facebook", "👥 فيسبوك"),
        ("whatsapp", "💬 واتساب"),
        ("linkedin", "💼 لينكد إن"),
        ("discord", "🎮 ديسكورد"),
    ]
    rows = []
    for i in range(0, len(platforms), 2):
        row = []
        for key, name in platforms[i:i+2]:
            icon_status = "✅ " if current_socials.get(key) else "➕ "
            row.append(InlineKeyboardButton(text=f"{icon_status}{name}", callback_data=f"soc_set:{key}"))
        rows.append(row)
    if any(current_socials.values()):
        rows.append([InlineKeyboardButton(text="🗑 مسح جميع أيقونات التواصل", callback_data="soc_delete_all")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pixels_menu_kb(has_meta: bool = False, has_tiktok: bool = False, has_ga: bool = False) -> InlineKeyboardMarkup:
    meta_icon = "✅" if has_meta else "➕"
    tt_icon = "✅" if has_tiktok else "➕"
    ga_icon = "✅" if has_ga else "➕"
    rows = [
        [InlineKeyboardButton(text=f"{meta_icon} Meta / Facebook Pixel", callback_data="set_pixel_meta")],
        [InlineKeyboardButton(text=f"{tt_icon} TikTok Pixel", callback_data="set_pixel_tiktok")],
        [InlineKeyboardButton(text=f"{ga_icon} Google Analytics (GA4)", callback_data="set_pixel_ga")],
    ]
    if has_meta or has_tiktok or has_ga:
        rows.append([InlineKeyboardButton(text="🗑 حذف جميع أكواد التتبع", callback_data="delete_pixels")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def customize_menu_kb(show_badge: bool = True) -> InlineKeyboardMarkup:
    badge_text = "✔️ إظهار الشارة" if show_badge else "❌ إخفاء الشارة"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 القوالب والتصاميم 🌟", callback_data="show_themes")],
        [InlineKeyboardButton(text="🌐 شريط أيقونات التواصل 📲", callback_data="customize_socials")],
        [InlineKeyboardButton(text="🔤 نوع الخط العربي ✍️", callback_data="customize_font"),
         InlineKeyboardButton(text="📢 شريط الإعلانات + رابط", callback_data="customize_marquee")],
        [InlineKeyboardButton(text="⏳ العداد التنازلي للعروض", callback_data="customize_countdown"),
         InlineKeyboardButton(text="🌐 دومين مخصص (CNAME)", callback_data="customize_domain")],
        [InlineKeyboardButton(text="🔮 بكسل التتبع الإعلاني 📊", callback_data="customize_pixels")],
        [InlineKeyboardButton(text="🎨 لون مميز (Accent)", callback_data="customize_color"),
         InlineKeyboardButton(text="🔘 شكل الأزرار", callback_data="customize_style")],
        [InlineKeyboardButton(text="🏆 نوع الشارة", callback_data="customize_badge_type"),
         InlineKeyboardButton(text=badge_text, callback_data="toggle_badge")],
        [InlineKeyboardButton(text="🎬 خلفيات تفاعلية حية ✨", callback_data="customize_bg_effects")],
        [InlineKeyboardButton(text="🎵 مشغل الصوتيات 🎧", callback_data="customize_music")],
        [InlineKeyboardButton(text="💬 زر محادثة واتساب المباشر", callback_data="customize_whatsapp")],
        [InlineKeyboardButton(text="🖼 الصورة الشخصية", callback_data="customize_avatar"),
         InlineKeyboardButton(text="⭐ التعليقات والتقييمات", callback_data="reviews_list")],
    ])


def reviews_manager_kb(reviews: list, show_reviews: bool = True) -> InlineKeyboardMarkup:
    rows = []
    toggle_text = "🔔 قسم التعليقات: 🟢 مفعل" if show_reviews else "🔔 قسم التعليقات: 🔴 معطل"
    rows.append([InlineKeyboardButton(text=toggle_text, callback_data="toggle_reviews_section")])
    
    for r in reviews:
        rev_id = r["id"]
        name = r.get("reviewer_name") or "زائر"
        rating = r.get("rating") or 5
        status_icon = "✅" if r.get("is_approved") else "⏳"
        stars = "⭐" * rating
        btn_text = f"{status_icon} {name} ({stars})"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"rev_view:{rev_id}")])
    rows.append([InlineKeyboardButton(text="🔄 تحديث القائمة", callback_data="reviews_refresh")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def review_detail_kb(review: dict) -> InlineKeyboardMarkup:
    rev_id = review["id"]
    is_approved = bool(review.get("is_approved"))
    rows = []
    if is_approved:
        rows.append([InlineKeyboardButton(text="⏸ إخفاء من الصفحة (إلغاء القبول)", callback_data=f"rev_unapprove:{rev_id}")])
    else:
        rows.append([InlineKeyboardButton(text="✅ قبول وعرض في الصفحة", callback_data=f"rev_approve:{rev_id}")])
    rows.append([InlineKeyboardButton(text="🗑 حذف التقييم نهائياً", callback_data=f"rev_delete:{rev_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع لقائمة التقييمات", callback_data="reviews_list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hide_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# ─────────────────────────── معاينة صفحة الـ Web App ───────────────────────────

def webapp_preview_kb(user_id: int) -> InlineKeyboardMarkup:
    url = f"{settings.WEBAPP_BASE_URL}/api/page/{user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 افتح صفحتي", web_app=WebAppInfo(url=url))],
        [InlineKeyboardButton(text="🔗 نسخ رابط الصفحة", url=url)],
    ])


# ─────────────────────────── إنشاء / تعديل صفحة ───────────────────────────

def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_creation")]
    ])


def skip_or_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ تخطي (بدون نبذة)", callback_data="skip_bio")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_creation")],
    ])


def links_progress_kb(count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ حفظ الروابط ({count} روابط)",
                              callback_data="done_links")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_creation")],
    ])


def fsm_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ إلغاء الإنشاء")]
    ], resize_keyboard=True)


def fsm_skip_bio_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⏭ تخطي (بدون نبذة)")],
        [KeyboardButton(text="❌ إلغاء الإنشاء")]
    ], resize_keyboard=True)


def fsm_links_progress_kb(count: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=f"✅ حفظ الروابط ({count} روابط)")],
        [KeyboardButton(text="❌ إلغاء الإنشاء")]
    ], resize_keyboard=True)


def fsm_cancel_link_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔙 إلغاء الرابط الحالي")]
    ], resize_keyboard=True)


def manage_links_kb(links: list, is_vip: bool = False) -> InlineKeyboardMarkup:
    rows = []
    for link in links:
        rows.append([
            InlineKeyboardButton(text=f"📝 تخصيص: {link['title']}", callback_data=f"ln_edit:{link['id']}"),
            InlineKeyboardButton(text=f"❌ حذف", callback_data=f"ln_del:{link['id']}")
        ])
    rows.append([InlineKeyboardButton(text="➕ إضافة رابط جديد", callback_data="ln_add_new")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع للقائمة الرئيسية", callback_data="ln_back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_link_options_kb(link_id: int, link: dict = None) -> InlineKeyboardMarkup:
    is_feat = bool(link and link.get("is_featured"))
    feat_text = "⭐ إلغاء التوهج الذهبي" if is_feat else "✨ تمييز بتوهج نبضي (Glow)"
    is_ban = bool(link and link.get("is_banner"))
    ban_text = "🖼 نمط بنر عريض (مفعّل)" if is_ban else "🖼 نمط صورة مصغرة (مفعّل)"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ تعديل العنوان", callback_data=f"le_title:{link_id}"),
         InlineKeyboardButton(text="🌐 تعديل الرابط (URL)", callback_data=f"le_url:{link_id}")],
        [InlineKeyboardButton(text="📝 وصف فرعي (Subtitle)", callback_data=f"le_sub:{link_id}"),
         InlineKeyboardButton(text="🏷 قسم فاصل قبل الرابط", callback_data=f"le_sec:{link_id}")],
        [InlineKeyboardButton(text="🖼 صورة مصغرة / غلاف", callback_data=f"le_thumb:{link_id}"),
         InlineKeyboardButton(text=ban_text, callback_data=f"le_toggle_banner:{link_id}")],
        [InlineKeyboardButton(text=feat_text, callback_data=f"le_toggle_feat:{link_id}")],
        [InlineKeyboardButton(text="⬅️ رجوع لمدير الروابط", callback_data="ln_back_manager")]
    ])


def fsm_cancel_edit_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔙 إلغاء التعديل")]
    ], resize_keyboard=True)


# ─────────────────────────── الاشتراك والدفع ───────────────────────────

def subscription_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎉 جميع الميزات مجانية بالكامل بدون اشتراك!", callback_data="all_free_info")],
    ])


def sponsor_channels_kb(channels: list) -> InlineKeyboardMarkup:
    rows = []
    for i, ch in enumerate(channels, 1):
        clean_ch = ch.lstrip("@")
        rows.append([InlineKeyboardButton(text=f"📢 قناة/جروب رقم {i}", url=f"https://t.me/{clean_ch}")])
    rows.append([InlineKeyboardButton(text="🔄 التحقق واستلام الـ VIP", callback_data="verify_channel_vip")])
    rows.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="back_vip")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ─────────────────────────── القوالب ───────────────────────────

def themes_kb(current_theme: int, is_vip: bool = True, unlocked_themes: list = None) -> InlineKeyboardMarkup:
    rows = []
    for tid, name, is_premium in THEMES:
        prefix = "✅ " if tid == current_theme else ""
        data = f"set_theme:{tid}"
        rows.append([InlineKeyboardButton(text=f"{prefix}{name}", callback_data=data)])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع للتخصيص المتقدم", callback_data="customize_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def buy_theme_kb(theme_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"⭐ شراء بـ {settings.PREMIUM_THEME_PRICE} نجمة",
            callback_data=f"pay_theme:{theme_id}",
        )],
        [InlineKeyboardButton(text="⬅️ رجوع للقوالب", callback_data="show_themes")],
    ])


# ─────────────────────────── لوحة الأدمن ───────────────────────────

def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 إحصائيات البوت", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 إذاعة جماعية", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="💎 ترقية إلى VIP", callback_data="admin_upgrade"),
         InlineKeyboardButton(text="❌ إلغاء VIP", callback_data="admin_downgrade")],
        [InlineKeyboardButton(text="📢 قنوات الاشتراك الإجباري", callback_data="admin_channels")],
        [InlineKeyboardButton(text="🎁 نظام الإحالات", callback_data="admin_referrals")],
        [InlineKeyboardButton(text="🚫 حظر/رفع حظر مستخدم", callback_data="admin_ban")],
        [InlineKeyboardButton(text="✉️ رسالة خاصة لمستخدم", callback_data="admin_dm")],
        [InlineKeyboardButton(text="🏆 المتصدرون بالإحالات", callback_data="admin_leaderboard")],
        [InlineKeyboardButton(text="🔒 تسجيل الخروج من اللوحة", callback_data="admin_logout")],
    ])


def admin_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ رجوع للوحة الأدمن", callback_data="admin_back")]
    ])


def admin_vip_durations_kb(target_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗓 أسبوع (7 أيام)", callback_data=f"admin_set_vip:{target_user_id}:7"),
            InlineKeyboardButton(text="🗓 شهر (30 يوم)", callback_data=f"admin_set_vip:{target_user_id}:30"),
        ],
        [
            InlineKeyboardButton(text="🗓 3 أشهر (90 يوم)", callback_data=f"admin_set_vip:{target_user_id}:90"),
            InlineKeyboardButton(text="🗓 6 أشهر (180 يوم)", callback_data=f"admin_set_vip:{target_user_id}:180"),
        ],
        [
            InlineKeyboardButton(text="🗓 سنة (365 يوم)", callback_data=f"admin_set_vip:{target_user_id}:365"),
            InlineKeyboardButton(text="🗓 سنتين (730 يوم)", callback_data=f"admin_set_vip:{target_user_id}:730"),
        ],
        [
            InlineKeyboardButton(text="👑 مدى الحياة (دائم للأبد ✨)", callback_data=f"admin_set_vip:{target_user_id}:99999"),
        ],
        [
            InlineKeyboardButton(text="❌ إلغاء / إزالة اشتراك VIP", callback_data=f"admin_set_vip:{target_user_id}:0"),
        ],
        [
            InlineKeyboardButton(text="⬅️ رجوع للوحة الأدمن", callback_data="admin_back"),
        ],
    ])


def admin_channels_kb(has_channels: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="➕ إضافة قناة/قروب", callback_data="admin_add_channel")]]
    if has_channels:
        rows.append([InlineKeyboardButton(text="🔄 فحص صلاحيات البوت بالقنوات", callback_data="admin_test_channels")])
        rows.append([InlineKeyboardButton(text="🗑 حذف قناة", callback_data="admin_remove_channel")])
    rows.append([InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_referrals_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚙️ تغيير عدد الإحالات المطلوبة (حالياً: {settings.REFERRAL_TARGET})",
                              callback_data="admin_set_ref_target")],
        [InlineKeyboardButton(text="🏆 المتصدرون", callback_data="admin_leaderboard")],
        [InlineKeyboardButton(text="⬅️ رجوع", callback_data="admin_back")],
    ])


# ─────────────────────────── الاشتراك الإجباري ───────────────────────────

def force_sub_kb(channels: list) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        rows.append([InlineKeyboardButton(text=f"📢 {ch['title'] or 'اشترك'}", url=ch["invite_url"])])
    rows.append([InlineKeyboardButton(text="✅ تحققت من الاشتراك", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ─────────────────────────── الإحالة ───────────────────────────

def referral_kb(share_url: str) -> InlineKeyboardMarkup:
    share_text = "🔥 أنشئ صفحة بروفايلك ونظّم كل روابطك وحساباتك في رابط واحد بتصاميم خرافية ومجانية بالكامل 100%! جرّب البوت الآن واستفد منه:"
    tg_share = f"https://t.me/share/url?url={share_url}&text={share_text}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📲 شارك البوت مع أصدقائك الآن", url=tg_share)],
    ])


# ─────────────────────────── الأفاتار ───────────────────────────

def avatar_menu_kb(has_avatar: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="📤 رفع صورة جديدة", callback_data="upload_avatar")]]
    if has_avatar:
        rows.append([InlineKeyboardButton(text="🗑 حذف الصورة", callback_data="delete_avatar")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ─────────────────────────── الدعم الفني ───────────────────────────

def support_kb() -> InlineKeyboardMarkup:
    support_id = 6641619062
    dev = settings.DEVELOPER_USERNAME or "d91ik"
    rows = [
        [InlineKeyboardButton(text="💬 مراسلة الدعم الفني", url=f"https://t.me/{dev}")],
        [InlineKeyboardButton(text="👤 حساب الدعم (ID: 6641619062)", url=f"tg://user?id={support_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

