"""Versao de assets estaticos (cache buster) para os templates.

Cada arranque do processo gera uma versao nova, por isso um deploy invalida a
cache do browser sem editar templates. APP_ASSET_VERSION, se definida, fixa a
versao (util para testes ou para forcar uma versao conhecida).
"""

from __future__ import annotations

import os
import time

ASSET_VERSION: str = (os.getenv("APP_ASSET_VERSION") or "").strip() or str(int(time.time()))
