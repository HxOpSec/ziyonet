from typing import Any, Optional

import aiosqlite

from config import settings
from utils.validators import normalize_order, normalize_sort


class BookService:
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
            where.append("(title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?)")
            like = f"%{q}%"
            params.extend([like, like, like, like])
        if category:
            where.append("category = ?")
            params.append(category)
        if year:
            where.append("year = ?")
            params.append(year)
        if available is not None:
            where.append("copies_available > 0" if available else "copies_available = 0")

        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        sort_sql = normalize_sort(sort_by)
        order_sql = normalize_order(order)

        total_cursor = await db.execute(f"SELECT COUNT(*) as total FROM books {where_clause}", params)
        total_row = await total_cursor.fetchone()
        total = total_row["total"] if total_row else 0

        query = f"""
            SELECT *
            FROM books
            {where_clause}
            ORDER BY {sort_sql} {order_sql}
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
        query = """
            INSERT INTO books (
                title, author, isbn, category, description, year, publisher,
                pages, language, copies_total, copies_available, cover_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            data.get("title"),
            data.get("author"),
            data.get("isbn"),
            data.get("category"),
            data.get("description"),
            data.get("year"),
            data.get("publisher"),
            data.get("pages"),
            data.get("language", "ru"),
            data.get("copies_total", 1),
            data.get("copies_available", 1),
            data.get("cover_url"),
        )
        cursor = await db.execute(query, values)
        await db.commit()
        return await self.get_book(db, cursor.lastrowid)

    async def update_book(self, db: aiosqlite.Connection, book_id: int, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        if not data:
            return await self.get_book(db, book_id)

        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        params = list(data.values()) + [book_id]
        await db.execute(
            f"UPDATE books SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params,
        )
        await db.commit()
        return await self.get_book(db, book_id)

    async def delete_book(self, db: aiosqlite.Connection, book_id: int) -> bool:
        cursor = await db.execute("DELETE FROM books WHERE id = ?", (book_id,))
        await db.commit()
        return cursor.rowcount > 0
