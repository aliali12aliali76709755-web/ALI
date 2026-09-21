"""
إعدادات البوت العامة (تُقرأ من ملف .env)
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)


class Settings:
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "8855056827:AAE4pTQSH6zCdqOLdSzbZwp1VsEiY2KT25s")
    ADMIN_ID: int = int(os.environ.get("ADMIN_ID", "6641619062"))
    SECONDARY_ADMIN_USERNAME: str = os.environ.get("SECONDARY_ADMIN_USERNAME", "d91ik").lstrip("@").lower()
    BOT_USERNAME: str = os.environ.get("BOT_USERNAME", "OmniLink2Bot")
    VIP_STARS_PRICE: int = int(os.environ.get("VIP_STARS_PRICE", "500"))
    VIP_USD_PRICE: int = int(os.environ.get("VIP_USD_PRICE", "20"))
    ADMIN_CONTACT: str = os.environ.get("ADMIN_CONTACT", "@d91ik")
    WEBAPP_BASE_URL: str = (os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("WEBAPP_BASE_URL", "http://localhost:8001")).rstrip("/")
    DB_PATH: str = os.environ.get("SQLITE_DB_PATH", str(ROOT_DIR / "data" / "bot_data.db"))
    AVATARS_DIR: str = os.environ.get("AVATARS_DIR", str(ROOT_DIR / "data" / "avatars"))

    FREE_LINKS_LIMIT: int = 3
    VIP_DURATION_DAYS: int = 365
    # مكافأة الإحالة: شهر واحد (30 يوم) فقط
    REFERRAL_REWARD_DAYS: int = int(os.environ.get("REFERRAL_REWARD_DAYS", "30"))

    ADMIN_PANEL_TRIGGER_WORD: str = os.environ.get("ADMIN_PANEL_TRIGGER_WORD", "صويري")
    ADMIN_PANEL_PASSWORD: str = os.environ.get("ADMIN_PANEL_PASSWORD", "76891796")

    REFERRAL_TARGET: int = int(os.environ.get("REFERRAL_TARGET", "10"))
    CREATOR_REFERRAL_TARGET: int = int(os.environ.get("CREATOR_REFERRAL_TARGET", "50"))

    # أسعار القوالب المدفوعة (بالنجوم)
    PREMIUM_THEME_PRICE: int = int(os.environ.get("PREMIUM_THEME_PRICE", "100"))

    # خطط الاشتراك (شهر / 3 أشهر / 6 أشهر / سنة) بالنجوم
    VIP_PRICE_1M: int = int(os.environ.get("VIP_STARS_PRICE_1M", "50"))
    VIP_PRICE_3M: int = int(os.environ.get("VIP_STARS_PRICE_3M", "130"))
    VIP_PRICE_6M: int = int(os.environ.get("VIP_STARS_PRICE_6M", "240"))
    VIP_PRICE_12M: int = int(os.environ.get("VIP_STARS_PRICE_12M", "400"))
    VIP_PRICE_LIFETIME: int = int(os.environ.get("VIP_STARS_PRICE_LIFETIME", "1500"))

    # يوزر المطور (للتواصل)
    DEVELOPER_USERNAME: str = os.environ.get("DEVELOPER_USERNAME", "d91ik").lstrip("@")

    # مكافأة الاشتراك بالقنوات
    CHANNEL_JOIN_REWARD_DAYS: int = int(os.environ.get("CHANNEL_JOIN_REWARD_DAYS", "30"))
    SPONSOR_CHANNELS: list = [ch.strip() for ch in os.environ.get("SPONSOR_CHANNELS", "").split(",") if ch.strip()]


settings = Settings()
