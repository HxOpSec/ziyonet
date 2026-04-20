import aiosqlite
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
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
    allow_origins=settings.allowed_origins_list,
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
        await ensure_seed_books(db)
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


async def ensure_seed_books(db: aiosqlite.Connection) -> None:
    cursor = await db.execute("SELECT COUNT(*) AS total FROM books")
    row = await cursor.fetchone()
    if row and row["total"] > 0:
        return

    books = [
        ("Введение в алгоритмы", "Томас Кормен", "978-5-8459-2123-0", "Информатика", "Классический труд по алгоритмам и структурам данных.", 2021, "Вильямс", 1328, "ru", 6, 6, "https://placehold.co/240x320?text=Algorithms"),
        ("Чистый код", "Роберт Мартин", "978-5-496-00487-9", "Программирование", "Практики написания поддерживаемого и читаемого кода.", 2020, "Питер", 464, "ru", 5, 4, "https://placehold.co/240x320?text=Clean+Code"),
        ("Проектирование баз данных", "Карлос Корнелл", "978-5-9775-4074-0", "Базы данных", "Нормализация, индексы и транзакционные модели.", 2019, "БХВ", 512, "ru", 4, 3, "https://placehold.co/240x320?text=Databases"),
        ("Computer Networks", "Andrew S. Tanenbaum", "978-0-13-212695-3", "Сети", "Протоколы, архитектура и практические аспекты сетей.", 2018, "Pearson", 960, "en", 4, 4, "https://placehold.co/240x320?text=Networks"),
        ("Modern Operating Systems", "Andrew S. Tanenbaum", "978-0-13-359162-0", "ОС", "Процессы, память, файловые системы и безопасность.", 2017, "Pearson", 1136, "en", 4, 2, "https://placehold.co/240x320?text=OS"),
        ("Designing Data-Intensive Applications", "Martin Kleppmann", "978-1-4493-7332-0", "Архитектура ПО", "Надёжные и масштабируемые системы обработки данных.", 2022, "O'Reilly", 616, "en", 5, 5, "https://placehold.co/240x320?text=DDIA"),
        ("FastAPI в действии", "Сергей Иванов", "978-5-6047289-1-2", "Web-разработка", "Построение API на FastAPI с практическими примерами.", 2024, "Лаборатория знаний", 320, "ru", 7, 7, "https://placehold.co/240x320?text=FastAPI"),
        ("Python для анализа данных", "Уэс Маккинни", "978-5-8459-2009-7", "Data Science", "NumPy, pandas и визуализация данных на Python.", 2021, "Вильямс", 544, "ru", 6, 5, "https://placehold.co/240x320?text=Python+Data"),
        ("Искусственный интеллект: современный подход", "Стюарт Рассел", "978-5-4461-1480-8", "ИИ", "Методы ИИ, поиск, рассуждение и машинное обучение.", 2020, "Диалектика", 1408, "ru", 3, 2, "https://placehold.co/240x320?text=AI"),
        ("Deep Learning", "Ian Goodfellow", "978-0-262-03561-3", "Машинное обучение", "Нейросети, оптимизация и практические подходы.", 2019, "MIT Press", 800, "en", 3, 3, "https://placehold.co/240x320?text=Deep+Learning"),
        ("Clean Architecture", "Robert C. Martin", "978-0-13-449416-6", "Архитектура ПО", "Принципы и шаблоны создания устойчивых систем.", 2018, "Prentice Hall", 432, "en", 4, 4, "https://placehold.co/240x320?text=Architecture"),
        ("The Pragmatic Programmer", "David Thomas", "978-0-13-595705-9", "Программирование", "Практический подход к профессиональной разработке.", 2021, "Addison-Wesley", 352, "en", 5, 4, "https://placehold.co/240x320?text=Pragmatic"),
    ]
    await db.executemany(
        """
        INSERT INTO books (
            title, author, isbn, category, description, year, publisher, pages,
            language, copies_total, copies_available, cover_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        books,
    )
    await db.commit()


app.include_router(books_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(admin_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith(f"{settings.API_PREFIX}/chat") and exc.status_code == 502:
        return JSONResponse(
            status_code=502,
            content={
                "detail": (
                    "ИИ-сервис временно недоступен или отвечает слишком долго. "
                    "Проверьте, что Ollama запущен на http://localhost:11434, и повторите запрос."
                )
            },
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
