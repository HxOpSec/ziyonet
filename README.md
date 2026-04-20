# Ziyonet

Профессиональная веб-библиотека университета с локальным ИИ-ассистентом (Ollama).

## Возможности
- Каталог книг: поиск, фильтры, сортировка, пагинация
- Чат с ИИ: режимы `fast` и `deep`
- Админка: JWT-авторизация, CRUD книг, статистика, логи ИИ
- Аналитика: популярные книги, использование ИИ, экспорт CSV/PDF
- Оптимизации: in-memory TTL+LRU cache, индексы SQLite, gzip, debounce на фронтенде

## Структура
- `/backend` — FastAPI + SQLite + сервисы ИИ
- `/frontend` — HTML/CSS/JS интерфейс каталога и админки
- `/docs` — архитектурные заметки

## Быстрый старт
```bash
cd /home/runner/work/ziyonet/ziyonet/backend
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Открыть:
- Главная: `http://localhost:8000/`
- Админка: `http://localhost:8000/admin.html`

По умолчанию создаётся админ:
- `admin / admin123` (переопределяется через `.env`)

## Основные API
- `GET /api/books`
- `GET /api/books/{id}`
- `POST /api/books` (admin)
- `PUT /api/books/{id}` (admin)
- `DELETE /api/books/{id}` (admin)
- `POST /api/chat`
- `POST /api/admin/login`
- `GET /api/admin/stats` (admin)
- `GET /api/admin/logs` (admin)
- `GET /api/analytics/popular-books` (admin)
- `GET /api/analytics/ai-usage` (admin)
