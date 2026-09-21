import sys
import asyncio
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from bot import database as db
from bot.webapp_template import render_page, THEME_STYLES, get_verified_badge_html
from bot.keyboards import bg_effects_kb, badge_types_kb, music_menu_kb, whatsapp_btn_kb

def run(coro):
    return asyncio.run(coro)

@pytest.fixture(scope="module", autouse=True)
def _init():
    run(db.init_db())

def test_theme_16_exists_and_renders():
    assert 16 in THEME_STYLES
    user = {
        "user_id": 999111,
        "full_name": "Bento Tester",
        "page_title": "My Bento Page",
        "theme": 16,
        "is_vip": 1,
    }
    links = [
        {"id": 1, "title": "My YouTube", "url": "https://youtube.com/mych"},
        {"id": 2, "title": "My Instagram", "url": "https://instagram.com/myig"},
    ]
    html = render_page(user, links)
    assert "Bento 3D Grid" in html or "grid-template-columns" in html
    assert "My YouTube" in html
    assert "My Instagram" in html

def test_badges_generation():
    blue_html = get_verified_badge_html("blue")
    gold_html = get_verified_badge_html("gold_vip")
    diam_html = get_verified_badge_html("diamond")
    creator_html = get_verified_badge_html("creator")
    assert "badge-gold" in gold_html
    assert "badge-diamond" in diam_html
    assert "badge-creator" in creator_html
    assert "badge-blue" in blue_html

def test_reviews_db_crud():
    async def _test():
        uid = 888999
        rev_id = await db.add_review(uid, "Ali Tester", 5, "Amazing page!")
        assert rev_id > 0
        
        # Initially not approved
        approved = await db.get_reviews(uid, approved_only=True)
        assert len(approved) == 0
        
        all_revs = await db.get_reviews(uid, approved_only=False)
        assert len(all_revs) == 1
        assert all_revs[0]["reviewer_name"] == "Ali Tester"
        
        # Approve review
        ok = await db.approve_review(rev_id, True)
        assert ok is True
        approved_now = await db.get_reviews(uid, approved_only=True)
        assert len(approved_now) == 1
        
        # Delete review
        del_ok = await db.delete_review(rev_id)
        assert del_ok is True
        assert len(await db.get_reviews(uid, approved_only=False)) == 0

    run(_test())

def test_music_and_customization_db():
    async def _test():
        uid = 888999
        await db.get_or_create_user(uid, "music_tester", "Music Tester")
        await db.update_music(uid, "https://example.com/sound.mp3", "Calm Rain")
        await db.update_bg_effect(uid, "aurora")
        await db.update_badge_type(uid, "diamond")
        await db.update_whatsapp_btn(uid, '{"phone":"9647700000000","msg":"Hello"}')
        
        user = await db.get_user(uid)
        assert user["music_url"] == "https://example.com/sound.mp3"
        assert user["music_title"] == "Calm Rain"
        assert user["bg_effect"] == "aurora"
        assert user["badge_type"] == "diamond"
        assert "9647700000000" in user["whatsapp_btn"]

    run(_test())

def test_peak_activity_hours():
    async def _test():
        uid = 777666
        await db.get_or_create_user(uid, "peak_tester", "Peak Tester")
        await db.log_event(uid, "visit", ip="127.0.0.1", country="Iraq")
        await db.log_event(uid, "click", link_id=1, ip="127.0.0.1", country="Iraq")
        
        peaks = await db.get_peak_activity_hours(uid)
        assert len(peaks) > 0
        assert "hour" in peaks[0]
        assert "count" in peaks[0]

    run(_test())
