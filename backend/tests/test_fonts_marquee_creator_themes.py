import sys
import asyncio
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from bot import database as db
from bot.webapp_template import render_page, THEME_STYLES, FONT_MAP
from bot.keyboards import fonts_kb, marquee_menu_kb, THEMES

def run(coro):
    return asyncio.run(coro)

@pytest.fixture(scope="module", autouse=True)
def _init():
    run(db.init_db())

def test_creator_themes_17_to_20_exist():
    for tid in (17, 18, 19, 20):
        assert tid in THEME_STYLES
        theme_item = next((t for t in THEMES if t[0] == tid), None)
        assert theme_item is not None

def test_render_creator_theme_and_font():
    user = {
        "user_id": 555444,
        "full_name": "Elite Creator",
        "page_title": "MrBeast Arabic Studio",
        "theme": 17,
        "is_vip": 1,
        "font_family": "Cairo",
        "marquee_text": "🔥 شاهد الحلقة الجديدة الآن حصرياً!",
    }
    links = [
        {"id": 1, "title": "القناة الرسمية", "url": "https://youtube.com/c/creator"}
    ]
    html = render_page(user, links)
    assert "Cairo" in html
    assert "شاهد الحلقة الجديدة الآن" in html
    assert "marquee-bar" in html
    assert "Studio Minimalist" in html or "#0d0e12" in html

def test_font_and_marquee_db_updates():
    async def _test():
        uid = 555444
        await db.get_or_create_user(uid, "creator_tester", "Creator Tester")
        await db.update_font(uid, "Readex Pro")
        await db.update_marquee(uid, "خصم خاص على المنتجات")
        
        user = await db.get_user(uid)
        assert user["font_family"] == "Readex Pro"
        assert user["marquee_text"] == "خصم خاص على المنتجات"
        
        # Test delete marquee
        await db.update_marquee(uid, None)
        user_after = await db.get_user(uid)
        assert user_after["marquee_text"] is None

    run(_test())

def test_keyboards():
    f_kb = fonts_kb("Almarai")
    f_cbs = [btn.callback_data for row in f_kb.inline_keyboard for btn in row]
    assert "set_font:Almarai" in f_cbs
    assert "set_font:Amiri" in f_cbs
    assert "customize_back" in f_cbs

    m_kb = marquee_menu_kb(has_marquee=True)
    m_cbs = [btn.callback_data for row in m_kb.inline_keyboard for btn in row]
    assert "set_marquee_txt" in m_cbs
    assert "delete_marquee_txt" in m_cbs
