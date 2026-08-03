from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from appgenesis.routes.webhooks import verify_handler  # noqa: F401,E402
from appgenesis.routes.webhooks import receive_handler  # noqa: F401,E402

__all__ = ["router"]
