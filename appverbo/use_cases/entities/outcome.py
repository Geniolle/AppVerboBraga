from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EntityActionOutcome:
    kind: str
    redirect_url: str = ""
    redirect_status_code: int = 303
    template_context: dict[str, Any] | None = None
    template_status_code: int = 400

