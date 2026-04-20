import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query, status

from db import get_db
from schemas.book_schemas import BookCreate, BookOut, BooksPage, BookUpdate
from services.book_service import BookService
from utils.security import get_current_admin


router = APIRouter(prefix="/books", tags=["books"])
book_service = BookService()


@router.get("", response_model=BooksPage)
async def list_books(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    q: str | None = None,
    category: str | None = None,
    year: int | None = Query(default=None, ge=0, le=3000),
    available: bool | None = None,
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    db: aiosqlite.Connection = Depends(get_db),
):
    data = await book_service.list_books(
        db=db,
        page=page,
        per_page=per_page,
        q=q,
        category=category,
        year=year,
        available=available,
        sort_by=sort_by,
        order=order,
    )
    return data


@router.get("/{book_id}", response_model=BookOut)
async def get_book(book_id: int, db: aiosqlite.Connection = Depends(get_db)):
    book = await book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreate,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    try:
        return await book_service.create_book(db, payload.model_dump())
    except aiosqlite.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Book already exists or invalid data") from exc


@router.put("/{book_id}", response_model=BookOut)
async def update_book(
    book_id: int,
    payload: BookUpdate,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    existing = await book_service.get_book(db, book_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Book not found")
    data = payload.model_dump(exclude_unset=True)
    updated = await book_service.update_book(db, book_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Book not found")
    return updated


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    deleted = await book_service.delete_book(db, book_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Book not found")
