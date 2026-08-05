"""
FastAPI server:
- يقدّم صفحة الـ Web App لكل مستخدم على /api/page/{user_id}
- يستقبل أحداث التتبع (زيارة/نقرة رابط)
- يشغّل بوت التليجرام (aiogram) كمهمة خلفية داخل حلقة الأحداث
"""
import asyncio
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from bot.main import run_bot_polling  # noqa: E402
from bot import database as db          # noqa: E402
from bot.webapp_template import render_page  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """تشغيل البوت مع بداية السيرفر وإيقافه عند الإغلاق"""
    await db.init_db()
    bot_task = asyncio.create_task(run_bot_polling())
    logger.info("✅ FastAPI startup complete, bot task created")
    try:
        yield
    finally:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
        logger.info("👋 FastAPI shutdown complete")


app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")


# ─────────────────────────── صفحة الـ Web App ───────────────────────────

@api_router.get("/", include_in_schema=False)
async def api_root():
    return {"status": "ok", "message": "LinkTree Bot API"}


@api_router.get("/page/{user_id}", response_class=HTMLResponse)
async def get_user_page(user_id: int):
    """يقدّم صفحة LinkTree الشخصية لكل مستخدم كـ HTML"""
    user = await db.get_user(user_id)
    if not user:
        return HTMLResponse(
            "<h1 style='font-family:sans-serif;text-align:center;padding:40px'>"
            "❌ المستخدم غير موجود</h1>",
            status_code=404,
        )
    # إذا لم يُنشئ المستخدم صفحته بعد
    if not user.get("page_title"):
        return HTMLResponse(
            "<h1 style='font-family:sans-serif;text-align:center;padding:40px'>"
            "⏳ لم يتم إعداد الصفحة بعد</h1>",
            status_code=200,
        )
    links = await db.get_user_links(user_id)
    html = render_page(user, links)
    return HTMLResponse(html)


# ─────────────────────────── تتبع الأحداث ───────────────────────────

@api_router.post("/track/{user_id}/visit")
async def track_visit(user_id: int):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    await db.log_event(user_id, "visit")
    return JSONResponse({"ok": True})


@api_router.post("/track/{user_id}/click/{link_id}")
async def track_click(user_id: int, link_id: int):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    await db.log_event(user_id, "click", link_id=link_id)
    return JSONResponse({"ok": True})


@api_router.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
