"""
هاندلرات الاشتراك والدفع:
- عرض ميزات VIP
- الدفع عبر Telegram Stars لخطط متعددة (1/3/6/12 شهر)
- شراء القوالب البريميوم
- التواصل مع المطور للدفع اليدوي
"""
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice, PreCheckoutQuery,
)

from bot.config import settings
from bot.keyboards import subscription_kb, main_menu_kb, THEMES
from bot import database as db

router = Router(name="payment")


# خطط الاشتراك (months → (days, price_stars, label))
PLANS = {
    1:  (30,  None, "شهر واحد"),
    3:  (90,  None, "3 أشهر"),
    6:  (180, None, "6 أشهر"),
    12: (365, None, "سنة كاملة"),
}


def _plan_price(months: int) -> int:
    return {
        1:  settings.VIP_PRICE_1M,
        3:  settings.VIP_PRICE_3M,
        6:  settings.VIP_PRICE_6M,
        12: settings.VIP_PRICE_12M,
    }.get(months, settings.VIP_PRICE_12M)


VIP_INFO_TEXT = (
    "💎 <b>اشتراك VIP — كل الميزات في متناول يدك</b>\n\n"
    "✅ روابط <b>غير محدودة</b>\n"
    "🎨 <b>جميع القوالب مجانية</b> (بما فيها البريميوم الفاخرة)\n"
    "⚙️ <b>تخصيص متقدم</b> (تغيير لون الهوية وأشكال الأزرار)\n"
    "🖼 <b>صورة شخصية</b> (أفاتار حقيقي للبروفايل)\n"
    "📷 كود QR خاص بصفحتك\n"
    "📊 إحصائيات متقدمة جداً (مصادر الزوار، أنواع الأجهزة، توزيع الدول والجنس)\n"
    "✔️ شارة توثيق زرقاء اختيارية (تفعيل/إلغاء في أي وقت)\n\n"
    "<b>💡 سياسة انتهاء الاشتراك:</b>\n"
    "إذا انتهى اشتراكك الـ VIP، <b>ستظل صفحتك الشخصية وروابطك والقوالب التي اخترتها تعمل بشكل طبيعي أمام الجميع ولن تحذف أبداً!</b> ولكنك لن تتمكن من تعديل الصفحة أو روابطك، أو مراجعة إحصائيات الزوار حتى تجدد الاشتراك.\n\n"
    "<b>💰 اختر خطتك المناسبة:</b>\n"
    f"• شهر واحد: <b>{settings.VIP_PRICE_1M} ⭐</b>\n"
    f"• 3 أشهر:  <b>{settings.VIP_PRICE_3M} ⭐</b> (وفر ~33%)\n"
    f"• 6 أشهر:  <b>{settings.VIP_PRICE_6M} ⭐</b> (وفر ~41%)\n"
    f"• سنة كاملة: <b>{settings.VIP_PRICE_12M} ⭐</b> (وفر ~53%)\n\n"
    f"🎁 <b>أو مجاناً:</b> ادعُ {settings.REFERRAL_TARGET} أصدقاء "
    f"→ {settings.REFERRAL_REWARD_DAYS} يوم VIP مجاناً!\n\n"
    "اختر الخطة المناسبة بالأسفل 👇"
)


@router.message(F.text == "💎 اشتراك VIP")
@router.message(F.text == "💎 الاشتراك في VIP")
async def show_subscription(message: Message):
    await message.answer(
        "🎉 <b>البوت مجاني بالكامل 100%!</b>\n\n"
        "جميع الميزات الحصرية، القوالب، الصفحات المتعددة، وتخصيص الروابط متاحة مجاناً للجميع بدون أي اشتراك أو دفع!",
        reply_markup=main_menu_kb(is_vip=True)
    )


@router.callback_query(F.data.startswith("pay_plan:"))
@router.callback_query(F.data == "pay_with_stars")
async def cb_pay_plan(cq: CallbackQuery, bot: Bot):
    await cq.answer("🎉 البوت مجاني بالكامل لجميع المستخدمين بدون اشتراك!", show_alert=True)


@router.callback_query(F.data == "all_free_info")
async def cb_all_free_info(cq: CallbackQuery):
    await cq.answer("🎉 جميع الميزات مجانية بالكامل للجميع بدون أي اشتراك!", show_alert=True)


@router.pre_checkout_query()
async def on_pre_checkout(pcq: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pcq.id, ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    sp = message.successful_payment
    user_id = message.from_user.id
    payload = sp.invoice_payload or ""

    # قالب بريميوم؟
    if payload.startswith("theme_"):
        try:
            theme_id = int(payload.split("_")[1])
        except Exception:
            theme_id = None
        if theme_id:
            await db.unlock_theme(user_id, theme_id)
            await db.create_payment(
                user_id=user_id, amount=sp.total_amount,
                currency="STARS", status="completed",
                charge_id=sp.telegram_payment_charge_id,
                purpose=f"theme_{theme_id}",
            )
            theme_def = next((t for t in THEMES if t[0] == theme_id), None)
            theme_name = theme_def[1] if theme_def else "قالب"
            await message.answer(
                f"🎉 <b>تم شراء القالب بنجاح!</b>\n\n"
                f"👑 القالب: <b>{theme_name}</b>\n"
                "افتح «🎨 القوالب» لتفعيله على صفحتك.",
            )
            return

    # اشتراك VIP بخطط 1/3/6/12
    months = 12  # افتراضي
    if payload.startswith("vip_"):
        try:
            months = int(payload.split("_")[1])
        except Exception:
            months = 12
    if months not in PLANS:
        months = 12
    days = PLANS[months][0]

    await db.set_vip_status(user_id, True, days=days)
    await db.create_payment(
        user_id=user_id, amount=sp.total_amount, currency="STARS",
        status="completed", charge_id=sp.telegram_payment_charge_id,
        purpose=f"vip_{months}m",
    )
    duration_text = "مدى الحياة (اشتراك دائم للأبد 🔥)" if months == 999 else f"{days} يوم ({PLANS[months][2]})"
    await message.answer(
        f"🎉 <b>تم تفعيل اشتراكك في VIP بنجاح!</b>\n"
        f"⏳ مدة الاشتراك: <b>{duration_text}</b>.\n\n"
        "استمتع بجميع الميزات الحصرية والتخصيص المتقدم ✨\n"
        "اضغط «⭐ ميزات VIP» لرؤية كل ما تستفيد منه!",
        reply_markup=main_menu_kb(is_vip=True),
    )


@router.callback_query(F.data == "contact_admin_payment")
async def cb_contact_admin(cq: CallbackQuery):
    text = (
        "💬 <b>الدفع اليدوي</b>\n\n"
        f"للحصول على اشتراك VIP يدوياً:\n\n"
        f"1️⃣ تواصل مع المطور: <a href='https://t.me/{settings.DEVELOPER_USERNAME}'>@{settings.DEVELOPER_USERNAME}</a>\n"
        "2️⃣ اختر الخطة المناسبة (شهر / 3 / 6 / سنة)\n"
        "3️⃣ أرسل إثبات التحويل مع آيدي حسابك:\n"
        f"   <code>{cq.from_user.id}</code>\n\n"
        "بعد تأكيد المطور سيتم تفعيل حسابك تلقائياً ✅"
    )
    await cq.message.answer(text, disable_web_page_preview=True)
    await cq.answer()
