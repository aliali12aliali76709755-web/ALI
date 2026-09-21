"""
إدارة قاعدة بيانات SQLite (باستخدام aiosqlite للعمليات غير المتزامنة)
"""
import os
import aiosqlite
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from bot.config import settings

DB_PATH = settings.DB_PATH


async def init_db() -> None:
    """إنشاء الجداول الأساسية إذا لم تكن موجودة"""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                username      TEXT,
                full_name     TEXT,
                is_vip        INTEGER NOT NULL DEFAULT 0,
                vip_expires   TEXT,
                theme         INTEGER NOT NULL DEFAULT 0,
                page_title    TEXT,
                page_bio      TEXT,
                referred_by   INTEGER,
                referral_count INTEGER NOT NULL DEFAULT 0,
                is_banned     INTEGER NOT NULL DEFAULT 0,
                avatar_path   TEXT,
                unlocked_themes TEXT NOT NULL DEFAULT '[]',
                accent_color  TEXT,
                button_style  TEXT DEFAULT 'rounded',
                show_badge    INTEGER NOT NULL DEFAULT 1,
                claimed_join_reward INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT NOT NULL
            )
            """
        )
        # الترحيل: أضف الأعمدة الجديدة إذا لم تكن موجودة
        for ddl in [
            "ALTER TABLE users ADD COLUMN referred_by INTEGER",
            "ALTER TABLE users ADD COLUMN referral_count INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN is_banned INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN avatar_path TEXT",
            "ALTER TABLE users ADD COLUMN unlocked_themes TEXT NOT NULL DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN accent_color TEXT",
            "ALTER TABLE users ADD COLUMN button_style TEXT DEFAULT 'rounded'",
            "ALTER TABLE users ADD COLUMN show_badge INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN claimed_join_reward INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN music_url TEXT",
            "ALTER TABLE users ADD COLUMN music_title TEXT",
            "ALTER TABLE users ADD COLUMN bg_effect TEXT DEFAULT 'none'",
            "ALTER TABLE users ADD COLUMN marquee_text TEXT",
            "ALTER TABLE users ADD COLUMN marquee_url TEXT",
            "ALTER TABLE users ADD COLUMN font_family TEXT DEFAULT 'Tajawal'",
            "ALTER TABLE users ADD COLUMN countdown_title TEXT",
            "ALTER TABLE users ADD COLUMN countdown_target TEXT",
            "ALTER TABLE users ADD COLUMN custom_domain TEXT",
            "ALTER TABLE users ADD COLUMN meta_pixel TEXT",
            "ALTER TABLE users ADD COLUMN tiktok_pixel TEXT",
            "ALTER TABLE users ADD COLUMN ga_pixel TEXT",
            "ALTER TABLE users ADD COLUMN social_links TEXT DEFAULT '{}'",
        ]:
            try:
                await db.execute(ddl)
            except Exception:
                pass

        try:
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_custom_domain ON users(custom_domain)")
        except Exception:
            pass

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                reviewer_name TEXT NOT NULL,
                rating        INTEGER NOT NULL,
                comment       TEXT NOT NULL,
                is_approved   INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT NOT NULL
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                title          TEXT NOT NULL,
                url            TEXT NOT NULL,
                position       INTEGER NOT NULL DEFAULT 0,
                subtitle       TEXT,
                thumbnail_url  TEXT,
                is_banner      INTEGER NOT NULL DEFAULT 0,
                section_header TEXT,
                is_featured    INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        for ddl in [
            "ALTER TABLE links ADD COLUMN subtitle TEXT",
            "ALTER TABLE links ADD COLUMN thumbnail_url TEXT",
            "ALTER TABLE links ADD COLUMN is_banner INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE links ADD COLUMN section_header TEXT",
            "ALTER TABLE links ADD COLUMN is_featured INTEGER NOT NULL DEFAULT 0",
        ]:
            try:
                await db.execute(ddl)
            except Exception:
                pass
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS stats (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                link_id    INTEGER,
                event_type TEXT NOT NULL,
                country    TEXT,
                ip         TEXT,
                gender     TEXT,
                first_name TEXT,
                referrer   TEXT,
                browser    TEXT,
                os         TEXT,
                timestamp  TEXT NOT NULL
            )
            """
        )
        for ddl in [
            "ALTER TABLE stats ADD COLUMN country TEXT",
            "ALTER TABLE stats ADD COLUMN ip TEXT",
            "ALTER TABLE stats ADD COLUMN gender TEXT",
            "ALTER TABLE stats ADD COLUMN first_name TEXT",
            "ALTER TABLE stats ADD COLUMN referrer TEXT",
            "ALTER TABLE stats ADD COLUMN browser TEXT",
            "ALTER TABLE stats ADD COLUMN os TEXT",
        ]:
            try:
                await db.execute(ddl)
            except Exception:
                pass

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                amount       INTEGER NOT NULL,
                currency     TEXT NOT NULL,
                status       TEXT NOT NULL,
                telegram_payment_charge_id TEXT,
                purpose      TEXT,
                created_at   TEXT NOT NULL
            )
            """
        )
        try:
            await db.execute("ALTER TABLE payments ADD COLUMN purpose TEXT")
        except Exception:
            pass

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS referrals (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id  INTEGER NOT NULL,
                referred_id  INTEGER NOT NULL UNIQUE,
                created_at   TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS forced_channels (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id        TEXT NOT NULL UNIQUE,
                title          TEXT,
                invite_url     TEXT NOT NULL,
                created_at     TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_sessions (
                user_id      INTEGER PRIMARY KEY,
                authorized_at TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_referrals (
                referred_id  INTEGER PRIMARY KEY,
                referrer_id  INTEGER NOT NULL,
                created_at   TEXT NOT NULL
            )
            """
        )
        
        # Schema modifications for show_reviews and page_slug
        for ddl in [
            "ALTER TABLE users ADD COLUMN show_reviews INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE links ADD COLUMN page_slug TEXT",
            "ALTER TABLE reviews ADD COLUMN page_slug TEXT",
        ]:
            try:
                await db.execute(ddl)
            except Exception:
                pass

        # Sub-pages table for VIP multiple landing pages
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS sub_pages (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                slug           TEXT NOT NULL UNIQUE,
                page_title     TEXT,
                page_bio       TEXT,
                theme          INTEGER NOT NULL DEFAULT 0,
                accent_color   TEXT,
                button_style   TEXT DEFAULT 'rounded',
                show_badge     INTEGER NOT NULL DEFAULT 1,
                badge_type     TEXT DEFAULT 'blue',
                show_reviews   INTEGER NOT NULL DEFAULT 1,
                social_links   TEXT DEFAULT '{}',
                music_url      TEXT,
                music_title    TEXT,
                bg_effect      TEXT DEFAULT 'none',
                marquee_text   TEXT,
                marquee_url    TEXT,
                font_family    TEXT DEFAULT 'Tajawal',
                countdown_title TEXT,
                countdown_target TEXT,
                custom_domain  TEXT,
                meta_pixel     TEXT,
                tiktok_pixel   TEXT,
                ga_pixel       TEXT,
                created_at     TEXT NOT NULL
            )
            """
        )
        try:
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_sub_pages_custom_domain ON sub_pages(custom_domain)")
        except Exception:
            pass

        await db.commit()


# ─────────────────────────────── دوال المستخدمين ───────────────────────────────

async def get_or_create_user(user_id: int, username: str, full_name: str) -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET username=?, full_name=? WHERE user_id=?",
                (username, full_name, user_id),
            )
            await db.commit()
            return dict(row)

        now_iso = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO users (user_id, username, full_name, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, now_iso),
        )
        await db.commit()
        cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row)


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def is_user_vip(user_id: int) -> bool:
    return True


async def set_vip_status(user_id: int, is_vip: bool, days: int = None) -> None:
    """
    عند is_vip=True: يضيف عدد الأيام (days) لأي اشتراك فعال، أو ينشئ اشتراكاً جديداً.
    عند is_vip=False: يلغي الاشتراك.
    """
    days = days if days is not None else settings.VIP_DURATION_DAYS
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if is_vip:
            cur = await db.execute("SELECT vip_expires FROM users WHERE user_id=?", (user_id,))
            row = await cur.fetchone()
            now = datetime.now(timezone.utc)
            current_expiry = None
            if row and row["vip_expires"]:
                try:
                    current_expiry = datetime.fromisoformat(row["vip_expires"])
                except Exception:
                    current_expiry = None
            base = current_expiry if (current_expiry and current_expiry > now) else now
            if days >= 30000:
                new_expiry = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc).isoformat()
            else:
                new_expiry = (base + timedelta(days=days)).isoformat()
            await db.execute(
                "UPDATE users SET is_vip=1, vip_expires=? WHERE user_id=?",
                (new_expiry, user_id),
            )
        else:
            await db.execute(
                "UPDATE users SET is_vip=0, vip_expires=NULL, theme=0 WHERE user_id=?",
                (user_id,),
            )
        await db.commit()


async def update_user_page(user_id: int, page_title: str, page_bio: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET page_title=?, page_bio=? WHERE user_id=?",
            (page_title, page_bio, user_id),
        )
        await db.commit()


async def update_user_theme(user_id: int, theme: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET theme=? WHERE user_id=?", (theme, user_id))
        await db.commit()


async def update_user_avatar(user_id: int, avatar_path: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET avatar_path=? WHERE user_id=?", (avatar_path, user_id))
        await db.commit()


async def update_accent_color(user_id: int, color: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET accent_color=? WHERE user_id=?", (color, user_id))
        await db.commit()


async def update_button_style(user_id: int, style: str) -> None:
    if style not in ("rounded", "pill", "square", "tab"):
        style = "rounded"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET button_style=? WHERE user_id=?", (style, user_id))
        await db.commit()


async def update_show_badge(user_id: int, show_badge: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET show_badge=? WHERE user_id=?", (show_badge, user_id))
        await db.commit()


async def update_show_reviews(user_id: int, show_reviews: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET show_reviews=? WHERE user_id=?", (show_reviews, user_id))
        await db.commit()


async def has_claimed_join_reward(user_id: int) -> bool:
    user = await get_user(user_id)
    return bool(user and user.get("claimed_join_reward"))


async def mark_join_reward_claimed(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET claimed_join_reward=1 WHERE user_id=?", (user_id,))
        await db.commit()


async def get_all_user_ids() -> List[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE is_banned=0")
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def ban_user(user_id: int, banned: bool = True) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=? WHERE user_id=?", (1 if banned else 0, user_id))
        await db.commit()


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE lower(username)=?", (username.lower().lstrip("@"),))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_unlocked_themes(user_id: int) -> List[int]:
    user = await get_user(user_id)
    if not user:
        return []
    try:
        return json.loads(user.get("unlocked_themes") or "[]")
    except Exception:
        return []


async def unlock_theme(user_id: int, theme_id: int) -> None:
    unlocked = await get_unlocked_themes(user_id)
    if theme_id in unlocked:
        return
    unlocked.append(theme_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET unlocked_themes=? WHERE user_id=?",
            (json.dumps(unlocked), user_id),
        )
        await db.commit()


# ─────────────────────────────── دوال الروابط ───────────────────────────────

async def add_link(user_id: int, title: str, url: str, page_slug: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        if page_slug:
            cur = await db.execute(
                "SELECT COALESCE(MAX(position), 0) FROM links WHERE page_slug=?", (page_slug,)
            )
        else:
            cur = await db.execute(
                "SELECT COALESCE(MAX(position), 0) FROM links WHERE user_id=? AND page_slug IS NULL", (user_id,)
            )
        (max_pos,) = await cur.fetchone()
        cur = await db.execute(
            "INSERT INTO links (user_id, title, url, position, page_slug) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, url, (max_pos or 0) + 1, page_slug),
        )
        await db.commit()
        return cur.lastrowid


async def get_user_links(user_id: int, page_slug: str = None) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if page_slug:
            cur = await db.execute(
                "SELECT * FROM links WHERE page_slug=? ORDER BY position ASC", (page_slug,)
            )
        else:
            cur = await db.execute(
                "SELECT * FROM links WHERE user_id=? AND page_slug IS NULL ORDER BY position ASC", (user_id,)
            )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def count_user_links(user_id: int, page_slug: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        if page_slug:
            cur = await db.execute("SELECT COUNT(*) FROM links WHERE page_slug=?", (page_slug,))
        else:
            cur = await db.execute("SELECT COUNT(*) FROM links WHERE user_id=? AND page_slug IS NULL", (user_id,))
        (n,) = await cur.fetchone()
        return n


async def delete_user_links(user_id: int, page_slug: str = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        if page_slug:
            await db.execute("DELETE FROM links WHERE page_slug=?", (page_slug,))
        else:
            await db.execute("DELETE FROM links WHERE user_id=? AND page_slug IS NULL", (user_id,))
        await db.commit()


async def get_link(link_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM links WHERE id=?", (link_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def delete_link(link_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM links WHERE id=?", (link_id,))
        await db.commit()


async def update_link_title(link_id: int, title: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE links SET title=? WHERE id=?", (title, link_id))
        await db.commit()


async def update_link_url(link_id: int, url: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE links SET url=? WHERE id=?", (url, link_id))
        await db.commit()


# ─────────────────────────────── دوال الإحصائيات ───────────────────────────────

async def log_event(user_id: int, event_type: str, link_id: Optional[int] = None,
                    ip: Optional[str] = None, country: Optional[str] = None,
                    gender: Optional[str] = None, first_name: Optional[str] = None,
                    referrer: Optional[str] = None, browser: Optional[str] = None,
                    os: Optional[str] = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO stats (user_id, link_id, event_type, ip, country, gender, first_name, referrer, browser, os, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, link_id, event_type, ip, country, gender, first_name, referrer, browser, os,
             datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def get_user_stats(user_id: int) -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT COUNT(*) as c FROM stats WHERE user_id=? AND event_type='visit'",
            (user_id,),
        )
        visits = (await cur.fetchone())["c"]

        cur = await db.execute(
            """
            SELECT l.id, l.title, l.url, COUNT(s.id) as clicks
            FROM links l
            LEFT JOIN stats s ON s.link_id = l.id AND s.event_type='click'
            WHERE l.user_id = ?
            GROUP BY l.id
            ORDER BY l.position ASC
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
        link_stats = [dict(r) for r in rows]

        total_clicks = sum(r["clicks"] for r in link_stats)

        # إحصائيات جغرافية للزيارات
        cur = await db.execute(
            """SELECT COALESCE(country, 'غير معروف') as country, COUNT(*) as c
               FROM stats WHERE user_id=? AND event_type='visit'
               GROUP BY country ORDER BY c DESC LIMIT 10""",
            (user_id,),
        )
        geo_rows = await cur.fetchall()
        countries = [dict(r) for r in geo_rows]

        # توزيع الجنس
        cur = await db.execute(
            """SELECT COALESCE(gender, 'unknown') as gender, COUNT(*) as c
               FROM stats WHERE user_id=? AND event_type='visit'
               GROUP BY gender""",
            (user_id,),
        )
        gender_rows = await cur.fetchall()
        genders = {r["gender"]: r["c"] for r in gender_rows}

        # إحصائيات مصادر الزيارات (Referrers)
        cur = await db.execute(
            """SELECT COALESCE(referrer, 'مباشر / غير معروف') as referrer, COUNT(*) as c
               FROM stats WHERE user_id=? AND event_type='visit'
               GROUP BY referrer ORDER BY c DESC LIMIT 10""",
            (user_id,),
        )
        ref_rows = await cur.fetchall()
        referrers = [dict(r) for r in ref_rows]

        # إحصائيات الأجهزة (OS)
        cur = await db.execute(
            """SELECT COALESCE(os, 'آخر') as os, COUNT(*) as c
               FROM stats WHERE user_id=? AND event_type='visit'
               GROUP BY os ORDER BY c DESC LIMIT 10""",
            (user_id,),
        )
        os_rows = await cur.fetchall()
        os_list = [dict(r) for r in os_rows]

        # إحصائيات المتصفحات (Browsers)
        cur = await db.execute(
            """SELECT COALESCE(browser, 'آخر') as browser, COUNT(*) as c
               FROM stats WHERE user_id=? AND event_type='visit'
               GROUP BY browser ORDER BY c DESC LIMIT 10""",
            (user_id,),
        )
        browser_rows = await cur.fetchall()
        browsers = [dict(r) for r in browser_rows]

        return {
            "visits": visits,
            "total_clicks": total_clicks,
            "links": link_stats,
            "countries": countries,
            "genders": genders,
            "referrers": referrers,
            "os_list": os_list,
            "browsers": browsers,
        }


# ─────────────────────────────── دوال الدفع ───────────────────────────────

async def create_payment(user_id: int, amount: int, currency: str, status: str,
                         charge_id: Optional[str] = None, purpose: str = "vip") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO payments (user_id, amount, currency, status, telegram_payment_charge_id, purpose, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, amount, currency, status,
             charge_id, purpose, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def get_bot_stats() -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        (total_users,) = await cur.fetchone()

        now_iso = datetime.now(timezone.utc).isoformat()
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE is_vip=1 AND vip_expires > ?", (now_iso,)
        )
        (vip_users,) = await cur.fetchone()

        cur = await db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='completed' AND currency='STARS'"
        )
        (total_stars,) = await cur.fetchone()

        cur = await db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='completed' AND currency='USD'"
        )
        (total_usd,) = await cur.fetchone()

        cur = await db.execute("SELECT COUNT(*) FROM referrals")
        (total_referrals,) = await cur.fetchone()

        cur = await db.execute("SELECT COUNT(*) FROM forced_channels")
        (total_channels,) = await cur.fetchone()

        cur = await db.execute("SELECT COUNT(*) FROM users WHERE is_banned=1")
        (banned,) = await cur.fetchone()

        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        cur = await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM stats WHERE timestamp >= ?", (today,)
        )
        (active_today,) = await cur.fetchone()

        return {
            "total_users": total_users,
            "vip_users": vip_users,
            "total_stars": total_stars,
            "total_usd": total_usd,
            "total_referrals": total_referrals,
            "total_channels": total_channels,
            "banned": banned,
            "active_today": active_today,
        }


# ─────────────────────────────── دوال الإحالات (Referrals) ───────────────────────────────

async def record_referral(referrer_id: int, referred_id: int) -> bool:
    if referrer_id == referred_id:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM referrals WHERE referred_id=?", (referred_id,)
        )
        if await cur.fetchone():
            return False
        cur = await db.execute("SELECT 1 FROM users WHERE user_id=?", (referrer_id,))
        if not await cur.fetchone():
            return False
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            await db.execute(
                "INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (?, ?, ?)",
                (referrer_id, referred_id, now_iso),
            )
            await db.execute(
                "UPDATE users SET referred_by=? WHERE user_id=?", (referrer_id, referred_id)
            )
            await db.execute(
                "UPDATE users SET referral_count=referral_count+1 WHERE user_id=?", (referrer_id,)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_referral_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT referral_count FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else 0


async def get_total_referral_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else 0


async def reset_referral_progress(user_id: int) -> None:
    """يُصفّر عداد الإحالات (يُستدعى بعد منح المكافأة)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET referral_count=0 WHERE user_id=?", (user_id,))
        await db.commit()


async def add_pending_referral(referrer_id: int, referred_id: int) -> bool:
    if referrer_id == referred_id:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if already has a recorded referral
        cur = await db.execute("SELECT 1 FROM referrals WHERE referred_id=?", (referred_id,))
        if await cur.fetchone():
            return False
        # Check if already has a pending referral
        cur = await db.execute("SELECT 1 FROM pending_referrals WHERE referred_id=?", (referred_id,))
        if await cur.fetchone():
            return False
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            await db.execute(
                "INSERT OR REPLACE INTO pending_referrals (referred_id, referrer_id, created_at) VALUES (?, ?, ?)",
                (referred_id, referrer_id, now_iso),
            )
            await db.commit()
            return True
        except Exception:
            return False


async def get_pending_referral(referred_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT referrer_id FROM pending_referrals WHERE referred_id=?", (referred_id,))
        row = await cur.fetchone()
        return row[0] if row else None


async def delete_pending_referral(referred_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM pending_referrals WHERE referred_id=?", (referred_id,))
        await db.commit()


async def get_referral_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT user_id, username, full_name, referral_count
               FROM users WHERE referral_count > 0
               ORDER BY referral_count DESC LIMIT ?""",
            (limit,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ─────────────────────────────── دوال القنوات الإجبارية ───────────────────────────────

async def add_forced_channel(chat_id: str, title: str, invite_url: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO forced_channels (chat_id, title, invite_url, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, title, invite_url, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def remove_forced_channel(chat_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM forced_channels WHERE chat_id=?", (chat_id,))
        await db.commit()
        return cur.rowcount > 0


async def list_forced_channels() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM forced_channels ORDER BY id ASC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ─────────────────────────────── جلسات الأدمن ───────────────────────────────

async def grant_admin_session(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO admin_sessions (user_id, authorized_at) VALUES (?, ?)",
            (user_id, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def revoke_admin_session(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admin_sessions WHERE user_id=?", (user_id,))
        await db.commit()


async def has_admin_session(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM admin_sessions WHERE user_id=?", (user_id,))
        return (await cur.fetchone()) is not None


async def list_admin_sessions() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT s.user_id, s.authorized_at, u.username, u.full_name
               FROM admin_sessions s LEFT JOIN users u ON u.user_id = s.user_id
               ORDER BY s.authorized_at DESC"""
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ─────────────────────────────── الميزات التفاعلية الجديدة ───────────────────────────────

async def update_music(user_id: int, music_url: Optional[str], music_title: Optional[str] = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET music_url=?, music_title=? WHERE user_id=?",
            (music_url, music_title, user_id),
        )
        await db.commit()


async def update_bg_effect(user_id: int, bg_effect: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET bg_effect=? WHERE user_id=?", (bg_effect, user_id))
        await db.commit()


async def update_badge_type(user_id: int, badge_type: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET badge_type=? WHERE user_id=?", (badge_type, user_id))
        await db.commit()


async def update_whatsapp_btn(user_id: int, whatsapp_data: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET whatsapp_btn=? WHERE user_id=?", (whatsapp_data, user_id))
        await db.commit()


async def add_review(user_id: int, reviewer_name: str, rating: int, comment: str, page_slug: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO reviews (user_id, reviewer_name, rating, comment, is_approved, page_slug, created_at)
               VALUES (?, ?, ?, ?, 0, ?, ?)""",
            (user_id, reviewer_name, rating, comment, page_slug, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def approve_review(review_id: int, is_approved: bool = True) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        val = 1 if is_approved else 0
        cur = await db.execute("UPDATE reviews SET is_approved=? WHERE id=?", (val, review_id))
        await db.commit()
        return cur.rowcount > 0


async def delete_review(review_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM reviews WHERE id=?", (review_id,))
        await db.commit()
        return cur.rowcount > 0


async def get_reviews(user_id: int, approved_only: bool = True, page_slug: str = None) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if page_slug:
            if approved_only:
                cur = await db.execute(
                    "SELECT * FROM reviews WHERE page_slug=? AND is_approved=1 ORDER BY id DESC",
                    (page_slug,),
                )
            else:
                cur = await db.execute(
                    "SELECT * FROM reviews WHERE page_slug=? ORDER BY id DESC",
                    (page_slug,),
                )
        else:
            if approved_only:
                cur = await db.execute(
                    "SELECT * FROM reviews WHERE user_id=? AND page_slug IS NULL AND is_approved=1 ORDER BY id DESC",
                    (user_id,),
                )
            else:
                cur = await db.execute(
                    "SELECT * FROM reviews WHERE user_id=? AND page_slug IS NULL ORDER BY id DESC",
                    (user_id,),
                )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_review(review_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM reviews WHERE id=?", (review_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_peak_activity_hours(user_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
               FROM stats
               WHERE user_id=?
               GROUP BY hour
               ORDER BY count DESC
               LIMIT 5""",
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def update_marquee(user_id: int, marquee_text: Optional[str], marquee_url: Optional[str] = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET marquee_text=?, marquee_url=? WHERE user_id=?",
            (marquee_text, marquee_url, user_id),
        )
        await db.commit()


async def update_font(user_id: int, font_family: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET font_family=? WHERE user_id=?",
            (font_family, user_id),
        )
        await db.commit()


async def update_countdown(user_id: int, title: Optional[str], target_iso: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET countdown_title=?, countdown_target=? WHERE user_id=?",
            (title, target_iso, user_id),
        )
        await db.commit()


async def update_custom_domain(user_id: int, domain: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET custom_domain=? WHERE user_id=?",
            (domain.lower().strip() if domain else None, user_id),
        )
        await db.commit()


async def get_user_by_custom_domain(domain: str) -> Optional[Dict[str, Any]]:
    if not domain:
        return None
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE custom_domain=?", (domain.lower().strip(),))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_pixels(user_id: int, meta: Optional[str] = None, tiktok: Optional[str] = None, ga: Optional[str] = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET meta_pixel=?, tiktok_pixel=?, ga_pixel=? WHERE user_id=?",
            (meta, tiktok, ga, user_id),
        )
        await db.commit()


async def update_social_links(user_id: int, socials: dict) -> None:
    import json
    data_str = json.dumps(socials, ensure_ascii=False)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET social_links=? WHERE user_id=?",
            (data_str, user_id),
        )
        await db.commit()


async def get_link_by_id(link_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM links WHERE id=?", (link_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_link_extra(
    link_id: int,
    subtitle: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    is_banner: int = 0,
    section_header: Optional[str] = None,
    is_featured: int = 0,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE links 
               SET subtitle=?, thumbnail_url=?, is_banner=?, section_header=?, is_featured=?
               WHERE id=?""",
            (subtitle, thumbnail_url, is_banner, section_header, is_featured, link_id),
        )
        await db.commit()


# ─────────────────────────────── دوال الصفحات الفرعية (Sub-pages) ───────────────────────────────

async def create_sub_page(user_id: int, slug: str, title: str) -> bool:
    slug = slug.strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        if slug.isdigit():
            return False
        cur = await db.execute("SELECT 1 FROM sub_pages WHERE slug=?", (slug,))
        if await cur.fetchone():
            return False
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            await db.execute(
                "INSERT INTO sub_pages (user_id, slug, page_title, created_at) VALUES (?, ?, ?, ?)",
                (user_id, slug, title, now_iso),
            )
            await db.commit()
            return True
        except Exception:
            return False


async def get_sub_page(slug: str) -> Optional[Dict[str, Any]]:
    slug = slug.strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM sub_pages WHERE slug=?", (slug,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_sub_page_by_domain(domain: str) -> Optional[Dict[str, Any]]:
    domain = domain.strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM sub_pages WHERE custom_domain=?", (domain,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_user_sub_pages(user_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM sub_pages WHERE user_id=?", (user_id,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def delete_sub_page(user_id: int, slug: str) -> bool:
    slug = slug.strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM sub_pages WHERE user_id=? AND slug=?", (user_id, slug))
        if not await cur.fetchone():
            return False
        await db.execute("DELETE FROM sub_pages WHERE user_id=? AND slug=?", (user_id, slug))
        await db.execute("DELETE FROM links WHERE page_slug=?", (slug,))
        await db.execute("DELETE FROM reviews WHERE page_slug=?", (slug,))
        await db.commit()
        return True


async def update_sub_page_fields(user_id: int, slug: str, fields: Dict[str, Any]) -> bool:
    slug = slug.strip().lower()
    if not fields:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM sub_pages WHERE user_id=? AND slug=?", (user_id, slug))
        if not await cur.fetchone():
            return False
        set_clause = ", ".join([f"{k}=?" for k in fields.keys()])
        values = list(fields.values()) + [user_id, slug]
        try:
            await db.execute(
                f"UPDATE sub_pages SET {set_clause} WHERE user_id=? AND slug=?",
                values
            )
            await db.commit()
            return True
        except Exception:
            return False




