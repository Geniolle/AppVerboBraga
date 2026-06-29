from typing import Any


_SYSTEM_HARDCODED_PROCESS_KEYS: frozenset[str] = frozenset({"administrativo", "sessoes"})

_SUPPORTED_RENDER_FIELD_TYPES_V1: frozenset[str] = frozenset(
    {"text", "number", "email", "phone", "date", "flag", "header", "list"}
)
_TEXTUAL_RENDER_FIELD_TYPES_V1: frozenset[str] = frozenset(
    {"text", "number", "email", "phone"}
)


# ###################################################################################
# (1) HELPERS DE NORMALIZACAO E ENRIQUECIMENTO
# ###################################################################################


def _normalize_process_tab_lookup_v1(raw_value: Any) -> str:
    return str(raw_value or "").strip().lower()


def _normalize_process_tab_field_type_v1(raw_value: Any) -> str:
    clean_type = _normalize_process_tab_lookup_v1(raw_value)
    if clean_type in _SUPPORTED_RENDER_FIELD_TYPES_V1:
        return clean_type
    return "text"


def _normalize_process_tab_bool_v1(raw_value: Any) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    return _normalize_process_tab_lookup_v1(raw_value) in {"1", "true", "sim", "yes", "on"}


def _normalize_process_tab_size_v1(raw_size: Any, field_type: str) -> int | None:
    if field_type not in _TEXTUAL_RENDER_FIELD_TYPES_V1:
        return None
    try:
        parsed_size = int(str(raw_size or "").strip())
    except (TypeError, ValueError):
        return None
    return parsed_size if parsed_size > 0 else None


def _normalize_process_tab_list_source_type_v1(raw_value: Any, field_definition: dict[str, Any]) -> str:
    clean_source_type = _normalize_process_tab_lookup_v1(raw_value)
    if clean_source_type in {"manual", "automatic"}:
        return clean_source_type
    if (
        field_definition.get("automatic_source_process_key")
        or field_definition.get("automaticSourceProcessKey")
        or field_definition.get("automatic_source_field_key")
        or field_definition.get("automaticSourceFieldKey")
    ):
        return "automatic"
    return "manual"


def _build_render_input_type_v1(field_type: str) -> str:
    if field_type == "list":
        return "select"
    if field_type == "phone":
        return "tel"
    if field_type == "flag":
        return "checkbox"
    if field_type in {"number", "email", "date"}:
        return field_type
    return "text"


def _normalize_render_options_v1(raw_options: Any) -> list[dict[str, str]]:
    if not isinstance(raw_options, list):
        return []

    normalized_options: list[dict[str, str]] = []
    seen_values: set[str] = set()

    for raw_option in raw_options:
        if isinstance(raw_option, dict):
            clean_value = str(
                raw_option.get("value")
                or raw_option.get("key")
                or raw_option.get("label")
                or ""
            ).strip()
            clean_label = str(
                raw_option.get("label")
                or raw_option.get("value")
                or raw_option.get("key")
                or ""
            ).strip()
            clean_status = str(raw_option.get("status") or "").strip().lower()
        else:
            clean_value = str(raw_option or "").strip()
            clean_label = clean_value
            clean_status = ""

        if not clean_value or not clean_label:
            continue

        option_lookup = clean_value.lower()
        if option_lookup in seen_values:
            continue

        seen_values.add(option_lookup)
        normalized_options.append(
            {
                "value": clean_value,
                "label": clean_label,
                "status": clean_status,
            }
        )

    return normalized_options


def _build_render_field_meta_map_v1(
    *,
    menu_key: str,
    setting: dict[str, Any],
    sidebar_menu_settings: list[dict[str, Any]],
    visible_sidebar_menu_keys: set[str] | list[str] | tuple[str, ...] | None = None,
    menu_process_history_map: dict[str, list[dict[str, Any]]] | None = None,
    active_entity_id: int | None = None,
) -> dict[str, dict[str, Any]]:
    normalized_fields_by_key: dict[str, dict[str, Any]] = {}

    for collection_key in ("process_additional_fields", "process_field_options"):
        raw_fields = setting.get(collection_key)
        if not isinstance(raw_fields, list):
            continue

        for raw_field in raw_fields:
            if not isinstance(raw_field, dict):
                continue

            field_key = _normalize_process_tab_lookup_v1(raw_field.get("key"))
            if not field_key:
                continue

            existing_field = normalized_fields_by_key.get(field_key, {})
            field_type = _normalize_process_tab_field_type_v1(
                existing_field.get("field_type")
                or raw_field.get("field_type")
                or raw_field.get("type")
            )
            normalized_field: dict[str, Any] = {
                "key": field_key,
                "label": str(
                    raw_field.get("label")
                    or existing_field.get("label")
                    or field_key
                ).strip()
                or field_key,
                "field_type": field_type,
                "input_type": _build_render_input_type_v1(field_type),
                "required": _normalize_process_tab_bool_v1(
                    raw_field.get("is_required", raw_field.get("required", existing_field.get("required")))
                )
                if field_type != "header"
                else False,
                "size": _normalize_process_tab_size_v1(
                    raw_field.get("size", existing_field.get("size")),
                    field_type,
                ),
                "list_source_type": _normalize_process_tab_list_source_type_v1(
                    raw_field.get("list_source_type")
                    or raw_field.get("listSourceType")
                    or existing_field.get("list_source_type"),
                    raw_field,
                ),
                "manual_list_key": _normalize_process_tab_lookup_v1(
                    raw_field.get("manual_list_key")
                    or raw_field.get("manualListKey")
                    or raw_field.get("list_key")
                    or raw_field.get("listKey")
                    or existing_field.get("manual_list_key")
                ),
                "list_key": _normalize_process_tab_lookup_v1(
                    raw_field.get("list_key")
                    or raw_field.get("listKey")
                    or raw_field.get("manual_list_key")
                    or raw_field.get("manualListKey")
                    or existing_field.get("list_key")
                ),
                "automatic_source_process_key": _normalize_process_tab_lookup_v1(
                    raw_field.get("automatic_source_process_key")
                    or raw_field.get("automaticSourceProcessKey")
                    or existing_field.get("automatic_source_process_key")
                ),
                "automatic_source_section_key": _normalize_process_tab_lookup_v1(
                    raw_field.get("automatic_source_section_key")
                    or raw_field.get("automaticSourceSectionKey")
                    or existing_field.get("automatic_source_section_key")
                ),
                "automatic_source_field_key": _normalize_process_tab_lookup_v1(
                    raw_field.get("automatic_source_field_key")
                    or raw_field.get("automaticSourceFieldKey")
                    or existing_field.get("automatic_source_field_key")
                ),
                "automatic_only_active": _normalize_process_tab_bool_v1(
                    raw_field.get("automatic_only_active")
                    or raw_field.get("automaticOnlyActive")
                    or existing_field.get("automatic_only_active")
                ),
                "options": [],
            }

            if field_type == "list":
                pre_resolved_options = _normalize_render_options_v1(
                    raw_field.get("resolved_list_options")
                    or raw_field.get("resolved_options")
                    or raw_field.get("options")
                    or raw_field.get("list_options")
                    or existing_field.get("options")
                )
                if pre_resolved_options:
                    normalized_field["options"] = pre_resolved_options
                else:
                    from appverbo.services.profile import resolve_field_list_options_v1

                    resolved_options = _normalize_render_options_v1(
                        resolve_field_list_options_v1(
                            active_entity_id=active_entity_id,
                            current_menu_key=menu_key,
                            field_definition=normalized_field,
                            sidebar_menu_settings=sidebar_menu_settings,
                            visible_sidebar_menu_keys=visible_sidebar_menu_keys,
                            menu_process_history_map=menu_process_history_map,
                        )
                    )
                    normalized_field["options"] = resolved_options

            normalized_fields_by_key[field_key] = normalized_field

    return normalized_fields_by_key


def is_system_hardcoded_process(menu_key: str) -> bool:
    """Returns True only for processes whose fields are always hardcoded (never dynamic)."""
    return str(menu_key or "").strip().lower() in _SYSTEM_HARDCODED_PROCESS_KEYS


# ###################################################################################
# (2) RESOLVER DE CAMPOS RENDERIZAVEIS PARA SUBPROCESSOS DINAMICOS
# ###################################################################################


def resolve_subprocess_section_fields_v1(
    menu_key: str,
    section_header_key: str,
    sidebar_menu_settings: list[dict[str, Any]],
    visible_sidebar_menu_keys: set[str] | list[str] | tuple[str, ...] | None = None,
    menu_process_history_map: dict[str, list[dict[str, Any]]] | None = None,
    active_entity_id: int | None = None,
) -> list[dict[str, Any]]:
    """
    Resolver reutilizável: retorna os campos configurados para uma secção de um subprocesso dinâmico.
    Filtra por header_key == section_header_key em process_visible_field_rows do processo menu_key.
    Retorna [] para processos do sistema (Administrativo, Estruturas).
    """
    clean_menu_key = _normalize_process_tab_lookup_v1(menu_key)
    if is_system_hardcoded_process(clean_menu_key):
        return []

    clean_header_key = _normalize_process_tab_lookup_v1(section_header_key)
    if not clean_menu_key or not clean_header_key:
        return []

    for setting in sidebar_menu_settings:
        if not isinstance(setting, dict):
            continue
        if _normalize_process_tab_lookup_v1(setting.get("key")) != clean_menu_key:
            continue

        field_meta_by_key = _build_render_field_meta_map_v1(
            menu_key=clean_menu_key,
            setting=setting,
            sidebar_menu_settings=sidebar_menu_settings,
            visible_sidebar_menu_keys=visible_sidebar_menu_keys,
            menu_process_history_map=menu_process_history_map,
            active_entity_id=active_entity_id,
        )

        result: list[dict[str, Any]] = []
        seen: set[str] = set()

        for row in (setting.get("process_visible_field_rows") or []):
            if not isinstance(row, dict):
                continue
            if _normalize_process_tab_lookup_v1(row.get("header_key")) != clean_header_key:
                continue
            field_key = _normalize_process_tab_lookup_v1(row.get("field_key"))
            if not field_key or field_key in seen:
                continue
            seen.add(field_key)
            field_meta = field_meta_by_key.get(field_key)
            if not field_meta:
                result.append(
                    {
                        "key": field_key,
                        "label": field_key,
                        "header_key": clean_header_key,
                        "header_label": clean_header_key,
                        "field_type": "text",
                        "input_type": "text",
                        "required": False,
                        "size": None,
                        "list_source_type": "manual",
                        "manual_list_key": "",
                        "list_key": "",
                        "automatic_source_process_key": "",
                        "automatic_source_section_key": "",
                        "automatic_source_field_key": "",
                        "automatic_only_active": False,
                        "options": [],
                    }
                )
                continue
            if str(field_meta.get("field_type") or "").strip().lower() == "header":
                continue
            header_meta = field_meta_by_key.get(clean_header_key) or {}
            result.append(
                {
                    **field_meta,
                    "header_key": clean_header_key,
                    "header_label": str(header_meta.get("label") or clean_header_key).strip() or clean_header_key,
                }
            )

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
