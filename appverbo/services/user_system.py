from __future__ import annotations

ALLOWED_USER_SYSTEM_TYPES = {"default", "owner", "legado"}

_USER_SYSTEM_TYPE_LABELS: dict[str, str] = {
    "default": "Default",
    "owner": "Owner",
    "legado": "Legado",
}


def normalize_user_system_type_v1(value: str | None) -> str:
    clean = (value or "").strip().lower()
    return clean if clean in ALLOWED_USER_SYSTEM_TYPES else "default"


def get_user_system_type_label_v1(value: str | None) -> str:
    return _USER_SYSTEM_TYPE_LABELS.get(normalize_user_system_type_v1(value), "Default")


def is_owner_system_v1(value: str | None) -> bool:
    return normalize_user_system_type_v1(value) == "owner"


__all__ = [
    "ALLOWED_USER_SYSTEM_TYPES",
    "normalize_user_system_type_v1",
    "get_user_system_type_label_v1",
    "is_owner_system_v1",
]
