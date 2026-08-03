from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, TypeVar

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 10


@dataclass(frozen=True)
class Page:
    items: list
    page: int
    page_size: int
    total_items: int

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 1
        return max(1, -(-self.total_items // self.page_size))


def paginate(items: Sequence[T], page: int, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
    """Slice an in-memory sequence into a Page. Does not query the database."""

    safe_page = max(1, page)
    safe_page_size = max(1, page_size)
    start = (safe_page - 1) * safe_page_size
    end = start + safe_page_size
    return Page(
        items=list(items[start:end]),
        page=safe_page,
        page_size=safe_page_size,
        total_items=len(items),
    )


__all__ = ["Page", "paginate", "DEFAULT_PAGE_SIZE"]
