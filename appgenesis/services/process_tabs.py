from typing import Any

from appgenesis.services.process_settings.process_sections import (
    resolve_process_section_fields_v1,
    resolve_process_sections_v1,
)


_SYSTEM_HARDCODED_PROCESS_KEYS: frozenset[str] = frozenset({"administrativo", "sessoes"})

_SUPPORTED_RENDER_FIELD_TYPES_V1: frozenset[str] = frozenset(
    {"text", "number", "email", "phone", "date", "time", "flag", "header", "list"}
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
    if clean_source_type in {"manual", "automatic", "field_list", "active_menus", "profile_menu_tabs"}:
        return clean_source_type
    if (
        field_definition.get("automatic_source_process_key")
        or field_definition.get("automaticSourceProcessKey")
        or field_definition.get("automatic_source_field_key")
        or field_definition.get("automaticSourceFieldKey")
    ):
        return "automatic"
    return "manual"


def _is_legacy_profile_menu_tabs_render_config_v1(
    *,
    menu_key: str,
    field_key: str,
    list_source_type: str,
    automatic_source_process_key: str,
    automatic_source_field_key: str,
) -> bool:
    return (
        list_source_type == "automatic"
        and menu_key == "perfil_de_autorizacao"
        and field_key == "custom_processo"
        and automatic_source_process_key == "perfil_de_autorizacao"
        and automatic_source_field_key in {"custom_perfil", "custom_perfil_2", "custom_nome_do_perfil"}
    )


def _find_field_key_by_label_v1(setting: dict[str, Any], target_label_lookup: str) -> str:
    """Procura, entre os campos configurados do processo, um campo cujo label normalizado
    corresponda a target_label_lookup. Generico para qualquer processo/menu (ex: "processo")."""
    for collection_key in ("process_additional_fields", "process_field_options"):
        raw_fields = setting.get(collection_key)
        if not isinstance(raw_fields, list):
            continue
        for raw_field in raw_fields:
            if not isinstance(raw_field, dict):
                continue
            field_key = _normalize_process_tab_lookup_v1(raw_field.get("key"))
            if field_key and _normalize_process_tab_lookup_v1(raw_field.get("label")) == target_label_lookup:
                return field_key
    return ""


def _build_render_input_type_v1(field_type: str) -> str:
    if field_type == "list":
        return "select"
    if field_type == "phone":
        return "tel"
    if field_type == "flag":
        return "checkbox"
    if field_type in {"number", "email", "date", "time"}:
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
    current_field_values: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    normalized_fields_by_key: dict[str, dict[str, Any]] = {}
    visible_field_header_map: dict[str, str] = {}

    for raw_row in (setting.get("process_visible_field_rows") or []):
        if not isinstance(raw_row, dict):
            continue
        field_key = _normalize_process_tab_lookup_v1(raw_row.get("field_key"))
        header_key = _normalize_process_tab_lookup_v1(raw_row.get("header_key"))
        if field_key and header_key and field_key not in visible_field_header_map:
            visible_field_header_map[field_key] = header_key

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
                "header_key": _normalize_process_tab_lookup_v1(
                    raw_field.get("header_key")
                    or existing_field.get("header_key")
                    or visible_field_header_map.get(field_key)
                ),
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
                "manual_list_items": (
                    raw_field.get("manual_list_items")
                    or raw_field.get("manualListItems")
                    or existing_field.get("manual_list_items")
                    or []
                ),
                "manual_list_options": (
                    raw_field.get("manual_list_options")
                    or raw_field.get("manualListOptions")
                    or existing_field.get("manual_list_options")
                    or []
                ),
                "manual_list_items_csv": str(
                    raw_field.get("manual_list_items_csv")
                    or raw_field.get("manualListItemsCsv")
                    or existing_field.get("manual_list_items_csv")
                    or ""
                ).strip(),
                "options": [],
            }

            if _is_legacy_profile_menu_tabs_render_config_v1(
                menu_key=menu_key,
                field_key=field_key,
                list_source_type=normalized_field["list_source_type"],
                automatic_source_process_key=normalized_field["automatic_source_process_key"],
                automatic_source_field_key=normalized_field["automatic_source_field_key"],
            ):
                normalized_field["list_source_type"] = "profile_menu_tabs"

            if (
                normalized_field["list_source_type"] == "profile_menu_tabs"
                and not normalized_field["automatic_source_field_key"]
            ):
                # Generico para qualquer processo: se nenhum campo de origem foi configurado
                # explicitamente, usa o campo irmao rotulado "Processo" no mesmo processo/menu.
                sibling_field_key = _find_field_key_by_label_v1(setting, "processo")
                if sibling_field_key and sibling_field_key != field_key:
                    normalized_field["automatic_source_field_key"] = sibling_field_key

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
                    from appgenesis.services.profile import resolve_field_list_options_v1

                    resolved_options = _normalize_render_options_v1(
                        resolve_field_list_options_v1(
                            active_entity_id=active_entity_id,
                            current_menu_key=menu_key,
                            field_definition=normalized_field,
                            sidebar_menu_settings=sidebar_menu_settings,
                            visible_sidebar_menu_keys=visible_sidebar_menu_keys,
                            menu_process_history_map=menu_process_history_map,
                            current_field_values=current_field_values,
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
    current_field_values: dict[str, Any] | None = None,
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
        result = resolve_process_section_fields_v1(setting, clean_header_key)
        if result:
            field_meta_by_key = _build_render_field_meta_map_v1(
                menu_key=clean_menu_key,
                setting=setting,
                sidebar_menu_settings=sidebar_menu_settings,
                visible_sidebar_menu_keys=visible_sidebar_menu_keys,
                menu_process_history_map=menu_process_history_map,
                active_entity_id=active_entity_id,
                current_field_values=current_field_values,
            )

            resolved_result: list[dict[str, Any]] = []
            for field in result:
                clean_field_key = _normalize_process_tab_lookup_v1(field.get("key"))
                field_meta = field_meta_by_key.get(clean_field_key)
                if field_meta:
                    resolved_result.append(
                        {
                            **field_meta,
                            "header_key": clean_header_key,
                            "header_label": str(
                                field_meta_by_key.get(clean_header_key, {}).get("label")
                                or clean_header_key
                            ).strip()
                            or clean_header_key,
                        }
                    )
                else:
                    resolved_result.append(dict(field))

            from appgenesis.services.profile import (
                _build_profile_menu_tabs_controller_key_candidates_v1,
                build_profile_menu_tabs_dependency_map_v1,
            )

            section_field_keys = {
                str(item.get("key") or "").strip().lower()
                for item in resolved_result
                if str(item.get("key") or "").strip()
            }
            section_field_labels = {
                str(item.get("key") or "").strip().lower(): str(item.get("label") or "").strip()
                for item in resolved_result
                if str(item.get("key") or "").strip()
            }
            dependency_map = build_profile_menu_tabs_dependency_map_v1(
                sidebar_menu_settings=sidebar_menu_settings,
                visible_sidebar_menu_keys=visible_sidebar_menu_keys,
                menu_process_history_map=menu_process_history_map,
            )

            for field in resolved_result:
                if str(field.get("list_source_type") or "").strip().lower() != "profile_menu_tabs":
                    continue

                candidate_keys = _build_profile_menu_tabs_controller_key_candidates_v1(
                    current_menu_key=clean_menu_key,
                    field_definition=field,
                )
                dependent_field_key = ""

                for candidate_key in candidate_keys:
                    if candidate_key in section_field_keys:
                        dependent_field_key = candidate_key
                        break

                if not dependent_field_key:
                    for field_key, field_label in section_field_labels.items():
                        if _normalize_process_tab_lookup_v1(field_label) == "processo":
                            dependent_field_key = field_key
                            break

                if not dependent_field_key:
                    for field_key, field_label in section_field_labels.items():
                        if _normalize_process_tab_lookup_v1(field_label) == "nome_do_perfil":
                            dependent_field_key = field_key
                            break

                if not dependent_field_key:
                    for field_key, field_label in section_field_labels.items():
                        if _normalize_process_tab_lookup_v1(field_label) == "perfil":
                            dependent_field_key = field_key
                            break

                if dependent_field_key and not str(field.get("automatic_source_field_key") or "").strip():
                    field["automatic_source_field_key"] = dependent_field_key
                if dependent_field_key and not str(field.get("profile_source_field_key") or "").strip():
                    field["profile_source_field_key"] = dependent_field_key

                if not _normalize_render_options_v1(field.get("options")):
                    from appgenesis.services.profile import resolve_field_list_options_v1

                    field["options"] = _normalize_render_options_v1(
                        resolve_field_list_options_v1(
                            active_entity_id=active_entity_id,
                            current_menu_key=clean_menu_key,
                            field_definition=field,
                            sidebar_menu_settings=sidebar_menu_settings,
                            visible_sidebar_menu_keys=visible_sidebar_menu_keys,
                            menu_process_history_map=menu_process_history_map,
                            current_field_values=current_field_values,
                        )
                    )

                field["dependent_field_key"] = dependent_field_key
                field["dependent_options_map"] = dependency_map
                field["options"] = _normalize_render_options_v1(field.get("options"))

            return resolved_result
        return []

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
            process_sections = resolve_process_sections_v1(setting)
            if process_sections:
                tabs = []
                for section in process_sections:
                    section_key = str(section.get("key") or "").strip().lower()
                    if not section_key:
                        continue
                    section_label = str(section.get("label") or "").strip() or section_key.replace("_", " ").title()
                    layout = "list" if setting.get("is_list_process") else "form"
                    tabs.append(
                        ProcessTabConfig(
                            section_key,
                            section_label,
                            "#dynamic-process-card",
                            layout,
                            section_key,
                        )
                    )
                if tabs and not (
                    len(tabs) == 1
                    and tabs[0].key == "__geral__"
                    and not (process_sections[0].get("quantity_rule_keys") or [])
                ):
                    return tabs
            break

    return []


def resolve_process_tab_options_v1(
    menu_key: str,
    sidebar_menu_settings: list[dict[str, Any]],
    *,
    visible_sidebar_menu_keys: set[str] | list[str] | tuple[str, ...] | None = None,
) -> list[dict[str, str]]:
    clean_menu_key = _normalize_process_tab_lookup_v1(menu_key)
    visible_keys = {
        _normalize_process_tab_lookup_v1(raw_key)
        for raw_key in (visible_sidebar_menu_keys or [])
        if _normalize_process_tab_lookup_v1(raw_key)
    }

    if not clean_menu_key:
        return []

    if visible_keys and clean_menu_key not in visible_keys:
        return []

    return [
        {
            "value": str(tab.key or "").strip(),
            "label": str(tab.label or tab.key or "").strip() or str(tab.key or "").strip(),
            "status": "active",
        }
        for tab in resolve_process_tabs_v1(clean_menu_key, sidebar_menu_settings)
        if str(tab.key or "").strip()
    ]
