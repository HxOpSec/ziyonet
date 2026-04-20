import html


def sanitize_text(value: str) -> str:
    return html.escape(value.strip())


ALLOWED_SORT_FIELDS = {
    "title": "title",
    "year": "year",
    "created_at": "created_at",
}


def normalize_sort(sort_by: str) -> str:
    return ALLOWED_SORT_FIELDS.get(sort_by, "created_at")


def normalize_order(order: str) -> str:
    return "ASC" if order.lower() == "asc" else "DESC"
