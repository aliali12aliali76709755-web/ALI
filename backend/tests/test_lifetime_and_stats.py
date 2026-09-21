import sys
import asyncio
from pathlib import Path
import pytest
from datetime import datetime

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from bot import database as db
from bot.config import settings

def run(coro):
    return asyncio.run(coro)

@pytest.fixture(scope="module", autouse=True)
def _init():
    run(db.init_db())

def test_lifetime_vip_setting():
    uid = 888801
    async def _test():
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute("DELETE FROM users WHERE user_id=?", (uid,))
            await conn.commit()
        await db.get_or_create_user(uid, "lifetime_user", "Lifetime User")
        # Treat days >= 30000 as lifetime (e.g. 99999)
        await db.set_vip_status(uid, True, days=99999)
        user = await db.get_user(uid)
        is_vip = await db.is_user_vip(uid)
        return user, is_vip
        
    user, is_vip = run(_test())
    assert is_vip
    assert user["vip_expires"].startswith("9999-")

def test_referrer_and_device_tracking():
    uid = 888802
    async def _test():
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute("DELETE FROM users WHERE user_id=?", (uid,))
            await conn.execute("DELETE FROM stats WHERE user_id=?", (uid,))
            await conn.commit()
        await db.get_or_create_user(uid, "stats_user", "Stats User")
        # Log visits with devices and traffic source info
        await db.log_event(uid, "visit", referrer="تليجرام (Telegram)", browser="جوجل كروم (Chrome)", os="آيفون/آيباد (iOS)")
        await db.log_event(uid, "visit", referrer="واتساب (WhatsApp)", browser="سفاري (Safari)", os="أندرويد (Android)")
        
        stats = await db.get_user_stats(uid)
        return stats
        
    stats = run(_test())
    assert stats["visits"] >= 2
    
    referrers = [r["referrer"] for r in stats["referrers"]]
    assert "تليجرام (Telegram)" in referrers
    assert "واتساب (WhatsApp)" in referrers
    
    os_list = [o["os"] for o in stats["os_list"]]
    assert "آيفون/آيباد (iOS)" in os_list
    assert "أندرويد (Android)" in os_list

def test_dual_referrals_creator():
    referrer_id = 888803
    referred_id_1 = 888804
    referred_id_2 = 888805
    
    async def _test():
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute("DELETE FROM referrals WHERE referrer_id=? OR referred_id IN (?, ?)", (referrer_id, referred_id_1, referred_id_2))
            await conn.execute("DELETE FROM users WHERE user_id IN (?, ?, ?)", (referrer_id, referred_id_1, referred_id_2))
            await conn.commit()
            
        await db.get_or_create_user(referrer_id, "ref_referrer", "Referrer")
        await db.get_or_create_user(referred_id_1, "ref_referred_1", "Referred 1")
        await db.get_or_create_user(referred_id_2, "ref_referred_2", "Referred 2")
        
        # Test record referrals
        r1 = await db.record_referral(referrer_id, referred_id_1)
        r2 = await db.record_referral(referrer_id, referred_id_2)
        
        count = await db.get_referral_count(referrer_id)
        total_count = await db.get_total_referral_count(referrer_id)
        return r1, r2, count, total_count

    r1, r2, count, total_count = run(_test())
    assert r1
    assert r2
    assert count >= 2
    assert total_count >= 2
