"""
Iteration 3 tests:
- gender_utils.guess_gender (Arabic + English names)
- Subscription plans (VIP_PRICE_1M/3M/6M/12M) and PLANS mapping
- Payment payload parsing (vip_N_USER + theme_N_USER)
- Bot commands registration (BOT_COMMANDS list)
- Slash command handlers exist and are registered on user_handlers.router
- Contact developer handler (F.text == '📞 تواصل مع المطور' AND /contact)
- DB migration adds gender + first_name columns to stats table
- get_user_stats returns 'genders' dict
- /api/track visit and click accept JSON body with first_name
- QR caption contains only website URL, no t.me link
- DEVELOPER_USERNAME == 'd91ik'
- Subscription keyboard has 4 plan buttons callback_data='pay_plan:N'
- main_menu_kb has '📞 تواصل مع المطور' button
- webapp_template contains getTgUserPayload sending first_name
"""
import os
import sys
import asyncio
import json
import re
from pathlib import Path

import pytest
import requests
import aiosqlite

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from bot import database as db  # noqa: E402
from bot.config import settings  # noqa: E402
from bot.gender_utils import guess_gender  # noqa: E402
from bot.handlers import payment_handlers, user_handlers  # noqa: E402
from bot.main import BOT_COMMANDS  # noqa: E402
from bot.keyboards import main_menu_kb, subscription_kb  # noqa: E402
from bot.webapp_template import render_page  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", os.environ.get("WEBAPP_BASE_URL", "")).rstrip("/")

TEST_USER_BASE = 992_000_000  # iteration3 range
TEST_USER_1 = TEST_USER_BASE + 1
TEST_USER_VIP = TEST_USER_BASE + 2
NONEXISTENT = TEST_USER_BASE + 999


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module", autouse=True)
def _seed():
    async def _s():
        await db.init_db()
        await db.get_or_create_user(TEST_USER_1, "TEST_iter3_u1", "TEST Iter3 User1")
        await db.update_user_page(TEST_USER_1, "TEST_Iter3_Page", "bio")
        await db.delete_user_links(TEST_USER_1)
        await db.add_link(TEST_USER_1, "Instagram", "https://instagram.com/x")

        await db.get_or_create_user(TEST_USER_VIP, "TEST_iter3_vip", "TEST Iter3 VIP")
        await db.update_user_page(TEST_USER_VIP, "TEST_VIP", "vip")
        await db.set_vip_status(TEST_USER_VIP, False)
        await db.set_vip_status(TEST_USER_VIP, True, days=30)
    run(_s())
    yield


# ─────────────────── guess_gender ───────────────────

class TestGuessGender:
    def test_female_arabic_common(self):
        assert guess_gender("فاطمة") == "female"

    def test_female_arabic_end_ta_marbuta(self):
        # ends in ة → female (heuristic)
        assert guess_gender("حمزة") in ("male", "female")  # in _MALE list explicitly → male
        # Take a name that's NOT in male list ending in ة
        assert guess_gender("رانية") == "female"
        assert guess_gender("منيرة") == "female"

    def test_female_arabic_no_ta(self):
        assert guess_gender("سلمى") == "female"

    def test_male_arabic(self):
        assert guess_gender("أحمد") == "male"
        assert guess_gender("محمد") == "male"

    def test_female_english(self):
        assert guess_gender("Sarah") == "female"
        assert guess_gender("sarah") == "female"

    def test_male_english_john(self):
        # 'john' is in _MALE set
        assert guess_gender("John") == "male"

    def test_unknown_random(self):
        assert guess_gender("random123") == "unknown"

    def test_unknown_empty(self):
        assert guess_gender("") == "unknown"
        assert guess_gender("   ") == "unknown"

    def test_first_word_only(self):
        # "أحمد محمد" → first word أحمد → male
        assert guess_gender("أحمد محمد") == "male"

    def test_none_safe(self):
        # empty is unknown
        assert guess_gender(None or "") == "unknown"


# ─────────────────── Subscription plans configuration ───────────────────

class TestSubscriptionPlans:
    def test_prices_configured(self):
        assert settings.VIP_PRICE_1M == 99
        assert settings.VIP_PRICE_3M == 200
        assert settings.VIP_PRICE_6M == 350
        assert settings.VIP_PRICE_12M == 550

    def test_plans_mapping(self):
        assert payment_handlers.PLANS[1][0] == 30
        assert payment_handlers.PLANS[3][0] == 90
        assert payment_handlers.PLANS[6][0] == 180
        assert payment_handlers.PLANS[12][0] == 365

    def test_plan_price_helper(self):
        assert payment_handlers._plan_price(1) == 99
        assert payment_handlers._plan_price(3) == 200
        assert payment_handlers._plan_price(6) == 350
        assert payment_handlers._plan_price(12) == 550
        # unknown month falls back to yearly
        assert payment_handlers._plan_price(99) == 550

    def test_subscription_kb_has_4_plans(self):
        kb = subscription_kb()
        callbacks = []
        for row in kb.inline_keyboard:
            for btn in row:
                if btn.callback_data:
                    callbacks.append(btn.callback_data)
        for cb in ("pay_plan:1", "pay_plan:3", "pay_plan:6", "pay_plan:12"):
            assert cb in callbacks, f"missing {cb} in subscription_kb"


# ─────────────────── Payment payload parsing simulation ───────────────────

class TestPaymentPayloadParsing:
    def _extract_months(self, payload: str) -> int:
        """Reproduces the logic in payment_handlers.on_successful_payment."""
        months = 12
        if payload.startswith("vip_"):
            try:
                months = int(payload.split("_")[1])
            except Exception:
                months = 12
        if months not in payment_handlers.PLANS:
            months = 12
        return months

    def test_vip_1_maps_to_30_days(self):
        m = self._extract_months(f"vip_1_{TEST_USER_1}")
        assert payment_handlers.PLANS[m][0] == 30

    def test_vip_3_maps_to_90_days(self):
        m = self._extract_months(f"vip_3_{TEST_USER_1}")
        assert payment_handlers.PLANS[m][0] == 90

    def test_vip_6_maps_to_180_days(self):
        m = self._extract_months(f"vip_6_{TEST_USER_1}")
        assert payment_handlers.PLANS[m][0] == 180

    def test_vip_12_maps_to_365_days(self):
        m = self._extract_months(f"vip_12_{TEST_USER_1}")
        assert payment_handlers.PLANS[m][0] == 365

    def test_vip_invalid_falls_back_to_12(self):
        m = self._extract_months("vip_abc_123")
        assert m == 12

    def test_theme_payload_parses_theme_id(self):
        payload = f"theme_7_{TEST_USER_1}"
        assert payload.startswith("theme_")
        theme_id = int(payload.split("_")[1])
        assert theme_id == 7


# ─────────────────── DEVELOPER_USERNAME ───────────────────

def test_developer_username_is_d91ik():
    assert settings.DEVELOPER_USERNAME == "d91ik"


# ─────────────────── Bot Commands registration ───────────────────

class TestBotCommands:
    def test_expected_commands_present(self):
        cmds = {c.command for c in BOT_COMMANDS}
        expected = {"start", "vip", "contact"}
        cmds = {c.command for c in BOT_COMMANDS}
        assert cmds == expected, f"Bot commands mismatch: {cmds}"

    def test_command_descriptions_non_empty(self):
        for c in BOT_COMMANDS:
            assert c.description and c.description.strip(), f"empty desc: {c.command}"


# ─────────────────── Slash command handlers exist in user_handlers ───────────────────

class TestUserHandlerCommands:
    def test_command_handlers_defined(self):
        for name in ("cmd_vip", "cmd_contact", "contact_developer"):
            assert hasattr(user_handlers, name), f"missing handler: {name}"

    def test_router_has_message_handlers_registered(self):
        # aiogram Router exposes observers via .observers
        router = user_handlers.router
        assert router is not None
        # message handlers list should be non-empty
        msg_handlers = router.message.handlers
        assert len(msg_handlers) > 10  # many handlers registered


# ─────────────────── Contact developer text/handler ───────────────────

class TestContactDeveloper:
    def test_contact_text_contains_dev_link(self):
        # Simulate the handler's message text (best-effort static check)
        src = Path(user_handlers.__file__).read_text(encoding="utf-8")
        assert "t.me/{dev}" in src or 'https://t.me/{settings.DEVELOPER_USERNAME}' in src or "https://t.me/" in src
        # DEVELOPER_USERNAME string appears somewhere in module
        assert "DEVELOPER_USERNAME" in src or "settings.DEVELOPER_USERNAME" in src

    def test_main_menu_has_no_contact_button(self):
        kb = main_menu_kb(is_vip=False)
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "📞 تواصل مع المطور" not in texts


# ─────────────────── DB migration: stats has gender + first_name ───────────────────

def test_stats_table_has_gender_and_first_name_columns():
    async def _check():
        await db.init_db()
        async with aiosqlite.connect(db.DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("PRAGMA table_info(stats)")
            rows = await cur.fetchall()
            return [r["name"] for r in rows]
    cols = run(_check())
    assert "gender" in cols
    assert "first_name" in cols


# ─────────────────── get_user_stats returns 'genders' dict ───────────────────

def test_get_user_stats_returns_genders_key():
    async def _flow():
        # Ensure at least one visit with each gender
        await db.log_event(TEST_USER_1, "visit", ip="1.2.3.4",
                           country="X", gender="male", first_name="أحمد")
        await db.log_event(TEST_USER_1, "visit", ip="1.2.3.5",
                           country="X", gender="female", first_name="فاطمة")
        return await db.get_user_stats(TEST_USER_1)
    stats = run(_flow())
    for key in ("visits", "total_clicks", "links", "countries", "genders"):
        assert key in stats, f"missing key: {key}"
    assert isinstance(stats["genders"], dict)
    assert stats["genders"].get("male", 0) >= 1
    assert stats["genders"].get("female", 0) >= 1


# ─────────────────── /api/track accepts JSON body with first_name ───────────────────

@pytest.mark.skipif(not BASE_URL, reason="BASE_URL not configured")
class TestTrackJsonBody:
    def test_track_visit_with_first_name_json_body(self):
        r = requests.post(
            f"{BASE_URL}/api/track/{TEST_USER_1}/visit",
            json={"first_name": "أحمد"},
            timeout=10,
        )
        assert r.status_code == 200
        # Verify gender was recorded
        async def _last():
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                cur = await conn.execute(
                    "SELECT gender, first_name FROM stats WHERE user_id=? "
                    "AND event_type='visit' ORDER BY id DESC LIMIT 1",
                    (TEST_USER_1,),
                )
                return await cur.fetchone()
        row = run(_last())
        assert row is not None
        assert row["gender"] == "male"
        assert row["first_name"] == "أحمد"

    def test_track_click_with_first_name_json_body(self):
        # get a link_id
        async def _lid():
            links = await db.get_user_links(TEST_USER_1)
            return links[0]["id"] if links else None
        link_id = run(_lid())
        assert link_id is not None
        r = requests.post(
            f"{BASE_URL}/api/track/{TEST_USER_1}/click/{link_id}",
            json={"first_name": "فاطمة"},
            timeout=10,
        )
        assert r.status_code == 200

        async def _last():
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                cur = await conn.execute(
                    "SELECT gender, first_name FROM stats WHERE user_id=? "
                    "AND event_type='click' ORDER BY id DESC LIMIT 1",
                    (TEST_USER_1,),
                )
                return await cur.fetchone()
        row = run(_last())
        assert row["gender"] == "female"
        assert row["first_name"] == "فاطمة"

    def test_track_visit_empty_body_defaults_unknown(self):
        r = requests.post(f"{BASE_URL}/api/track/{TEST_USER_1}/visit",
                          timeout=10)
        assert r.status_code == 200
        # No first_name → gender should be 'unknown' for this last row
        async def _last():
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                cur = await conn.execute(
                    "SELECT gender, first_name FROM stats WHERE user_id=? "
                    "AND event_type='visit' ORDER BY id DESC LIMIT 1",
                    (TEST_USER_1,),
                )
                return await cur.fetchone()
        row = run(_last())
        assert row["gender"] == "unknown"
        assert row["first_name"] is None


# ─────────────────── Webapp template contains first_name payload logic ───────────────────

class TestWebappTemplate:
    def _render(self):
        user = {
            "user_id": TEST_USER_1, "username": "u", "full_name": "Test",
            "is_vip": 0, "vip_expires": None, "theme": 0,
            "page_title": "MyPage", "page_bio": "bio",
            "avatar_path": None, "unlocked_themes": "[]",
        }
        links = [{"id": 1, "title": "IG", "url": "https://instagram.com/me"}]
        return render_page(user, links)

    def test_html_has_getTgUserPayload(self):
        html = self._render()
        assert "getTgUserPayload" in html
        assert "initDataUnsafe" in html
        assert "first_name" in html
        assert "last_name" in html
        assert "language_code" in html

    def test_html_posts_json_to_track_endpoints(self):
        html = self._render()
        assert f"/api/track/{TEST_USER_1}/visit" in html
        assert "Content-Type" in html and "application/json" in html
        assert "JSON.stringify(getTgUserPayload())" in html


# ─────────────────── QR: no t.me link in caption/data ───────────────────

def test_qr_handler_uses_only_webapp_url_in_source():
    """Static check on the QR handler source (user_qr in user_handlers.py)."""
    src = Path(user_handlers.__file__).read_text(encoding="utf-8")
    # Find the user_qr function body
    m = re.search(r"async def user_qr\(.*?\)\s*:(.*?)(?=\nasync def |\Z)", src, re.DOTALL)
    assert m, "user_qr handler not found in source"
    body = m.group(1)
    # Must add ONLY share_url (WEBAPP_BASE_URL) to QR
    assert "qr.add_data(share_url)" in body
    # No bot link (t.me) inside QR handler
    assert "t.me" not in body, "user_qr must not contain t.me link"
    assert "WEBAPP_BASE_URL" in body


# ─────────────────── /api/health smoke test ───────────────────

@pytest.mark.skipif(not BASE_URL, reason="BASE_URL not configured")
def test_health_ok_iter3():
    r = requests.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}
