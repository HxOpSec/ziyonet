import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status

from db import get_db
from schemas.user_schemas import TokenResponse, UserCreate, UserLogin, UserOut
from utils.security import create_access_token, get_current_admin, get_password_hash, verify_password


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute(
        "SELECT id, username, password_hash, is_active FROM users WHERE username = ?",
        (payload.username,),
    )
    user = await cursor.fetchone()
    if not user or not user["is_active"] or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(payload.username)
    return TokenResponse(access_token=token)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: UserCreate,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    try:
        cursor = await db.execute(
            "INSERT INTO users (username, password_hash, email, is_active) VALUES (?, ?, ?, 1)",
            (payload.username, get_password_hash(payload.password), payload.email),
        )
        await db.commit()
        user_id = cursor.lastrowid
        created = await db.execute(
            "SELECT id, username, email, is_active FROM users WHERE id = ?",
            (user_id,),
        )
        row = await created.fetchone()
        return dict(row)
    except aiosqlite.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Username already exists") from exc


@router.get("/stats")
async def get_stats(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    books_row = await (await db.execute("SELECT COUNT(*) as c FROM books")).fetchone()
    logs_row = await (await db.execute("SELECT COUNT(*) as c FROM ai_logs")).fetchone()
    users_row = await (await db.execute("SELECT COUNT(*) as c FROM users")).fetchone()
    return {
        "books_total": books_row["c"] if books_row else 0,
        "ai_requests_total": logs_row["c"] if logs_row else 0,
        "users_total": users_row["c"] if users_row else 0,
    }


@router.get("/logs")
async def get_logs(
    page: int = 1,
    per_page: int = 20,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    page = max(1, page)
    per_page = max(1, min(100, per_page))
    offset = (page - 1) * per_page

    total_row = await (await db.execute("SELECT COUNT(*) as c FROM ai_logs")).fetchone()
    cursor = await db.execute(
        """
        SELECT l.*, u.username
        FROM ai_logs l
        LEFT JOIN users u ON u.id = l.user_id
        ORDER BY l.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (per_page, offset),
    )
    rows = await cursor.fetchall()
    return {
        "items": [dict(row) for row in rows],
        "total": total_row["c"] if total_row else 0,
        "page": page,
        "per_page": per_page,
    }
