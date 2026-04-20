import time
from collections import defaultdict, deque
from pathlib import Path

import aiosqlite
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.admin_api import router as admin_router
from api.analytics_api import router as analytics_router
from api.books_api import router as books_router
from api.chat_api import router as chat_router
from config import settings
from db import get_db, init_db
from utils.security import get_password_hash


app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

_RATE_STATE: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60
        points = _RATE_STATE[ip]
        while points and points[0] < now - window:
            points.popleft()
        if len(points) >= settings.API_RATE_LIMIT:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        points.append(now)
    return await call_next(request)


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
