from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from appverbo.routes.webhooks import verify_handler  # noqa: F401,E402
from appverbo.routes.webhooks import receive_handler  # noqa: F401,E402

__all__ = ["router"]
