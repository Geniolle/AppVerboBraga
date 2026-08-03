from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RedirectOutcome:
    """A use case result that should become an HTTP redirect."""

    url: str
    status_code: int = 303


@dataclass(frozen=True)
class TemplateOutcome:
    """A use case result that should render a Jinja2 template."""

    template_name: str
    context: dict[str, Any] = field(default_factory=dict)
    status_code: int = 200


@dataclass(frozen=True)
class JsonOutcome:
    """A use case result that should be serialized as JSON."""

    payload: dict[str, Any]
    status_code: int = 200


Outcome = RedirectOutcome | TemplateOutcome | JsonOutcome


@dataclass(frozen=True)
class UseCaseResult:
    """Generic wrapper returned by use cases before conversion to an HTTP outcome."""

    outcome: Outcome
    data: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "RedirectOutcome",
    "TemplateOutcome",
    "JsonOutcome",
    "Outcome",
    "UseCaseResult",
]
