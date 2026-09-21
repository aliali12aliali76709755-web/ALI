"""
حالات الـ FSM (Finite State Machine) لإدارة تدفق المحادثة
"""
from aiogram.fsm.state import State, StatesGroup


class PageCreationStates(StatesGroup):
    """حالات إنشاء / تعديل صفحة المستخدم"""
    waiting_title = State()
    waiting_bio = State()
    waiting_link_title = State()
    waiting_link_url = State()


class AvatarStates(StatesGroup):
    """حالة رفع الصورة الشخصية"""
    waiting_photo = State()


class LinkEditStates(StatesGroup):
    """حالات تعديل الروابط الفردية"""
    waiting_edit_title = State()
    waiting_edit_url = State()
    waiting_new_title = State()
    waiting_new_url = State()
    waiting_link_subtitle = State()
    waiting_link_thumbnail = State()
    waiting_link_section = State()


class AdminAuthStates(StatesGroup):
    waiting_password = State()


class AdminStates(StatesGroup):
    waiting_broadcast_message = State()
    waiting_upgrade_user_id = State()
    waiting_downgrade_user_id = State()
    waiting_add_channel = State()
    waiting_remove_channel = State()
    waiting_set_referral_target = State()
    waiting_admin_dm_user = State()
    waiting_admin_dm_text = State()
    waiting_ban_input = State()


class CustomizationStates(StatesGroup):
    waiting_music_url = State()
    waiting_music_title = State()
    waiting_wa_phone = State()
    waiting_wa_msg = State()
    waiting_marquee_text = State()
    waiting_marquee_url = State()
    waiting_countdown_title = State()
    waiting_countdown_target = State()
    waiting_custom_domain = State()
    waiting_meta_pixel = State()
    waiting_tiktok_pixel = State()
    waiting_ga_pixel = State()
    waiting_social_url = State()


class SubPageStates(StatesGroup):
    waiting_slug = State()
    waiting_title = State()
    waiting_bio = State()
    
    # Manage specific sub-page
    waiting_sp_new_link_title = State()
    waiting_sp_new_link_url = State()
