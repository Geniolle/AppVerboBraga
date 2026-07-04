from __future__ import annotations

from typing import Any


####################################################################################
# (1) CONSTANTE DO CONTEXTO DE ORIGEM
####################################################################################

ADMIN_MENU_ORIGIN = "administrativo_menu"


####################################################################################
# (2) NORMALIZAR TEXTO
####################################################################################

def _normalize_text_v1(value: Any) -> str:
    return str(value or "").strip().lower()


####################################################################################
# (3) LER VALOR BOOLEANO
####################################################################################

def _is_truthy_v1(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    clean_value = _normalize_text_v1(value)
    return clean_value in {"1", "true", "sim", "yes", "on"}


####################################################################################
# (4) IDENTIFICAR SE O PROCESSO PERTENCE AO ADMINISTRATIVO -> MENU
####################################################################################

def is_admin_menu_process_v1(
    menu_key: Any,
    menu_config: dict[str, Any] | None = None,
    source_context: Any = "",
) -> bool:
    clean_context = _normalize_text_v1(source_context)

    if clean_context == ADMIN_MENU_ORIGIN:
        return True

    if not isinstance(menu_config, dict):
        return False

    created_from = _normalize_text_v1(menu_config.get("created_from"))

    if created_from == ADMIN_MENU_ORIGIN:
        return True

    if _is_truthy_v1(menu_config.get("settings_tabs_enabled")):
        return True

    if _is_truthy_v1(menu_config.get("admin_process_settings_enabled")):
        return True

    return False
