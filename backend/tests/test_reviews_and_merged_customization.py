import sys
import asyncio
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from bot import database as db
from bot.keyboards import (
    main_menu_kb, customize_menu_kb, themes_kb,
    reviews_manager_kb, review_detail_kb,
)

def run(coro):
    return asyncio.run(coro)

@pytest.fixture(scope="module", autouse=True)
def _init():
    run(db.init_db())

def test_main_menu_merged_options():
    kb = main_menu_kb(is_vip=True)
    all_buttons = [btn.text for row in kb.keyboard for btn in row]
    assert "🎯 تخصيص متقدم والقوالب" in all_buttons
    assert "🎨 القوالب" not in all_buttons  # Merged!

def test_customize_menu_includes_themes_and_reviews():
    kb = customize_menu_kb(show_badge=True)
    all_cb_data = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "show_themes" in all_cb_data
    assert "reviews_list" in all_cb_data

def test_themes_kb_has_back_button():
    kb = themes_kb(current_theme=1, is_vip=True, unlocked_themes=[])
    all_cb_data = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "customize_back" in all_cb_data

def test_reviews_manager_keyboards():
    dummy_reviews = [
        {"id": 101, "reviewer_name": "Sami", "rating": 5, "is_approved": 1, "comment": "Great!"},
        {"id": 102, "reviewer_name": "Noor", "rating": 4, "is_approved": 0, "comment": "Nice!"},
    ]
    kb = reviews_manager_kb(dummy_reviews)
    all_cb_data = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "rev_view:101" in all_cb_data
    assert "rev_view:102" in all_cb_data
    assert "reviews_refresh" in all_cb_data

    # Test detail keyboard for approved review
    detail_app = review_detail_kb(dummy_reviews[0])
    app_cbs = [btn.callback_data for row in detail_app.inline_keyboard for btn in row]
    assert "rev_unapprove:101" in app_cbs
    assert "rev_delete:101" in app_cbs

    # Test detail keyboard for pending review
    detail_pen = review_detail_kb(dummy_reviews[1])
    pen_cbs = [btn.callback_data for row in detail_pen.inline_keyboard for btn in row]
    assert "rev_approve:102" in pen_cbs
    assert "rev_delete:102" in pen_cbs
