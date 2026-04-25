from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from appverbo.routes.entities import create_handler  # noqa: F401,E402
from appverbo.routes.entities import update_handler  # noqa: F401,E402
from appverbo.routes.entities import delete_handler  # noqa: F401,E402

__all__ = ["router"]
