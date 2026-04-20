import time

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from config import settings
from db import get_db
from schemas.chat_schemas import ChatRequest, ChatResponse
from services.book_service import BookService
from services.ollama_client import OptimizedOllamaClient
from utils.security import get_optional_current_admin


router = APIRouter(prefix="/chat", tags=["chat"])
ollama_client = OptimizedOllamaClient()
book_service = BookService()


@router.post("", response_model=ChatResponse)
async def ask_chat(
    payload: ChatRequest,
    db: aiosqlite.Connection = Depends(get_db),
    user: dict | None = Depends(get_optional_current_admin),
):
    context = None
    if payload.book_id is not None:
        book = await book_service.get_book(db, payload.book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        context = (
            f"Название: {book['title']}\n"
            f"Автор: {book['author']}\n"
            f"Категория: {book.get('category') or 'не указана'}\n"
            f"Описание: {book.get('description') or 'нет описания'}"
        )

    started = time.perf_counter()
    try:
        answer, response_time_ms, cached = await ollama_client.ask(
            question=payload.message,
            mode=payload.mode,
            book_context=context,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    measured = int((time.perf_counter() - started) * 1000)
    final_ms = response_time_ms or measured

    await db.execute(
        """
        INSERT INTO ai_logs (user_id, question, answer, model, response_time_ms, mode)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user.get("id") if user else None,
            payload.message,
            answer,
            settings.OLLAMA_MODEL,
            final_ms,
            payload.mode,
        ),
    )
    await db.commit()

    return ChatResponse(answer=answer, mode=payload.mode, response_time_ms=final_ms, cached=cached)
