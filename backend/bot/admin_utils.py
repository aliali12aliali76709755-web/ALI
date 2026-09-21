"""
أدوات مشتركة لتحديد ما إذا كان المستخدم أدمن (بأي وسيلة)
"""
from bot.config import settings
from bot import database as db


async def is_admin_or_authorized(user_id: int, username: str = "") -> bool:
    """يرجع True إذا كان المستخدم أدمن أصلي، أو ثانوي، أو صادق بكلمة السر"""
    if user_id == settings.ADMIN_ID:
        return True
    if settings.SECONDARY_ADMIN_USERNAME and username and \
            username.lower().lstrip("@") == settings.SECONDARY_ADMIN_USERNAME:
        return True
    if await db.has_admin_session(user_id):
        return True
    return False
