"""
FastAPI server:
- يقدّم صفحة الـ Web App لكل مستخدم على /api/page/{user_id}
- يستقبل أحداث التتبع (زيارة/نقرة رابط) مع تتبع البلد
- يشغّل بوت التليجرام (aiogram) كمهمة خلفية داخل حلقة الأحداث
- يقدّم الصور الشخصية عبر /api/avatar/{user_id}
"""
import asyncio
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from bot.main import run_bot_polling  # noqa: E402
from bot import database as db          # noqa: E402
from bot.webapp_template import render_page  # noqa: E402
from bot.config import settings         # noqa: E402
from bot.gender_utils import guess_gender  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────── تتبع البلد من IP ───────────────────────

_ip_country_cache = {}


async def resolve_country(ip: Optional[str]) -> Optional[str]:
    if not ip:
        return None
    # تجاوز العناوين الداخلية
    if ip.startswith(("10.", "192.168.", "127.", "172.16.", "172.17.", "172.18.",
                      "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
                      "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
                      "172.29.", "172.30.", "172.31.")) or ip in ("localhost", "::1"):
        return "محلي"
    if ip in _ip_country_cache:
        return _ip_country_cache[ip]
    country = None
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"http://ip-api.com/json/{ip}?fields=status,country")
            data = r.json()
            if data.get("status") == "success":
                country = data.get("country") or None
    except Exception as e:
        logger.warning(f"country lookup failed for {ip}: {e}")
    _ip_country_cache[ip] = country
    return country


def extract_ip(request: Request) -> Optional[str]:
    xff = request.headers.get("x-forwarded-for") or ""
    if xff:
        return xff.split(",")[0].strip()
    xr = request.headers.get("x-real-ip")
    if xr:
        return xr.strip()
    return request.client.host if request.client else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    os.makedirs(settings.AVATARS_DIR, exist_ok=True)
    
    # Start Cloudflare Tunnel automatically if enabled and not running on Render
    tunnel = None
    is_render = bool(os.environ.get("RENDER"))
    enable_tunnel = os.environ.get("ENABLE_AUTO_TUNNEL", "false" if is_render else "true").lower() == "true"
    if enable_tunnel and not is_render:
        try:
            from tunnel import CloudflareTunnel
            port = int(os.environ.get("PORT", "8001"))
            tunnel = CloudflareTunnel(port=port)
            tunnel_url = tunnel.start()
            settings.WEBAPP_BASE_URL = tunnel_url
            os.environ["WEBAPP_BASE_URL"] = tunnel_url
            logger.info(f"Updated WEBAPP_BASE_URL to tunnel URL: {tunnel_url}")
        except Exception as e:
            logger.error(f"Failed to start auto-tunnel: {e}")
    elif is_render and os.environ.get("RENDER_EXTERNAL_URL"):
        render_url = os.environ["RENDER_EXTERNAL_URL"].rstrip("/")
        settings.WEBAPP_BASE_URL = render_url
        logger.info(f"Running on Render with public URL: {render_url}")
            
    import threading
    
    def _start_bot_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_bot_polling())
        except Exception as err:
            logger.error(f"Bot thread error: {err}", exc_info=True)
        finally:
            loop.close()

    bot_thread = threading.Thread(target=_start_bot_thread, name="BotPollingThread", daemon=True)
    bot_thread.start()
    logger.info("✅ FastAPI startup complete, bot dedicated thread started")
    try:
        yield
    finally:
        if tunnel:
            tunnel.stop()
        logger.info("👋 FastAPI shutdown complete")


app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def root_handler(request: Request):
    host = request.headers.get("host", "").split(":")[0].lower().strip()
    if host:
        # Check main user pages
        user = await db.get_user_by_custom_domain(host)
        if user and user.get("page_title"):
            user_id = user["user_id"]
            links = await db.get_user_links(user_id)
            reviews = await db.get_reviews(user_id, approved_only=True)
            html = render_page(user, links, reviews=reviews)
            return HTMLResponse(html)
        
        # Check sub-pages
        sub_page = await db.get_sub_page_by_domain(host)
        if sub_page:
            owner_id = sub_page["user_id"]
            owner = await db.get_user(owner_id)
            is_vip = await db.is_user_vip(owner_id) if owner else False
            sub_page_data = dict(sub_page)
            sub_page_data["is_vip"] = is_vip
            sub_page_data["avatar_path"] = owner.get("avatar_path") if owner else None
            
            links = await db.get_user_links(owner_id, page_slug=sub_page["slug"])
            reviews = await db.get_reviews(owner_id, approved_only=True, page_slug=sub_page["slug"])
            html = render_page(sub_page_data, links, reviews=reviews)
            return HTMLResponse(html)

    return HTMLResponse(
        "<div style='font-family:sans-serif;text-align:center;padding:50px'>"
        "<h1>✨ LinkTree Bot Service</h1><p>Active and running seamlessly.</p></div>"
    )


@api_router.get("/", include_in_schema=False)
async def api_root():
    return {"status": "ok", "message": "LinkTree Bot API"}


@api_router.get("/page/{user_id_or_slug}", response_class=HTMLResponse)
async def get_user_page(user_id_or_slug: str):
    is_int = False
    try:
        user_id = int(user_id_or_slug)
        is_int = True
    except ValueError:
        pass

    if is_int:
        user = await db.get_user(user_id)
        if not user:
            return HTMLResponse(
                "<h1 style='font-family:sans-serif;text-align:center;padding:40px'>"
                "❌ المستخدم غير موجود</h1>",
                status_code=404,
            )
        if not user.get("page_title"):
            return HTMLResponse(
                "<h1 style='font-family:sans-serif;text-align:center;padding:40px'>"
                "⏳ لم يتم إعداد الصفحة بعد</h1>",
                status_code=200,
            )
        links = await db.get_user_links(user_id)
        reviews = await db.get_reviews(user_id, approved_only=True)
        html = render_page(user, links, reviews=reviews)
        return HTMLResponse(html)
    else:
        # Check sub-pages
        sub_page = await db.get_sub_page(user_id_or_slug)
        if not sub_page:
            return HTMLResponse(
                "<h1 style='font-family:sans-serif;text-align:center;padding:40px'>"
                "❌ الصفحة المطلوبة غير موجودة</h1>",
                status_code=404,
            )
        
        owner_id = sub_page["user_id"]
        owner = await db.get_user(owner_id)
        is_vip = await db.is_user_vip(owner_id) if owner else False
        
        sub_page_data = dict(sub_page)
        sub_page_data["is_vip"] = is_vip
        sub_page_data["avatar_path"] = owner.get("avatar_path") if owner else None
        
        links = await db.get_user_links(owner_id, page_slug=user_id_or_slug)
        reviews = await db.get_reviews(owner_id, approved_only=True, page_slug=user_id_or_slug)
        html = render_page(sub_page_data, links, reviews=reviews)
        return HTMLResponse(html)


@api_router.get("/avatar/{user_id}")
async def get_avatar(user_id: int):
    user = await db.get_user(user_id)
    if not user or not user.get("avatar_path"):
        raise HTTPException(status_code=404, detail="no avatar")
    path = user["avatar_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="file missing")
    return FileResponse(path, media_type="image/jpeg")


def parse_visitor_meta(request: Request) -> tuple[str, str, str]:
    ref_param = request.query_params.get("ref")
    referer_hdr = request.headers.get("referer", "")
    
    referrer = "مباشر / غير معروف"
    if ref_param:
        ref_low = ref_param.lower()
        if ref_low in ("telegram", "tg"):
            referrer = "تليجرام (Telegram)"
        elif ref_low in ("instagram", "ig"):
            referrer = "إنستغرام (Instagram)"
        elif ref_low in ("facebook", "fb"):
            referrer = "فيسبوك (Facebook)"
        elif ref_low in ("whatsapp", "wa"):
            referrer = "واتساب (WhatsApp)"
        else:
            referrer = f"رابط خاص ({ref_param})"
    elif referer_hdr:
        referer_low = referer_hdr.lower()
        if "t.me" in referer_low or "telegram" in referer_low:
            referrer = "تليجرام (Telegram)"
        elif "instagram.com" in referer_low:
            referrer = "إنستغرام (Instagram)"
        elif "facebook.com" in referer_low or "fb.com" in referer_low:
            referrer = "فيسبوك (Facebook)"
        elif "whatsapp.com" in referer_low or "wa.me" in referer_low:
            referrer = "واتساب (WhatsApp)"
        elif "google.com" in referer_low:
            referrer = "بحث جوجل (Google)"
        else:
            referrer = "موقع خارجي"
            
    ua = request.headers.get("user-agent", "").lower()
    
    os_name = "آخر (Other)"
    if "android" in ua:
        os_name = "أندرويد (Android)"
    elif "iphone" in ua or "ipad" in ua:
        os_name = "آيفون/آيباد (iOS)"
    elif "windows" in ua:
        os_name = "ويندوز (Windows)"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "ماك (macOS)"
    elif "linux" in ua:
        os_name = "لينكس (Linux)"
        
    browser_name = "آخر (Other)"
    if "chrome" in ua and "safari" in ua and "edge" not in ua and "opr" not in ua:
        browser_name = "جوجل كروم (Chrome)"
    elif "safari" in ua and "chrome" not in ua:
        browser_name = "سفاري (Safari)"
    elif "firefox" in ua:
        browser_name = "فايرفوكس (Firefox)"
    elif "edge" in ua or "edg" in ua:
        browser_name = "مايكروسوفت إيدج (Edge)"
    elif "opera" in ua or "opr" in ua:
        browser_name = "أوبرا (Opera)"
        
    return referrer, browser_name, os_name


@api_router.post("/track/{user_id}/visit")
async def track_visit(user_id: int, request: Request):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    ip = extract_ip(request)
    country = await resolve_country(ip)
    # نحاول استخراج first_name من الجسم (يُرسل من WebApp)
    first_name = None
    gender = "unknown"
    try:
        body = await request.json()
        if isinstance(body, dict):
            first_name = (body.get("first_name") or "").strip() or None
            if first_name:
                gender = guess_gender(first_name)
    except Exception:
        pass
    
    referrer, browser, os_name = parse_visitor_meta(request)
    await db.log_event(user_id, "visit", ip=ip, country=country,
                       gender=gender, first_name=first_name,
                       referrer=referrer, browser=browser, os=os_name)
    return JSONResponse({"ok": True})


@api_router.post("/track/{user_id}/click/{link_id}")
async def track_click(user_id: int, link_id: int, request: Request):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    ip = extract_ip(request)
    country = await resolve_country(ip)
    first_name = None
    gender = "unknown"
    try:
        body = await request.json()
        if isinstance(body, dict):
            first_name = (body.get("first_name") or "").strip() or None
            if first_name:
                gender = guess_gender(first_name)
    except Exception:
        pass
    
    referrer, browser, os_name = parse_visitor_meta(request)
    await db.log_event(user_id, "click", link_id=link_id, ip=ip, country=country,
                       gender=gender, first_name=first_name,
                       referrer=referrer, browser=browser, os=os_name)
    return JSONResponse({"ok": True})


@api_router.post("/review/{user_id}")
async def submit_review(user_id: int, request: Request):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json")
    
    reviewer_name = (body.get("reviewer_name") or "زائر").strip()[:50]
    rating = int(body.get("rating") or 5)
    rating = max(1, min(5, rating))
    comment = (body.get("comment") or "").strip()[:500]
    if not comment:
        raise HTTPException(status_code=400, detail="comment is required")
        
    rev_id = await db.add_review(user_id, reviewer_name, rating, comment)
    
    # Notify owner on Telegram
    try:
        from aiogram import Bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from bot.config import settings
        bot = Bot(token=settings.BOT_TOKEN)
        stars_str = "⭐" * rating
        msg = (
            "🌟 <b>تقييم جديد لصفحتك!</b>\n\n"
            f"👤 من: <b>{reviewer_name}</b>\n"
            f"⭐️ التقييم: <b>{stars_str} ({rating}/5)</b>\n"
            f"💬 التعليق: <i>\"{comment}\"</i>\n\n"
            "هل تود قبول هذا التقييم ليظهر في صفحتك؟"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ قبول وعرض التقييم", callback_data=f"approve_rev:{rev_id}"),
             InlineKeyboardButton(text="🗑 حذف التقييم", callback_data=f"delete_rev:{rev_id}")]
        ])
        await bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=kb)
        await bot.session.close()
    except Exception as e:
        logger.warning(f"Could not notify owner of review: {e}")
        
    return JSONResponse({"ok": True, "review_id": rev_id})


@api_router.get("/reviews/{user_id}")
async def list_user_reviews(user_id: int):
    return await db.get_reviews(user_id, approved_only=True)


@api_router.get("/health")
async def health():
    return {"status": "healthy"}


@api_router.get("/stats")
async def public_stats():
    return await db.get_bot_stats()


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
