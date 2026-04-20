from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    isbn: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=0, le=3000)
    publisher: Optional[str] = Field(default=None, max_length=255)
    pages: Optional[int] = Field(default=None, ge=1, le=100000)
    language: str = Field(default="ru", max_length=20)
    copies_total: int = Field(default=1, ge=0, le=100000)
    copies_available: int = Field(default=1, ge=0, le=100000)
    cover_url: Optional[str] = Field(default=None, max_length=1000)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    author: Optional[str] = Field(default=None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=0, le=3000)
    publisher: Optional[str] = Field(default=None, max_length=255)
    pages: Optional[int] = Field(default=None, ge=1, le=100000)
    language: Optional[str] = Field(default=None, max_length=20)
    copies_total: Optional[int] = Field(default=None, ge=0, le=100000)
    copies_available: Optional[int] = Field(default=None, ge=0, le=100000)
    cover_url: Optional[str] = Field(default=None, max_length=1000)


class BookOut(BookBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BooksPage(BaseModel):
    items: list[BookOut]
    total: int
    page: int
    per_page: int
