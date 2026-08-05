"""
إعدادات البوت العامة (تُقرأ من ملف .env)
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    # التوكن الخاص بالبوت من BotFather
    BOT_TOKEN: str = os.environ["BOT_TOKEN"]

    # آيدي الأدمن (المسؤول)
    ADMIN_ID: int = int(os.environ["ADMIN_ID"])

    # يوزر البوت (بدون @) - يستخدم في كود QR ورابط المشاركة
    BOT_USERNAME: str = os.environ.get("BOT_USERNAME", "MyLinktreeBot")

    # سعر الاشتراك السنوي بتليجرام ستارز
    VIP_STARS_PRICE: int = int(os.environ.get("VIP_STARS_PRICE", "500"))

    # سعر الاشتراك السنوي بالدولار (للتحويل اليدوي)
    VIP_USD_PRICE: int = int(os.environ.get("VIP_USD_PRICE", "20"))

    # يوزر الأدمن للتواصل معه للدفع اليدوي
    ADMIN_CONTACT: str = os.environ.get("ADMIN_CONTACT", "@Admin")

    # الرابط الأساسي لصفحة الـ Web App (يجب أن يكون HTTPS)
    WEBAPP_BASE_URL: str = os.environ["WEBAPP_BASE_URL"].rstrip("/")

    # مسار قاعدة بيانات SQLite
    DB_PATH: str = os.environ.get("SQLITE_DB_PATH", "/app/backend/bot_data.db")

    # الحد الأقصى لعدد الروابط للمستخدم المجاني
    FREE_LINKS_LIMIT: int = 3

    # مدة الاشتراك بالأيام
    VIP_DURATION_DAYS: int = 365


settings = Settings()
