"""
إدارة قاعدة بيانات SQLite (باستخدام aiosqlite للعمليات غير المتزامنة)
"""
import aiosqlite
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from bot.config import settings

DB_PATH = settings.DB_PATH


async def init_db() -> None:
    """إنشاء الجداول الأساسية إذا لم تكن موجودة"""
    async with aiosqlite.connect(DB_PATH) as db:
        # جدول المستخدمين
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
                created_at    TEXT NOT NULL
            )
            """
        )
        # جدول الروابط
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                title     TEXT NOT NULL,
                url       TEXT NOT NULL,
                position  INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )
        # جدول الإحصائيات (زوار / نقرات الروابط)
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS stats (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                link_id    INTEGER,
                event_type TEXT NOT NULL,
                timestamp  TEXT NOT NULL
            )
            """
        )
        # جدول عمليات الدفع
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                amount       INTEGER NOT NULL,
                currency     TEXT NOT NULL,
                status       TEXT NOT NULL,
                telegram_payment_charge_id TEXT,
                created_at   TEXT NOT NULL
            )
            """
        )
        await db.commit()


# ─────────────────────────────── دوال المستخدمين ───────────────────────────────

async def get_or_create_user(user_id: int, username: str, full_name: str) -> Dict[str, Any]:
    """إحضار المستخدم من القاعدة أو إنشاؤه إن لم يكن موجوداً"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if row:
            # تحديث اليوزرنيم/الاسم لو تغيّر
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
    """التحقق ما إذا كان المستخدم VIP فعالاً (لم ينتهِ اشتراكه)"""
    user = await get_user(user_id)
    if not user or not user["is_vip"]:
        return False
    if not user["vip_expires"]:
        return False
    expires = datetime.fromisoformat(user["vip_expires"])
    if expires < datetime.now(timezone.utc):
        # انتهاء الاشتراك -> نُعيده مجاناً
        await set_vip_status(user_id, False)
        return False
    return True


async def set_vip_status(user_id: int, is_vip: bool, days: int = None) -> None:
    """تفعيل/إلغاء اشتراك VIP للمستخدم"""
    days = days or settings.VIP_DURATION_DAYS
    async with aiosqlite.connect(DB_PATH) as db:
        if is_vip:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
            await db.execute(
                "UPDATE users SET is_vip=1, vip_expires=? WHERE user_id=?",
                (expires_at, user_id),
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


async def get_all_user_ids() -> List[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users")
        rows = await cur.fetchall()
        return [r[0] for r in rows]


# ─────────────────────────────── دوال الروابط ───────────────────────────────

async def add_link(user_id: int, title: str, url: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COALESCE(MAX(position), 0) FROM links WHERE user_id=?", (user_id,)
        )
        (max_pos,) = await cur.fetchone()
        cur = await db.execute(
            "INSERT INTO links (user_id, title, url, position) VALUES (?, ?, ?, ?)",
            (user_id, title, url, (max_pos or 0) + 1),
        )
        await db.commit()
        return cur.lastrowid


async def get_user_links(user_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM links WHERE user_id=? ORDER BY position ASC", (user_id,)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def count_user_links(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM links WHERE user_id=?", (user_id,))
        (n,) = await cur.fetchone()
        return n


async def delete_user_links(user_id: int) -> None:
    """حذف جميع روابط المستخدم (يُستخدم عند إعادة بناء الصفحة)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM links WHERE user_id=?", (user_id,))
        await db.commit()


# ─────────────────────────────── دوال الإحصائيات ───────────────────────────────

async def log_event(user_id: int, event_type: str, link_id: Optional[int] = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO stats (user_id, link_id, event_type, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, link_id, event_type, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def get_user_stats(user_id: int) -> Dict[str, Any]:
    """إحضار إحصائيات المستخدم (زوار الصفحة + عدد النقرات لكل رابط)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # عدد الزوار (visit)
        cur = await db.execute(
            "SELECT COUNT(*) as c FROM stats WHERE user_id=? AND event_type='visit'",
            (user_id,),
        )
        visits = (await cur.fetchone())["c"]

        # عدد النقرات لكل رابط
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
        return {"visits": visits, "total_clicks": total_clicks, "links": link_stats}


# ─────────────────────────────── دوال الدفع ───────────────────────────────

async def create_payment(user_id: int, amount: int, currency: str, status: str,
                         charge_id: Optional[str] = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO payments (user_id, amount, currency, status, telegram_payment_charge_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, amount, currency, status,
             charge_id, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def get_bot_stats() -> Dict[str, Any]:
    """إحصائيات عامة للبوت (للأدمن)"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        (total_users,) = await cur.fetchone()

        now_iso = datetime.now(timezone.utc).isoformat()
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE is_vip=1 AND vip_expires > ?", (now_iso,)
        )
        (vip_users,) = await cur.fetchone()

        # إجمالي الأرباح (الستارز)
        cur = await db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='completed' AND currency='STARS'"
        )
        (total_stars,) = await cur.fetchone()

        # إجمالي المدفوعات اليدوية بالدولار
        cur = await db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='completed' AND currency='USD'"
        )
        (total_usd,) = await cur.fetchone()

        return {
            "total_users": total_users,
            "vip_users": vip_users,
            "total_stars": total_stars,
            "total_usd": total_usd,
        }
