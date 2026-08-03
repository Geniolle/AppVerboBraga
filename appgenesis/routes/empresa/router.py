from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from appgenesis.routes.empresa import update_handler  # noqa: F401,E402

__all__ = ["router"]
