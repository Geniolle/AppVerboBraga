from __future__ import annotations

import unicodedata
from typing import Any

PROCESS_LAYOUT_SINGLE = "single"
PROCESS_LAYOUT_LIST = "list"

PROCESS_LIST_COLUMN_FIELD = "field"
PROCESS_LIST_COLUMN_MENU_SCOPE = "menu_visibility_scope"
PROCESS_LIST_COLUMN_STATUS = "status"


def _normalize_lookup_text(raw_value: Any) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(raw_value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    return " ".join(normalized.split())


def _normalize_layout_value(raw_value: Any) -> str:
    clean_value = _normalize_lookup_text(raw_value)
    if clean_value in {"list", "lista", "listavel", "listavel_padrao"}:
        return PROCESS_LAYOUT_LIST
    return PROCESS_LAYOUT_SINGLE


def _normalize_bool(raw_value: Any, default: bool = False) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    clean_value = _normalize_lookup_text(raw_value)
    if not clean_value:
        return default
    return clean_value in {"1", "true", "sim", "yes", "on", "ativo", "active"}


def _normalize_label(raw_value: Any) -> str:
    clean_value = " ".join(str(raw_value or "").strip().split())
    return clean_value.lower()


def _normalize_title_label(raw_value: Any, fallback: str = "") -> str:
    clean_value = " ".join(str(raw_value or "").strip().split())
    return clean_value or fallback


def _normalize_positive_int(raw_value: Any, default: int = 0) -> int:
    try:
        parsed_value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return parsed_value if parsed_value > 0 else default


def _upper_first(raw_value: str) -> str:
    clean_value = str(raw_value or "").strip()
    if not clean_value:
        return ""
    return clean_value[:1].upper() + clean_value[1:]


def _build_field_label_map(
    field_options: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
) -> dict[str, str]:
    labels_by_key: dict[str, str] = {}
    for raw_item in field_options or []:
        if not isinstance(raw_item, dict):
            continue
        field_key = str(raw_item.get("key") or "").strip().lower()
        if not field_key:
            continue
        field_label = _normalize_title_label(raw_item.get("label"), fallback=field_key)
        labels_by_key[field_key] = field_label
    return labels_by_key


def _extract_visible_field_specs(
    visible_field_rows: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    field_options: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
) -> list[dict[str, str]]:
    field_labels = _build_field_label_map(field_options)
    normalized_fields: list[dict[str, str]] = []
    seen_field_keys: set[str] = set()

    for raw_row in visible_field_rows or []:
        if not isinstance(raw_row, dict):
            continue
        field_key = str(raw_row.get("field_key") or raw_row.get("key") or "").strip().lower()
        if not field_key or field_key in seen_field_keys:
            continue
        seen_field_keys.add(field_key)
        normalized_fields.append(
            {
                "field_key": field_key,
                "label": field_labels.get(field_key, field_key),
            }
        )

    return normalized_fields


def _normalize_column_source_kind(raw_value: Any) -> str:
    clean_value = _normalize_lookup_text(raw_value)
    if clean_value in {
        PROCESS_LIST_COLUMN_FIELD,
        "visible_field",
        "field_value",
        "campo",
    }:
        return PROCESS_LIST_COLUMN_FIELD
    if clean_value in {
        PROCESS_LIST_COLUMN_MENU_SCOPE,
        "system",
        "sistema",
        "visibility_scope",
        "scope",
    }:
        return PROCESS_LIST_COLUMN_MENU_SCOPE
    if clean_value in {
        PROCESS_LIST_COLUMN_STATUS,
        "estado",
    }:
        return PROCESS_LIST_COLUMN_STATUS
    return ""


def _build_list_column_config(
    *,
    key: str,
    label: str,
    source_kind: str,
    field_key: str = "",
    css_class: str = "",
    responsive_priority: int = 0,
    always_visible: bool = False,
) -> dict[str, Any]:
    return {
        "key": str(key or "").strip().lower(),
        "label": _normalize_title_label(label),
        "source_kind": source_kind,
        "field_key": str(field_key or "").strip().lower(),
        "css_class": str(css_class or "").strip(),
        "responsive_priority": _normalize_positive_int(responsive_priority, 0),
        "always_visible": bool(always_visible),
    }


def _build_explicit_list_columns(
    raw_columns: Any,
    visible_fields: list[dict[str, str]],
) -> list[dict[str, Any]]:
    if not isinstance(raw_columns, list):
        return []

    visible_field_labels = {
        str(item.get("field_key") or "").strip().lower(): str(item.get("label") or "").strip()
        for item in visible_fields
        if isinstance(item, dict)
    }
    normalized_columns: list[dict[str, Any]] = []
    seen_column_keys: set[str] = set()

    for raw_item in raw_columns:
        if not isinstance(raw_item, dict):
            continue
        source_kind = _normalize_column_source_kind(
            raw_item.get("source_kind")
            or raw_item.get("source")
            or raw_item.get("type")
        )
        if not source_kind:
            continue

        field_key = str(raw_item.get("field_key") or "").strip().lower()
        column_key = str(raw_item.get("key") or field_key or source_kind).strip().lower()
        if not column_key or column_key in seen_column_keys:
            continue
        seen_column_keys.add(column_key)

        default_label = (
            visible_field_labels.get(field_key, "")
            if source_kind == PROCESS_LIST_COLUMN_FIELD
            else "Sistema"
            if source_kind == PROCESS_LIST_COLUMN_MENU_SCOPE
            else "Estado"
        )
        default_css_class = (
            "admin-col-main-v1"
            if source_kind == PROCESS_LIST_COLUMN_FIELD and not normalized_columns
            else "admin-col-system-v1"
            if source_kind == PROCESS_LIST_COLUMN_MENU_SCOPE
            else "admin-col-status-v1"
            if source_kind == PROCESS_LIST_COLUMN_STATUS
            else ""
        )
        normalized_columns.append(
            _build_list_column_config(
                key=column_key,
                label=raw_item.get("label") or default_label,
                source_kind=source_kind,
                field_key=field_key,
                css_class=raw_item.get("css_class") or default_css_class,
                responsive_priority=raw_item.get("responsive_priority"),
                always_visible=_normalize_bool(
                    raw_item.get("always_visible"),
                    default=source_kind in {PROCESS_LIST_COLUMN_FIELD, PROCESS_LIST_COLUMN_STATUS},
                ),
            )
        )

    return normalized_columns


def _build_default_list_columns(
    *,
    visible_fields: list[dict[str, str]],
    singular_label: str,
    state_enabled: bool,
    include_remaining_fields: bool,
    show_system_column: bool,
) -> list[dict[str, Any]]:
    columns: list[dict[str, Any]] = []

    primary_field = visible_fields[0] if visible_fields else {}
    primary_field_key = str(primary_field.get("field_key") or "").strip().lower()
    primary_field_label = _normalize_title_label(
        primary_field.get("label"),
        fallback=_upper_first(singular_label),
    )
    columns.append(
        _build_list_column_config(
            key=primary_field_key or "primary",
            label=primary_field_label or _upper_first(singular_label),
            source_kind=PROCESS_LIST_COLUMN_FIELD,
            field_key=primary_field_key,
            css_class="admin-col-main-v1",
            always_visible=True,
        )
    )

    if include_remaining_fields:
        for index, raw_field in enumerate(visible_fields[1:], start=1):
            field_key = str(raw_field.get("field_key") or "").strip().lower()
            if not field_key:
                continue
            columns.append(
                _build_list_column_config(
                    key=field_key,
                    label=raw_field.get("label") or field_key,
                    source_kind=PROCESS_LIST_COLUMN_FIELD,
                    field_key=field_key,
                    css_class="",
                    responsive_priority=index + 1,
                    always_visible=False,
                )
            )

    if show_system_column:
        columns.append(
            _build_list_column_config(
                key="system",
                label="Sistema",
                source_kind=PROCESS_LIST_COLUMN_MENU_SCOPE,
                css_class="admin-col-system-v1",
                responsive_priority=2,
                always_visible=False,
            )
        )

    if state_enabled:
        columns.append(
            _build_list_column_config(
                key="status",
                label="Estado",
                source_kind=PROCESS_LIST_COLUMN_STATUS,
                css_class="admin-col-status-v1",
                always_visible=True,
            )
        )

    return columns


def resolve_dynamic_process_layout_config(
    menu_key: str,
    menu_label: str = "",
    menu_config: dict[str, Any] | None = None,
    *,
    visible_field_rows: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    field_options: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
) -> dict[str, Any]:
    clean_menu_config = menu_config if isinstance(menu_config, dict) else {}
    list_config = (
        clean_menu_config.get("process_list_config")
        if isinstance(clean_menu_config.get("process_list_config"), dict)
        else {}
    )
    joined_lookup = " ".join(
        part
        for part in (
            _normalize_lookup_text(menu_key),
            _normalize_lookup_text(menu_label),
            _normalize_lookup_text(clean_menu_config.get("label")),
        )
        if part
    )

    explicit_layout = _normalize_layout_value(
        list_config.get("layout")
        or clean_menu_config.get("process_layout")
    )
    inferred_layout = PROCESS_LAYOUT_SINGLE
    # Flag generica e independente do layout "list": permite que qualquer processo passe a criar
    # registos com historico (botao "Criar <processo>" + lista de registos criados) apenas com uma
    # configuracao de dados no seu menu_config, sem precisar do layout de tabela completo.
    explicit_uses_record_history = _normalize_bool(
        list_config.get("uses_record_history")
        if "uses_record_history" in list_config
        else clean_menu_config.get("process_record_uses_history"),
        default=False,
    )
    uses_record_history = explicit_layout == PROCESS_LAYOUT_LIST or explicit_uses_record_history
    # _normalize_title_label preserva a capitalizacao configurada (ex.: "Agenda" -> "Criar Agenda"),
    # ao contrario de _normalize_label (usada apenas pelos padroes legados abaixo, que ja sao
    # literais em minusculas). Nenhum processo existente configura estes campos hoje, por isso nao
    # ha regressao de capitalizacao para processos ja configurados.
    singular_label = _normalize_title_label(
        list_config.get("singular_label")
        or clean_menu_config.get("process_record_singular_label")
    )
    plural_label = _normalize_title_label(
        list_config.get("plural_label")
        or clean_menu_config.get("process_record_plural_label")
    )
    state_enabled_default = explicit_layout == PROCESS_LAYOUT_LIST
    show_system_column_default = explicit_layout == PROCESS_LAYOUT_LIST
    include_remaining_fields_default = False

    # Compatibilidade temporária centralizada para processos já existentes.
    if "assiduidade" in joined_lookup or "ausencia" in joined_lookup:
        uses_record_history = True
        singular_label = singular_label or "ausência"
        plural_label = plural_label or "ausências"
        state_enabled_default = False
    elif "autorizacao" in joined_lookup:
        uses_record_history = True
        inferred_layout = PROCESS_LAYOUT_LIST
        singular_label = singular_label or "perfil"
        plural_label = plural_label or "perfis"
        state_enabled_default = True
        show_system_column_default = True
    elif "departamento" in joined_lookup:
        uses_record_history = True
        singular_label = singular_label or "departamento"
        plural_label = plural_label or "departamentos"
        state_enabled_default = True

    layout = explicit_layout if explicit_layout == PROCESS_LAYOUT_LIST else inferred_layout

    # Fallback generico: quando o processo usa historico de registos mas nao configurou um
    # singular_label explicito nem corresponde a um dos padroes legados acima, usa o proprio nome
    # visivel do menu (ex.: "Calendario" -> "Criar Calendario"), em vez do rotulo generico
    # "registo". Funciona para qualquer processo futuro que ative process_record_uses_history.
    if not singular_label and uses_record_history:
        menu_label_fallback = _normalize_title_label(menu_label)
        if menu_label_fallback:
            singular_label = menu_label_fallback
            plural_label = plural_label or (
                menu_label_fallback if menu_label_fallback.lower().endswith("s")
                else f"{menu_label_fallback}s"
            )

    singular_label = singular_label or "registo"
    plural_label = plural_label or "registos"
    state_enabled = _normalize_bool(
        list_config.get("state_enabled")
        if "state_enabled" in list_config
        else clean_menu_config.get("process_record_state_enabled"),
        default=state_enabled_default if layout == PROCESS_LAYOUT_LIST else False,
    )
    show_system_column = _normalize_bool(
        list_config.get("show_system_column")
        if "show_system_column" in list_config
        else clean_menu_config.get("process_record_show_system_column"),
        default=show_system_column_default if layout == PROCESS_LAYOUT_LIST else False,
    )
    include_remaining_fields = _normalize_bool(
        list_config.get("include_remaining_fields")
        if "include_remaining_fields" in list_config
        else clean_menu_config.get("process_record_include_remaining_fields"),
        default=include_remaining_fields_default,
    )

    visible_fields = _extract_visible_field_specs(visible_field_rows, field_options)
    explicit_columns = _build_explicit_list_columns(
        list_config.get("columns")
        if "columns" in list_config
        else clean_menu_config.get("process_list_columns"),
        visible_fields,
    )
    list_columns = explicit_columns or _build_default_list_columns(
        visible_fields=visible_fields,
        singular_label=singular_label,
        state_enabled=bool(state_enabled and layout == PROCESS_LAYOUT_LIST),
        include_remaining_fields=include_remaining_fields,
        show_system_column=show_system_column,
    )

    return {
        "layout": layout,
        "is_list_process": layout == PROCESS_LAYOUT_LIST,
        "uses_record_history": uses_record_history or layout == PROCESS_LAYOUT_LIST,
        "singular_label": singular_label,
        "plural_label": plural_label,
        "create_title": f"Criar {singular_label}",
        "edit_title": f"Editar {singular_label}",
        "active_title": f"{_upper_first(plural_label)} ativos",
        "inactive_title": f"{_upper_first(plural_label)} inativos",
        "empty_active_message": f"Sem {plural_label} ativos.",
        "empty_inactive_message": f"Sem {plural_label} inativos.",
        "state_enabled": bool(state_enabled and layout == PROCESS_LAYOUT_LIST),
        "status_field_key": "__estado",
        "show_system_column": bool(show_system_column and layout == PROCESS_LAYOUT_LIST),
        "include_remaining_fields": bool(include_remaining_fields and layout == PROCESS_LAYOUT_LIST),
        "list_columns": list_columns if layout == PROCESS_LAYOUT_LIST else [],
    }


__all__ = [
    "PROCESS_LAYOUT_LIST",
    "PROCESS_LAYOUT_SINGLE",
    "resolve_dynamic_process_layout_config",
]
