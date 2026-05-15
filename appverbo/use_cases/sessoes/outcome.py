from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SessionActionOutcome:
    redirect_url: str
    redirect_status_code: int = 303


@dataclass(frozen=True)
class SessionJsonOutcome:
    payload: dict[str, Any]
    status_code: int = 200
