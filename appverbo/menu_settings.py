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


def _normalize_custom_field_key(raw_key: str) -> str:
    clean_value = str(raw_key or "").strip().lower()
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")
    if not clean_value:
        return ""
    if not clean_value.startswith("custom_"):
        clean_value = f"custom_{clean_value}"
    return clean_value


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


def _fix_common_mojibake(raw_text: str) -> str:
    text_value = str(raw_text or "")
    if not text_value:
        return ""
    if "Ã" not in text_value and "Â" not in text_value and "�" not in text_value:
        return text_value
    try:
        repaired = text_value.encode("latin1").decode("utf-8")
    except UnicodeError:
        return text_value
    return repaired or text_value


def _normalize_additional_field_label(raw_label: Any) -> str:
    clean_label = _fix_common_mojibake(str(raw_label or ""))
    clean_label = " ".join(clean_label.strip().split())
    if not clean_label:
        return ""
    clean_label = clean_label.upper()
    for pattern, replacement in PT_PT_LABEL_REPLACEMENTS:
        clean_label = re.sub(pattern, replacement, clean_label)
    return clean_label


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
        else:
            item_label = _normalize_additional_field_label(raw_item)
            item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
            item_size = _normalize_additional_field_size(
                ADDITIONAL_FIELD_DEFAULT_SIZE,
                item_type,
            )

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
        }
        if item_size is not None:
            normalized_item["size"] = item_size
        normalized.append(normalized_item)

    return normalized


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
    if clean_menu_key not in SIDEBAR_MENU_PROTECTED_KEYS and additional_options:
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
    db_by_key = {str(row.menu_key): row for row in rows}

    settings: list[dict[str, Any]] = []
    for item in SIDEBAR_MENU_DEFAULTS:
        menu_key = str(item["key"])
        row = db_by_key.get(menu_key)
        if row is None:
            menu_label = str(item["label"])
            is_active = True
            is_deleted = False
        else:
            menu_label = str(row.menu_label or item["label"]).strip() or str(item["label"])
            is_active = bool(row.is_active)
            is_deleted = bool(row.is_deleted)

        menu_config = _parse_menu_config(None if row is None else row.menu_config)
        process_additional_fields = get_menu_process_additional_fields(menu_config)
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
                "default_label": str(defaults_by_key[menu_key]["label"]),
                "requires_admin": bool(item["requires_admin"]),
                "is_active": bool(is_active),
                "is_deleted": bool(is_deleted),
                "can_delete": menu_key not in SIDEBAR_MENU_PROTECTED_KEYS,
                "menu_config": menu_config,
                "process_additional_fields": process_additional_fields,
                "process_visible_fields": process_visible_fields,
                "process_visible_field_header_map": process_visible_field_header_map,
                "process_visible_field_rows": process_visible_field_rows,
                "process_field_options": process_field_options,
                "process_selectable_field_options": process_selectable_field_options,
                "process_header_options": process_header_options,
                "additional_field_type_options": [dict(item) for item in ADDITIONAL_FIELD_TYPES],
            }
        )

    return settings


def get_visible_sidebar_menu_keys(
    settings: list[dict[str, Any]],
    current_user_is_admin: bool,
) -> set[str]:
    visible_keys: set[str] = set()
    for item in settings:
        if item.get("requires_admin") and not current_user_is_admin:
            continue
        if not item.get("is_active") or item.get("is_deleted"):
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
            WHERE menu_key = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": menu_key},
    ).scalar_one_or_none()
    return _parse_menu_config(raw_menu_config)


def set_sidebar_menu_visibility(session: Session, menu_key: str, make_visible: bool) -> tuple[bool, str]:
    clean_menu_key = (menu_key or "").strip().lower()
    if clean_menu_key not in SIDEBAR_MENU_KEYS:
        return False, "Menu inválido."
    if clean_menu_key in SIDEBAR_MENU_PROTECTED_KEYS and not make_visible:
        return False, "Não é permitido ocultar este menu."

    ensure_sidebar_menu_settings_defaults(session)
    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET is_active = :is_active,
                is_deleted = :is_deleted
            WHERE menu_key = :menu_key
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


def update_sidebar_menu_label(session: Session, menu_key: str, menu_label: str) -> tuple[bool, str]:
    clean_menu_key = (menu_key or "").strip().lower()
    clean_menu_label = " ".join((menu_label or "").strip().split())
    if clean_menu_key not in SIDEBAR_MENU_KEYS:
        return False, "Menu inválido."
    if not clean_menu_label:
        return False, "Nome do menu é obrigatório."

    ensure_sidebar_menu_settings_defaults(session)
    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_label = :menu_label
            WHERE menu_key = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_label": clean_menu_label,
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
    clean_menu_key = (menu_key or "").strip().lower()
    if clean_menu_key not in SIDEBAR_MENU_KEYS:
        return False, "Menu inválido."

    ensure_sidebar_menu_settings_defaults(session)
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
        return False, "Este processo não possui campos configuráveis."

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
            WHERE menu_key = :menu_key
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
    clean_menu_key = (menu_key or "").strip().lower()
    if clean_menu_key not in SIDEBAR_MENU_KEYS:
        return False, "Menu inválido."
    if clean_menu_key in SIDEBAR_MENU_PROTECTED_KEYS:
        return False, "Não é permitido editar campos adicionais deste menu."

    ensure_sidebar_menu_settings_defaults(session)
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
            WHERE menu_key = :menu_key
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()
    return True, ""


def delete_sidebar_menu_setting(session: Session, menu_key: str) -> tuple[bool, str]:
    clean_menu_key = (menu_key or "").strip().lower()
    if clean_menu_key not in SIDEBAR_MENU_KEYS:
        return False, "Menu inválido."
    if clean_menu_key in SIDEBAR_MENU_PROTECTED_KEYS:
        return False, "Não é permitido excluir este menu."

    ensure_sidebar_menu_settings_defaults(session)
    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET is_active = FALSE,
                is_deleted = TRUE
            WHERE menu_key = :menu_key
            """
        ),
        {"menu_key": clean_menu_key},
    )
    session.commit()
    return True, ""
