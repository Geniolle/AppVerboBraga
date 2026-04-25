from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

SIDEBAR_MENU_DEFAULTS: tuple[dict[str, Any], ...] = (
    {"key": "home", "label": "Home", "requires_admin": False},
    {"key": "administrativo", "label": "Administrativo", "requires_admin": True},
    {"key": "documentos", "label": "Meu perfil", "requires_admin": True},
    {"key": "funcionarios", "label": "Funcionarios", "requires_admin": True},
    {"key": "financeiro", "label": "Financeiro", "requires_admin": True},
    {"key": "relatorios", "label": "Relatorios", "requires_admin": True},
    {"key": "links", "label": "Links", "requires_admin": False},
    {"key": "contato", "label": "Contacto", "requires_admin": False},
    {"key": "tutorial", "label": "Tutorial", "requires_admin": False},
)

SIDEBAR_MENU_KEYS = {item["key"] for item in SIDEBAR_MENU_DEFAULTS}
SIDEBAR_MENU_PROTECTED_KEYS = {"home", "administrativo"}
SIDEBAR_MENU_DELETE_PROTECTED_KEYS = {"home", "administrativo", "configuracao"}
SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS = {"home"}
MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS = {"home"}
MENU_VISIBILITY_SCOPES = ("owner", "legado")
MENU_VISIBILITY_SCOPE_ALL = "all"
MENU_CONFIG_DISPLAY_ORDER_KEY = "display_order"
ADDITIONAL_FIELD_TEXTUAL_TYPES = {"text", "email", "phone", "number"}
ADDITIONAL_FIELD_TYPES: tuple[dict[str, str], ...] = (
    {"key": "text", "label": "Texto"},
    {"key": "number", "label": "Número"},
    {"key": "email", "label": "Email"},
    {"key": "phone", "label": "Telefone"},
    {"key": "date", "label": "Data"},
    {"key": "flag", "label": "Flag"},
    {"key": "header", "label": "Cabeçalho (aba)"},
)
ADDITIONAL_FIELD_TYPE_KEYS = {item["key"] for item in ADDITIONAL_FIELD_TYPES}
ADDITIONAL_FIELD_DEFAULT_TYPE = "text"
ADDITIONAL_FIELD_DEFAULT_SIZE = 30
ADDITIONAL_FIELD_MAX_SIZE = 255

MENU_PROCESS_FIELD_OPTIONS_BY_KEY: dict[str, tuple[dict[str, str], ...]] = {
    "home": (
        {"key": "resumo_geral", "label": "Resumo geral"},
        {"key": "indicadores", "label": "Indicadores"},
        {"key": "graficos", "label": "Gráficos"},
    ),
    "administrativo": (
        {"key": "entidade", "label": "Entidade"},
        {"key": "utilizador", "label": "Utilizador"},
        {"key": "definicoes", "label": "Definições"},
    ),
    "configuracao": (
        {"key": "geral", "label": "Geral"},
        {"key": "configuracao_campos", "label": "Configuração dos campos"},
        {"key": "campos_adicionais", "label": "Campos adicionais"},
    ),
    "documentos": (
        {"key": "nome", "label": "Nome"},
        {"key": "telefone", "label": "Telefone"},
        {"key": "email", "label": "Email"},
        {"key": "data_nascimento", "label": "Data de nascimento"},
        {"key": "whatsapp", "label": "WhatsApp"},
        {"key": "autorizacao_whatsapp", "label": "Autorização para avisos por WhatsApp"},
        {"key": "conta", "label": "Conta"},
        {"key": "estado_membro", "label": "Estado de membro"},
        {"key": "colaborador", "label": "Colaborador"},
        {"key": "entidades", "label": "Entidades"},
        {"key": "ultima_verificacao_whatsapp", "label": "Última verificação WhatsApp"},
        {"key": "detalhe_verificacao", "label": "Detalhe da verificação"},
    ),
    "funcionarios": (
        {"key": "nome", "label": "Nome"},
        {"key": "telefone", "label": "Telefone"},
        {"key": "email", "label": "Email"},
        {"key": "estado", "label": "Estado"},
    ),
    "financeiro": (
        {"key": "nome", "label": "Nome"},
        {"key": "estado", "label": "Estado"},
        {"key": "criado_em", "label": "Criado em"},
    ),
    "relatorios": (
        {"key": "nome", "label": "Nome"},
        {"key": "estado", "label": "Estado"},
        {"key": "criado_em", "label": "Criado em"},
    ),
    "links": (
        {"key": "sessao", "label": "Sessão"},
        {"key": "contactos", "label": "Contactos"},
    ),
    "contato": (
        {"key": "email", "label": "Email"},
        {"key": "telefone", "label": "Telefone"},
    ),
    "tutorial": (
        {"key": "passos", "label": "Passos"},
        {"key": "ajuda", "label": "Ajuda"},
    ),
}

MENU_PROCESS_DEFAULT_VISIBLE_FIELDS_BY_KEY: dict[str, list[str]] = {
    "home": ["resumo_geral", "indicadores", "graficos"],
    "administrativo": ["entidade", "utilizador", "definicoes"],
    "configuracao": ["geral", "configuracao_campos", "campos_adicionais"],
    "documentos": ["nome", "telefone", "email"],
    "funcionarios": ["nome", "telefone", "email"],
    "financeiro": ["nome", "estado", "criado_em"],
    "relatorios": ["nome", "estado", "criado_em"],
    "links": ["sessao", "contactos"],
    "contato": ["email", "telefone"],
    "tutorial": ["passos", "ajuda"],
}

MENU_DOCUMENTOS_FIELD_OPTIONS: tuple[dict[str, str], ...] = tuple(
    MENU_PROCESS_FIELD_OPTIONS_BY_KEY["documentos"]
)
MENU_DOCUMENTOS_FIELD_KEYS = tuple(item["key"] for item in MENU_DOCUMENTOS_FIELD_OPTIONS)
MENU_DOCUMENTOS_FIELD_LABELS = {
    item["key"]: item["label"] for item in MENU_DOCUMENTOS_FIELD_OPTIONS
}
MENU_DOCUMENTOS_FIELDS_DEFAULT = ["nome", "telefone", "email"]


def _sidebar_menu_defaults_by_key() -> dict[str, dict[str, Any]]:
    return {item["key"]: dict(item) for item in SIDEBAR_MENU_DEFAULTS}


def _normalize_menu_key(menu_key: Any) -> str:
    return str(menu_key or "").strip().lower()

def _is_menu_delete_protected(menu_key: Any, menu_label: Any = "") -> bool:
    clean_menu_key = _normalize_menu_key(menu_key)
    if clean_menu_key in SIDEBAR_MENU_DELETE_PROTECTED_KEYS:
        return True
    clean_menu_label = _normalize_sentence_case_text(menu_label)
    if clean_menu_label in {"Configuração", "Configuracao"}:
        return True
    return False

def _normalize_menu_display_order(raw_order: Any) -> int | None:
    try:
        parsed_order = int(str(raw_order).strip())
    except (TypeError, ValueError):
        return None
    if parsed_order < 0:
        return None
    return parsed_order

def _normalize_menu_visibility_scope_value(raw_scope: Any) -> str:
    clean_scope = str(raw_scope or "").strip().lower()
    if clean_scope in {"owner", "legado"}:
        return clean_scope
    return ""

def normalize_menu_visibility_scopes(raw_scopes: Any) -> list[str]:
    if isinstance(raw_scopes, str):
        clean_scope = _normalize_menu_visibility_scope_value(raw_scopes)
        return [clean_scope] if clean_scope else list(MENU_VISIBILITY_SCOPES)
    if isinstance(raw_scopes, (list, tuple, set)):
        normalized: list[str] = []
        seen: set[str] = set()
        for raw_scope in raw_scopes:
            clean_scope = _normalize_menu_visibility_scope_value(raw_scope)
            if not clean_scope or clean_scope in seen:
                continue
            seen.add(clean_scope)
            normalized.append(clean_scope)
        if normalized:
            return normalized
    return list(MENU_VISIBILITY_SCOPES)

def get_menu_visibility_scopes(menu_config: dict[str, Any] | None) -> list[str]:
    if not isinstance(menu_config, dict):
        return list(MENU_VISIBILITY_SCOPES)
    return normalize_menu_visibility_scopes(menu_config.get("visibility_scopes"))

def get_menu_visibility_scope_mode(menu_config: dict[str, Any] | None) -> str:
    scopes = get_menu_visibility_scopes(menu_config)
    if scopes == ["owner"]:
        return "owner"
    if scopes == ["legado"]:
        return "legado"
    return MENU_VISIBILITY_SCOPE_ALL

def get_menu_visibility_scope_label(menu_config: dict[str, Any] | None) -> str:
    mode = get_menu_visibility_scope_mode(menu_config)
    if mode == "owner":
        return "Owner"
    if mode == "legado":
        return "Legado"
    return "Owner e Legado"


def _menu_exists(session: Session, menu_key: str) -> bool:
    clean_menu_key = _normalize_menu_key(menu_key)
    if not clean_menu_key:
        return False
    return (
        session.execute(
            text(
                """
                SELECT 1
                FROM sidebar_menu_settings
                WHERE lower(trim(menu_key)) = :menu_key
                LIMIT 1
                """
            ),
            {"menu_key": clean_menu_key},
        ).scalar_one_or_none()
        is not None
    )


def _normalize_custom_field_key(raw_key: str) -> str:
    clean_value = str(raw_key or "").strip().lower()
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")
    if not clean_value:
        return ""
    if not clean_value.startswith("custom_"):
        clean_value = f"custom_{clean_value}"
    return clean_value


def _normalize_sentence_case_text(raw_text: Any) -> str:
    clean_text = _fix_common_mojibake(str(raw_text or ""))
    clean_text = " ".join(clean_text.strip().split())
    if not clean_text:
        return ""
    lowered_text = clean_text.lower()
    if len(lowered_text) == 1:
        return lowered_text.upper()
    return f"{lowered_text[0].upper()}{lowered_text[1:]}"


def _build_custom_field_key_from_label(label: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", label or "")
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        normalized = "campo"
    return f"custom_{normalized}"


def _build_menu_key_from_label(label: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", label or "")
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        return ""
    if normalized[0].isdigit():
        normalized = f"menu_{normalized}"
    return normalized


PT_PT_LABEL_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bACRONIMO\b", "ACRÓNIMO"),
    (r"\bCODIGO\b", "CÓDIGO"),
    (r"\bPAIS\b", "PAÍS"),
    (r"\bNUMERO\b", "NÚMERO"),
    (r"\bRESPONSAVEL\b", "RESPONSÁVEL"),
    (r"\bFREGESIA\b", "FREGUESIA"),
    (r"\bSOCIAS\b", "SOCIAIS"),
    (r"\bENDERECO\b", "ENDEREÇO"),
    (r"\bDESCRICAO\b", "DESCRIÇÃO"),
    (r"\bINFORMACOES\b", "INFORMAÇÕES"),
    (r"\bCONFIGURACOES\b", "CONFIGURAÇÕES"),
    (r"\bENTEDIDADE\b", "ENTIDADE"),
)

PT_PT_QUESTION_MARK_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bconfigura\?\?o\b", "configuração"),
    (r"\bconfigura\?\?es\b", "configurações"),
    (r"\bdefini\?\?es\b", "definições"),
    (r"\binforma\?\?es\b", "informações"),
    (r"\ba\?\?es\b", "ações"),
    (r"\bna\?o\b", "não"),
    (r"\bpa\?s\b", "país"),
)


def _fix_common_mojibake(raw_text: str) -> str:
    text_value = str(raw_text or "")
    if not text_value:
        return ""
    fixed_text = text_value
    if "Ã" in text_value or "Â" in text_value or "�" in text_value:
        try:
            repaired = text_value.encode("latin1").decode("utf-8")
            fixed_text = repaired or text_value
        except UnicodeError:
            fixed_text = text_value
    for pattern, replacement in PT_PT_QUESTION_MARK_REPLACEMENTS:
        fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)
    return fixed_text

def _normalize_system_menu_label(menu_key: Any, menu_label: Any) -> str:
    clean_menu_key = _normalize_menu_key(menu_key)
    clean_menu_label = _normalize_sentence_case_text(menu_label)
    if clean_menu_key == "configuracao":
        return "Configuração"
    return clean_menu_label


def _normalize_additional_field_label(raw_label: Any) -> str:
    clean_label = _fix_common_mojibake(str(raw_label or ""))
    clean_label = " ".join(clean_label.strip().split())
    if not clean_label:
        return ""
    clean_label = clean_label.upper()
    for pattern, replacement in PT_PT_LABEL_REPLACEMENTS:
        clean_label = re.sub(pattern, replacement, clean_label)
    return _normalize_sentence_case_text(clean_label)


def _normalize_additional_field_type(raw_type: Any) -> str:
    clean_value = str(raw_type or "").strip().lower()
    if clean_value in ADDITIONAL_FIELD_TYPE_KEYS:
        return clean_value
    return ADDITIONAL_FIELD_DEFAULT_TYPE


def _normalize_additional_field_size(raw_size: Any, field_type: str) -> int | None:
    if field_type not in ADDITIONAL_FIELD_TEXTUAL_TYPES:
        return None
    try:
        parsed_size = int(str(raw_size or "").strip())
    except (TypeError, ValueError):
        parsed_size = ADDITIONAL_FIELD_DEFAULT_SIZE
    parsed_size = max(1, min(parsed_size, ADDITIONAL_FIELD_MAX_SIZE))
    return parsed_size

def _normalize_additional_field_required(raw_required: Any) -> bool:
    if isinstance(raw_required, bool):
        return raw_required
    clean_value = str(raw_required or "").strip().lower()
    return clean_value in {"1", "true", "sim", "yes", "on"}


def normalize_menu_process_additional_fields(raw_fields: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_fields, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    seen_keys: set[str] = set()

    for raw_item in raw_fields:
        item_label = ""
        item_key = ""
        item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
        item_size: int | None = None
        item_is_required = False
        if isinstance(raw_item, dict):
            item_label = _normalize_additional_field_label(raw_item.get("label"))
            item_key = _normalize_custom_field_key(str(raw_item.get("key") or ""))
            item_type = _normalize_additional_field_type(
                raw_item.get("field_type", raw_item.get("type"))
            )
            item_size = _normalize_additional_field_size(
                raw_item.get("size", raw_item.get("max_length")),
                item_type,
            )
            item_is_required = _normalize_additional_field_required(
                raw_item.get("is_required", raw_item.get("required"))
            )
        else:
            item_label = _normalize_additional_field_label(raw_item)
            item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
            item_size = _normalize_additional_field_size(
                ADDITIONAL_FIELD_DEFAULT_SIZE,
                item_type,
            )
            item_is_required = False

        if not item_label:
            continue

        normalized_label_key = item_label.lower()
        if normalized_label_key in seen_labels:
            continue
        seen_labels.add(normalized_label_key)

        candidate_key = item_key or _build_custom_field_key_from_label(item_label)
        unique_key = candidate_key
        suffix_index = 2
        while unique_key in seen_keys:
            unique_key = f"{candidate_key}_{suffix_index}"
            suffix_index += 1
        seen_keys.add(unique_key)

        normalized_item: dict[str, Any] = {
            "key": unique_key,
            "label": item_label,
            "field_type": item_type,
            "is_required": bool(item_is_required and item_type != "header"),
        }
        if item_size is not None:
            normalized_item["size"] = item_size
        normalized.append(normalized_item)

    if not normalized:
        return normalized

    header_items = [
        dict(item)
        for item in normalized
        if str(item.get("field_type") or "").strip().lower() == "header"
    ]
    non_header_items = [
        dict(item)
        for item in normalized
        if str(item.get("field_type") or "").strip().lower() != "header"
    ]
    return header_items + non_header_items


def get_menu_process_additional_fields(menu_config: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(menu_config, dict):
        return []
    return normalize_menu_process_additional_fields(menu_config.get("additional_fields"))


def get_menu_process_field_options(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    clean_menu_key = (menu_key or "").strip().lower()
    raw_options = MENU_PROCESS_FIELD_OPTIONS_BY_KEY.get(clean_menu_key, tuple())
    additional_options = get_menu_process_additional_fields(menu_config)
    if clean_menu_key not in MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS and additional_options:
        return [dict(item) for item in additional_options]
    options = [dict(item) for item in raw_options]
    if additional_options:
        options.extend(additional_options)
    return options


def get_menu_process_field_types_map(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> dict[str, str]:
    types_map: dict[str, str] = {}
    for item in get_menu_process_field_options(menu_key, menu_config):
        clean_key = str(item.get("key") or "").strip().lower()
        if not clean_key:
            continue
        clean_type = str(item.get("field_type") or "").strip().lower()
        types_map[clean_key] = clean_type
    return types_map


def get_menu_process_header_options(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    types_map = get_menu_process_field_types_map(menu_key, menu_config)
    return [
        dict(item)
        for item in get_menu_process_field_options(menu_key, menu_config)
        if str(types_map.get(str(item.get("key") or "").strip().lower()) or "").strip().lower() == "header"
    ]


def get_menu_process_selectable_field_options(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    types_map = get_menu_process_field_types_map(menu_key, menu_config)
    return [
        dict(item)
        for item in get_menu_process_field_options(menu_key, menu_config)
        if str(types_map.get(str(item.get("key") or "").strip().lower()) or "").strip().lower() != "header"
    ]


def get_menu_process_default_visible_fields(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    clean_menu_key = (menu_key or "").strip().lower()
    options = get_menu_process_field_options(clean_menu_key, menu_config)
    available_option_keys = {
        str(item.get("key") or "").strip().lower()
        for item in options
        if str(item.get("key") or "").strip()
    }
    defaults = MENU_PROCESS_DEFAULT_VISIBLE_FIELDS_BY_KEY.get(clean_menu_key)
    if isinstance(defaults, list) and defaults:
        filtered_defaults = [
            str(field_key).strip().lower()
            for field_key in defaults
            if str(field_key).strip().lower() in available_option_keys
        ]
        if filtered_defaults:
            return filtered_defaults
    if not options:
        return []
    return [str(options[0].get("key") or "").strip().lower()]


def normalize_menu_process_visible_fields(
    menu_key: str,
    raw_fields: Any,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    clean_menu_key = (menu_key or "").strip().lower()
    allowed_field_keys = {
        str(item.get("key") or "").strip().lower()
        for item in get_menu_process_field_options(clean_menu_key, menu_config)
        if str(item.get("key") or "").strip()
    }
    if not allowed_field_keys:
        return []

    if not isinstance(raw_fields, (list, tuple, set)):
        return get_menu_process_default_visible_fields(clean_menu_key, menu_config)

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_field in raw_fields:
        clean_field = str(raw_field or "").strip().lower()
        if clean_field not in allowed_field_keys:
            continue
        if clean_field in seen:
            continue
        seen.add(clean_field)
        normalized.append(clean_field)

    if not normalized:
        return get_menu_process_default_visible_fields(clean_menu_key, menu_config)
    return normalized


def normalize_documentos_visible_fields(raw_fields: Any) -> list[str]:
    return normalize_menu_process_visible_fields("documentos", raw_fields)


def get_menu_process_visible_field_header_map(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> dict[str, str]:
    if not isinstance(menu_config, dict):
        return {}

    clean_menu_key = (menu_key or "").strip().lower()
    types_map = get_menu_process_field_types_map(clean_menu_key, menu_config)
    header_keys = {
        key for key, field_type in types_map.items() if field_type == "header"
    }
    selectable_field_keys = {
        key for key, field_type in types_map.items() if field_type != "header"
    }
    if not selectable_field_keys:
        return {}

    mapped: dict[str, str] = {}
    raw_map = menu_config.get("visible_field_headers")
    if isinstance(raw_map, dict):
        for raw_field_key, raw_header_key in raw_map.items():
            field_key = str(raw_field_key or "").strip().lower()
            header_key = str(raw_header_key or "").strip().lower()
            if field_key in selectable_field_keys and header_key in header_keys:
                mapped[field_key] = header_key

    visible_fields = normalize_menu_process_visible_fields(
        clean_menu_key,
        menu_config.get("visible_fields"),
        menu_config,
    )
    active_header = ""
    for raw_field in visible_fields:
        clean_field = str(raw_field or "").strip().lower()
        if clean_field in header_keys:
            active_header = clean_field
            continue
        if clean_field in selectable_field_keys and clean_field not in mapped and active_header:
            mapped[clean_field] = active_header

    return mapped


def get_menu_process_visible_field_rows(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    clean_menu_key = (menu_key or "").strip().lower()
    selectable_options = get_menu_process_selectable_field_options(clean_menu_key, menu_config)
    selectable_keys = {
        str(item.get("key") or "").strip().lower()
        for item in selectable_options
        if str(item.get("key") or "").strip()
    }
    if not selectable_keys:
        return []

    visible_fields = normalize_menu_process_visible_fields(
        clean_menu_key,
        None if not isinstance(menu_config, dict) else menu_config.get("visible_fields"),
        menu_config,
    )
    header_map = get_menu_process_visible_field_header_map(clean_menu_key, menu_config)

    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_field in visible_fields:
        clean_field = str(raw_field or "").strip().lower()
        if clean_field not in selectable_keys:
            continue
        if clean_field in seen:
            continue
        seen.add(clean_field)
        rows.append(
            {
                "field_key": clean_field,
                "header_key": str(header_map.get(clean_field) or "").strip().lower(),
            }
        )

    if rows:
        return rows

    defaults = get_menu_process_default_visible_fields(clean_menu_key, menu_config)
    default_rows = [
        {"field_key": field_key, "header_key": ""}
        for field_key in defaults
        if field_key in selectable_keys
    ]
    if default_rows:
        return default_rows

    first_option = selectable_options[0]
    return [{"field_key": str(first_option.get("key") or "").strip().lower(), "header_key": ""}]


def _parse_menu_config(raw_menu_config: Any) -> dict[str, Any]:
    if isinstance(raw_menu_config, dict):
        return dict(raw_menu_config)
    if isinstance(raw_menu_config, str):
        clean_value = raw_menu_config.strip()
        if clean_value:
            try:
                parsed_value = json.loads(clean_value)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed_value, dict):
                return parsed_value
    return {}


def ensure_sidebar_menu_settings_defaults(session: Session) -> None:
    existing_rows = session.execute(text("SELECT menu_key FROM sidebar_menu_settings")).all()
    existing_keys = {str(row.menu_key) for row in existing_rows}
    changed = False

    for item in SIDEBAR_MENU_DEFAULTS:
        menu_key = str(item["key"])
        if menu_key in existing_keys:
            continue
        session.execute(
            text(
                """
                INSERT INTO sidebar_menu_settings (menu_key, menu_label, is_active, is_deleted)
                VALUES (:menu_key, :menu_label, :is_active, :is_deleted)
                """
            ),
            {
                "menu_key": menu_key,
                "menu_label": str(item["label"]),
                "is_active": True,
                "is_deleted": False,
            },
        )
        changed = True

    documentos_label = session.execute(
        text(
            """
            SELECT menu_label
            FROM sidebar_menu_settings
            WHERE menu_key = 'documentos'
            LIMIT 1
            """
        )
    ).scalar_one_or_none()
    if isinstance(documentos_label, str) and documentos_label.strip() == "Documentos":
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_label = :menu_label
                WHERE menu_key = 'documentos'
                """
            ),
            {"menu_label": "Meu perfil"},
        )
        changed = True

    configuracao_label = session.execute(
        text(
            """
            SELECT menu_label
            FROM sidebar_menu_settings
            WHERE menu_key = 'configuracao'
            LIMIT 1
            """
        )
    ).scalar_one_or_none()
    if configuracao_label is not None and _normalize_system_menu_label("configuracao", configuracao_label) != str(configuracao_label):
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_label = :menu_label
                WHERE menu_key = 'configuracao'
                """
            ),
            {"menu_label": "Configuração"},
        )
        changed = True

    if changed:
        session.commit()


def get_sidebar_menu_settings(session: Session) -> list[dict[str, Any]]:
    ensure_sidebar_menu_settings_defaults(session)
    defaults_by_key = _sidebar_menu_defaults_by_key()
    rows = session.execute(
        text(
            """
            SELECT menu_key, menu_label, is_active, is_deleted, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()
    db_by_key = {
        _normalize_menu_key(row.menu_key): row
        for row in rows
        if _normalize_menu_key(row.menu_key)
    }

    settings: list[dict[str, Any]] = []
    for default_index, item in enumerate(SIDEBAR_MENU_DEFAULTS):
        menu_key = str(item["key"])
        row = db_by_key.get(menu_key)
        if row is None:
            menu_label = _normalize_system_menu_label(menu_key, item["label"])
            is_active = True
            is_deleted = False
        else:
            menu_label = _normalize_system_menu_label(
                menu_key,
                row.menu_label or item["label"],
            ) or _normalize_system_menu_label(menu_key, item["label"])
            is_active = bool(row.is_active)
            is_deleted = bool(row.is_deleted)

        menu_config = _parse_menu_config(None if row is None else row.menu_config)
        process_additional_fields = get_menu_process_additional_fields(menu_config)
        explicit_display_order = _normalize_menu_display_order(
            menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY)
        )
        effective_display_order = (
            explicit_display_order if explicit_display_order is not None else default_index
        )
        process_visible_fields = normalize_menu_process_visible_fields(
            menu_key,
            menu_config.get("visible_fields"),
            menu_config,
        )
        process_field_options = get_menu_process_field_options(menu_key, menu_config)
        process_selectable_field_options = get_menu_process_selectable_field_options(menu_key, menu_config)
        process_header_options = get_menu_process_header_options(menu_key, menu_config)
        process_visible_field_header_map = get_menu_process_visible_field_header_map(menu_key, menu_config)
        process_visible_field_rows = get_menu_process_visible_field_rows(menu_key, menu_config)

        settings.append(
            {
                "key": menu_key,
                "label": menu_label,
                "default_label": _normalize_system_menu_label(
                    menu_key,
                    defaults_by_key[menu_key]["label"],
                ),
                "requires_admin": bool(item["requires_admin"]),
                "is_active": bool(is_active),
                "is_deleted": bool(is_deleted),
                "can_delete": not _is_menu_delete_protected(menu_key, menu_label),
                "menu_config": menu_config,
                "visibility_scopes": get_menu_visibility_scopes(menu_config),
                "visibility_scope_mode": get_menu_visibility_scope_mode(menu_config),
                "visibility_scope_label": get_menu_visibility_scope_label(menu_config),
                "process_additional_fields": process_additional_fields,
                "process_visible_fields": process_visible_fields,
                "process_visible_field_header_map": process_visible_field_header_map,
                "process_visible_field_rows": process_visible_field_rows,
                "process_field_options": process_field_options,
                "process_selectable_field_options": process_selectable_field_options,
                "process_header_options": process_header_options,
                "additional_field_type_options": [dict(item) for item in ADDITIONAL_FIELD_TYPES],
                "_fallback_order": default_index,
                "_has_explicit_order": explicit_display_order is not None,
                "_effective_order": effective_display_order,
            }
        )

    extra_db_keys = sorted(
        key
        for key in db_by_key.keys()
        if key not in defaults_by_key
    )
    for extra_index, menu_key in enumerate(extra_db_keys):
        row = db_by_key.get(menu_key)
        if row is None:
            continue

        menu_label = _normalize_system_menu_label(menu_key, row.menu_label or menu_key) or menu_key
        is_active = bool(row.is_active)
        is_deleted = bool(row.is_deleted)
        menu_config = _parse_menu_config(row.menu_config)
        requires_admin = bool(menu_config.get("requires_admin", True))
        process_additional_fields = get_menu_process_additional_fields(menu_config)
        fallback_order = len(SIDEBAR_MENU_DEFAULTS) + extra_index
        explicit_display_order = _normalize_menu_display_order(
            menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY)
        )
        effective_display_order = (
            explicit_display_order if explicit_display_order is not None else fallback_order
        )
        process_visible_fields = normalize_menu_process_visible_fields(
            menu_key,
            menu_config.get("visible_fields"),
            menu_config,
        )
        process_field_options = get_menu_process_field_options(menu_key, menu_config)
        process_selectable_field_options = get_menu_process_selectable_field_options(menu_key, menu_config)
        process_header_options = get_menu_process_header_options(menu_key, menu_config)
        process_visible_field_header_map = get_menu_process_visible_field_header_map(menu_key, menu_config)
        process_visible_field_rows = get_menu_process_visible_field_rows(menu_key, menu_config)

        settings.append(
            {
                "key": menu_key,
                "label": menu_label,
                "default_label": menu_label,
                "requires_admin": requires_admin,
                "is_active": is_active,
                "is_deleted": is_deleted,
                "can_delete": not _is_menu_delete_protected(menu_key, menu_label),
                "menu_config": menu_config,
                "visibility_scopes": get_menu_visibility_scopes(menu_config),
                "visibility_scope_mode": get_menu_visibility_scope_mode(menu_config),
                "visibility_scope_label": get_menu_visibility_scope_label(menu_config),
                "process_additional_fields": process_additional_fields,
                "process_visible_fields": process_visible_fields,
                "process_visible_field_header_map": process_visible_field_header_map,
                "process_visible_field_rows": process_visible_field_rows,
                "process_field_options": process_field_options,
                "process_selectable_field_options": process_selectable_field_options,
                "process_header_options": process_header_options,
                "additional_field_type_options": [dict(item) for item in ADDITIONAL_FIELD_TYPES],
                "_fallback_order": fallback_order,
                "_has_explicit_order": explicit_display_order is not None,
                "_effective_order": effective_display_order,
            }
        )

    settings.sort(
        key=lambda item: (
            int(item.get("_effective_order", 0)),
            0 if bool(item.get("_has_explicit_order")) else 1,
            int(item.get("_fallback_order", 0)),
            str(item.get("label") or "").lower(),
        )
    )
    total_settings = len(settings)
    for order_index, setting_row in enumerate(settings):
        setting_row["order_index"] = order_index
        setting_row["can_move_up"] = order_index > 0
        setting_row["can_move_down"] = order_index < (total_settings - 1)
        setting_row["display_order"] = int(setting_row.get("_effective_order", order_index))
        setting_row.pop("_fallback_order", None)
        setting_row.pop("_has_explicit_order", None)
        setting_row.pop("_effective_order", None)

    return settings

def _persist_sidebar_menu_display_order(
    session: Session,
    ordered_menu_keys: list[str],
) -> None:
    changed = False
    for order_index, raw_menu_key in enumerate(ordered_menu_keys):
        clean_menu_key = _normalize_menu_key(raw_menu_key)
        if not clean_menu_key:
            continue
        menu_config = _load_menu_config(session, clean_menu_key)
        current_order = _normalize_menu_display_order(menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY))
        if current_order == order_index:
            continue
        menu_config[MENU_CONFIG_DISPLAY_ORDER_KEY] = order_index
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": clean_menu_key,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            },
        )
        changed = True
    if changed:
        session.commit()

def move_sidebar_menu_setting(
    session: Session,
    menu_key: str,
    direction: str,
) -> tuple[bool, str]:
    clean_menu_key = _normalize_menu_key(menu_key)
    clean_direction = str(direction or "").strip().lower()
    if clean_direction not in {"up", "down"}:
        return False, "Direção inválida."

    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."

    settings = get_sidebar_menu_settings(session)
    ordered_menu_keys = [str(item.get("key") or "").strip().lower() for item in settings if str(item.get("key") or "").strip()]
    try:
        current_index = ordered_menu_keys.index(clean_menu_key)
    except ValueError:
        return False, "Menu inválido."

    if clean_direction == "up":
        if current_index <= 0:
            return False, "Esta pasta já está no topo."
        target_index = current_index - 1
    else:
        if current_index >= (len(ordered_menu_keys) - 1):
            return False, "Esta pasta já está no fim."
        target_index = current_index + 1

    ordered_menu_keys[current_index], ordered_menu_keys[target_index] = (
        ordered_menu_keys[target_index],
        ordered_menu_keys[current_index],
    )
    _persist_sidebar_menu_display_order(session, ordered_menu_keys)
    return True, ""


def get_visible_sidebar_menu_keys(
    settings: list[dict[str, Any]],
    current_user_is_admin: bool,
    current_entity_scope: str | None = None,
) -> set[str]:
    clean_entity_scope = _normalize_menu_visibility_scope_value(current_entity_scope)
    visible_keys: set[str] = set()
    for item in settings:
        if item.get("requires_admin") and not current_user_is_admin:
            continue
        if not item.get("is_active") or item.get("is_deleted"):
            continue
        visibility_scopes = normalize_menu_visibility_scopes(item.get("visibility_scopes"))
        if clean_entity_scope and clean_entity_scope not in visibility_scopes:
            continue
        visible_keys.add(str(item["key"]))
    if "home" not in visible_keys:
        visible_keys.add("home")
    return visible_keys


def _load_menu_config(session: Session, menu_key: str) -> dict[str, Any]:
    raw_menu_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": menu_key},
    ).scalar_one_or_none()
    return _parse_menu_config(raw_menu_config)


def set_sidebar_menu_visibility(session: Session, menu_key: str, make_visible: bool) -> tuple[bool, str]:
    clean_menu_key = _normalize_menu_key(menu_key)
    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."
    if clean_menu_key in SIDEBAR_MENU_PROTECTED_KEYS and not make_visible:
        return False, "Não é permitido ocultar este menu."

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET is_active = :is_active,
                is_deleted = :is_deleted
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "is_active": bool(make_visible),
            "is_deleted": False,
        },
    )
    session.commit()
    return True, ""


def update_sidebar_menu_label(
    session: Session,
    menu_key: str,
    menu_label: str,
    visibility_scope_mode: str | None = None,
) -> tuple[bool, str]:
    clean_menu_key = _normalize_menu_key(menu_key)
    clean_menu_label = _normalize_sentence_case_text(menu_label)
    if clean_menu_key == "configuracao":
        clean_menu_label = "Configuração"
    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."
    if not clean_menu_label:
        return False, "Nome do menu é obrigatório."

    menu_config = _load_menu_config(session, clean_menu_key)
    clean_scope_mode = str(visibility_scope_mode or "").strip().lower()
    if clean_scope_mode:
        if clean_scope_mode == MENU_VISIBILITY_SCOPE_ALL:
            normalized_visibility_scopes = list(MENU_VISIBILITY_SCOPES)
        elif clean_scope_mode in MENU_VISIBILITY_SCOPES:
            normalized_visibility_scopes = [clean_scope_mode]
        else:
            return False, "Escopo de exibição inválido."
        menu_config["visibility_scopes"] = normalized_visibility_scopes
    else:
        menu_config["visibility_scopes"] = get_menu_visibility_scopes(menu_config)

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_label = :menu_label,
                menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_label": clean_menu_label,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()
    return True, ""


def update_sidebar_menu_process_fields(
    session: Session,
    menu_key: str,
    visible_fields: list[str] | tuple[str, ...] | set[str],
    visible_headers: list[str] | tuple[str, ...] | set[str] | None = None,
) -> tuple[bool, str]:
    clean_menu_key = _normalize_menu_key(menu_key)
    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."

    menu_config = _load_menu_config(session, clean_menu_key)
    if not get_menu_process_field_options(clean_menu_key, menu_config):
        return False, "Este processo não possui campos configuráveis."

    types_map = get_menu_process_field_types_map(clean_menu_key, menu_config)
    selectable_keys = {
        key for key, field_type in types_map.items() if field_type != "header"
    }
    header_keys = {
        key for key, field_type in types_map.items() if field_type == "header"
    }
    if not selectable_keys:
        if not header_keys:
            return False, "Este processo não possui campos configuráveis."

        requested_header_keys: list[str] = []
        requested_seen: set[str] = set()
        for raw_field in list(visible_fields or []):
            clean_field = str(raw_field or "").strip().lower()
            if clean_field not in header_keys:
                continue
            if clean_field in requested_seen:
                continue
            requested_seen.add(clean_field)
            requested_header_keys.append(clean_field)

        ordered_header_keys = [
            str(item.get("key") or "").strip().lower()
            for item in get_menu_process_field_options(clean_menu_key, menu_config)
            if str(item.get("key") or "").strip().lower() in header_keys
        ]
        if not ordered_header_keys:
            ordered_header_keys = sorted(header_keys)
        if requested_header_keys:
            ordered_header_keys = requested_header_keys

        menu_config["visible_fields"] = ordered_header_keys
        menu_config["visible_field_headers"] = {}

        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": clean_menu_key,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            },
        )
        session.commit()
        return True, ""

    raw_visible_fields = list(visible_fields or [])
    raw_visible_headers = list(visible_headers or [])
    rows_count = max(len(raw_visible_fields), len(raw_visible_headers))

    normalized_rows: list[dict[str, str]] = []
    seen_field_keys: set[str] = set()
    for row_index in range(rows_count):
        field_key = (
            str(raw_visible_fields[row_index] if row_index < len(raw_visible_fields) else "")
            .strip()
            .lower()
        )
        header_key = (
            str(raw_visible_headers[row_index] if row_index < len(raw_visible_headers) else "")
            .strip()
            .lower()
        )
        if field_key not in selectable_keys:
            continue
        if field_key in seen_field_keys:
            continue
        seen_field_keys.add(field_key)
        normalized_rows.append(
            {
                "field_key": field_key,
                "header_key": header_key if header_key in header_keys else "",
            }
        )

    if not normalized_rows:
        defaults = get_menu_process_default_visible_fields(clean_menu_key, menu_config)
        for field_key in defaults:
            if field_key not in selectable_keys:
                continue
            if field_key in seen_field_keys:
                continue
            seen_field_keys.add(field_key)
            normalized_rows.append({"field_key": field_key, "header_key": ""})
    if not normalized_rows:
        first_field_key = next(iter(selectable_keys))
        normalized_rows.append({"field_key": first_field_key, "header_key": ""})

    final_visible_fields: list[str] = []
    emitted_keys: set[str] = set()
    active_header_key = ""
    for row in normalized_rows:
        field_key = row["field_key"]
        header_key = row["header_key"]
        if header_key and header_key != active_header_key:
            final_visible_fields.append(header_key)
            emitted_keys.add(header_key)
            active_header_key = header_key
        if not header_key:
            active_header_key = ""
        if field_key in emitted_keys:
            continue
        final_visible_fields.append(field_key)
        emitted_keys.add(field_key)

    menu_config["visible_fields"] = final_visible_fields
    menu_config["visible_field_headers"] = {
        row["field_key"]: row["header_key"]
        for row in normalized_rows
        if row.get("header_key")
    }

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()
    return True, ""


def update_sidebar_menu_additional_fields(
    session: Session,
    menu_key: str,
    additional_fields: list[dict[str, Any]] | tuple[dict[str, Any], ...] | set[Any] | list[str] | tuple[str, ...],
) -> tuple[bool, str]:
    clean_menu_key = _normalize_menu_key(menu_key)
    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."
    if clean_menu_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return False, "Não é permitido editar campos adicionais deste menu."

    menu_config = _load_menu_config(session, clean_menu_key)
    normalized_additional_fields = normalize_menu_process_additional_fields(
        additional_fields
    )
    menu_config["additional_fields"] = normalized_additional_fields
    visible_fields = normalize_menu_process_visible_fields(
        clean_menu_key,
        menu_config.get("visible_fields"),
        menu_config,
    )
    additional_keys = [
        str(item.get("key") or "").strip().lower()
        for item in normalized_additional_fields
        if str(item.get("key") or "").strip()
    ]
    for additional_key in additional_keys:
        if additional_key not in visible_fields:
            visible_fields.append(additional_key)
    additional_header_keys = [
        str(item.get("key") or "").strip().lower()
        for item in normalized_additional_fields
        if str(item.get("field_type") or "").strip().lower() == "header"
        and str(item.get("key") or "").strip()
    ]
    if additional_header_keys:
        additional_header_key_set = set(additional_header_keys)
        prioritized_header_keys = [
            header_key for header_key in additional_header_keys if header_key in visible_fields
        ]
        remaining_visible_fields = [
            visible_key for visible_key in visible_fields if visible_key not in additional_header_key_set
        ]
        visible_fields = prioritized_header_keys + remaining_visible_fields
    menu_config["visible_fields"] = visible_fields
    visible_field_headers = menu_config.get("visible_field_headers")
    if isinstance(visible_field_headers, dict):
        additional_type_map = {
            str(item.get("key") or "").strip().lower(): str(item.get("field_type") or "").strip().lower()
            for item in normalized_additional_fields
            if str(item.get("key") or "").strip()
        }
        allowed_field_keys = {
            key for key, field_type in additional_type_map.items() if field_type != "header"
        }
        allowed_header_keys = {
            key for key, field_type in additional_type_map.items() if field_type == "header"
        }
        cleaned_map: dict[str, str] = {}
        for raw_field_key, raw_header_key in visible_field_headers.items():
            field_key = str(raw_field_key or "").strip().lower()
            header_key = str(raw_header_key or "").strip().lower()
            if field_key not in allowed_field_keys:
                continue
            if header_key not in allowed_header_keys:
                continue
            cleaned_map[field_key] = header_key
        menu_config["visible_field_headers"] = cleaned_map

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()
    return True, ""


def create_sidebar_menu_setting(
    session: Session,
    menu_label: str,
    visibility_scope_mode: str | None = None,
) -> tuple[bool, str, str]:
    clean_menu_label = _normalize_sentence_case_text(menu_label)
    if not clean_menu_label:
        return False, "Nome da pasta é obrigatório.", ""

    clean_menu_key = _build_menu_key_from_label(clean_menu_label)
    if not clean_menu_key:
        return False, "Nome da pasta inválido.", ""
    clean_menu_label = _normalize_system_menu_label(clean_menu_key, clean_menu_label)

    ensure_sidebar_menu_settings_defaults(session)

    existing_key = session.execute(
        text(
            """
            SELECT 1
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": clean_menu_key},
    ).scalar_one_or_none()
    if existing_key is not None:
        return False, "Já existe uma pasta com este nome.", ""

    existing_label = session.execute(
        text(
            """
            SELECT 1
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_label)) = :menu_label
            LIMIT 1
            """
        ),
        {"menu_label": clean_menu_label.lower()},
    ).scalar_one_or_none()
    if existing_label is not None:
        return False, "Já existe uma pasta com este nome.", ""

    clean_scope_mode = str(visibility_scope_mode or "").strip().lower()
    if clean_scope_mode == MENU_VISIBILITY_SCOPE_ALL or not clean_scope_mode:
        visibility_scopes = list(MENU_VISIBILITY_SCOPES)
    elif clean_scope_mode in MENU_VISIBILITY_SCOPES:
        visibility_scopes = [clean_scope_mode]
    else:
        return False, "Escopo de exibição inválido.", ""

    next_display_order = len(get_sidebar_menu_settings(session))
    menu_config = {
        "requires_admin": True,
        "visibility_scopes": visibility_scopes,
        "additional_fields": [],
        "visible_fields": [],
        "visible_field_headers": {},
        MENU_CONFIG_DISPLAY_ORDER_KEY: next_display_order,
    }

    session.execute(
        text(
            """
            INSERT INTO sidebar_menu_settings (menu_key, menu_label, is_active, is_deleted, menu_config)
            VALUES (:menu_key, :menu_label, TRUE, FALSE, :menu_config)
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_label": clean_menu_label,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()
    return True, "", clean_menu_key


def delete_sidebar_menu_setting(session: Session, menu_key: str) -> tuple[bool, str]:
    clean_menu_key = _normalize_menu_key(menu_key)
    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."

    existing_label = session.execute(
        text(
            """
            SELECT menu_label
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": clean_menu_key},
    ).scalar_one_or_none()

    if _is_menu_delete_protected(clean_menu_key, existing_label):
        return False, "Não é permitido excluir este menu."

    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET is_active = FALSE,
                is_deleted = TRUE
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {"menu_key": clean_menu_key},
    )
    session.commit()
    return True, ""
