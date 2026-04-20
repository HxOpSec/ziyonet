from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    mode: Literal["fast", "deep"] = "fast"
    book_id: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    mode: Literal["fast", "deep"]
    response_time_ms: int
    cached: bool = False
