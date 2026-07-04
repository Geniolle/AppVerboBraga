from __future__ import annotations

from typing import Any

from .admin_tabs import (
    get_admin_process_settings_tabs_v1,
    resolve_admin_process_settings_tab_v1,
)
from .menu_origin import is_admin_menu_process_v1


####################################################################################
# (1) MONTAR CONTEXTO DAS ABAS PARA A TELA DE EDICAO DO PROCESSO
####################################################################################

def build_admin_process_settings_context_v1(
    menu_key: Any,
    menu_config: dict[str, Any] | None = None,
    raw_settings_tab: Any = "",
    source_context: Any = "",
) -> dict[str, Any]:
    settings_tabs_enabled = is_admin_menu_process_v1(
        menu_key=menu_key,
        menu_config=menu_config,
        source_context=source_context,
    )

    if not settings_tabs_enabled:
        return {
            "settings_tabs_enabled": False,
            "settings_tabs": [],
            "settings_tab": "",
        }

    return {
        "settings_tabs_enabled": True,
        "settings_tabs": get_admin_process_settings_tabs_v1(),
        "settings_tab": resolve_admin_process_settings_tab_v1(raw_settings_tab),
    }
