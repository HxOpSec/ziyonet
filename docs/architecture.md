# Architecture

## Backend
- **Framework**: FastAPI
- **DB**: SQLite (`aiosqlite`), таблицы `books`, `users`, `ai_logs`
- **Security**: JWT (`python-jose`), bcrypt (`passlib`), CORS, in-memory rate limit
- **AI**: `OptimizedOllamaClient` с retry, timeout, кэшем TTL/LRU, режимами `fast/deep`
- **API modules**:
  - `api/books_api.py`
  - `api/chat_api.py`
  - `api/admin_api.py`
  - `api/analytics_api.py`

## Frontend
- Чистый HTML/CSS/JS, без тяжелых фреймворков
- Главная: каталог + чат
- Админка: авторизация, CRUD книг, статистика
- Оптимизации: debounce поиска, lazy loading, localStorage cache и избранное

## Data flow
1. Пользователь выполняет поиск/фильтр книг через `/api/books`.
2. Вопросы к ИИ идут в `/api/chat`, далее в Ollama.
3. Ответы ИИ логируются в `ai_logs`.
4. Админ получает статистику через `/api/admin/stats` и `/api/analytics/*`.
