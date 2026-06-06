from __future__ import annotations

from appverbo.page_state.pagina_default import resolver_pagina_default_v1
from datetime import datetime, timezone
from typing import Any
import unicodedata

from fastapi import Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_START
from appverbo.admin_subprocesses.menu.configuracao import MENU_CONFIG
from appverbo.admin_subprocesses.menu.service import build_admin_menu_state
from appverbo.admin_subprocesses.repositories.menu_repository import MenuAdminRepository
from appverbo.admin_subprocesses.registry import get_admin_subprocess_config
from appverbo.admin_subprocesses.sessoes.common import (
    build_sessoes_admin_return_url_v2,
    get_sessoes_visible_fields_v2,
    get_sessoes_visible_columns_v2,
)
from appverbo.admin_subprocesses.runtime import build_admin_subprocess_state_from_repository

# APPVERBO_ADMIN_SUBPROCESS_PAGE_IMPORTS_V2_END
from appverbo.admin_subprocesses.utilizador.pagina import montar_estado_pagina_utilizador_v1
from appverbo.core import *  # noqa: F403,F401
from appverbo.db.bootstrap import ensure_admin_process_title_default_definitions_v1
from appverbo.models import AdminDefinition
from appverbo.menu_settings import (
    MENU_MEU_PERFIL_KEY,
    infer_sidebar_icon_key,
    normalize_sidebar_icon_key,
    resolve_menu_key_alias,
)
from appverbo.routes.profile.router import router
from appverbo.services import *  # noqa: F403,F401
from appverbo.services.admin_definition_scope import list_admin_definitions_in_scope_v1
from appverbo.services.entity_scope import build_entity_scope_label_v1
from appverbo.services.menu_admin_context import (
    build_menu_admin_context_v1,
    build_menu_admin_page_payload_v1,
)
from appverbo.services.sessoes_admin_context import (
    build_sessoes_admin_context_v1,
    build_sessoes_admin_page_payload_v1,
)
from appverbo.services.users.context import build_user_admin_edit_context_v1


def _write_meu_perfil_page_flow_debug_log_v1(
    request: Request,
    stage: str,
    data: dict[str, Any] | None = None,
) -> None:
    import json
    import os
    from pathlib import Path

    try:
        log_dir = Path(
            os.environ.get(
                "APPVERBO_PROFILE_SAVE_LOG_DIR",
                "appverbo_runtime_logs",
            )
        )
        log_dir.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "logger": "APPVERBO_MEU_PERFIL_PAGE_FLOW_DEBUG_V1",
            "stage": str(stage or "").strip(),
            "request": {
                "method": str(getattr(request, "method", "") or ""),
                "path": str(getattr(getattr(request, "url", None), "path", "") or ""),
                "url": str(getattr(request, "url", "") or ""),
                "client": str(getattr(getattr(request, "client", None), "host", "") or ""),
            },
            "data": data or {},
        }

        log_line = json.dumps(log_entry, ensure_ascii=False, default=str, sort_keys=True)
        log_path = log_dir / "meu_perfil_process_flow.log"
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(log_line + "\n")

        print("APPVERBO_MEU_PERFIL_PAGE_FLOW_DEBUG " + log_line, flush=True)
    except Exception as exc:
        print("APPVERBO_MEU_PERFIL_PAGE_FLOW_DEBUG_ERROR " + repr(exc), flush=True)


def _resolve_first_dynamic_section_key(menu_row: dict[str, Any] | None) -> str:
    if not isinstance(menu_row, dict):
        return "__empty__"
    raw_rows = menu_row.get("process_visible_field_rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        return "__empty__"

    section_order: list[str] = []
    seen_sections: set[str] = set()
    first_field_key = ""
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
        if section_key in seen_sections:
            continue
        seen_sections.add(section_key)
        section_order.append(section_key)

    if not section_order:
        return "__empty__"
    if len(section_order) == 1 and section_order[0] == "__geral__":
        return f"field:{first_field_key}" if first_field_key else "__empty__"
    return section_order[0]


def _resolve_admin_menu_target_v1(settings_edit_key: str) -> str:
    if str(settings_edit_key or "").strip():
        return "#settings-menu-edit-card"

    return "#admin-menu-card"


def _is_targeted_edit_request_v1(
    edit_identifier: object,
    target_selector: object,
    expected_target_selector: str,
) -> bool:
    clean_edit_identifier = str(edit_identifier or "").strip()
    clean_target_selector = _normalize_target_selector_v1(target_selector)
    clean_expected_target_selector = _normalize_target_selector_v1(
        expected_target_selector
    )

    return bool(
        clean_edit_identifier
        and clean_target_selector
        and clean_target_selector == clean_expected_target_selector
    )


def _is_admin_menu_edit_request_v1(
    settings_edit_key: str,
    target_selector: str,
) -> bool:
    return _is_targeted_edit_request_v1(
        settings_edit_key,
        target_selector,
        "#settings-menu-edit-card",
    )


def _resolve_admin_definicoes_target_v1(definition_edit_id: str) -> str:
    if str(definition_edit_id or "").strip():
        return "#admin-definicoes-card-edit"

    return "#admin-definicoes-card"


def _is_admin_definicoes_edit_request_v1(
    definition_edit_id: str,
    target_selector: str,
) -> bool:
    return _is_targeted_edit_request_v1(
        definition_edit_id,
        target_selector,
        "#admin-definicoes-card-edit",
    )


def _resolve_targeted_edit_key_v1(
    edit_identifier: object,
    target_selector: object,
    expected_target_selector: str,
) -> str:
    clean_edit_identifier = str(edit_identifier or "").strip()

    if not _is_targeted_edit_request_v1(
        clean_edit_identifier,
        target_selector,
        expected_target_selector,
    ):
        return ""

    return clean_edit_identifier


def _resolve_admin_sessoes_target_v1(sidebar_section_edit_key: str) -> str:
    if str(sidebar_section_edit_key or "").strip():
        return "#admin-sidebar-sections-form-card"

    return "#admin-sidebar-sections-card"


def _is_admin_sessoes_edit_request_v1(
    sidebar_section_edit_key: str,
    target_selector: str,
) -> bool:
    return _is_targeted_edit_request_v1(
        sidebar_section_edit_key,
        target_selector,
        "#admin-sidebar-sections-form-card",
    )


def _normalize_target_selector_v1(value: object) -> str:
    clean_value = str(value or "").strip()
    if not clean_value:
        return ""
    return clean_value if clean_value.startswith("#") else f"#{clean_value}"


def _filter_sessoes_rows_for_scope_v1(
    rows: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    current_entity_scope: object,
) -> list[dict[str, Any]]:
    clean_entity_scope = str(current_entity_scope or "").strip().lower()
    filtered_rows: list[dict[str, Any]] = []

    for raw_row in rows or []:
        row = dict(raw_row or {})
        row_scope_mode = str(row.get("visibility_scope_mode") or "").strip().lower()

        if row_scope_mode == "owner" and clean_entity_scope != "owner":
            continue

        filtered_rows.append(row)

    return filtered_rows


def _load_selected_entity_name_for_admin_subprocess_v1(
    session: Session,
    selected_entity_id: object,
) -> str:
    clean_selected_entity_id = str(selected_entity_id or "").strip()

    if not clean_selected_entity_id.isdigit():
        return ""

    try:
        from appverbo.models.entity import Entity as _EntityModel

        entity_name = session.execute(
            select(_EntityModel.name)
            .where(_EntityModel.id == int(clean_selected_entity_id))
            .limit(1)
        ).scalar_one_or_none()
    except Exception:
        return ""

    return str(entity_name or "").strip()


def _decorate_admin_subprocess_state_with_entity_name_v1(
    state: Any,
    entity_name: object,
) -> Any:
    if state is None:
        return None

    clean_entity_name = str(entity_name or "").strip()

    if isinstance(getattr(state, "active_rows", None), list):
        state.active_rows = [
            {**dict(row or {}), "entity_name": clean_entity_name}
            for row in state.active_rows
        ]

    if isinstance(getattr(state, "inactive_rows", None), list):
        state.inactive_rows = [
            {**dict(row or {}), "entity_name": clean_entity_name}
            for row in state.inactive_rows
        ]

    if isinstance(getattr(state, "edit_data", None), dict):
        state.edit_data = {
            **dict(state.edit_data),
            "entity_name": clean_entity_name,
        }

    if isinstance(getattr(state, "create_data", None), dict):
        state.create_data = {
            **dict(state.create_data),
            "entity_name": clean_entity_name,
        }

    return state


def _filter_sessoes_admin_subprocess_state_for_scope_v1(
    state: Any,
    current_entity_scope: object,
) -> Any:
    if state is None:
        return None

    state.active_rows = _filter_sessoes_rows_for_scope_v1(
        list(getattr(state, "active_rows", []) or []),
        current_entity_scope,
    )
    state.inactive_rows = _filter_sessoes_rows_for_scope_v1(
        list(getattr(state, "inactive_rows", []) or []),
        current_entity_scope,
    )

    if isinstance(getattr(state, "edit_data", None), dict):
        filtered_edit_rows = _filter_sessoes_rows_for_scope_v1(
            [dict(state.edit_data)],
            current_entity_scope,
        )
        if filtered_edit_rows:
            state.edit_data = filtered_edit_rows[0]
        else:
            state.edit_data = None
            state.edit_key = ""
            state.mode = "create"

    return state


def _resolve_requested_dynamic_context_v1(
    request: Request,
    *,
    fallback_target: object = "",
    fallback_profile_section: object = "",
    fallback_dynamic_process_section: object = "",
    fallback_section_key: object = "",
) -> tuple[str, str, str, bool]:
    clean_target_from_query = _normalize_target_selector_v1(
        request.query_params.get("target", fallback_target)
    )
    clean_profile_section_from_query = str(
        request.query_params.get("profile_section", fallback_profile_section) or ""
    ).strip().lower()
    clean_dynamic_section_from_query = str(
        request.query_params.get("dynamic_process_section", "")
        or request.query_params.get("section_key", "")
        or fallback_dynamic_process_section
        or fallback_section_key
        or ""
    ).strip()

    has_explicit_non_dynamic_target = bool(
        clean_target_from_query and clean_target_from_query != "#dynamic-process-card"
    )
    has_admin_dynamic_process_context = bool(
        clean_dynamic_section_from_query
        and (
            clean_target_from_query == "#dynamic-process-card"
            or not has_explicit_non_dynamic_target
        )
    )

    if not has_admin_dynamic_process_context:
        clean_dynamic_section_from_query = ""

    return (
        clean_target_from_query,
        clean_profile_section_from_query,
        clean_dynamic_section_from_query,
        has_admin_dynamic_process_context,
    )


def _build_definicoes_options_from_rows_v1(
    rows: list[dict[str, Any]],
    *,
    empty_message: str,
    value_candidates: tuple[str, ...],
    label_candidates: tuple[str, ...],
    fixed_options: tuple[tuple[str, str], ...] = (),
    current_value: object = "",
) -> tuple[tuple[str, str], ...]:
    normalized_options: list[tuple[str, str]] = []
    seen_values: set[str] = set()

    def _push_option(option_key: object, option_label: object) -> None:
        clean_key = str(option_key or "").strip().lower()
        clean_label = str(option_label or "").strip()
        option_value = clean_label or clean_key
        normalized_option_value = option_value.strip().lower()

        if not normalized_option_value or normalized_option_value in seen_values:
            return

        seen_values.add(normalized_option_value)
        normalized_options.append((option_value, clean_label or clean_key))

    for fixed_option in fixed_options:
        if not isinstance(fixed_option, tuple) or len(fixed_option) != 2:
            continue

        _push_option(fixed_option[0], fixed_option[1])

    for raw_row in rows:
        if not isinstance(raw_row, dict):
            continue

        if bool(raw_row.get("is_deleted")):
            continue

        raw_status = str(raw_row.get("status") or "").strip().lower()
        raw_is_active = raw_row.get("is_active")
        is_active = bool(raw_is_active) or raw_status in {"active", "ativo", "1", "true", "on"}

        if not is_active:
            continue

        option_value = ""
        option_label = ""

        for candidate_key in value_candidates:
            candidate_value = str(raw_row.get(candidate_key) or "").strip()
            if candidate_value:
                option_value = candidate_value
                break

        for candidate_key in label_candidates:
            candidate_label = str(raw_row.get(candidate_key) or "").strip()
            if candidate_label:
                option_label = candidate_label
                break

        _push_option(option_value, option_label)

    clean_current_value = str(current_value or "").strip()
    normalized_current_value = clean_current_value.lower()
    if normalized_current_value and normalized_current_value not in seen_values:
        normalized_options.append((clean_current_value, clean_current_value))

    if not normalized_options:
        return (("", empty_message),)

    return (("", "Selecione"), *tuple(normalized_options))


def _build_definicoes_process_options_v1(
    session_rows: list[dict[str, Any]],
    current_value: object = "",
) -> tuple[tuple[str, str], ...]:
    return _build_definicoes_options_from_rows_v1(
        session_rows,
        empty_message="Sem sessões ativas",
        value_candidates=("label", "name", "key", "id"),
        label_candidates=("label", "name", "key", "id"),
        fixed_options=(("Geral", "Geral"),),
        current_value=current_value,
    )


def _build_definicoes_subprocess_options_v1(
    menu_rows: list[dict[str, Any]],
    current_value: object = "",
) -> tuple[tuple[str, str], ...]:
    return _build_definicoes_options_from_rows_v1(
        menu_rows,
        empty_message="Sem subprocessos ativos no Menu",
        value_candidates=("label", "name", "key", "menu_key"),
        label_candidates=("label", "name", "key", "menu_key"),
        fixed_options=(("Geral", "Geral"),),
        current_value=current_value,
    )


# ###################################################################################
# (X) DEFINICOES GERAIS - TAMANHO, FONTE E COR DAS ABAS ADMINISTRATIVAS
# ###################################################################################

def _normalize_definition_lookup_text_v1(value: object) -> str:
    clean_value = " ".join(str(value or "").strip().split()).lower()
    normalized = unicodedata.normalize("NFD", clean_value)
    return "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )


def _parse_tabs_width_ch_v1(value: object) -> int | None:
    raw_value = str(value or "").strip().replace(",", ".")

    if not raw_value:
        return None

    try:
        parsed_value = int(float(raw_value))
    except (TypeError, ValueError):
        return None

    if parsed_value <= 0:
        return None

    # Limites defensivos para evitar layout quebrado por valores extremos.
    return max(8, min(60, parsed_value))


def _parse_tabs_text_size_px_v1(value: object) -> int | None:
    raw_value = str(value or "").strip().replace(",", ".")

    if not raw_value:
        return None

    try:
        parsed_value = int(float(raw_value))
    except (TypeError, ValueError):
        return None

    if parsed_value <= 0:
        return None

    # Limites defensivos para evitar texto ilegivel ou exagerado na aba.
    return max(10, min(40, parsed_value))


def _parse_tabs_font_family_v1(value: object) -> str | None:
    raw_value = " ".join(str(value or "").strip().split())

    if not raw_value:
        return None

    if len(raw_value) > 120:
        return None

    if any(token in raw_value for token in ("\n", "\r", ";", "{", "}")):
        return None

    return raw_value


def _parse_font_weight_value_v1(value: object) -> int | None:
    raw_value = str(value or "").strip().replace(",", ".")

    if not raw_value:
        return None

    try:
        parsed_value = int(float(raw_value))
    except (TypeError, ValueError):
        return None

    if parsed_value <= 0:
        return None

    return max(300, min(900, parsed_value))


def _parse_tabs_color_hex_v1(value: object) -> str | None:
    raw_value = "".join(str(value or "").strip().split())

    if not raw_value:
        return None

    if raw_value.startswith("#"):
        raw_value = raw_value[1:]

    if len(raw_value) == 3 and all(character in "0123456789abcdefABCDEF" for character in raw_value):
        raw_value = "".join(character * 2 for character in raw_value)
    elif len(raw_value) == 6 and all(
        character in "0123456789abcdefABCDEF" for character in raw_value
    ):
        raw_value = raw_value
    else:
        return None

    return "#" + raw_value.upper()


# ###################################################################################
# (X.1) CONSTANTES DE ESTILO - PROCESSO/SUBPROCESSO (DEFINICOES)
# ###################################################################################

ADMIN_PROCESS_TITLE_STYLE_DEFINITION_KEYS_V1: dict[str, dict[str, tuple[str, ...] | str]] = {
    "font_size": {
        "parameter_type": "tamanho",
        "parameter_names": (
            "titulo processo tamanho",
            "titulo do processo tamanho",
            "titulo tamanho",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "font_family": {
        "parameter_type": "fonte",
        "parameter_names": (
            "titulo processo fonte",
            "titulo do processo fonte",
            "titulo fonte",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "color": {
        "parameter_type": "cor",
        "parameter_names": (
            "titulo processo cor",
            "titulo do processo cor",
            "titulo cor",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
}

# ###################################################################################
# (X.2) CONSTANTES DE ESTILO - TEXTO DOS ITENS DOS CARDS (DEFINICOES)
# ###################################################################################

ADMIN_SUBPROCESS_CARD_ITEM_STYLE_DEFINITION_KEYS_V1: dict[str, dict[str, tuple[str, ...] | str]] = {
    "font_size": {
        "parameter_type": "tamanho",
        "parameter_names": (
            "card item texto tamanho",
            "item card texto tamanho",
            "item texto tamanho",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "font_family": {
        "parameter_type": "fonte",
        "parameter_names": (
            "card item texto fonte",
            "item card texto fonte",
            "item texto fonte",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "color": {
        "parameter_type": "cor",
        "parameter_names": (
            "card item texto cor",
            "item card texto cor",
            "item texto cor",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "font_weight": {
        "parameter_type": "tamanho",
        "parameter_names": (
            "card item texto peso",
            "item card texto peso",
            "item texto peso",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
}

# ###################################################################################
# (X.3) CONSTANTES DE ESTILO - CABECALHO DE TABELAS/COLUNAS (DEFINICOES)
# ###################################################################################

ADMIN_SUBPROCESS_CARD_TABLE_HEAD_STYLE_DEFINITION_KEYS_V1: dict[str, dict[str, tuple[str, ...] | str]] = {
    "color": {
        "parameter_type": "cor",
        "parameter_names": (
            "card cabecalho texto cor",
            "cabecalho texto cor",
            "header texto cor",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
}

# ###################################################################################
# (X.4) CONSTANTES DE ESTILO - BARRA DO CABECALHO (DEFINICOES)
# ###################################################################################

ADMIN_TOPBAR_STYLE_DEFINITION_KEYS_V1: dict[str, dict[str, tuple[str, ...] | str]] = {
    "color": {
        "parameter_type": "cor",
        "parameter_names": (
            "barra cabecalho cor",
            "barra do cabecalho cor",
            "topbar cor",
            "header bar color",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
}

# ###################################################################################
# (X.5) CONSTANTES DE ESTILO - BARRA LATERAL (DEFINICOES)
# ###################################################################################

ADMIN_SIDEBAR_STYLE_DEFINITION_KEYS_V1: dict[str, dict[str, tuple[str, ...] | str]] = {
    "background_color": {
        "parameter_type": "cor",
        "parameter_names": (
            "barra lateral fundo cor",
            "sidebar fundo cor",
            "sidebar background color",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "active_background_color": {
        "parameter_type": "cor",
        "parameter_names": (
            "barra lateral item ativo fundo cor",
            "sidebar item ativo fundo cor",
            "sidebar active background color",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "text_color": {
        "parameter_type": "cor",
        "parameter_names": (
            "barra lateral texto cor",
            "sidebar texto cor",
            "sidebar text color",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "text_size": {
        "parameter_type": "tamanho",
        "parameter_names": (
            "barra lateral texto tamanho",
            "sidebar texto tamanho",
            "sidebar text size",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "font_family": {
        "parameter_type": "fonte",
        "parameter_names": (
            "barra lateral texto fonte",
            "barra lateral tipo de letra",
            "sidebar texto fonte",
            "sidebar font family",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "font_weight": {
        "parameter_type": "tamanho",
        "parameter_names": (
            "barra lateral texto peso",
            "sidebar texto peso",
            "sidebar font weight",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "icon_color": {
        "parameter_type": "cor",
        "parameter_names": (
            "barra lateral icone cor",
            "sidebar icone cor",
            "sidebar icon color",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
    "section_text_color": {
        "parameter_type": "cor",
        "parameter_names": (
            "barra lateral secao texto cor",
            "sidebar secao texto cor",
            "sidebar section text color",
        ),
        "process_name": "geral",
        "subprocess_name": "geral",
    },
}
ADMIN_SIDEBAR_MENU_ICON_DEFINITION_KEYS_V1: dict[str, tuple[str, ...] | str] = {
    "parameter_type": "icone",
    "parameter_names": (
        "icone menu lateral",
        "icone do menu lateral",
        "icone processo",
        "icone do processo",
        "sidebar icon",
    ),
}

def _resolve_definition_initial_value_by_alias_v1(
    *,
    rows: list[AdminDefinition],
    parameter_type: str,
    parameter_names: tuple[str, ...],
    process_name: str,
    subprocess_name: str,
) -> str | None:
    normalized_parameter_type = _normalize_definition_lookup_text_v1(parameter_type)
    normalized_parameter_names = {
        _normalize_definition_lookup_text_v1(parameter_name)
        for parameter_name in parameter_names
        if str(parameter_name or "").strip()
    }
    normalized_process_name = _normalize_definition_lookup_text_v1(process_name)
    normalized_subprocess_name = _normalize_definition_lookup_text_v1(subprocess_name)

    for row in rows:
        if _normalize_definition_lookup_text_v1(row.status) != "active":
            continue
        if _normalize_definition_lookup_text_v1(row.parameter_type) != normalized_parameter_type:
            continue
        if _normalize_definition_lookup_text_v1(row.parameter_name) not in normalized_parameter_names:
            continue
        if _normalize_definition_lookup_text_v1(row.process_name) != normalized_process_name:
            continue
        if _normalize_definition_lookup_text_v1(row.subprocess_name) != normalized_subprocess_name:
            continue
        return str(row.initial_value or "")

    return None


def _resolve_sidebar_menu_icon_key_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    menu_key: object,
    menu_label: object,
    menu_section_label: object,
) -> str:
    default_icon_key = infer_sidebar_icon_key(
        menu_key,
        menu_label,
        menu_section_label,
    )
    parameter_names = tuple(
        str(name)
        for name in ADMIN_SIDEBAR_MENU_ICON_DEFINITION_KEYS_V1.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(ADMIN_SIDEBAR_MENU_ICON_DEFINITION_KEYS_V1["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(menu_section_label or ""),
        subprocess_name=str(menu_label or ""),
    )

    if not str(raw_value or "").strip():
        return default_icon_key

    normalized_icon_key = normalize_sidebar_icon_key(raw_value)
    if normalized_icon_key == "circle" and default_icon_key != "circle":
        return default_icon_key

    return normalized_icon_key


def _apply_sidebar_icon_keys_to_menu_settings_v1(
    *,
    rows: list[AdminDefinition],
    sidebar_menu_settings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized_settings: list[dict[str, Any]] = []

    for raw_setting in sidebar_menu_settings:
        setting = dict(raw_setting or {})
        setting["sidebar_icon_key"] = _resolve_sidebar_menu_icon_key_from_definitions_v1(
            rows=rows,
            menu_key=setting.get("key"),
            menu_label=setting.get("label"),
            menu_section_label=(
                setting.get("menu_section_label")
                or setting.get("sidebar_section_label")
                or setting.get("section")
                or ""
            ),
        )
        normalized_settings.append(setting)

    return normalized_settings


def _resolve_admin_tabs_width_ch_from_definitions_v1(
    *,
    session: Any | None = None,
    rows: list[AdminDefinition] | None = None,
    default_width_ch: int = 24,
) -> int:
    definition_rows = rows
    if definition_rows is None:
        if session is None:
            return int(default_width_ch)
        definition_rows = session.execute(
            select(AdminDefinition).order_by(AdminDefinition.id.desc())
        ).scalars().all()

    for row in definition_rows:
        if _normalize_definition_lookup_text_v1(row.status) != "active":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_type) != "tamanho":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_name) != "aba geral":
            continue

        if _normalize_definition_lookup_text_v1(row.process_name) != "geral":
            continue

        if _normalize_definition_lookup_text_v1(row.subprocess_name) != "geral":
            continue

        parsed_width_ch = _parse_tabs_width_ch_v1(row.initial_value)

        if parsed_width_ch is not None:
            return parsed_width_ch

    return int(default_width_ch)


def _resolve_admin_tabs_font_family_from_definitions_v1(
    *,
    session: Any | None = None,
    rows: list[AdminDefinition] | None = None,
    default_font_family: str = '"Segoe UI", Tahoma, Arial, sans-serif',
) -> str:
    definition_rows = rows
    if definition_rows is None:
        if session is None:
            fallback_font_family = _parse_tabs_font_family_v1(default_font_family)
            if fallback_font_family is not None:
                return fallback_font_family
            return '"Segoe UI", Tahoma, Arial, sans-serif'
        definition_rows = session.execute(
            select(AdminDefinition).order_by(AdminDefinition.id.desc())
        ).scalars().all()

    for row in definition_rows:
        if _normalize_definition_lookup_text_v1(row.status) != "active":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_type) != "fonte":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_name) != "aba fonte":
            continue

        if _normalize_definition_lookup_text_v1(row.process_name) != "geral":
            continue

        if _normalize_definition_lookup_text_v1(row.subprocess_name) != "geral":
            continue

        parsed_font_family = _parse_tabs_font_family_v1(row.initial_value)

        if parsed_font_family is not None:
            return parsed_font_family

    fallback_font_family = _parse_tabs_font_family_v1(default_font_family)
    if fallback_font_family is not None:
        return fallback_font_family
    return '"Segoe UI", Tahoma, Arial, sans-serif'


def _resolve_admin_tabs_text_size_px_from_definitions_v1(
    *,
    session: Any | None = None,
    rows: list[AdminDefinition] | None = None,
    default_text_size_px: int = 13,
) -> int:
    definition_rows = rows
    if definition_rows is None:
        if session is None:
            fallback_text_size_px = _parse_tabs_text_size_px_v1(default_text_size_px)
            if fallback_text_size_px is not None:
                return fallback_text_size_px
            return 13
        definition_rows = session.execute(
            select(AdminDefinition).order_by(AdminDefinition.id.desc())
        ).scalars().all()

    for row in definition_rows:
        if _normalize_definition_lookup_text_v1(row.status) != "active":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_type) != "tamanho":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_name) != "aba texto tamanho":
            continue

        if _normalize_definition_lookup_text_v1(row.process_name) != "geral":
            continue

        if _normalize_definition_lookup_text_v1(row.subprocess_name) != "geral":
            continue

        parsed_text_size_px = _parse_tabs_text_size_px_v1(row.initial_value)

        if parsed_text_size_px is not None:
            return parsed_text_size_px

    fallback_text_size_px = _parse_tabs_text_size_px_v1(default_text_size_px)
    if fallback_text_size_px is not None:
        return fallback_text_size_px
    return 13


def _resolve_admin_tabs_color_hex_from_definitions_v1(
    *,
    session: Any | None = None,
    rows: list[AdminDefinition] | None = None,
    default_color_hex: str = "#1F4FA3",
) -> str:
    definition_rows = rows
    if definition_rows is None:
        if session is None:
            fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
            if fallback_color_hex is not None:
                return fallback_color_hex
            return "#1F4FA3"
        definition_rows = session.execute(
            select(AdminDefinition).order_by(AdminDefinition.id.desc())
        ).scalars().all()

    for row in definition_rows:
        if _normalize_definition_lookup_text_v1(row.status) != "active":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_type) != "cor":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_name) != "aba cor":
            continue

        if _normalize_definition_lookup_text_v1(row.process_name) != "geral":
            continue

        if _normalize_definition_lookup_text_v1(row.subprocess_name) != "geral":
            continue

        parsed_color_hex = _parse_tabs_color_hex_v1(row.initial_value)

        if parsed_color_hex is not None:
            return parsed_color_hex

    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#1F4FA3"


def _resolve_admin_tabs_text_color_hex_from_definitions_v1(
    *,
    session: Any | None = None,
    rows: list[AdminDefinition] | None = None,
    default_text_color_hex: str = "",
) -> str:
    definition_rows = rows
    if definition_rows is None:
        if session is None:
            fallback_text_color_hex = _parse_tabs_color_hex_v1(default_text_color_hex)
            if fallback_text_color_hex is not None:
                return fallback_text_color_hex
            return ""
        definition_rows = session.execute(
            select(AdminDefinition).order_by(AdminDefinition.id.desc())
        ).scalars().all()

    for row in definition_rows:
        if _normalize_definition_lookup_text_v1(row.status) != "active":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_type) != "cor":
            continue

        if _normalize_definition_lookup_text_v1(row.parameter_name) != "aba texto":
            continue

        if _normalize_definition_lookup_text_v1(row.process_name) != "geral":
            continue

        if _normalize_definition_lookup_text_v1(row.subprocess_name) != "geral":
            continue

        parsed_text_color_hex = _parse_tabs_color_hex_v1(row.initial_value)

        if parsed_text_color_hex is not None:
            return parsed_text_color_hex

    fallback_text_color_hex = _parse_tabs_color_hex_v1(default_text_color_hex)
    if fallback_text_color_hex is not None:
        return fallback_text_color_hex
    return ""


def _resolve_admin_process_title_font_size_px_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_text_size_px: int = 20,
) -> int:
    config = ADMIN_PROCESS_TITLE_STYLE_DEFINITION_KEYS_V1["font_size"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_text_size_px = _parse_tabs_text_size_px_v1(raw_value)
    if parsed_text_size_px is not None:
        return parsed_text_size_px
    fallback_text_size_px = _parse_tabs_text_size_px_v1(default_text_size_px)
    if fallback_text_size_px is not None:
        return fallback_text_size_px
    return 20


def _resolve_admin_process_title_font_family_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_font_family: str = '"Segoe UI", Tahoma, Arial, sans-serif',
) -> str:
    config = ADMIN_PROCESS_TITLE_STYLE_DEFINITION_KEYS_V1["font_family"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_font_family = _parse_tabs_font_family_v1(raw_value)
    if parsed_font_family is not None:
        return parsed_font_family
    fallback_font_family = _parse_tabs_font_family_v1(default_font_family)
    if fallback_font_family is not None:
        return fallback_font_family
    return '"Segoe UI", Tahoma, Arial, sans-serif'


def _resolve_admin_process_title_color_hex_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_color_hex: str = "#0F172A",
) -> str:
    config = ADMIN_PROCESS_TITLE_STYLE_DEFINITION_KEYS_V1["color"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_color_hex = _parse_tabs_color_hex_v1(raw_value)
    if parsed_color_hex is not None:
        return parsed_color_hex
    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#0F172A"


def _resolve_admin_card_item_font_size_px_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_text_size_px: int = 12,
) -> int:
    config = ADMIN_SUBPROCESS_CARD_ITEM_STYLE_DEFINITION_KEYS_V1["font_size"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_text_size_px = _parse_tabs_text_size_px_v1(raw_value)
    if parsed_text_size_px is not None:
        return parsed_text_size_px
    fallback_text_size_px = _parse_tabs_text_size_px_v1(default_text_size_px)
    if fallback_text_size_px is not None:
        return fallback_text_size_px
    return 12


def _resolve_admin_card_item_font_family_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_font_family: str = 'Inter, "Segoe UI", sans-serif',
) -> str:
    config = ADMIN_SUBPROCESS_CARD_ITEM_STYLE_DEFINITION_KEYS_V1["font_family"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_font_family = _parse_tabs_font_family_v1(raw_value)
    if parsed_font_family is not None:
        return parsed_font_family
    fallback_font_family = _parse_tabs_font_family_v1(default_font_family)
    if fallback_font_family is not None:
        return fallback_font_family
    return 'Inter, "Segoe UI", sans-serif'


def _resolve_admin_card_item_color_hex_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_color_hex: str = "#0F1F3A",
) -> str:
    config = ADMIN_SUBPROCESS_CARD_ITEM_STYLE_DEFINITION_KEYS_V1["color"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_color_hex = _parse_tabs_color_hex_v1(raw_value)
    if parsed_color_hex is not None:
        return parsed_color_hex
    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#0F1F3A"


def _resolve_admin_card_item_font_weight_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_font_weight: int = 500,
) -> int:
    config = ADMIN_SUBPROCESS_CARD_ITEM_STYLE_DEFINITION_KEYS_V1["font_weight"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_font_weight = _parse_font_weight_value_v1(raw_value)
    if parsed_font_weight is not None:
        return parsed_font_weight
    fallback_font_weight = _parse_font_weight_value_v1(default_font_weight)
    if fallback_font_weight is not None:
        return fallback_font_weight
    return 500


def _resolve_admin_card_table_head_color_hex_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_color_hex: str = "#000000",
) -> str:
    config = ADMIN_SUBPROCESS_CARD_TABLE_HEAD_STYLE_DEFINITION_KEYS_V1["color"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_color_hex = _parse_tabs_color_hex_v1(raw_value)
    if parsed_color_hex is not None:
        return parsed_color_hex
    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#000000"


def _resolve_admin_topbar_color_hex_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_color_hex: str = "#334A62",
) -> str:
    config = ADMIN_TOPBAR_STYLE_DEFINITION_KEYS_V1["color"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_color_hex = _parse_tabs_color_hex_v1(raw_value)
    if parsed_color_hex is not None:
        return parsed_color_hex
    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#334A62"


def _resolve_admin_sidebar_background_color_hex_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_color_hex: str = "#F3F3F4",
) -> str:
    config = ADMIN_SIDEBAR_STYLE_DEFINITION_KEYS_V1["background_color"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_color_hex = _parse_tabs_color_hex_v1(raw_value)
    if parsed_color_hex is not None:
        return parsed_color_hex
    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#F3F3F4"


def _resolve_admin_sidebar_active_background_color_hex_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_color_hex: str = "#E4E6EA",
) -> str:
    config = ADMIN_SIDEBAR_STYLE_DEFINITION_KEYS_V1["active_background_color"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_color_hex = _parse_tabs_color_hex_v1(raw_value)
    if parsed_color_hex is not None:
        return parsed_color_hex
    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#E4E6EA"


def _resolve_admin_sidebar_text_color_hex_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_color_hex: str = "#5C6572",
) -> str:
    config = ADMIN_SIDEBAR_STYLE_DEFINITION_KEYS_V1["text_color"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_color_hex = _parse_tabs_color_hex_v1(raw_value)
    if parsed_color_hex is not None:
        return parsed_color_hex
    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#5C6572"


def _resolve_admin_sidebar_text_size_px_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_text_size_px: int = 14,
) -> int:
    config = ADMIN_SIDEBAR_STYLE_DEFINITION_KEYS_V1["text_size"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_text_size_px = _parse_tabs_text_size_px_v1(raw_value)
    if parsed_text_size_px is not None:
        return parsed_text_size_px
    fallback_text_size_px = _parse_tabs_text_size_px_v1(default_text_size_px)
    if fallback_text_size_px is not None:
        return fallback_text_size_px
    return 14


def _resolve_admin_sidebar_font_family_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_font_family: str = '"Segoe UI", Tahoma, Arial, sans-serif',
) -> str:
    config = ADMIN_SIDEBAR_STYLE_DEFINITION_KEYS_V1["font_family"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_font_family = _parse_tabs_font_family_v1(raw_value)
    if parsed_font_family is not None:
        return parsed_font_family
    fallback_font_family = _parse_tabs_font_family_v1(default_font_family)
    if fallback_font_family is not None:
        return fallback_font_family
    return '"Segoe UI", Tahoma, Arial, sans-serif'


def _resolve_admin_sidebar_font_weight_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_font_weight: int = 500,
) -> int:
    config = ADMIN_SIDEBAR_STYLE_DEFINITION_KEYS_V1["font_weight"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_font_weight = _parse_font_weight_value_v1(raw_value)
    if parsed_font_weight is not None:
        return parsed_font_weight
    fallback_font_weight = _parse_font_weight_value_v1(default_font_weight)
    if fallback_font_weight is not None:
        return fallback_font_weight
    return 500


def _resolve_admin_sidebar_icon_color_hex_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_color_hex: str = "#5F6B7D",
) -> str:
    config = ADMIN_SIDEBAR_STYLE_DEFINITION_KEYS_V1["icon_color"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_color_hex = _parse_tabs_color_hex_v1(raw_value)
    if parsed_color_hex is not None:
        return parsed_color_hex
    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#5F6B7D"


def _resolve_admin_sidebar_section_text_color_hex_from_definitions_v1(
    *,
    rows: list[AdminDefinition],
    default_color_hex: str = "#808792",
) -> str:
    config = ADMIN_SIDEBAR_STYLE_DEFINITION_KEYS_V1["section_text_color"]
    parameter_names = tuple(
        str(name)
        for name in config.get("parameter_names", ())
        if str(name or "").strip()
    )
    raw_value = _resolve_definition_initial_value_by_alias_v1(
        rows=rows,
        parameter_type=str(config["parameter_type"]),
        parameter_names=parameter_names,
        process_name=str(config["process_name"]),
        subprocess_name=str(config["subprocess_name"]),
    )
    parsed_color_hex = _parse_tabs_color_hex_v1(raw_value)
    if parsed_color_hex is not None:
        return parsed_color_hex
    fallback_color_hex = _parse_tabs_color_hex_v1(default_color_hex)
    if fallback_color_hex is not None:
        return fallback_color_hex
    return "#808792"


def _resolve_initial_menu_target(
    resolved_menu: str,
    resolved_profile_tab: str,
    resolved_admin_tab: str,
    settings_edit_key: str,
    definition_edit_id: str,
    can_manage_all_entities: bool,
    sidebar_menu_settings: list[dict[str, Any]],
) -> tuple[str, str]:
    clean_menu_key = resolve_menu_key_alias(resolved_menu)
    settings_by_key = {
        str(raw_row.get("key") or "").strip().lower(): raw_row
        for raw_row in sidebar_menu_settings
        if isinstance(raw_row, dict) and str(raw_row.get("key") or "").strip()
    }

    if clean_menu_key == "home":
        return "#home-summary-card", ""
    if clean_menu_key == "perfil":
        if resolved_profile_tab == "morada":
            return "#perfil-morada-card", ""
        if resolved_profile_tab == "treinamento":
            return "#dados-treinamento-card", ""
        return "#perfil-pessoal-card", ""
    if clean_menu_key == "administrativo":
        if resolved_admin_tab == "menu":
            return _resolve_admin_menu_target_v1(settings_edit_key), ""
        if resolved_admin_tab == "definicoes":
            return _resolve_admin_definicoes_target_v1(definition_edit_id), ""
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        if resolved_admin_tab == "sessoes":
            return "#admin-sidebar-sections-card", ""
        if resolved_admin_tab in {"menu", "contas"}:
            return "#admin-account-status-card", ""
        if resolved_admin_tab == "utilizador":
            return "#create-user-card", ""
        return "#create-entity-card", ""
    if clean_menu_key == "configuracao":
        if settings_edit_key:
            return "#settings-menu-edit-card", ""
        return "#admin-account-status-card", ""
    if clean_menu_key == MENU_MEU_PERFIL_KEY:
        return "#perfil-pessoal-card", ""

    matched_menu_row = settings_by_key.get(clean_menu_key)
    if matched_menu_row is not None:
        return "#dynamic-process-card", _resolve_first_dynamic_section_key(matched_menu_row)
    return "", ""


# APPVERBO_ADMIN_TAB_MENU_CANONICAL_V1_START

def _normalize_admin_tab_menu_v1(raw_admin_tab: object) -> str:
    clean_admin_tab = str(raw_admin_tab or "").strip().lower()

    legacy_aliases = {
        "contas": "menu",
    }

    clean_admin_tab = legacy_aliases.get(clean_admin_tab, clean_admin_tab)

    if clean_admin_tab not in {"utilizador", "entidade", "menu", "sessoes", "definicoes"}:
        return "entidade"

    return clean_admin_tab

# APPVERBO_ADMIN_TAB_MENU_CANONICAL_V1_END


# APPVERBO_ADMIN_PROCESS_MENU_FALLBACK_V1_START
def _resolve_blank_admin_process_menu_v1(
    *,
    raw_menu: object,
    raw_admin_tab: object,
    raw_target: object,
    raw_settings_edit_key: object,
    raw_definition_edit_id: object,
    raw_sidebar_section_edit_key: object,
    raw_sidebar_sections_tab: object,
) -> str:
    clean_menu = resolve_menu_key_alias(raw_menu)
    if clean_menu:
        return clean_menu

    clean_admin_tab = _normalize_admin_tab_menu_v1(raw_admin_tab)
    clean_target = _normalize_target_selector_v1(raw_target)
    clean_settings_edit_key = str(raw_settings_edit_key or "").strip()
    clean_definition_edit_id = str(raw_definition_edit_id or "").strip()
    clean_sidebar_section_edit_key = str(raw_sidebar_section_edit_key or "").strip()
    clean_sidebar_sections_tab = str(raw_sidebar_sections_tab or "").strip().lower()

    if clean_admin_tab in {"menu", "sessoes", "definicoes"}:
        return "sessoes"

    if clean_admin_tab in {"entidade", "utilizador"}:
        return "administrativo"

    if clean_target in {
        "#settings-menu-edit-card",
        "#admin-menu-card",
        "#admin-menu-card-create",
        "#admin-menu-card-inactive",
        "#admin-definicoes-card",
        "#admin-definicoes-card-edit",
        "#admin-definicoes-card-create",
        "#admin-definicoes-card-inactive",
        "#admin-sidebar-sections-card",
        "#admin-sidebar-sections-form-card",
        "#admin-sidebar-sections-card-create",
        "#admin-sidebar-sections-card-inactive",
    }:
        return "sessoes"

    if (
        clean_settings_edit_key
        or clean_definition_edit_id
        or clean_sidebar_section_edit_key
        or clean_sidebar_sections_tab == "sessoes"
    ):
        return "sessoes"

    return "home"


# APPVERBO_ADMIN_PROCESS_MENU_FALLBACK_V1_END


# APPVERBO_ADMIN_TAB_SESSOES_FALLBACK_V1_START
def _resolve_sessions_admin_tab_fallback_v1(
    *,
    resolved_menu: str,
    resolved_admin_tab: str,
    target: str,
    sidebar_sections_tab: str,
    sidebar_section_edit_key: str,
) -> str:
    if str(resolved_menu or "").strip().lower() != "administrativo":
        return resolved_admin_tab

    clean_target = str(target or "").strip().lower()
    if clean_target.startswith("#"):
        clean_target = clean_target[1:]

    clean_sidebar_sections_tab = str(sidebar_sections_tab or "").strip().lower()
    clean_sidebar_section_edit_key = str(sidebar_section_edit_key or "").strip()
    session_target_keys = {
        "admin-sidebar-sections-card",
        "admin-sidebar-sections-form-card",
        "admin-sidebar-sections-card-create",
        "admin-sidebar-sections-card-inactive",
    }

    if (
        clean_sidebar_sections_tab == "sessoes"
        or bool(clean_sidebar_section_edit_key)
        or clean_target in session_target_keys
    ):
        return "sessoes"

    return resolved_admin_tab


# APPVERBO_ADMIN_TAB_SESSOES_FALLBACK_V1_END





@router.get("/users/new", response_class=HTMLResponse)
def new_user_page(
    request: Request,
    success: str | None = None,
    error: str | None = None,
    invite_link: str | None = None,
    entity_success: str | None = None,
    entity_error: str | None = None,
    profile_success: str | None = None,
    profile_error: str | None = None,
    settings_success: str | None = None,
    settings_error: str | None = None,
    profile_tab: str = "pessoal",
    menu: str = "home",
    admin_tab: str = "entidade",
    entity_edit_id: str = "",
    user_edit_id: str = "",
    definition_edit_id: str = "",
    entity_view: str = "",
    user_view: str = "",
    settings_edit_key: str = "",
    settings_action: str = "",
    settings_tab: str = "",
    target: str = "",
    profile_section: str = "",
    dynamic_process_section: str = "",
    section_key: str = "",
    sidebar_section_edit_key: str = "",
    sidebar_sections_tab: str = "",
    appverbo_after_save: str = "",
) -> HTMLResponse:
    resolved_profile_tab = profile_tab.strip().lower()
    if resolved_profile_tab not in {"pessoal", "morada", "treinamento"}:
        resolved_profile_tab = "pessoal"
    resolved_menu = _resolve_blank_admin_process_menu_v1(
        raw_menu=menu,
        raw_admin_tab=admin_tab,
        raw_target=target,
        raw_settings_edit_key=settings_edit_key,
        raw_definition_edit_id=definition_edit_id,
        raw_sidebar_section_edit_key=sidebar_section_edit_key,
        raw_sidebar_sections_tab=sidebar_sections_tab,
    )
    resolved_admin_tab = _normalize_admin_tab_menu_v1(admin_tab)
    resolved_admin_tab = _resolve_sessions_admin_tab_fallback_v1(
        resolved_menu=resolved_menu,
        resolved_admin_tab=resolved_admin_tab,
        target=target,
        sidebar_sections_tab=sidebar_sections_tab,
        sidebar_section_edit_key=sidebar_section_edit_key,
    )
    (
        clean_target_from_query,
        clean_profile_section_from_query,
        clean_dynamic_section_from_query,
        has_admin_dynamic_process_context,
    ) = _resolve_requested_dynamic_context_v1(
        request,
        fallback_target=target,
        fallback_profile_section=profile_section,
        fallback_dynamic_process_section=dynamic_process_section,
        fallback_section_key=section_key,
    )
    if (
        resolved_menu in {"administrativo", "sessoes"}
        and has_admin_dynamic_process_context
        and clean_target_from_query == "#dynamic-process-card"
    ):
        resolved_admin_tab = "definicoes"
    parsed_entity_edit_id: int | None = None
    clean_entity_edit_id = entity_edit_id.strip()
    if clean_entity_edit_id.isdigit():
        parsed_entity_edit_id = int(clean_entity_edit_id)
    parsed_user_edit_id: int | None = None
    clean_user_edit_id = user_edit_id.strip()
    if clean_user_edit_id.isdigit():
        parsed_user_edit_id = int(clean_user_edit_id)
    clean_definition_edit_id = str(definition_edit_id or "").strip()
    readonly_truthy_values = {"1", "true", "sim", "yes", "on"}
    entity_readonly_mode = (
        entity_view.strip().lower() in readonly_truthy_values and parsed_entity_edit_id is not None
    )
    user_readonly_mode = (
        user_view.strip().lower() in readonly_truthy_values and parsed_user_edit_id is not None
    )
    clean_settings_edit_key = resolve_menu_key_alias(settings_edit_key)
    clean_settings_action = settings_action.strip().lower()
    # APPVERBO_ADMIN_MENU_ALLOW_MOVE_ACTIONS_V1
    if clean_settings_action not in {"toggle", "edit", "delete", "create", "move_up", "move_down"}:
        clean_settings_action = "edit"
    clean_settings_tab = settings_tab.strip().lower()
    if clean_settings_tab not in {
        "geral",
        "menu",
        "campos-config",
        "campos-adicionais",
        "campos-quantidade",
        "lista",
        "campos-subsequentes",
        "sessoes-sidebar",
    }:
        clean_settings_tab = ""

    is_admin_menu_tab = (
        resolved_menu in {"administrativo", "sessoes"}
        and resolved_admin_tab == "menu"
    )
    is_admin_definicoes_tab = (
        resolved_menu in {"administrativo", "sessoes"}
        and resolved_admin_tab == "definicoes"
    )
    is_admin_sessoes_tab_request_v1 = (
        resolved_menu in {"administrativo", "sessoes"}
        and resolved_admin_tab == "sessoes"
    )
    is_admin_menu_edit_request_v1 = (
        is_admin_menu_tab
        and _is_admin_menu_edit_request_v1(
            clean_settings_edit_key,
            clean_target_from_query,
        )
    )
    is_admin_definicoes_edit_request_v1 = (
        is_admin_definicoes_tab
        and _is_admin_definicoes_edit_request_v1(
            clean_definition_edit_id,
            clean_target_from_query,
        )
    )
    is_admin_sessoes_edit_request_v1 = (
        is_admin_sessoes_tab_request_v1
        and _is_admin_sessoes_edit_request_v1(
            sidebar_section_edit_key,
            clean_target_from_query,
        )
    )
    effective_settings_edit_key = clean_settings_edit_key
    effective_settings_action = clean_settings_action
    effective_settings_tab = clean_settings_tab
    effective_definition_edit_id = clean_definition_edit_id
    effective_sidebar_section_edit_key = _resolve_targeted_edit_key_v1(
        sidebar_section_edit_key,
        clean_target_from_query,
        "#admin-sidebar-sections-form-card",
    )

    if is_admin_menu_tab and not is_admin_menu_edit_request_v1:
        effective_settings_edit_key = ""
        effective_settings_tab = ""

        if clean_settings_action != "create":
            effective_settings_action = ""

    if is_admin_definicoes_tab and not is_admin_definicoes_edit_request_v1:
        effective_definition_edit_id = ""

    if is_admin_sessoes_tab_request_v1 and not is_admin_sessoes_edit_request_v1:
        effective_sidebar_section_edit_key = ""

    admin_tabs_width_ch_v1 = 24
    admin_tabs_text_size_px_v1 = 13
    admin_tabs_font_family_v1 = '"Segoe UI", Tahoma, Arial, sans-serif'
    admin_tabs_color_hex_v1 = "#1F4FA3"
    admin_tabs_text_color_hex_v1 = ""
    admin_process_title_font_size_px_v1 = 20
    admin_process_title_font_family_v1 = '"Segoe UI", Tahoma, Arial, sans-serif'
    admin_process_title_color_hex_v1 = "#0F172A"
    admin_card_item_font_size_px_v1 = 12
    admin_card_item_font_family_v1 = 'Inter, "Segoe UI", sans-serif'
    admin_card_item_color_hex_v1 = "#0F1F3A"
    admin_card_item_font_weight_v1 = 500
    admin_card_table_head_color_hex_v1 = "#000000"
    admin_topbar_color_hex_v1 = "#334A62"
    admin_sidebar_bg_color_hex_v1 = "#F3F3F4"
    admin_sidebar_active_bg_color_hex_v1 = "#E4E6EA"
    admin_sidebar_text_color_hex_v1 = "#5C6572"
    admin_sidebar_text_size_px_v1 = 14
    admin_sidebar_font_family_v1 = '"Segoe UI", Tahoma, Arial, sans-serif'
    admin_sidebar_font_weight_v1 = 500
    admin_sidebar_icon_color_hex_v1 = "#5F6B7D"
    admin_sidebar_section_text_color_hex_v1 = "#808792"
    menu_settings_edit_key = (
        effective_settings_edit_key
        if (is_admin_menu_tab or is_admin_sessoes_tab_request_v1)
        else ""
    )
    menu_admin_page_payload = build_menu_admin_page_payload_v1({})

    ensure_admin_process_title_default_definitions_v1()

    with SessionLocal() as session:
        current_user = get_current_user(request, session)
        if current_user is None:
            return RedirectResponse(
                url="/login?error=Efetue login para continuar.",
                status_code=status.HTTP_302_FOUND,
            )
        selected_entity_id = get_session_entity_id(request)

        admin_definition_rows_v1 = list_admin_definitions_in_scope_v1(
            session,
            selected_entity_id=selected_entity_id,
        )
        admin_tabs_width_ch_v1 = _resolve_admin_tabs_width_ch_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_width_ch=24,
        )
        admin_tabs_text_size_px_v1 = _resolve_admin_tabs_text_size_px_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_text_size_px=13,
        )
        admin_tabs_font_family_v1 = _resolve_admin_tabs_font_family_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_font_family='"Segoe UI", Tahoma, Arial, sans-serif',
        )
        admin_tabs_color_hex_v1 = _resolve_admin_tabs_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#1F4FA3",
        )
        admin_tabs_text_color_hex_v1 = _resolve_admin_tabs_text_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_text_color_hex="",
        )
        admin_process_title_font_size_px_v1 = _resolve_admin_process_title_font_size_px_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_text_size_px=20,
        )
        admin_process_title_font_family_v1 = _resolve_admin_process_title_font_family_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_font_family='"Segoe UI", Tahoma, Arial, sans-serif',
        )
        admin_process_title_color_hex_v1 = _resolve_admin_process_title_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#0F172A",
        )
        admin_card_item_font_size_px_v1 = _resolve_admin_card_item_font_size_px_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_text_size_px=12,
        )
        admin_card_item_font_family_v1 = _resolve_admin_card_item_font_family_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_font_family='Inter, "Segoe UI", sans-serif',
        )
        admin_card_item_color_hex_v1 = _resolve_admin_card_item_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#0F1F3A",
        )
        admin_card_item_font_weight_v1 = _resolve_admin_card_item_font_weight_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_font_weight=500,
        )
        admin_card_table_head_color_hex_v1 = _resolve_admin_card_table_head_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#000000",
        )
        admin_topbar_color_hex_v1 = _resolve_admin_topbar_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#334A62",
        )
        admin_sidebar_bg_color_hex_v1 = _resolve_admin_sidebar_background_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#F3F3F4",
        )
        admin_sidebar_active_bg_color_hex_v1 = _resolve_admin_sidebar_active_background_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#E4E6EA",
        )
        admin_sidebar_text_color_hex_v1 = _resolve_admin_sidebar_text_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#5C6572",
        )
        admin_sidebar_text_size_px_v1 = _resolve_admin_sidebar_text_size_px_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_text_size_px=14,
        )
        admin_sidebar_font_family_v1 = _resolve_admin_sidebar_font_family_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_font_family='"Segoe UI", Tahoma, Arial, sans-serif',
        )
        admin_sidebar_font_weight_v1 = _resolve_admin_sidebar_font_weight_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_font_weight=500,
        )
        admin_sidebar_icon_color_hex_v1 = _resolve_admin_sidebar_icon_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#5F6B7D",
        )
        admin_sidebar_section_text_color_hex_v1 = _resolve_admin_sidebar_section_text_color_hex_from_definitions_v1(
            rows=admin_definition_rows_v1,
            default_color_hex="#808792",
        )
        current_user_is_admin = is_admin_user(
            session, current_user["id"], current_user["login_email"]
        )
        entity_permissions = get_user_entity_permissions(
            session,
            current_user["id"],
            current_user["login_email"],
            selected_entity_id,
        )
        page_data = get_page_data(
            session,
            actor_user_id=current_user["id"],
            actor_login_email=current_user["login_email"],
            selected_entity_id=selected_entity_id,
        )
        visible_menu_keys = {
            str(raw_key or "").strip().lower()
            for raw_key in page_data.get("visible_sidebar_menu_keys", [])
            if str(raw_key or "").strip()
        }
        # APPVERBO_PAGE_HANDLER_ALLOW_MEU_PERFIL_V1_START
        # O menu "meu_perfil" e um processo especial que pode nao aparecer em
        # visible_sidebar_menu_keys, mas deve ser aceite quando vem no redirect
        # pos-save. Caso contrario, /users/new?menu=meu_perfil cai em Home.
        # Tambem permite menus nao visiveis se for retorno pos-save, para manter
        # o contexto de edicao.
        is_post_save_return = str(appverbo_after_save or "").strip() == "1"
        if (
            resolved_menu not in {"perfil", MENU_MEU_PERFIL_KEY}
            and resolved_menu not in visible_menu_keys
            and not is_post_save_return
        ):
            resolved_menu = "home"
        # APPVERBO_PAGE_HANDLER_ALLOW_MEU_PERFIL_V1_END
        user_personal_data = get_user_personal_data(session, current_user["id"], selected_entity_id)

        is_admin_menu_scope_v1 = resolved_menu in {"administrativo", "sessoes"}
        is_entidade_tab_v1 = is_admin_menu_scope_v1 and resolved_admin_tab == "entidade"
        is_utilizador_tab_v1 = is_admin_menu_scope_v1 and resolved_admin_tab == "utilizador"
        is_sessoes_tab_v1 = is_admin_menu_scope_v1 and resolved_admin_tab == "sessoes"
        is_definicoes_tab_v1 = is_admin_menu_scope_v1 and resolved_admin_tab == "definicoes"

        should_load_entity_context_v1 = bool(
            parsed_entity_edit_id is not None or is_entidade_tab_v1
        )
        should_load_user_context_v1 = bool(
            parsed_user_edit_id is not None or is_utilizador_tab_v1
        )
        should_load_sessoes_context_v1 = bool(
            is_sessoes_tab_v1
            or is_definicoes_tab_v1
            or effective_sidebar_section_edit_key
            or str(sidebar_sections_tab or "").strip().lower() == "sessoes"
        )

        next_entity_internal_number = ""
        entity_edit_data = get_entity_edit_defaults()
        if should_load_entity_context_v1:
            next_entity_internal_number = get_next_entity_internal_number(session)
            entity_edit_data = get_entity_edit_data(
                session,
                parsed_entity_edit_id,
                allowed_entity_ids=entity_permissions["allowed_entity_ids"],
            )

        user_edit_data = get_user_edit_defaults()
        if should_load_user_context_v1:
            user_edit_context = build_user_admin_edit_context_v1(
                session=session,
                actor_user_id=int(current_user["id"]),
                actor_login_email=str(current_user["login_email"]),
                selected_entity_id=selected_entity_id,
                user_edit_id=parsed_user_edit_id,
            )
            user_edit_data = user_edit_context.get("user_edit_data", get_user_edit_defaults())

        sessoes_admin_page_payload = build_sessoes_admin_page_payload_v1({})
        if should_load_sessoes_context_v1:
            sessoes_admin_context = build_sessoes_admin_context_v1(
                session=session,
                actor_user_id=int(current_user["id"]),
                actor_login_email=str(current_user["login_email"]),
                selected_entity_id=selected_entity_id,
                session_edit_key=effective_sidebar_section_edit_key,
            )
            sessoes_admin_page_payload = build_sessoes_admin_page_payload_v1(
                sessoes_admin_context
            )

        active_sidebar_sections_v22 = list(
            sessoes_admin_page_payload.get("active_sidebar_sections", [])
        )
        inactive_sidebar_sections_v22 = list(
            sessoes_admin_page_payload.get("inactive_sidebar_sections", [])
        )
        sidebar_section_edit_data_v22 = dict(
            sessoes_admin_page_payload.get("sidebar_section_edit_data", {})
        )
        if is_admin_menu_tab or (
            resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "definicoes"
        ):
            menu_admin_context = build_menu_admin_context_v1(
                session=session,
                actor_user_id=int(current_user["id"]),
                actor_login_email=str(current_user["login_email"]),
                selected_entity_id=selected_entity_id,
                menu_edit_key=menu_settings_edit_key,
            )
            menu_admin_page_payload = build_menu_admin_page_payload_v1(
                menu_admin_context
            )

        settings_edit_data: dict[str, Any] | None = None
        if menu_settings_edit_key:
            candidate_menu_edit_data = dict(menu_admin_page_payload.get("menu_edit_data", {}))

            if str(candidate_menu_edit_data.get("key") or "").strip():
                settings_edit_data = candidate_menu_edit_data
            else:
                for row in menu_admin_page_payload.get("menu_settings", []):
                    row_key = str(row.get("key", "")).strip().lower()
                    if row_key == menu_settings_edit_key:
                        settings_edit_data = dict(row)
                        break

    initial_menu_target, initial_dynamic_process_section = _resolve_initial_menu_target(
        resolved_menu=resolved_menu,
        resolved_profile_tab=resolved_profile_tab,
        resolved_admin_tab=resolved_admin_tab,
        settings_edit_key=menu_settings_edit_key,
        definition_edit_id=effective_definition_edit_id,
        can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
        sidebar_menu_settings=list(
            menu_admin_page_payload.get("menu_settings", [])
            if is_admin_menu_tab
            else page_data.get("sidebar_menu_settings", [])
        ),
    )

    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_START
    if clean_target_from_query:
        initial_menu_target = clean_target_from_query

    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_START
    if (
        resolved_menu in {"administrativo", "sessoes"}
        and resolved_admin_tab == "utilizador"
        and parsed_user_edit_id is not None
    ):
        initial_menu_target = "#edit-user-card"
        initial_dynamic_process_section = ""
    # APPVERBO_PAGE_HANDLER_UTILIZADOR_EDIT_TARGET_V2_END


    if (
        resolved_menu == MENU_MEU_PERFIL_KEY
        and clean_target_from_query != "#dynamic-process-card"
        and not clean_dynamic_section_from_query
    ):
        initial_menu_target = "#perfil-pessoal-card"

    if (
        resolved_menu == MENU_MEU_PERFIL_KEY
        and clean_dynamic_section_from_query
        and not clean_target_from_query
    ):
        initial_menu_target = "#dynamic-process-card"

    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query

    if resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "sessoes":
        initial_menu_target = _resolve_admin_sessoes_target_v1(
            effective_sidebar_section_edit_key
        )
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    elif resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "menu":
        if has_admin_dynamic_process_context:
            initial_menu_target = "#dynamic-process-card"
            initial_dynamic_process_section = clean_dynamic_section_from_query
        else:
            initial_menu_target = _resolve_admin_menu_target_v1(menu_settings_edit_key)
            initial_dynamic_process_section = ""
            clean_dynamic_section_from_query = ""
    elif resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "definicoes":
        if has_admin_dynamic_process_context:
            initial_menu_target = "#dynamic-process-card"
            initial_dynamic_process_section = clean_dynamic_section_from_query
        else:
            initial_menu_target = _resolve_admin_definicoes_target_v1(
                effective_definition_edit_id
            )
            initial_dynamic_process_section = ""
            clean_dynamic_section_from_query = ""

    is_post_save_return = str(appverbo_after_save or "").strip() == "1"
    # APPVERBO_PAGE_STATE_CONTEXT_V1_START
    page_state = resolver_pagina_default_v1(
        resolved_menu=resolved_menu,
        resolved_admin_tab=resolved_admin_tab,
        resolved_profile_tab=resolved_profile_tab,
        parsed_user_edit_id=parsed_user_edit_id,
        user_view=user_view,
        parsed_entity_edit_id=parsed_entity_edit_id,
        entity_view=entity_view,
        clean_settings_edit_key=effective_settings_edit_key,
        clean_settings_action=effective_settings_action,
        clean_target_from_query=clean_target_from_query,
        clean_profile_section_from_query=clean_profile_section_from_query,
        clean_dynamic_section_from_query=clean_dynamic_section_from_query,
        sidebar_section_edit_key=effective_sidebar_section_edit_key,
        is_post_save_return=is_post_save_return,
    )
    # APPVERBO_PAGE_STATE_CONTEXT_V1_END
    # APPVERBO_PAGE_HANDLER_POST_SAVE_CONTEXT_V1_END

    # ###################################################################################
    # A aba Administrativo -> Menu usa o alvo canonico admin-menu-card
    # apenas quando nao estamos a reentrar num subprocesso dinamico.
    if resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "menu":
        if has_admin_dynamic_process_context:
            initial_menu_target = "#dynamic-process-card"
            initial_dynamic_process_section = clean_dynamic_section_from_query
        else:
            initial_menu_target = _resolve_admin_menu_target_v1(menu_settings_edit_key)
            initial_dynamic_process_section = ""
            clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_BACKEND_RENDER_V4_END

    # APPVERBO_ADMIN_PROCESS_ONLY_V1_START
    # Quando o utilizador clica apenas no processo "Administrativo",
    # a tela deve mostrar somente o bloco central de subprocessos.
    # Os cards de Entidade, Utilizador, Sessoes e Menu so aparecem
    # depois do clique no subprocesso correspondente.
    raw_admin_tab_param_for_process_only = str(
        request.query_params.get("admin_tab", "") or ""
    ).strip()
    raw_target_param_for_process_only = str(request.query_params.get("target", "") or "").strip()
    raw_hash_target_for_process_only = str(request.query_params.get("hash", "") or "").strip()
    raw_settings_edit_key_for_process_only = str(
        request.query_params.get("settings_edit_key", "") or ""
    ).strip()
    raw_sidebar_section_edit_key_for_process_only = str(
        request.query_params.get("sidebar_section_edit_key", "") or ""
    ).strip()
    raw_settings_tab_for_process_only = str(
        request.query_params.get("settings_tab", "") or ""
    ).strip()
    raw_sidebar_sections_tab_for_process_only = str(
        request.query_params.get("sidebar_sections_tab", "") or ""
    ).strip()
    clean_settings_action_for_admin_refresh = str(settings_action or "").strip().lower()

    admin_process_only = (
        resolved_menu in {"administrativo", "sessoes"}
        and not raw_admin_tab_param_for_process_only
        and not raw_target_param_for_process_only
        and not raw_hash_target_for_process_only
        and not raw_settings_edit_key_for_process_only
        and not raw_sidebar_section_edit_key_for_process_only
        and not raw_settings_tab_for_process_only
        and not raw_sidebar_sections_tab_for_process_only
    )

    if admin_process_only:
        initial_menu_target = "#menu-tabs-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_PROCESS_ONLY_V1_END


    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V4_START
    if resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "menu":
        if has_admin_dynamic_process_context:
            initial_menu_target = "#dynamic-process-card"
            initial_dynamic_process_section = clean_dynamic_section_from_query
        else:
            initial_menu_target = _resolve_admin_menu_target_v1(menu_settings_edit_key)
            initial_dynamic_process_section = ""
            clean_dynamic_section_from_query = ""
    # APPVERBO_ADMIN_MENU_NATIVE_POST_CONTEXT_V4_END

    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_START
    admin_subprocess_state_v2 = None
    admin_menu_state = None
    admin_subprocess_state_definicoes_v1 = None

    # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_START
    # Entidade permanece no fluxo legado em /users/new.
    # O renderer V2 ainda nao entrega as secoes de listagem esperadas no template
    # e acabava por mostrar apenas o botao "Criar entidade".
    if resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "entidade":
        admin_subprocess_state_v2 = None
    # APPVERBO_ADMIN_SUBPROCESS_STATE_ENTIDADE_V2_END

    if resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "sessoes":
        sessoes_subprocess_config_v2 = get_admin_subprocess_config("sessoes")

        if sessoes_subprocess_config_v2 is not None:
            current_entity_scope_for_sessoes = str(
                page_data.get("current_entity_scope") or ""
            ).strip().lower()
            sessoes_entity_name_v1 = _load_selected_entity_name_for_admin_subprocess_v1(
                session,
                selected_entity_id,
            )

            admin_subprocess_state_v2 = build_admin_subprocess_state_from_repository(
                config=sessoes_subprocess_config_v2,
                session=session,
                edit_key=effective_sidebar_section_edit_key,
                success=settings_success if resolved_admin_tab == "sessoes" else "",
                error=settings_error if resolved_admin_tab == "sessoes" else "",
                return_url=build_sessoes_admin_return_url_v2(
                    admin_tab="sessoes",
                    target="admin-sidebar-sections-card",
                ),
                context={
                    "page_state": page_state,
                    "current_user": current_user,
                    "selected_entity_id": selected_entity_id,
                    "allowed_entity_ids": entity_permissions["allowed_entity_ids"],
                    "can_manage_all_entities": entity_permissions["can_manage_all_entities"],
                },
            )

            if admin_subprocess_state_v2 is not None:
                admin_subprocess_state_v2 = _filter_sessoes_admin_subprocess_state_for_scope_v1(
                    admin_subprocess_state_v2,
                    current_entity_scope_for_sessoes,
                )
                admin_subprocess_state_v2 = _decorate_admin_subprocess_state_with_entity_name_v1(
                    admin_subprocess_state_v2,
                    sessoes_entity_name_v1,
                )

                original_options = []
                for field in sessoes_subprocess_config_v2.fields:
                    if field.key == "visibility_scope_mode":
                        original_options = list(field.options)
                        break

                filtered_options = []
                for val, label in original_options:
                    if val == "owner" and current_entity_scope_for_sessoes != "owner":
                        continue
                    filtered_options.append((val, label))

                admin_subprocess_state_v2.field_options["visibility_scope_mode"] = tuple(filtered_options)
                admin_subprocess_state_v2.active_fields = tuple(
                    get_sessoes_visible_fields_v2(current_entity_scope_for_sessoes)
                )

                if current_entity_scope_for_sessoes != "owner":
                    create_data_v1 = dict(admin_subprocess_state_v2.create_data or {})
                    create_data_v1["visibility_scope_mode"] = str(
                        create_data_v1.get("visibility_scope_mode") or "legado"
                    ).strip() or "legado"
                    admin_subprocess_state_v2.create_data = create_data_v1

                    if isinstance(admin_subprocess_state_v2.edit_data, dict):
                        edit_data_v1 = dict(admin_subprocess_state_v2.edit_data or {})
                        edit_data_v1["visibility_scope_mode"] = str(
                            edit_data_v1.get("visibility_scope_mode") or "legado"
                        ).strip() or "legado"
                        admin_subprocess_state_v2.edit_data = edit_data_v1

                admin_subprocess_state_v2.active_columns = tuple(
                    get_sessoes_visible_columns_v2(current_entity_scope_for_sessoes)
                )
    elif resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "menu":
        admin_menu_state = build_admin_menu_state(
            rows=[
                row
                for row in menu_admin_page_payload.get("menu_settings", [])
                if not bool(row.get("is_deleted"))
            ],
            section_options=tuple(
                (
                    str(option.get("key") or "").strip().lower(),
                    str(option.get("label") or "").strip(),
                )
                for option in menu_admin_page_payload.get("sidebar_section_options", [])
                if str(option.get("key") or "").strip()
                and str(option.get("label") or "").strip()
            ),
            can_manage_all_entities=bool(entity_permissions["can_manage_all_entities"]),
            success=settings_success if resolved_admin_tab == "menu" else "",
            error=settings_error if resolved_admin_tab == "menu" else "",
            return_url=f"/users/new?menu={resolved_menu}&admin_tab=menu&target=admin-menu-card#admin-menu-card",
        )
    elif resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "definicoes":
        definicoes_subprocess_config_v1 = get_admin_subprocess_config("definicoes")

        if definicoes_subprocess_config_v1 is not None:
            menu_rows_for_definicoes_subprocess_options_v1: list[dict[str, Any]] = list(
                menu_admin_page_payload.get("menu_settings", [])
            )
            session_rows_for_definicoes_process_options_v1: list[dict[str, Any]] = list(
                sessoes_admin_page_payload.get("active_sidebar_sections", [])
            )

            if not session_rows_for_definicoes_process_options_v1:
                session_rows_for_definicoes_process_options_v1 = list(
                    sessoes_admin_page_payload.get("active_sessions", [])
                    or sessoes_admin_page_payload.get("sessions", [])
                    or sessoes_admin_page_payload.get("all_sessions", [])
                )

            with SessionLocal() as definicoes_subprocess_session_v1:
                admin_subprocess_state_definicoes_v1 = build_admin_subprocess_state_from_repository(
                    config=definicoes_subprocess_config_v1,
                    session=definicoes_subprocess_session_v1,
                    edit_key=effective_definition_edit_id,
                    success=success or "",
                    error=error or "",
                    return_url=build_sessoes_admin_return_url_v2(
                        admin_tab="definicoes",
                        target="admin-definicoes-card",
                    ),
                    context={
                        "page_state": page_state,
                        "current_user": current_user,
                        "selected_entity_id": selected_entity_id,
                        "allowed_entity_ids": entity_permissions["allowed_entity_ids"],
                        "can_manage_all_entities": entity_permissions["can_manage_all_entities"],
                    },
                )

                if not menu_rows_for_definicoes_subprocess_options_v1:
                    menu_repository_v1 = MenuAdminRepository(MENU_CONFIG)
                    menu_rows_for_definicoes_subprocess_options_v1 = list(
                        menu_repository_v1.list_active(
                            session=definicoes_subprocess_session_v1
                        )
                    )

                current_definition_scope_label_v1 = build_entity_scope_label_v1(
                    definicoes_subprocess_session_v1,
                    selected_entity_id,
                )

            if admin_subprocess_state_definicoes_v1 is not None:
                create_data_v1 = dict(admin_subprocess_state_definicoes_v1.create_data or {})
                create_data_v1["entity_scope_label"] = current_definition_scope_label_v1
                admin_subprocess_state_definicoes_v1.create_data = create_data_v1

                edit_process_value_v1 = ""
                edit_subprocess_value_v1 = ""
                if isinstance(admin_subprocess_state_definicoes_v1.edit_data, dict):
                    edit_process_value_v1 = str(
                        admin_subprocess_state_definicoes_v1.edit_data.get("process_name") or ""
                    ).strip()
                    edit_subprocess_value_v1 = str(
                        admin_subprocess_state_definicoes_v1.edit_data.get("subprocess_name") or ""
                    ).strip()

                admin_subprocess_state_definicoes_v1.field_options["process_name"] = (
                    _build_definicoes_process_options_v1(
                        session_rows_for_definicoes_process_options_v1,
                        edit_process_value_v1,
                    )
                )
                admin_subprocess_state_definicoes_v1.field_options["subprocess_name"] = (
                    _build_definicoes_subprocess_options_v1(
                        menu_rows_for_definicoes_subprocess_options_v1,
                        edit_subprocess_value_v1,
                    )
                )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_SESSOES_V2_END

    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_START
    # Estado nativo em paralelo para validar o subprocesso Utilizador sem trocar a tela legada.
    # O bloco usa sessao propria para ficar isolado da estrutura legada da pagina.
    admin_subprocess_shadow_state_v1 = None

    if resolved_admin_tab == "utilizador":
        utilizador_subprocess_config_v1 = get_admin_subprocess_config("utilizador")

        if utilizador_subprocess_config_v1 is not None:
            with SessionLocal() as admin_subprocess_shadow_session_v1:
                admin_subprocess_shadow_state_v1 = build_admin_subprocess_state_from_repository(
                    config=utilizador_subprocess_config_v1,
                    session=admin_subprocess_shadow_session_v1,
                    edit_key=clean_user_edit_id,
                    success=success or "",
                    error=error or "",
                    return_url="/users/new?menu=administrativo&admin_tab=utilizador",
                    context={
                        "page_state": page_state,
                        "page_state_refresh_home_url": page_state.get("refresh_home_url", "/users/new?menu=home"),
                        "current_user": current_user,
                        "selected_entity_id": selected_entity_id,
                        "allowed_entity_ids": entity_permissions["allowed_entity_ids"],
                        "can_manage_all_entities": entity_permissions["can_manage_all_entities"],
                    },
                )
    # APPVERBO_ADMIN_SUBPROCESS_STATE_UTILIZADOR_SHADOW_V1_END

    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_START
    admin_subprocess_state_utilizador_v1 = None

    if resolved_admin_tab == "utilizador":
        with SessionLocal() as utilizador_subprocess_session_v1:
            admin_subprocess_state_utilizador_v1 = montar_estado_pagina_utilizador_v1(
                session=utilizador_subprocess_session_v1,
                user_edit_id=clean_user_edit_id,
                user_view=user_view,
                selected_entity_id=selected_entity_id,
                allowed_entity_ids=entity_permissions["allowed_entity_ids"],
                entity_rows=page_data.get("entities", []),
                profile_rows=page_data.get("profiles", []),
                success=success or "",
                error=error or "",
            )
    # APPVERBO_UTILIZADOR_SUBPROCESS_STATE_ISOLADO_V3_END





    context = {
        "admin_subprocess_state_utilizador_v1": admin_subprocess_state_utilizador_v1,
        "page_state": page_state,
        "page_state_refresh_home_url": page_state.get("refresh_home_url", "/users/new?menu=home"),
        "request": request,
        "errors": [error] if error else [],
        "success": success or "",
        "generated_invite_link": (invite_link or "").strip(),
        "form_data": get_form_defaults(),
        "entity_form_data": get_entity_form_defaults(),
        "entity_edit_data": entity_edit_data,
        "user_edit_data": user_edit_data,
        "entity_readonly_mode": bool(entity_readonly_mode),
        "user_readonly_mode": bool(user_readonly_mode),
        "current_user": current_user,
        "current_user_is_admin": current_user_is_admin,
        "user_personal_data": user_personal_data,
        "entity_success": entity_success or "",
        "entity_error": entity_error or "",
        "next_entity_internal_number": str(next_entity_internal_number),
        "profile_success": profile_success or "",
        "profile_error": profile_error or "",
        "settings_success": settings_success or "",
        "settings_error": settings_error or "",
        "settings_edit_data": settings_edit_data,
        "settings_edit_key": effective_settings_edit_key,
        "settings_action": effective_settings_action,
        "settings_tab": effective_settings_tab,
        "profile_tab": resolved_profile_tab,
        "initial_menu": resolved_menu,
        "initial_menu_target": initial_menu_target,
        "initial_dynamic_process_section": initial_dynamic_process_section,
        "initial_profile_section": clean_profile_section_from_query,
        "requested_profile_section": clean_profile_section_from_query,
        "requested_dynamic_process_section": clean_dynamic_section_from_query,
        "appverbo_after_save": is_post_save_return,
        "admin_process_only": bool(admin_process_only),
        "sidebar_section_edit_key": str(effective_sidebar_section_edit_key or "").strip().lower(),
        "sidebar_section_edit_data": sidebar_section_edit_data_v22,
        "active_sidebar_sections": active_sidebar_sections_v22,
        "inactive_sidebar_sections": inactive_sidebar_sections_v22,
        "sessions": list(sessoes_admin_page_payload.get("sessions", [])),
        "all_sessions": list(sessoes_admin_page_payload.get("all_sessions", [])),
        "active_sessions": list(sessoes_admin_page_payload.get("active_sessions", [])),
        "inactive_sessions": list(sessoes_admin_page_payload.get("inactive_sessions", [])),
        "pending_sessions": list(sessoes_admin_page_payload.get("pending_sessions", [])),
        "blocked_sessions": list(sessoes_admin_page_payload.get("blocked_sessions", [])),
        "session_edit_data": dict(sessoes_admin_page_payload.get("session_edit_data", {})),
        "session_permissions": dict(sessoes_admin_page_payload.get("session_permissions", {})),
        "session_list_pagination": dict(
            sessoes_admin_page_payload.get("session_list_pagination", {})
        ),
        "sidebar_sections_tab": str(
            sessoes_admin_page_payload.get("sidebar_sections_tab") or "sessoes"
        ),
        "admin_tab": resolved_admin_tab,
        "admin_tabs_width_ch": int(admin_tabs_width_ch_v1),
        "admin_tabs_text_size_px": int(admin_tabs_text_size_px_v1),
        "admin_tabs_font_family": str(admin_tabs_font_family_v1),
        "admin_tabs_color_hex": str(admin_tabs_color_hex_v1),
        "admin_tabs_text_color_hex": str(admin_tabs_text_color_hex_v1),
        "admin_process_title_font_size_px": int(admin_process_title_font_size_px_v1),
        "admin_process_title_font_family": str(admin_process_title_font_family_v1),
        "admin_process_title_color_hex": str(admin_process_title_color_hex_v1),
        "admin_card_item_font_size_px": int(admin_card_item_font_size_px_v1),
        "admin_card_item_font_family": str(admin_card_item_font_family_v1),
        "admin_card_item_color_hex": str(admin_card_item_color_hex_v1),
        "admin_card_item_font_weight": int(admin_card_item_font_weight_v1),
        "admin_card_table_head_color_hex": str(admin_card_table_head_color_hex_v1),
        "admin_topbar_color_hex": str(admin_topbar_color_hex_v1),
        "admin_sidebar_bg_color_hex": str(admin_sidebar_bg_color_hex_v1),
        "admin_sidebar_active_bg_color_hex": str(admin_sidebar_active_bg_color_hex_v1),
        "admin_sidebar_text_color_hex": str(admin_sidebar_text_color_hex_v1),
        "admin_sidebar_text_size_px": int(admin_sidebar_text_size_px_v1),
        "admin_sidebar_font_family": str(admin_sidebar_font_family_v1),
        "admin_sidebar_font_weight": int(admin_sidebar_font_weight_v1),
        "admin_sidebar_icon_color_hex": str(admin_sidebar_icon_color_hex_v1),
        "admin_sidebar_section_text_color_hex": str(admin_sidebar_section_text_color_hex_v1),
        "admin_subprocess_state": (
            admin_subprocess_state_utilizador_v1
            if resolved_admin_tab == "utilizador"
            else (
                admin_subprocess_state_definicoes_v1
                if resolved_admin_tab == "definicoes"
                else admin_subprocess_state_v2
            )
        ),
        "admin_subprocess_state_utilizador": admin_subprocess_state_utilizador_v1,
        "admin_subprocess_state_definicoes_v1": admin_subprocess_state_definicoes_v1,
        "admin_subprocess_state_definicoes": admin_subprocess_state_definicoes_v1,
        "admin_subprocess_shadow_state_v1": admin_subprocess_state_utilizador_v1,
        "admin_subprocess_shadow_state": admin_subprocess_shadow_state_v1,
        "admin_menu_state": admin_menu_state,
        "admin_menu_template_ready_v1": True,
        "admin_menu_template_mode": (str(request.query_params.get("admin_menu_template_mode") or "native").strip().lower() or "native"),
        "current_user_can_manage_all_entities": bool(entity_permissions["can_manage_all_entities"]),
        **page_data,
    }
    is_admin_menu_or_definicoes_tab_v1 = (
        is_admin_menu_tab
        or (resolved_menu in {"administrativo", "sessoes"} and resolved_admin_tab == "definicoes")
    )
    if is_admin_menu_or_definicoes_tab_v1:
        context["sidebar_menu_settings"] = list(
            menu_admin_page_payload.get("menu_settings", [])
        )
        context["sidebar_section_options"] = list(
            menu_admin_page_payload.get("sidebar_section_options", [])
        )
        context["menu_section_options"] = list(
            menu_admin_page_payload.get("menu_section_options", [])
        )
    else:
        context["sidebar_menu_settings"] = list(
            page_data.get("sidebar_menu_settings", [])
        )
        context["sidebar_section_options"] = list(
            page_data.get("sidebar_section_options", [])
        )
        context["menu_section_options"] = list(
            page_data.get("sidebar_section_options", [])
        )
    context["sidebar_menu_settings"] = _apply_sidebar_icon_keys_to_menu_settings_v1(
        rows=admin_definition_rows_v1,
        sidebar_menu_settings=list(context.get("sidebar_menu_settings", [])),
    )
    context["menu_permissions"] = dict(
        menu_admin_page_payload.get("menu_permissions", {})
    )
    context["menu_list_pagination"] = dict(
        menu_admin_page_payload.get("menu_list_pagination", {})
    )
    context["menu_edit_data"] = dict(
        menu_admin_page_payload.get("menu_edit_data", {})
    )
    _write_meu_perfil_page_flow_debug_log_v1(
        request,
        "04_users_new_render_context",
        {
            "resolved_menu": resolved_menu,
            "resolved_profile_tab": resolved_profile_tab,
            "resolved_admin_tab": resolved_admin_tab,
            "clean_target_from_query": clean_target_from_query,
            "clean_profile_section_from_query": clean_profile_section_from_query,
            "clean_dynamic_section_from_query": clean_dynamic_section_from_query,
            "initial_menu_target": initial_menu_target,
            "initial_dynamic_process_section": initial_dynamic_process_section,
            "is_post_save_return": is_post_save_return,
            "profile_success": profile_success or "",
            "profile_error": profile_error or "",
        },
    )
    return templates.TemplateResponse(request, "new_user.html", context)
