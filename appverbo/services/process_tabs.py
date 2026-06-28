from typing import Any


_SYSTEM_HARDCODED_PROCESS_KEYS: frozenset[str] = frozenset({"administrativo", "sessoes"})


def is_system_hardcoded_process(menu_key: str) -> bool:
    """Returns True only for processes whose fields are always hardcoded (never dynamic)."""
    return str(menu_key or "").strip().lower() in _SYSTEM_HARDCODED_PROCESS_KEYS


def resolve_subprocess_section_fields_v1(
    menu_key: str,
    section_header_key: str,
    sidebar_menu_settings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Resolver reutilizável: retorna os campos configurados para uma secção de um subprocesso dinâmico.
    Filtra por header_key == section_header_key em process_visible_field_rows do processo menu_key.
    Retorna [] para processos do sistema (Administrativo, Estruturas).
    """
    clean_menu_key = str(menu_key or "").strip().lower()
    if is_system_hardcoded_process(clean_menu_key):
        return []

    clean_header_key = str(section_header_key or "").strip().lower()
    if not clean_menu_key or not clean_header_key:
        return []

    for setting in sidebar_menu_settings:
        if not isinstance(setting, dict):
            continue
        if str(setting.get("key") or "").strip().lower() != clean_menu_key:
            continue

        field_options_by_key: dict[str, dict[str, Any]] = {
            str(opt.get("key") or "").strip().lower(): opt
            for opt in (setting.get("process_field_options") or [])
            if isinstance(opt, dict) and str(opt.get("key") or "").strip()
            and opt.get("field_type") != "header"
        }

        result: list[dict[str, Any]] = []
        seen: set[str] = set()

        for row in (setting.get("process_visible_field_rows") or []):
            if not isinstance(row, dict):
                continue
            if str(row.get("header_key") or "").strip().lower() != clean_header_key:
                continue
            field_key = str(row.get("field_key") or "").strip().lower()
            if not field_key or field_key in seen:
                continue
            seen.add(field_key)
            opt = field_options_by_key.get(field_key)
            if opt:
                result.append(dict(opt))

        return result

    return []


class ProcessTabConfig:
    def __init__(
        self,
        key: str,
        label: str,
        target: str,
        layout_type: str = "list",  # "list", "form", "custom"
        dynamic_process_section: str = "",
    ):
        self.key = key
        self.label = label
        self.target = target
        self.layout_type = layout_type
        self.dynamic_process_section = dynamic_process_section

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "target": self.target,
            "layout_type": self.layout_type,
            "dynamic_process_section": self.dynamic_process_section,
        }


def resolve_process_tabs_v1(menu_key: str, sidebar_menu_settings: list[dict[str, Any]]) -> list[ProcessTabConfig]:
    clean_menu = str(menu_key or "").strip().lower()
    
    # 1. Base hardcoded configurations for core admin sub-processes
    if clean_menu == "administrativo":
        return [
            ProcessTabConfig("entidade", "Entidade", "#create-entity-card", "custom"),
            ProcessTabConfig("utilizador", "Utilizador", "#create-user-card", "custom"),
        ]
    elif clean_menu == "sessoes":
        return [
            ProcessTabConfig("sessoes", "Sessões", "#admin-sidebar-sections-card", "custom"),
            ProcessTabConfig("contas", "Menu", "#menu-subprocess-card-active", "custom"),
        ]
    elif clean_menu == "perfil_de_autorizacao":
        return [
            ProcessTabConfig("perfis", "Perfis", "#auth-profile-card", "list"),
            ProcessTabConfig("objeto_de_autorizacao", "Objeto de autorização", "#auth-objeto-card", "list"),
        ]

    # 2. Dynamic processes sections resolution (e.g. from header options)
    for setting in sidebar_menu_settings:
        if not isinstance(setting, dict):
            continue
        setting_key = str(setting.get("key") or "").strip().lower()
        if setting_key == clean_menu:
            raw_rows = setting.get("process_visible_field_rows")
            if isinstance(raw_rows, list) and raw_rows:
                section_order = []
                seen_sections = set()
                first_field_key = ""
                section_labels = {}

                header_labels = {}
                for opt in setting.get("process_field_options", []):
                    if not isinstance(opt, dict):
                        continue
                    opt_key = str(opt.get("key") or "").strip().lower()
                    if opt.get("field_type") == "header" and opt_key:
                        header_labels[opt_key] = str(opt.get("label") or "").strip()

                for raw_row in raw_rows:
                    if not isinstance(raw_row, dict):
                        continue
                    field_key = str(raw_row.get("field_key") or "").strip().lower()
                    if not field_key:
                        continue
                    if not first_field_key:
                        first_field_key = field_key
                    header_key = str(raw_row.get("header_key") or "").strip().lower()
                    section_key = header_key or "__geral__"

                    if section_key not in seen_sections:
                        seen_sections.add(section_key)
                        section_order.append(section_key)
                        
                        setting_label = str(setting.get("label") or "").strip()
                        default_fallback = setting_label if section_key == "__geral__" else section_key.replace("_", " ").title()
                        section_labels[section_key] = header_labels.get(section_key) or default_fallback

                if section_order and not (len(section_order) == 1 and section_order[0] == "__geral__"):
                    tabs = []
                    for s_key in section_order:
                        layout = "list" if setting.get("is_list_process") else "form"
                        tabs.append(ProcessTabConfig(s_key, section_labels[s_key], "#dynamic-process-card", layout, s_key))
                    return tabs
            break

    return []
