import html
from html.parser import HTMLParser


def sanitize_text(value: str) -> str:
    return sanitize(value)


def sanitize(value: str | None, max_len: int = 1000) -> str:
    if not value:
        return ""
    cleaned = value[:max_len]
    cleaned = _strip_html_tags(cleaned)
    return html.escape(cleaned.strip())


def _strip_html_tags(value: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(value)
    stripper.close()
    return stripper.get_data()


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_data(self) -> str:
        return "".join(self._parts)


ALLOWED_SORT_FIELDS = {
    "title": "title",
    "year": "year",
    "created_at": "created_at",
}


def normalize_sort(sort_by: str) -> str:
    return ALLOWED_SORT_FIELDS.get(sort_by, "created_at")


def normalize_order(order: str) -> str:
    return "ASC" if order.lower() == "asc" else "DESC"
