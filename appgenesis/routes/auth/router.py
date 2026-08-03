from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from appgenesis.routes.auth import pages  # noqa: F401,E402
from appgenesis.routes.auth import session_handlers  # noqa: F401,E402
from appgenesis.routes.auth import invite_handlers  # noqa: F401,E402
from appgenesis.routes.auth import oauth_handlers  # noqa: F401,E402
from appgenesis.routes.auth import password_reset_handlers  # noqa: F401,E402

__all__ = ["router"]
