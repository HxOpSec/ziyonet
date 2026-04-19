from datetime import datetime

import aiosqlite
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from db import get_db
from utils.security import get_current_admin


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/popular-books")
async def popular_books(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    cursor = await db.execute(
        """
        SELECT b.id as book_id, b.title, COUNT(*) as asks
        FROM ai_logs l
        JOIN books b ON instr(lower(l.question), lower(b.title)) > 0
        GROUP BY b.id, b.title
        ORDER BY asks DESC
        LIMIT 10
        """
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@router.get("/ai-usage")
async def ai_usage(
    days: int = Query(default=30, ge=1, le=365),
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    cursor = await db.execute(
        """
        SELECT
            date(created_at) as day,
            SUM(CASE WHEN mode = 'fast' THEN 1 ELSE 0 END) as fast_count,
            SUM(CASE WHEN mode = 'deep' THEN 1 ELSE 0 END) as deep_count,
            COALESCE(AVG(response_time_ms), 0) as avg_response_time_ms
        FROM ai_logs
        WHERE created_at >= datetime('now', ?)
        GROUP BY date(created_at)
        ORDER BY day DESC
        """,
        (f"-{days} day",),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@router.get("/export/csv")
async def export_books_csv(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    cursor = await db.execute("SELECT id, title, author, isbn, category, year, copies_available FROM books ORDER BY title")
    rows = await cursor.fetchall()
    lines = ["id,title,author,isbn,category,year,copies_available"]
    for row in rows:
        values = [str(row[k] or "").replace('"', '""') for k in row.keys()]
        lines.append(",".join([f'"{v}"' for v in values]))
    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=books.csv"},
    )


@router.get("/export/pdf")
async def export_books_pdf(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    cursor = await db.execute("SELECT title, author, year FROM books ORDER BY title LIMIT 200")
    rows = await cursor.fetchall()
    text = "\\n".join([f"{row['title']} — {row['author']} ({row['year'] or 'n/a'})" for row in rows]) or "No books"
    safe_text = text.replace("(", "[").replace(")", "]")

    pdf_lines = [
        "%PDF-1.4",
        "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj",
        "2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj",
        "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj",
        f"4 0 obj<< /Length {len(safe_text) + 40} >>stream\nBT /F1 10 Tf 40 800 Td ({safe_text[:2000]}) Tj ET\nendstream endobj",
        "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj",
        "xref\n0 6\n0000000000 65535 f ",
        "trailer<< /Size 6 /Root 1 0 R >>",
        "startxref\n0\n%%EOF",
    ]
    binary = "\n".join(pdf_lines).encode("latin-1", errors="ignore")
    return Response(
        content=binary,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=books-{datetime.utcnow().date()}.pdf"
        },
    )
