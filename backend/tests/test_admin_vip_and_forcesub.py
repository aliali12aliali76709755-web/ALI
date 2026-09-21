import sys
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from bot import database as db
from bot.middlewares import normalize_chat_ref, check_user_subscribed
from bot.keyboards import admin_vip_durations_kb

def run(coro):
    return asyncio.run(coro)

@pytest.fixture(scope="module", autouse=True)
def _init():
    run(db.init_db())

def test_normalize_chat_ref():
    assert normalize_chat_ref("@mychannel") == "@mychannel"
    assert normalize_chat_ref("mychannel") == "@mychannel"
    assert normalize_chat_ref("https://t.me/mychannel") == "@mychannel"
    assert normalize_chat_ref("-1001234567890") == -1001234567890
    assert normalize_chat_ref("-100999") == -100999

def test_check_user_subscribed_catches_non_member():
    async def _test():
        # Setup channel in DB
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute("DELETE FROM forced_channels WHERE chat_id='@test_forcesub_ch'")
            await conn.commit()
            
        await db.add_forced_channel("@test_forcesub_ch", "Test Channel", "https://t.me/test_forcesub_ch")
        
        mock_bot = MagicMock()
        
        # 1. User status is left
        mock_member_left = MagicMock()
        mock_member_left.status = "left"
        mock_bot.get_chat_member = AsyncMock(return_value=mock_member_left)
        not_sub = await check_user_subscribed(mock_bot, 123456)
        assert any(c["chat_id"] == "@test_forcesub_ch" for c in not_sub)
        
        # 2. Telegram raises exception (e.g. USER_NOT_PARTICIPANT)
        mock_bot.get_chat_member = AsyncMock(side_effect=Exception("Bad Request: USER_NOT_PARTICIPANT"))
        not_sub_err = await check_user_subscribed(mock_bot, 123456)
        assert len(not_sub_err) > 0
        
        # 3. User is member
        mock_member_ok = MagicMock()
        mock_member_ok.status = "member"
        mock_bot.get_chat_member = AsyncMock(return_value=mock_member_ok)
        not_sub_ok = await check_user_subscribed(mock_bot, 123456)
        assert len(not_sub_ok) == 0
        
        # Cleanup
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute("DELETE FROM forced_channels WHERE chat_id='@test_forcesub_ch'")
            await conn.commit()

    run(_test())

def test_admin_vip_durations_keyboard():
    kb = admin_vip_durations_kb(987654321)
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "admin_set_vip:987654321:7" in callbacks
    assert "admin_set_vip:987654321:30" in callbacks
    assert "admin_set_vip:987654321:90" in callbacks
    assert "admin_set_vip:987654321:180" in callbacks
    assert "admin_set_vip:987654321:365" in callbacks
    assert "admin_set_vip:987654321:730" in callbacks
    assert "admin_set_vip:987654321:99999" in callbacks
    assert "admin_set_vip:987654321:0" in callbacks
