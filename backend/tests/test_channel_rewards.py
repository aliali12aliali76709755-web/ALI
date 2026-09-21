"""
Unit tests for force channel subscription rewards.
"""
import sys
import asyncio
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from bot import database as db
from bot.config import settings

BASE = 993_000_000


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module", autouse=True)
def _init():
    run(db.init_db())


def test_claimed_join_reward_column_present():
    async def _check():
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("PRAGMA table_info(users)")
            cols = [r["name"] for r in await cur.fetchall()]
            return cols
    cols = run(_check())
    assert "claimed_join_reward" in cols, "claimed_join_reward column is missing in users table"


def test_channel_join_reward_defaults_and_helpers():
    uid = BASE + 10

    async def _flow():
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute("DELETE FROM users WHERE user_id=?", (uid,))
            await conn.commit()
            
        await db.get_or_create_user(uid, "test_channel_ch", "Channel Tester")
        # Check initial state
        has_claimed = await db.has_claimed_join_reward(uid)
        assert not has_claimed

        # Mark as claimed
        await db.mark_join_reward_claimed(uid)
        has_claimed_after = await db.has_claimed_join_reward(uid)
        return has_claimed_after

    has_claimed_after = run(_flow())
    assert has_claimed_after


def test_settings_channel_reward_configured():
    assert settings.CHANNEL_JOIN_REWARD_DAYS == 30
    assert settings.SPONSOR_CHANNELS == ["@d91ik"]
