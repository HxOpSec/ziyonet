import html
import re


def sanitize_text(value: str) -> str:
    return sanitize(value)


def sanitize(value: str | None, max_len: int = 1000) -> str:
    if not value:
        return ""
    cleaned = value[:max_len]
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    return html.escape(cleaned.strip())


ALLOWED_SORT_FIELDS = {
    "title": "title",
    "year": "year",
    "created_at": "created_at",
}


def normalize_sort(sort_by: str) -> str:
    return ALLOWED_SORT_FIELDS.get(sort_by, "created_at")


def normalize_order(order: str) -> str:
    return "ASC" if order.lower() == "asc" else "DESC"
