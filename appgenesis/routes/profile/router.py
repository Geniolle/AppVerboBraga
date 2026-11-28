from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

from appgenesis.routes.profile import page_handler  # noqa: F401,E402
from appgenesis.routes.profile.handlers import sidebar_sections  # noqa: F401,E402
from appgenesis.routes.profile.handlers import menu_subprocess  # noqa: F401,E402
from appgenesis.routes.profile.handlers import auth_profile  # noqa: F401,E402
from appgenesis.routes.profile.handlers import personal  # noqa: F401,E402
from appgenesis.routes.profile.handlers import process_data  # noqa: F401,E402
from appgenesis.routes.profile.handlers import admin_lists  # noqa: F401,E402

__all__ = [
    "router",
    "admin_lists",
    "auth_profile",
    "menu_subprocess",
    "page_handler",
    "personal",
    "process_data",
    "sidebar_sections",
]
