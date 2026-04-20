import aiosqlite
from pathlib import Path
from typing import AsyncGenerator

from config import settings


DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")


CREATE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE,
        category TEXT,
        description TEXT,
        year INTEGER,
        publisher TEXT,
        pages INTEGER,
        language TEXT DEFAULT 'ru',
        copies_total INTEGER DEFAULT 1,
        copies_available INTEGER DEFAULT 1,
        cover_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question TEXT NOT NULL,
        answer TEXT,
        model TEXT,
        response_time_ms INTEGER,
        mode TEXT CHECK(mode IN ('fast', 'deep')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)",
    "CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)",
    "CREATE INDEX IF NOT EXISTS idx_books_category ON books(category)",
    "CREATE INDEX IF NOT EXISTS idx_books_year ON books(year)",
    "CREATE INDEX IF NOT EXISTS idx_ai_logs_created ON ai_logs(created_at)",
]


async def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        for statement in CREATE_STATEMENTS:
            await db.execute(statement)
        await db.commit()


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    try:
        yield conn
    finally:
        await conn.close()
