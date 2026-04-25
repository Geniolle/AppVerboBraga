from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from appverbo.routes.auth import pages  # noqa: F401,E402
from appverbo.routes.auth import session_handlers  # noqa: F401,E402
from appverbo.routes.auth import invite_handlers  # noqa: F401,E402
from appverbo.routes.auth import oauth_handlers  # noqa: F401,E402

__all__ = ["router"]
