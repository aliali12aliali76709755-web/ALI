"""
هاندلرات الاشتراك والدفع:
- عرض ميزات VIP
- الدفع عبر Telegram Stars (invoice + successful_payment)
- التواصل مع الأدمن للدفع اليدوي
"""
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice,
    PreCheckoutQuery,
)

from bot.config import settings
from bot.keyboards import subscription_kb, main_menu_kb
from bot import database as db

router = Router(name="payment")


VIP_INFO_TEXT = (
    "💎 <b>اشتراك VIP السنوي</b>\n\n"
    "استفد من كل ميزات LinkTree الاحترافية:\n\n"
    "✅ روابط <b>غير محدودة</b>\n"
    "🎨 قوالب حصرية (Dark Cyber / Neon Glow / Glassmorphism)\n"
    "📷 كود QR خاص بصفحتك للمشاركة\n"
    "📊 إحصائيات مفصّلة للزوار والنقرات\n\n"
    f"💰 <b>السعر السنوي:</b> {settings.VIP_STARS_PRICE} ⭐ "
    f"(أو ${settings.VIP_USD_PRICE} تحويل يدوي)\n"
    "⏳ <b>المدة:</b> 365 يوم كاملة\n\n"
    "اختر طريقة الدفع بالأسفل 👇"
)


@router.message(F.text == "💎 الاشتراك في VIP")
async def show_subscription(message: Message):
    is_vip = await db.is_user_vip(message.from_user.id)
    if is_vip:
        user = await db.get_user(message.from_user.id)
        await message.answer(
            f"✨ أنت بالفعل مشترك VIP!\n"
            f"⏳ ينتهي الاشتراك في: <code>{user['vip_expires'][:10]}</code>"
        )
        return
    await message.answer(VIP_INFO_TEXT, reply_markup=subscription_kb())


# ─────────────────────── الدفع بتليجرام ستارز ───────────────────────

@router.callback_query(F.data == "pay_with_stars")
async def cb_pay_with_stars(cq: CallbackQuery, bot: Bot):
    """إرسال فاتورة دفع بالنجوم"""
    prices = [LabeledPrice(label="VIP سنوي", amount=settings.VIP_STARS_PRICE)]
    await bot.send_invoice(
        chat_id=cq.from_user.id,
        title="اشتراك VIP سنوي",
        description="روابط غير محدودة + قوالب حصرية + QR + إحصائيات (365 يوم)",
        payload=f"vip_subscription_{cq.from_user.id}",
        provider_token="",  # فارغ لأن العملة XTR (Telegram Stars)
        currency="XTR",
        prices=prices,
        start_parameter="vip",
    )
    await cq.answer()


@router.pre_checkout_query()
async def on_pre_checkout(pcq: PreCheckoutQuery, bot: Bot):
    """الموافقة على عملية الدفع قبل تنفيذها"""
    await bot.answer_pre_checkout_query(pcq.id, ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    """تم الدفع بنجاح - تفعيل VIP فوراً"""
    sp = message.successful_payment
    user_id = message.from_user.id
    await db.set_vip_status(user_id, True, days=settings.VIP_DURATION_DAYS)
    await db.create_payment(
        user_id=user_id,
        amount=sp.total_amount,
        currency="STARS",
        status="completed",
        charge_id=sp.telegram_payment_charge_id,
    )
    await message.answer(
        "🎉 <b>تم تفعيل اشتراكك في VIP بنجاح!</b>\n"
        f"⏳ صالح لمدة {settings.VIP_DURATION_DAYS} يوم.\n\n"
        "استمتع بجميع الميزات الحصرية ✨",
        reply_markup=main_menu_kb(is_vip=True),
    )


# ─────────────────────── الدفع اليدوي (تواصل مع الأدمن) ───────────────────────

@router.callback_query(F.data == "contact_admin_payment")
async def cb_contact_admin(cq: CallbackQuery):
    text = (
        "💬 <b>الدفع اليدوي</b>\n\n"
        f"للحصول على اشتراك VIP يدوياً بمبلغ <b>${settings.VIP_USD_PRICE}</b>:\n\n"
        f"1️⃣ تواصل مع الإدارة: {settings.ADMIN_CONTACT}\n"
        "2️⃣ أرسل مبلغ الاشتراك عبر إحدى وسائل الدفع المتاحة\n"
        "3️⃣ أرسل إثبات التحويل مع آيدي حسابك:\n"
        f"   <code>{cq.from_user.id}</code>\n\n"
        "بعد تأكيد الأدمن سيتم تفعيل حسابك تلقائياً ✅"
    )
    await cq.message.answer(text)
    await cq.answer()
