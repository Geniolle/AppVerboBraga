from __future__ import annotations

from typing import Any


####################################################################################
# (1) DEFINICAO GLOBAL DAS ABAS DO ADMINISTRATIVO -> MENU
####################################################################################

ADMIN_PROCESS_SETTINGS_TABS: tuple[dict[str, str], ...] = (
    {"key": "geral", "label": "Geral"},
    {"key": "configuracao_campos", "label": "Configuração dos campos"},
    {"key": "campos_adicionais", "label": "Campos adicionais"},
    {"key": "lista", "label": "Lista"},
)


####################################################################################
# (2) NORMALIZAR CHAVE DA ABA
####################################################################################

def normalize_settings_tab_key_v1(value: Any) -> str:
    clean_value = str(value or "").strip().lower()
    clean_value = clean_value.replace("-", "_")
    return clean_value


####################################################################################
# (3) DEVOLVER ABAS PADRAO
####################################################################################

def get_admin_process_settings_tabs_v1() -> list[dict[str, str]]:
    return [dict(item) for item in ADMIN_PROCESS_SETTINGS_TABS]


####################################################################################
# (4) RESOLVER ABA ATIVA
####################################################################################

def resolve_admin_process_settings_tab_v1(raw_tab: Any) -> str:
    clean_tab = normalize_settings_tab_key_v1(raw_tab)

    available_tabs = {
        str(item["key"]).strip().lower()
        for item in ADMIN_PROCESS_SETTINGS_TABS
    }

    if clean_tab in available_tabs:
        return clean_tab

    return "geral"
