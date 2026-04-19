from pydantic import BaseModel


class PopularBookItem(BaseModel):
    book_id: int
    title: str
    asks: int


class AIUsageItem(BaseModel):
    day: str
    fast_count: int
    deep_count: int
    avg_response_time_ms: int
