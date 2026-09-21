"""
Bot-level DB and pure-function tests.
Covers: VIP extend behavior, referral reward days, unlock_theme,
        normalize_url + DOMAIN_RE, record_referral, forced channels,
        admin sessions, is_admin_or_authorized, get_bot_stats,
        ban_user filter, DB migration idempotency.
"""
import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from bot import database as db  # noqa: E402
from bot.config import settings  # noqa: E402
from bot.admin_utils import is_admin_or_authorized  # noqa: E402
from bot.handlers.user_handlers import normalize_url, DOMAIN_RE  # noqa: E402

# Unique high IDs for tests
BASE = 991_000_000


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module", autouse=True)
def _init():
    run(db.init_db())


# ────────────── DB migration idempotency ──────────────

def test_db_migration_idempotent_and_columns_present():
    async def _check():
        await db.init_db()  # run twice safely
        await db.init_db()
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("PRAGMA table_info(users)")
            cols = [r["name"] for r in await cur.fetchall()]
            return cols
    cols = run(_check())
    for expected in ("avatar_path", "unlocked_themes", "referred_by",
                     "referral_count", "is_banned"):
        assert expected in cols, f"Missing column: {expected}"


# ────────────── VIP extend behavior ──────────────

def test_set_vip_status_extends_existing_subscription():
    uid = BASE + 10

    async def _flow():
        await db.get_or_create_user(uid, "TEST_vipext", "TEST VIP Ext")
        # reset first
        await db.set_vip_status(uid, False)
        await db.set_vip_status(uid, True, days=30)
        u1 = await db.get_user(uid)
        exp1 = datetime.fromisoformat(u1["vip_expires"])
        # Second call should extend by 30 more days (not reset)
        await db.set_vip_status(uid, True, days=30)
        u2 = await db.get_user(uid)
        exp2 = datetime.fromisoformat(u2["vip_expires"])
        return exp1, exp2

    exp1, exp2 = run(_flow())
    delta = (exp2 - exp1).total_seconds()
    # Should be about 30 days ≈ 2_592_000 seconds
    assert 29 * 86400 <= delta <= 31 * 86400, f"delta was {delta}s, expected ≈ 30 days"


def test_set_vip_status_false_clears_subscription():
    uid = BASE + 11

    async def _flow():
        await db.get_or_create_user(uid, "TEST_vipoff", "TEST VIP Off")
        await db.set_vip_status(uid, True, days=10)
        assert await db.is_user_vip(uid)
        await db.set_vip_status(uid, False)
        u = await db.get_user(uid)
        return u

    u = run(_flow())
    assert u["is_vip"] == 0
    assert u["vip_expires"] is None
    assert u["theme"] == 0


# ────────────── Referral reward days configured to 30 ──────────────

def test_referral_reward_days_is_30():
    assert settings.REFERRAL_REWARD_DAYS == 30


# ────────────── Unlock theme ──────────────

def test_unlock_theme_adds_and_get_returns_list():
    uid = BASE + 20

    async def _flow():
        await db.get_or_create_user(uid, "TEST_theme", "TEST Theme")
        await db.unlock_theme(uid, 7)
        await db.unlock_theme(uid, 8)
        # duplicate should be idempotent
        await db.unlock_theme(uid, 7)
        return await db.get_unlocked_themes(uid)

    unlocked = run(_flow())
    assert isinstance(unlocked, list)
    assert 7 in unlocked and 8 in unlocked
    assert unlocked.count(7) == 1


# ────────────── normalize_url / DOMAIN_RE ──────────────

def test_normalize_url_adds_https():
    assert normalize_url("instagram.com/x") == "https://instagram.com/x"


def test_normalize_url_keeps_https():
    assert normalize_url("https://example.com/a") == "https://example.com/a"


def test_normalize_url_keeps_http():
    assert normalize_url("http://foo.bar") == "http://foo.bar"


def test_normalize_url_rejects_non_url():
    assert normalize_url("just some text") == ""
    assert normalize_url("") == ""


def test_domain_re_matches_bare_domain():
    assert DOMAIN_RE.match("instagram.com/user") is not None
    assert DOMAIN_RE.match("t.me/name") is not None
    assert DOMAIN_RE.match("plain text") is None


def test_pipe_format_parsed_correctly():
    # Simulate user_handlers pipe logic manually
    text = "انستقرام | instagram.com/me"
    assert "|" in text
    parts = [p.strip() for p in text.split("|", 1)]
    assert len(parts) == 2
    name, url_raw = parts
    normalized = normalize_url(url_raw)
    assert name == "انستقرام"
    assert normalized == "https://instagram.com/me"


# ────────────── Referrals ──────────────

def test_record_referral_success_and_increments_counter():
    referrer = BASE + 30
    referred = BASE + 31

    async def _flow():
        await db.get_or_create_user(referrer, "TEST_ref_r", "TEST Referrer")
        await db.get_or_create_user(referred, "TEST_ref_e", "TEST Referred")
        # Cleanup any stale referral rows from previous runs
        import aiosqlite as _a
        async with _a.connect(db.DB_PATH) as conn:
            await conn.execute("DELETE FROM referrals WHERE referred_id=?", (referred,))
            await conn.commit()
        # reset count
        await db.reset_referral_progress(referrer)
        ok = await db.record_referral(referrer, referred)
        return ok, await db.get_referral_count(referrer)

    ok, count = run(_flow())
    assert ok is True
    assert count == 1


def test_record_referral_prevents_duplicate():
    referrer = BASE + 30
    referred = BASE + 31

    async def _flow():
        return await db.record_referral(referrer, referred)

    assert run(_flow()) is False


def test_record_referral_prevents_self_referral():
    uid = BASE + 32

    async def _flow():
        await db.get_or_create_user(uid, "TEST_self", "TEST Self")
        return await db.record_referral(uid, uid)

    assert run(_flow()) is False


def test_reset_referral_progress_zeros_counter():
    referrer = BASE + 30

    async def _flow():
        await db.reset_referral_progress(referrer)
        return await db.get_referral_count(referrer)

    assert run(_flow()) == 0


# ────────────── Forced channels ──────────────

def test_forced_channels_add_list_remove():
    async def _flow():
        chat_id = "-100999TEST"
        # cleanup if present
        await db.remove_forced_channel(chat_id)
        ok1 = await db.add_forced_channel(chat_id, "TEST_channel", "https://t.me/TEST_channel")
        # duplicate should fail
        ok_dup = await db.add_forced_channel(chat_id, "TEST_channel", "https://t.me/x")
        channels = await db.list_forced_channels()
        titles = [c["title"] for c in channels]
        removed = await db.remove_forced_channel(chat_id)
        removed_again = await db.remove_forced_channel(chat_id)
        return ok1, ok_dup, "TEST_channel" in titles, removed, removed_again

    ok1, ok_dup, in_list, removed, removed_again = run(_flow())
    assert ok1 is True
    assert ok_dup is False
    assert in_list is True
    assert removed is True
    assert removed_again is False


# ────────────── Admin utilities ──────────────

def test_is_admin_or_authorized_primary_admin():
    assert run(is_admin_or_authorized(settings.ADMIN_ID, "someuser")) is True


def test_is_admin_or_authorized_secondary_username():
    # SECONDARY_ADMIN_USERNAME=d91ik
    assert run(is_admin_or_authorized(123, "d91ik")) is True
    assert run(is_admin_or_authorized(123, "@D91IK")) is True  # case-insensitive


def test_is_admin_or_authorized_rejects_random_user():
    assert run(is_admin_or_authorized(BASE + 40, "random_user")) is False


def test_admin_session_grant_check_revoke():
    uid = BASE + 41

    async def _flow():
        await db.revoke_admin_session(uid)
        has0 = await db.has_admin_session(uid)
        await db.grant_admin_session(uid)
        has1 = await db.has_admin_session(uid)
        auth = await is_admin_or_authorized(uid, "")
        await db.revoke_admin_session(uid)
        has2 = await db.has_admin_session(uid)
        return has0, has1, auth, has2

    h0, h1, auth, h2 = run(_flow())
    assert h0 is False
    assert h1 is True
    assert auth is True
    assert h2 is False


# ────────────── get_bot_stats keys ──────────────

def test_get_bot_stats_returns_all_keys():
    s = run(db.get_bot_stats())
    for k in ("total_users", "vip_users", "total_stars", "total_usd",
              "total_referrals", "total_channels", "banned", "active_today"):
        assert k in s
        assert isinstance(s[k], int)


# ────────────── ban_user filters broadcast list ──────────────

def test_banned_user_excluded_from_get_all_user_ids():
    uid = BASE + 50

    async def _flow():
        await db.get_or_create_user(uid, "TEST_ban", "TEST Ban")
        await db.ban_user(uid, False)
        ids_before = await db.get_all_user_ids()
        await db.ban_user(uid, True)
        ids_after = await db.get_all_user_ids()
        await db.ban_user(uid, False)  # cleanup
        return ids_before, ids_after

    before, after = run(_flow())
    assert uid in before
    assert uid not in after
