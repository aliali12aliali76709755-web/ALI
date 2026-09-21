import sys
import asyncio
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from bot import database as db
from bot.webapp_template import render_page
from bot.keyboards import countdown_menu_kb, custom_domain_menu_kb, pixels_menu_kb
from server import app

def run(coro):
    return asyncio.run(coro)

@pytest.fixture(scope="module", autouse=True)
def _init():
    run(db.init_db())

def test_render_clickable_marquee():
    user = {
        "user_id": 112233,
        "full_name": "Marquee Tester",
        "page_title": "Store Official",
        "is_vip": 1,
        "marquee_text": "خصم 70% على كافة المنتجات",
        "marquee_url": "https://store.example.com/deal",
    }
    html = render_page(user, [])
    assert "https://store.example.com/deal" in html
    assert "marquee-bar is-link" in html
    assert "خصم 70%" in html

def test_render_countdown_and_pixels():
    user = {
        "user_id": 112233,
        "full_name": "Pixel Tester",
        "page_title": "Black Friday Deals",
        "is_vip": 1,
        "countdown_title": "🔥 ينتهي العرض في:",
        "countdown_target": "2026-11-30T23:59:00",
        "meta_pixel": "123456789012",
        "tiktok_pixel": "TT-XYZ-999",
        "ga_pixel": "G-ABC1234567",
    }
    html = render_page(user, [])
    assert "countdown-widget" in html
    assert "2026-11-30T23:59:00" in html
    assert " ينتهي العرض في:" in html
    assert "123456789012" in html
    assert "TT-XYZ-999" in html
    assert "G-ABC1234567" in html
    assert "fbq('init'" in html
    assert "ttq.load" in html

def test_custom_domain_db_and_server():
    async def _test():
        uid = 887766
        await db.get_or_create_user(uid, "custom_hoster", "Domain Hoster")
        await db.update_user_page(uid, "My Custom Domain Page", "Welcome via CNAME")
        await db.update_custom_domain(uid, "bio.mybrand.com")

        # Verify DB retrieval
        found = await db.get_user_by_custom_domain("bio.mybrand.com")
        assert found is not None
        assert int(found["user_id"]) == uid

        # Test root endpoint with Host header
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/", headers={"host": "bio.mybrand.com"})
            assert res.status_code == 200
            assert "My Custom Domain Page" in res.text
            assert "Welcome via CNAME" in res.text

        # Cleanup domain
        await db.update_custom_domain(uid, None)
        assert await db.get_user_by_custom_domain("bio.mybrand.com") is None

    run(_test())

def test_new_keyboards():
    cd_kb = countdown_menu_kb(has_countdown=True)
    cbs = [btn.callback_data for row in cd_kb.inline_keyboard for btn in row]
    assert "set_countdown" in cbs
    assert "delete_countdown" in cbs

    dom_kb = custom_domain_menu_kb(has_domain=True)
    cbs_dom = [btn.callback_data for row in dom_kb.inline_keyboard for btn in row]
    assert "set_custom_domain" in cbs_dom
    assert "delete_custom_domain" in cbs_dom

    pix_kb = pixels_menu_kb(has_meta=True)
    cbs_pix = [btn.callback_data for row in pix_kb.inline_keyboard for btn in row]
    assert "set_pixel_meta" in cbs_pix
    assert "set_pixel_tiktok" in cbs_pix
    assert "set_pixel_ga" in cbs_pix
    assert "delete_pixels" in cbs_pix
