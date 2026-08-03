from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from appgenesis.routes.users import helpers  # noqa: F401,E402
from appgenesis.routes.users import create_handler  # noqa: F401,E402
from appgenesis.routes.users import resend_handler  # noqa: F401,E402
from appgenesis.routes.users import update_handler  # noqa: F401,E402
from appgenesis.routes.users import delete_handler  # noqa: F401,E402

__all__ = ["router"]
