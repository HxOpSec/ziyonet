from typing import Any, Optional

import aiosqlite

from config import settings
from utils.validators import normalize_order, normalize_sort, sanitize


class BookService:
    ALLOWED_UPDATE_FIELDS = {
        "title",
        "author",
        "isbn",
        "category",
        "description",
        "year",
        "publisher",
        "pages",
        "language",
        "copies_total",
        "copies_available",
        "cover_url",
    }

    async def list_books(
        self,
        db: aiosqlite.Connection,
        page: int,
        per_page: int,
        q: Optional[str] = None,
        category: Optional[str] = None,
        year: Optional[int] = None,
        available: Optional[bool] = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> dict[str, Any]:
        per_page = min(max(1, per_page), settings.MAX_BOOKS_PER_PAGE)
        page = max(1, page)
        offset = (page - 1) * per_page

        where = []
        params: list[Any] = []

        if q:
            q = sanitize(q, max_len=255)
            where.append("(title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?)")
            like = "%" + q + "%"
            params.extend([like, like, like, like])
        if category:
            category = sanitize(category, max_len=100)
            where.append("category = ?")
            params.append(category)
        if year:
            where.append("year = ?")
            params.append(year)
        if available is not None:
            where.append("copies_available > 0" if available else "copies_available = 0")

        where_clause = ""
        if where:
            where_clause = "WHERE " + " AND ".join(where)
        sort_sql = normalize_sort(sort_by)
        order_sql = normalize_order(order)

        total_query = "SELECT COUNT(*) as total FROM books " + where_clause
        total_cursor = await db.execute(total_query, params)
        total_row = await total_cursor.fetchone()
        total = total_row["total"] if total_row else 0

        query = """
            SELECT *
            FROM books
            """ + where_clause + """
            ORDER BY """ + sort_sql + " " + order_sql + """
            LIMIT ? OFFSET ?
        """
        rows_cursor = await db.execute(query, [*params, per_page, offset])
        rows = await rows_cursor.fetchall()
        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    async def get_book(self, db: aiosqlite.Connection, book_id: int) -> Optional[dict[str, Any]]:
        cursor = await db.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def create_book(self, db: aiosqlite.Connection, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        if isinstance(normalized.get("title"), str):
            normalized["title"] = sanitize(normalized["title"], max_len=255)
        if isinstance(normalized.get("author"), str):
            normalized["author"] = sanitize(normalized["author"], max_len=255)
        if isinstance(normalized.get("isbn"), str):
            normalized["isbn"] = sanitize(normalized["isbn"], max_len=50)
        if isinstance(normalized.get("category"), str):
            normalized["category"] = sanitize(normalized["category"], max_len=100)
        if isinstance(normalized.get("description"), str):
            normalized["description"] = sanitize(normalized["description"], max_len=2000)
        if isinstance(normalized.get("publisher"), str):
            normalized["publisher"] = sanitize(normalized["publisher"], max_len=255)
        if isinstance(normalized.get("language"), str):
            normalized["language"] = sanitize(normalized["language"], max_len=20)
        if isinstance(normalized.get("cover_url"), str):
            normalized["cover_url"] = sanitize(normalized["cover_url"], max_len=1000)

        query = """
            INSERT INTO books (
                title, author, isbn, category, description, year, publisher,
                pages, language, copies_total, copies_available, cover_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            normalized.get("title"),
            normalized.get("author"),
            normalized.get("isbn"),
            normalized.get("category"),
            normalized.get("description"),
            normalized.get("year"),
            normalized.get("publisher"),
            normalized.get("pages"),
            normalized.get("language", "ru"),
            normalized.get("copies_total", 1),
            normalized.get("copies_available", 1),
            normalized.get("cover_url"),
        )
        cursor = await db.execute(query, values)
        await db.commit()
        return await self.get_book(db, cursor.lastrowid)

    async def update_book(self, db: aiosqlite.Connection, book_id: int, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        if not data:
            return await self.get_book(db, book_id)

        safe_data = {key: value for key, value in data.items() if key in self.ALLOWED_UPDATE_FIELDS}
        if "title" in safe_data and isinstance(safe_data["title"], str):
            safe_data["title"] = sanitize(safe_data["title"], max_len=255)
        if "author" in safe_data and isinstance(safe_data["author"], str):
            safe_data["author"] = sanitize(safe_data["author"], max_len=255)
        if "isbn" in safe_data and isinstance(safe_data["isbn"], str):
            safe_data["isbn"] = sanitize(safe_data["isbn"], max_len=50)
        if "category" in safe_data and isinstance(safe_data["category"], str):
            safe_data["category"] = sanitize(safe_data["category"], max_len=100)
        if "description" in safe_data and isinstance(safe_data["description"], str):
            safe_data["description"] = sanitize(safe_data["description"], max_len=2000)
        if "publisher" in safe_data and isinstance(safe_data["publisher"], str):
            safe_data["publisher"] = sanitize(safe_data["publisher"], max_len=255)
        if "language" in safe_data and isinstance(safe_data["language"], str):
            safe_data["language"] = sanitize(safe_data["language"], max_len=20)
        if "cover_url" in safe_data and isinstance(safe_data["cover_url"], str):
            safe_data["cover_url"] = sanitize(safe_data["cover_url"], max_len=1000)

        if not safe_data:
            return await self.get_book(db, book_id)

        set_clause = ", ".join([key + " = ?" for key in safe_data.keys()])
        params = list(safe_data.values()) + [book_id]
        await db.execute(
            "UPDATE books SET " + set_clause + ", updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params,
        )
        await db.commit()
        return await self.get_book(db, book_id)

    async def delete_book(self, db: aiosqlite.Connection, book_id: int) -> bool:
        cursor = await db.execute("DELETE FROM books WHERE id = ?", (book_id,))
        await db.commit()
        return cursor.rowcount > 0
