"""
لوحات المفاتيح (Keyboards) - الأزرار الثابتة (Reply) والشفافة (Inline)
"""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo,
)
from bot.config import settings


# ─────────────────────────── لوحة المستخدم الرئيسية ───────────────────────────

def main_menu_kb(is_vip: bool = False) -> ReplyKeyboardMarkup:
    """اللوحة الرئيسية للمستخدم (Reply Keyboard ثابتة)"""
    rows = [
        [KeyboardButton(text="➕ إنشاء / تعديل صفحتي")],
        [KeyboardButton(text="🌐 معاينة صفحتي")],
        [KeyboardButton(text="💎 الاشتراك في VIP"),
         KeyboardButton(text="📊 إحصائياتي")],
        [KeyboardButton(text="🎨 تغيير التصميم"),
         KeyboardButton(text="📷 كود QR الخاص بي")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ─────────────────────────── معاينة صفحة الـ Web App ───────────────────────────

def webapp_preview_kb(user_id: int) -> InlineKeyboardMarkup:
    """زر لفتح صفحة الويب الشخصية كـ Web App"""
    url = f"{settings.WEBAPP_BASE_URL}/api/page/{user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 افتح صفحتي", web_app=WebAppInfo(url=url))]
    ])


# ─────────────────────────── أثناء إنشاء الصفحة ───────────────────────────

def add_link_prompt_kb() -> InlineKeyboardMarkup:
    """أزرار: إضافة رابط جديد / الانتهاء"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة رابط جديد", callback_data="add_new_link")],
        [InlineKeyboardButton(text="✅ الانتهاء وحفظ الصفحة", callback_data="finish_page")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_fsm")]
    ])


# ─────────────────────────── الاشتراك والدفع ───────────────────────────

def subscription_kb() -> InlineKeyboardMarkup:
    """خيارات الدفع للاشتراك في VIP"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"⭐ ادفع بـ {settings.VIP_STARS_PRICE} نجمة (Telegram Stars)",
            callback_data="pay_with_stars"
        )],
        [InlineKeyboardButton(
            text="💬 تواصل مع الإدارة للدفع اليدوي",
            callback_data="contact_admin_payment"
        )],
    ])


# ─────────────────────────── اختيار القالب ───────────────────────────

def themes_kb(current_theme: int = 0) -> InlineKeyboardMarkup:
    """قائمة اختيار قالب صفحة الـ Web App (لمستخدمي VIP فقط)"""
    themes = [
        (1, "🌌 القالب المظلم (Dark Cyber)"),
        (2, "💖 القالب الوردي اللامع (Neon Glow)"),
        (3, "🪟 القالب الزجاجي (Glassmorphism)"),
    ]
    rows = []
    for tid, name in themes:
        text = f"{'✅ ' if tid == current_theme else ''}{name}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"set_theme:{tid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ─────────────────────────── لوحة الأدمن ───────────────────────────

def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 إحصائيات البوت", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 إذاعة (Broadcast)", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="💎 ترقية مستخدم إلى VIP", callback_data="admin_upgrade")],
        [InlineKeyboardButton(text="❌ إلغاء اشتراك VIP", callback_data="admin_downgrade")],
    ])


def admin_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ رجوع للوحة الأدمن", callback_data="admin_back")]
    ])
