from __future__ import annotations

"""Instancia unica de Jinja2Templates (antes em ``appgenesis.core``).

Uma segunda instancia teria cache e globals proprios e podia divergir da que
`appgenesis/app.py` usa para renderizar.
"""

from fastapi.templating import Jinja2Templates

from appgenesis.config.settings import settings
from appgenesis.services.static_assets import ASSET_VERSION

templates = Jinja2Templates(directory=str(settings.BASE_DIR / "templates"))
templates.env.globals["asset_version"] = ASSET_VERSION

__all__ = ["templates"]
