from __future__ import annotations

_TRUE_VALUES = {"1", "true", "yes", "on", "ativo", "active"}
_FALSE_VALUES = {"0", "false", "no", "off", "inativo", "inactive"}


def normalize_text(value: object, *, default: str = "") -> str:
    """Trim and coerce any value to a plain string, never None."""

    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def normalize_bool(value: object, *, default: bool = False) -> bool:
    """Coerce common truthy/falsy representations (str, bool, int) to bool."""

    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    return default


def normalize_int(value: object, *, default: int | None = None) -> int | None:
    """Coerce a value to int, returning default when it cannot be parsed."""

    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if value is None:
        return default
    text = str(value).strip()
    if not text or not text.lstrip("-").isdigit():
        return default
    return int(text)


def normalize_key(value: object, *, default: str = "") -> str:
    """Normalize a value into a lowercase snake-case-safe key fragment."""

    text = normalize_text(value, default=default)
    return text.strip().lower().replace(" ", "_")


__all__ = ["normalize_text", "normalize_bool", "normalize_int", "normalize_key"]
