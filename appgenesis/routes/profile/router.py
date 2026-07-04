from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from appgenesis.routes.profile import page_handler  # noqa: F401,E402
from appgenesis.routes.profile import settings_handlers  # noqa: F401,E402
from appgenesis.routes.profile import profile_handlers  # noqa: F401,E402

__all__ = ["router"]
