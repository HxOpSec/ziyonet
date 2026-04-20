from pathlib import Path

import aiosqlite
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from api.admin_api import router as admin_router
from api.analytics_api import router as analytics_router
from api.books_api import router as books_router
from api.chat_api import router as chat_router
from config import settings
from db import get_db, init_db
from utils.rate_limit import limiter
from utils.security import get_password_hash


app = FastAPI(title=settings.APP_NAME)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(SlowAPIMiddleware)


@app.on_event("startup")
async def on_startup():
    await init_db()
    async for db in get_db():
        await ensure_default_admin(db)
        break


async def ensure_default_admin(db: aiosqlite.Connection) -> None:
    cursor = await db.execute("SELECT id FROM users WHERE username = ?", (settings.DEFAULT_ADMIN_USERNAME,))
    row = await cursor.fetchone()
    if row:
        return
    await db.execute(
        "INSERT INTO users (username, password_hash, is_active) VALUES (?, ?, 1)",
        (settings.DEFAULT_ADMIN_USERNAME, get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)),
    )
    await db.commit()


app.include_router(books_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(admin_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/admin.html")
async def admin_page():
    return FileResponse(FRONTEND_DIR / "admin.html")


@app.get("/book-detail.html")
async def book_detail_page():
    return FileResponse(FRONTEND_DIR / "book-detail.html")
