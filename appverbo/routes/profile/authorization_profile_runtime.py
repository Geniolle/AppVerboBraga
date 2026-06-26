from __future__ import annotations

from typing import Any

from appverbo.routes.profile import profile_handlers


def _normalize_authorization_profile_lookup_v1(value: Any) -> str:
    """Normaliza texto para identificar o processo Perfil de autorização."""
    normalized = profile_handlers._normalize_lookup_text(value)
    normalized = normalized.replace("_", " ").replace("-", " ")
    return " ".join(normalized.split())


def _is_authorization_profile_process_v1(
    menu_key: Any,
    process_setting: dict[str, Any] | None = None,
    section_key: Any = "",
) -> bool:
    """Identifica o processo dinâmico Perfil de autorização sem alterar outros processos."""
    process_label = ""
    if isinstance(process_setting, dict):
        process_label = str(process_setting.get("label") or "")

    joined = " ".join(
        part
        for part in (
            _normalize_authorization_profile_lookup_v1(menu_key),
            _normalize_authorization_profile_lookup_v1(process_label),
            _normalize_authorization_profile_lookup_v1(section_key),
        )
        if part
    )

    if not joined:
        return False

    return (
        ("perfil" in joined and "autorizacao" in joined)
        or ("profile" in joined and "authorization" in joined)
    )


_original_is_history_process_v1 = profile_handlers._is_history_process


def _is_history_process_with_authorization_profile_v1(
    menu_key: str,
    process_setting: dict[str, Any] | None = None,
    section_key: str = "",
) -> bool:
    """Permite que Perfil de autorização use a lista de registos/criação."""
    if _is_authorization_profile_process_v1(menu_key, process_setting, section_key):
        return True

    return _original_is_history_process_v1(menu_key, process_setting, section_key)


profile_handlers._is_history_process = _is_history_process_with_authorization_profile_v1
