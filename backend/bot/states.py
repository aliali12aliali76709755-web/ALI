"""
حالات الـ FSM (Finite State Machine) لإدارة تدفق المحادثة
"""
from aiogram.fsm.state import State, StatesGroup


class PageCreationStates(StatesGroup):
    """حالات إنشاء / تعديل صفحة المستخدم"""
    waiting_title = State()          # في انتظار عنوان الصفحة
    waiting_bio = State()            # في انتظار النبذة المختصرة
    waiting_link_title = State()     # في انتظار اسم الرابط
    waiting_link_url = State()       # في انتظار عنوان الرابط (URL)


class AdminStates(StatesGroup):
    """حالات لوحة تحكم الأدمن"""
    waiting_broadcast_message = State()   # في انتظار رسالة الإذاعة
    waiting_upgrade_user_id = State()     # في انتظار آيدي المستخدم للترقية
    waiting_downgrade_user_id = State()   # في انتظار آيدي المستخدم للإلغاء
