"""
Backend API tests - endpoints exposed by FastAPI.
Covers: /api/health, /api/stats, /api/page/{uid}, /api/avatar/{uid},
        /api/track/{uid}/visit, /api/track/{uid}/click/{lid}
"""
import os
import asyncio
import sys
from pathlib import Path

import pytest
import requests

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from bot import database as db  # noqa: E402
from bot.config import settings  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", os.environ["WEBAPP_BASE_URL"]).rstrip("/")

# Unique test user IDs (very high to avoid colliding with real Telegram IDs)
TEST_USER_BASE = 990_000_000
TEST_USER_1 = TEST_USER_BASE + 1          # simple existing user w/ page
TEST_USER_VIP_AVATAR = TEST_USER_BASE + 2 # VIP + avatar + theme 8
TEST_USER_NO_PAGE = TEST_USER_BASE + 3    # exists but no page_title
NONEXISTENT_USER = TEST_USER_BASE + 999


@pytest.fixture(scope="module", autouse=True)
def setup_test_users():
    """Seed test users needed for all API tests."""
    async def _seed():
        await db.init_db()
        # Simple user with a page + 3 platform links
        await db.get_or_create_user(TEST_USER_1, "TEST_apiuser1", "TEST User1")
        await db.update_user_page(TEST_USER_1, "TEST_Page1", "TEST bio")
        # Wipe & re-add exactly 3 links to check icon detection
        await db.delete_user_links(TEST_USER_1)
        await db.add_link(TEST_USER_1, "YouTube", "https://www.youtube.com/@me")
        await db.add_link(TEST_USER_1, "Instagram", "https://instagram.com/me")
        await db.add_link(TEST_USER_1, "Telegram", "https://t.me/me")

        # VIP user with avatar and theme=8
        await db.get_or_create_user(TEST_USER_VIP_AVATAR, "TEST_vipuser", "TEST VIP User")
        await db.update_user_page(TEST_USER_VIP_AVATAR, "TEST_VIP_Page", "VIP bio")
        await db.set_vip_status(TEST_USER_VIP_AVATAR, False)  # reset first
        await db.set_vip_status(TEST_USER_VIP_AVATAR, True, days=30)
        await db.update_user_theme(TEST_USER_VIP_AVATAR, 8)
        # Create a fake avatar file
        os.makedirs(settings.AVATARS_DIR, exist_ok=True)
        avatar_path = os.path.join(settings.AVATARS_DIR, f"{TEST_USER_VIP_AVATAR}.jpg")
        # 1x1 pixel JPEG bytes
        jpeg_bytes = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46,
            0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00,
            0xFF, 0xDB, 0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06,
            0x05, 0x08, 0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C,
            0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12, 0x13, 0x0F,
            0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28,
            0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
            0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF,
            0xD9,
        ])
        with open(avatar_path, "wb") as f:
            f.write(jpeg_bytes)
        await db.update_user_avatar(TEST_USER_VIP_AVATAR, avatar_path)

        # User with no page
        await db.get_or_create_user(TEST_USER_NO_PAGE, "TEST_nopage", "TEST No Page")
        # Explicitly clear page_title in case it was set previously
        await db.update_user_page(TEST_USER_NO_PAGE, "", "")

    asyncio.run(_seed())
    yield
    # No teardown - leaving test data for repro (prefixed with TEST_)


# ────────────── /api/health ──────────────

def test_health_ok():
    r = requests.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data == {"status": "healthy"}


# ────────────── /api/stats ──────────────

def test_stats_shape_and_types():
    r = requests.get(f"{BASE_URL}/api/stats", timeout=10)
    assert r.status_code == 200
    data = r.json()
    expected_keys = {
        "total_users", "vip_users", "total_stars", "total_usd",
        "total_referrals", "total_channels", "banned", "active_today",
    }
    assert expected_keys.issubset(set(data.keys())), f"Missing keys: {expected_keys - set(data.keys())}"
    for k in expected_keys:
        assert isinstance(data[k], int), f"{k} should be int, got {type(data[k])}"
        assert data[k] >= 0


# ────────────── /api/page/{user_id} ──────────────

def test_page_nonexistent_user_404():
    r = requests.get(f"{BASE_URL}/api/page/{NONEXISTENT_USER}", timeout=10)
    assert r.status_code == 404
    assert "غير موجود" in r.text  # Arabic 'not found'


def test_page_existing_user_arabic_html():
    r = requests.get(f"{BASE_URL}/api/page/{TEST_USER_1}", timeout=10)
    assert r.status_code == 200
    body = r.text
    assert "TEST_Page1" in body
    assert 'lang="ar"' in body
    assert 'dir="rtl"' in body


def test_page_platform_icons_auto_detected():
    r = requests.get(f"{BASE_URL}/api/page/{TEST_USER_1}", timeout=10)
    assert r.status_code == 200
    body = r.text
    assert "▶️" in body  # youtube
    assert "📸" in body  # instagram
    assert "✈️" in body  # telegram


def test_page_vip_user_has_avatar_img_and_verified_badge_and_theme8():
    r = requests.get(f"{BASE_URL}/api/page/{TEST_USER_VIP_AVATAR}", timeout=10)
    assert r.status_code == 200
    body = r.text
    # avatar image tag (not letter div)
    assert 'class="avatar avatar-img"' in body
    assert f'/api/avatar/{TEST_USER_VIP_AVATAR}' in body
    # Verified badge SVG
    assert "verified" in body
    assert "<svg" in body
    # Theme 8 (Cyberpunk) CSS marker
    assert "#fcee0a" in body


# ────────────── /api/avatar/{user_id} ──────────────

def test_avatar_no_avatar_returns_404():
    r = requests.get(f"{BASE_URL}/api/avatar/{TEST_USER_1}", timeout=10)
    assert r.status_code == 404


def test_avatar_nonexistent_user_returns_404():
    r = requests.get(f"{BASE_URL}/api/avatar/{NONEXISTENT_USER}", timeout=10)
    assert r.status_code == 404


def test_avatar_exists_returns_image():
    r = requests.get(f"{BASE_URL}/api/avatar/{TEST_USER_VIP_AVATAR}", timeout=10)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/")
    assert len(r.content) > 0


# ────────────── /api/track/{user_id}/visit ──────────────

def test_track_visit_records_event_with_country():
    async def _prev_visits():
        stats = await db.get_user_stats(TEST_USER_1)
        return stats["visits"]

    before = asyncio.run(_prev_visits())
    r = requests.post(
        f"{BASE_URL}/api/track/{TEST_USER_1}/visit",
        timeout=10,
        headers={"X-Forwarded-For": "8.8.8.8"},
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    after = asyncio.run(_prev_visits())
    assert after == before + 1


def test_track_visit_nonexistent_user_404():
    r = requests.post(f"{BASE_URL}/api/track/{NONEXISTENT_USER}/visit", timeout=10)
    assert r.status_code == 404


# ────────────── /api/track/{user_id}/click/{link_id} ──────────────

def test_track_click_records_event():
    async def _first_link_and_clicks():
        links = await db.get_user_links(TEST_USER_1)
        stats = await db.get_user_stats(TEST_USER_1)
        assert links, "test user must have links"
        link_id = links[0]["id"]
        clicks = next((l["clicks"] for l in stats["links"] if l["id"] == link_id), 0)
        return link_id, clicks

    link_id, before = asyncio.run(_first_link_and_clicks())
    r = requests.post(
        f"{BASE_URL}/api/track/{TEST_USER_1}/click/{link_id}",
        timeout=10,
        headers={"X-Forwarded-For": "1.1.1.1"},
    )
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    _, after = asyncio.run(_first_link_and_clicks())
    assert after == before + 1


def test_track_click_nonexistent_user_404():
    r = requests.post(f"{BASE_URL}/api/track/{NONEXISTENT_USER}/click/1", timeout=10)
    assert r.status_code == 404
