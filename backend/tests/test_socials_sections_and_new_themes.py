import sys
import asyncio
import json
import uuid
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from bot import database as db
from bot.webapp_template import render_page, THEME_STYLES
from bot.keyboards import THEMES, social_icons_menu_kb, edit_link_options_kb

def run(coro):
    return asyncio.run(coro)

@pytest.fixture(scope="module", autouse=True)
def _init():
    run(db.init_db())

def test_social_links_db_and_rendering():
    user_id = 999333
    run(db.get_or_create_user(user_id=user_id, username="influencer_pro_3", full_name="Pro Creator"))
    
    # Update social links
    socials = {
        "instagram": "https://instagram.com/pro_creator",
        "tiktok": "@tiktok_star",
        "youtube": "https://youtube.com/@channel",
        "whatsapp": "+9647701234567",
    }
    run(db.update_social_links(user_id, socials))
    
    user = run(db.get_user(user_id))
    assert user is not None
    saved_soc = json.loads(user["social_links"])
    assert saved_soc["instagram"] == "https://instagram.com/pro_creator"
    
    html = render_page(user, [])
    assert 'class="social-icons-bar"' in html
    assert 'href="https://instagram.com/pro_creator"' in html
    assert 'title="instagram"' in html
    assert 'title="youtube"' in html


def test_link_extra_attributes_and_rendering():
    user_id = 999444
    run(db.get_or_create_user(user_id=user_id, username="course_creator_4", full_name="Master Fahad"))
    
    existing_links = run(db.get_user_links(user_id))
    for l in existing_links:
        run(db.delete_link(l["id"]))

    run(db.add_link(user_id, "الدورة التأسيسية الشاملة", "https://course.example.com"))
    links = run(db.get_user_links(user_id))
    assert len(links) == 1
    link_id = links[0]["id"]
    
    # Update extra fields
    run(db.update_link_extra(
        link_id=link_id,
        subtitle="بداية الدورة 09/08/2026 • خصم خاص",
        thumbnail_url="https://example.com/banner.png",
        is_banner=1,
        section_header="🎓 دوراتي وكورساتي المميزة",
        is_featured=1,
    ))
    
    link = run(db.get_link_by_id(link_id))
    assert link["subtitle"] == "بداية الدورة 09/08/2026 • خصم خاص"
    assert link["thumbnail_url"] == "https://example.com/banner.png"
    assert link["is_banner"] == 1
    assert link["section_header"] == "🎓 دوراتي وكورساتي المميزة"
    assert link["is_featured"] == 1
    
    # Render page
    user = run(db.get_user(user_id))
    updated_links = run(db.get_user_links(user_id))
    html = render_page(user, updated_links)
    
    # Verify section header
    assert 'class="section-header"' in html
    assert "🎓 دوراتي وكورساتي المميزة" in html
    
    # Verify banner card & subtitle & featured glow
    assert "btn-banner" in html
    assert "is-featured" in html
    assert "banner-img" in html
    assert "بداية الدورة 09/08/2026 • خصم خاص" in html


def test_influencer_themes():
    theme_ids = [t[0] for t in THEMES]
    assert 21 in theme_ids  # SuperProfile Crimson
    assert 22 in theme_ids  # Kaizen Minimal
    assert 23 in theme_ids  # Academy Soft Pastel
    
    assert 21 in THEME_STYLES
    assert 22 in THEME_STYLES
    assert 23 in THEME_STYLES
    
    # Render with Theme 21
    user_t21 = {"user_id": 88801, "username": "abdelhamid", "page_title": "Abdelhamid", "theme": 21}
    html_21 = render_page(user_t21, [])
    assert "#0d0203" in html_21
    assert "3b050a" in html_21
    
    # Render with Theme 22
    user_t22 = {"user_id": 88802, "username": "kaizen", "page_title": "Kaizen", "theme": 22}
    html_22 = render_page(user_t22, [])
    assert "#f5f6f8" in html_22
    
    # Render with Theme 23
    user_t23 = {"user_id": 88803, "username": "fahad", "page_title": "Fahad Academy", "theme": 23}
    html_23 = render_page(user_t23, [])
    assert "#7db3db" in html_23


def test_keyboards_structure():
    soc_kb = social_icons_menu_kb({"instagram": "https://instagram.com/test"})
    assert any("Instagram" in btn.text or "انستغرام" in btn.text for row in soc_kb.inline_keyboard for btn in row)
    
    link_data = {"is_featured": 1, "is_banner": 1}
    edit_kb = edit_link_options_kb(123, link_data)
    assert any("إلغاء التوهج" in btn.text for row in edit_kb.inline_keyboard for btn in row)
    assert any("بنر عريض" in btn.text for row in edit_kb.inline_keyboard for btn in row)
