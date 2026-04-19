import hashlib
import time
from typing import Optional

import httpx

from config import settings
from services.cache_service import TTLCache


class OptimizedOllamaClient:
    def __init__(self):
        self.cache = TTLCache(settings.CACHE_MAX_SIZE)

    def _cache_key(self, question: str, mode: str, context: Optional[str]) -> str:
        payload = f"{mode}|{question.strip()}|{context or ''}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def ask(
        self,
        question: str,
        mode: str = "fast",
        book_context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple[str, int, bool]:
        key = self._cache_key(question, mode, book_context)
        cached = await self.cache.get(key)
        if cached is not None:
            return cached, 0, True

        is_deep = mode == "deep"
        timeout_seconds = settings.DEEP_MODE_TIMEOUT if is_deep else settings.FAST_MODE_TIMEOUT
        num_predict = max_tokens or (settings.DEEP_MODE_TOKENS if is_deep else settings.FAST_MODE_TOKENS)
        ttl = settings.CACHE_TTL_DEEP if is_deep else settings.CACHE_TTL_FAST

        system_prompt = (
            "Ты библиотечный ИИ-ассистент Ziyonet. Отвечай точно и по делу. "
            "Если данных недостаточно, скажи об этом явно."
        )
        if book_context:
            user_content = f"Контекст книги:\n{book_context}\n\nВопрос: {question}"
        else:
            user_content = question

        payload = {
            "model": settings.OLLAMA_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "options": {
                "num_threads": settings.OLLAMA_NUM_THREADS,
                "num_predict": num_predict,
                "num_ctx": 1024,
                "temperature": temperature if temperature is not None else 0.3,
            },
        }

        last_error = None
        started = time.perf_counter()
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                    response = await client.post(settings.OLLAMA_URL, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    answer = (
                        data.get("message", {}).get("content")
                        or data.get("response")
                        or "Не удалось получить ответ от модели."
                    )
                    elapsed_ms = int((time.perf_counter() - started) * 1000)
                    await self.cache.set(key, answer, ttl)
                    return answer, elapsed_ms, False
            except Exception as exc:
                last_error = exc
                continue

        raise RuntimeError(f"Ollama request failed: {last_error}")
