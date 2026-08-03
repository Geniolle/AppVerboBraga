from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from appgenesis.admin_subprocesses.registry import get_admin_subprocess_config

MENU_MEU_PERFIL_KEY = "meu_perfil"
MENU_MEU_PERFIL_LEGACY_KEY = "documentos"

SIDEBAR_MENU_DEFAULTS: tuple[dict[str, Any], ...] = (
    {"key": "home", "label": "Home", "requires_admin": False},
    {"key": "administrativo", "label": "Administrativo", "requires_admin": True},
    {"key": "empresa", "label": "Empresa", "requires_admin": True},
    {"key": MENU_MEU_PERFIL_KEY, "label": "Meus dados", "requires_admin": True},
    {"key": "funcionarios", "label": "Funcionarios", "requires_admin": True},
    {"key": "financeiro", "label": "Financeiro", "requires_admin": True},
    {"key": "relatorios", "label": "Relatorios", "requires_admin": True},
    {"key": "links", "label": "Links", "requires_admin": False},
    {"key": "contato", "label": "Contacto", "requires_admin": False},
    {"key": "tutorial", "label": "Tutorial", "requires_admin": False},
)

SIDEBAR_MENU_KEYS = {item["key"] for item in SIDEBAR_MENU_DEFAULTS}
SIDEBAR_MENU_PROTECTED_KEYS = {"home", "administrativo"}
SIDEBAR_MENU_DELETE_PROTECTED_KEYS = {"home", "administrativo"}
SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS = {"home"}
MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS = {"home"}
MENU_VISIBILITY_SCOPES = ("owner", "legado")
MENU_VISIBILITY_SCOPE_ALL = "all"
MENU_CONFIG_DISPLAY_ORDER_KEY = "display_order"
MENU_SECTION_DEFAULT_KEY = "igreja"
MENU_SECTION_OPTIONS: tuple[dict[str, str], ...] = (
    {"key": "sistema", "label": "Sistema"},
    {"key": "geral", "label": "Geral"},
    {"key": "dados_gerais", "label": "Dados gerais"},
    {"key": "igreja", "label": "Igreja"},
    {"key": "tesouraria", "label": "Tesouraria"},
)
MENU_SECTION_LABELS = {item["key"]: item["label"] for item in MENU_SECTION_OPTIONS}
MENU_SECTION_BY_SYSTEM_MENU_KEY = {
    "administrativo": "sistema",
    "perfil_de_autorizacao": "sistema",
    "empresa": "dados_gerais",
    "home": "geral",
    MENU_MEU_PERFIL_KEY: "igreja",
    "funcionarios": "igreja",
    "financeiro": "igreja",
    "relatorios": "igreja",
    "links": "igreja",
    "contato": "igreja",
    "tutorial": "igreja",
    "tesouraria": "tesouraria",
}
MENU_CONFIG_SIDEBAR_SECTION_KEY = "sidebar_section"
MENU_CONFIG_SIDEBAR_SECTIONS_KEY = "sidebar_sections"
MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY = "sidebar_global_refresh_version"
MENU_LEGACY_KEY_ALIAS = {
    "configuracao": "administrativo",
    "estruturas": "sessoes",
    MENU_MEU_PERFIL_LEGACY_KEY: MENU_MEU_PERFIL_KEY,
}
SIDEBAR_SECTION_DEFAULTS: tuple[dict[str, Any], ...] = (
    {"key": "sistema", "label": "Sistema", "visibility_scopes": ["owner", "legado"]},
    {"key": "geral", "label": "Geral", "visibility_scopes": ["owner", "legado"]},
    {
        "key": "dados_gerais",
        "label": "Dados gerais",
        "visibility_scopes": ["owner", "legado"],
    },
    {"key": "igreja", "label": "Igreja", "visibility_scopes": ["owner", "legado"]},
    {
        "key": "tesouraria",
        "label": "Tesouraria",
        "visibility_scopes": ["owner", "legado"],
    },
)
SIDEBAR_SECTION_DEFAULTS_BY_KEY = {
    str(item["key"]).strip().lower(): str(item["label"])
    for item in SIDEBAR_SECTION_DEFAULTS
}
SIDEBAR_SECTION_DELETE_PROTECTED_KEYS = frozenset(
    SIDEBAR_SECTION_DEFAULTS_BY_KEY.keys()
)
ADDITIONAL_FIELD_TEXTUAL_TYPES = {"text", "email", "phone", "number"}
ADDITIONAL_FIELD_TYPES: tuple[dict[str, str], ...] = (
    {"key": "text", "label": "Texto"},
    {"key": "number", "label": "Número"},
    {"key": "email", "label": "Email"},
    {"key": "phone", "label": "Telefone"},
    {"key": "date", "label": "Data"},
    {"key": "time", "label": "Horário"},
    {"key": "flag", "label": "Flag"},
    {"key": "header", "label": "Cabeçalho (aba)"},
    {"key": "list", "label": "Lista"},
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
    "empresa": (
        {"key": "dados_gerais", "label": "Dados gerais"},
        {"key": "morada", "label": "Morada"},
    ),
    MENU_MEU_PERFIL_KEY: (
        {"key": "nome", "label": "Nome"},
        {"key": "telefone", "label": "Telefone"},
        {"key": "email", "label": "Email"},
        {"key": "data_nascimento", "label": "Data de nascimento"},
        {"key": "whatsapp", "label": "WhatsApp"},
        {
            "key": "autorizacao_whatsapp",
            "label": "Autorização para avisos por WhatsApp",
        },
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
    "empresa": ["dados_gerais", "morada"],
    MENU_MEU_PERFIL_KEY: ["nome", "telefone", "email"],
    "funcionarios": ["nome", "telefone", "email"],
    "financeiro": ["nome", "estado", "criado_em"],
    "relatorios": ["nome", "estado", "criado_em"],
    "links": ["sessao", "contactos"],
    "contato": ["email", "telefone"],
    "tutorial": ["passos", "ajuda"],
}

MENU_MEU_PERFIL_FIELD_OPTIONS: tuple[dict[str, str], ...] = tuple(
    MENU_PROCESS_FIELD_OPTIONS_BY_KEY[MENU_MEU_PERFIL_KEY]
)
MENU_MEU_PERFIL_FIELD_KEYS = tuple(
    item["key"] for item in MENU_MEU_PERFIL_FIELD_OPTIONS
)
MENU_MEU_PERFIL_FIELD_LABELS = {
    item["key"]: item["label"] for item in MENU_MEU_PERFIL_FIELD_OPTIONS
}
MENU_MEU_PERFIL_FIELDS_DEFAULT = ["nome", "telefone", "pais", "email"]


def _sidebar_menu_defaults_by_key() -> dict[str, dict[str, Any]]:
    return {item["key"]: dict(item) for item in SIDEBAR_MENU_DEFAULTS}


def _normalize_menu_key(menu_key: Any) -> str:
    return str(menu_key or "").strip().lower()


def _resolve_legacy_menu_alias(menu_key: Any) -> str:
    clean_menu_key = _normalize_menu_key(menu_key)
    return MENU_LEGACY_KEY_ALIAS.get(clean_menu_key, clean_menu_key)


def resolve_menu_key_alias(menu_key: Any) -> str:
    return _resolve_legacy_menu_alias(menu_key)


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


def _normalize_visibility_scope_mode(raw_mode: Any) -> str:
    clean_mode = str(raw_mode or "").strip().lower()
    if clean_mode in MENU_VISIBILITY_SCOPES:
        return clean_mode
    return MENU_VISIBILITY_SCOPE_ALL


def _visibility_scope_mode_to_scopes(scope_mode: Any) -> list[str]:
    clean_mode = _normalize_visibility_scope_mode(scope_mode)
    if clean_mode in MENU_VISIBILITY_SCOPES:
        return [clean_mode]
    return list(MENU_VISIBILITY_SCOPES)


def _resolve_visibility_scope_mode_from_scopes(scopes: list[str]) -> str:
    if scopes == ["owner"]:
        return "owner"
    if scopes == ["legado"]:
        return "legado"
    return MENU_VISIBILITY_SCOPE_ALL


def _resolve_visibility_scope_label_from_mode(scope_mode: Any) -> str:
    clean_mode = _normalize_visibility_scope_mode(scope_mode)
    if clean_mode == "owner":
        return "Owner"
    if clean_mode == "legado":
        return "Legado"
    return "Default"


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
    return _resolve_visibility_scope_mode_from_scopes(scopes)


def get_menu_visibility_scope_label(menu_config: dict[str, Any] | None) -> str:
    return _resolve_visibility_scope_label_from_mode(
        get_menu_visibility_scope_mode(menu_config)
    )


def normalize_menu_section_key(raw_section: Any, menu_key: Any = "") -> str:
    clean_section = str(raw_section or "").strip().lower()
    clean_section = clean_section.replace("-", "_").replace(" ", "_")
    clean_section = re.sub(r"[^a-z0-9_]+", "", clean_section)
    clean_section = re.sub(r"_+", "_", clean_section).strip("_")

    if clean_section in MENU_SECTION_LABELS:
        return clean_section

    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if clean_menu_key in MENU_SECTION_BY_SYSTEM_MENU_KEY:
        return MENU_SECTION_BY_SYSTEM_MENU_KEY[clean_menu_key]

    return MENU_SECTION_DEFAULT_KEY


def get_menu_section_label(section_key: Any) -> str:
    clean_section = normalize_menu_section_key(section_key)
    return MENU_SECTION_LABELS.get(
        clean_section, MENU_SECTION_LABELS[MENU_SECTION_DEFAULT_KEY]
    )


def _menu_exists(session: Session, menu_key: str) -> bool:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
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


def _resolve_sidebar_menu_settings_entity_id(session: Session) -> int | None:
    entity_id = session.execute(
        text(
            """
            SELECT entity_id
            FROM sidebar_menu_settings
            WHERE entity_id IS NOT NULL
            ORDER BY entity_id
            LIMIT 1
            """
        )
    ).scalar_one_or_none()

    if entity_id is not None:
        return int(entity_id)

    first_active_entity_id = session.execute(
        text(
            """
            SELECT id
            FROM entities
            WHERE is_active = true
            ORDER BY id
            LIMIT 1
            """
        )
    ).scalar_one_or_none()

    if first_active_entity_id is not None:
        return int(first_active_entity_id)

    # Fallback for test databases or early bootstrap environments.
    return 1


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


def _normalize_menu_label_preserve_case(raw_label: Any) -> str:
    clean_label = _fix_common_mojibake(str(raw_label or ""))
    clean_label = " ".join(clean_label.strip().split())
    return clean_label


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


def _get_additional_field_group_key(field_type: Any) -> str:
    return (
        "header"
        if _normalize_additional_field_type(field_type) == "header"
        else "field"
    )


def _build_group_scoped_custom_field_key(label: str, field_type: Any) -> str:
    return _build_custom_field_key_from_label(
        f"{_get_additional_field_group_key(field_type)} {label}"
    )


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


def _normalize_sidebar_section_key(raw_key: Any) -> str:
    clean_value = str(raw_key or "").strip().lower()
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")
    if not clean_value:
        return ""
    if clean_value[0].isdigit():
        clean_value = f"secao_{clean_value}"
    return clean_value


def _build_sidebar_section_key_from_label(label: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(label or ""))
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
        normalized = f"secao_{normalized}"
    return normalized


def _normalize_sidebar_section_label(raw_label: Any) -> str:
    clean_label = _fix_common_mojibake(str(raw_label or ""))
    clean_label = " ".join(clean_label.strip().split())
    if not clean_label:
        return ""
    return _normalize_sentence_case_text(clean_label)


def _normalize_sidebar_section_visibility_scopes(raw_scopes: Any) -> list[str]:
    return normalize_menu_visibility_scopes(raw_scopes)


def get_sidebar_section_visibility_scopes(
    section_config: dict[str, Any] | None,
) -> list[str]:
    if not isinstance(section_config, dict):
        return list(MENU_VISIBILITY_SCOPES)
    if "visibility_scopes" in section_config:
        return _normalize_sidebar_section_visibility_scopes(
            section_config.get("visibility_scopes")
        )
    raw_scope_mode = (
        section_config.get("visibility_scope_mode")
        or section_config.get("scope_mode")
        or section_config.get("scope")
    )
    if raw_scope_mode:
        return _visibility_scope_mode_to_scopes(raw_scope_mode)
    return list(MENU_VISIBILITY_SCOPES)


def get_sidebar_section_visibility_scope_mode(
    section_config: dict[str, Any] | None,
) -> str:
    scopes = get_sidebar_section_visibility_scopes(section_config)
    return _resolve_visibility_scope_mode_from_scopes(scopes)


def get_sidebar_section_visibility_scope_label(
    section_config: dict[str, Any] | None,
) -> str:
    return _resolve_visibility_scope_label_from_mode(
        get_sidebar_section_visibility_scope_mode(section_config)
    )


def _normalize_sidebar_section_status_v5(raw_status: Any) -> str:
    if isinstance(raw_status, bool):
        return "ativo" if raw_status else "inativo"

    clean_status = str(raw_status or "").strip().lower()

    if clean_status in {"inativo", "inactive", "0", "false", "no", "nao", "não", "off"}:
        return "inativo"

    return "ativo"


def _sidebar_section_status_label_v5(raw_status: Any) -> str:
    return (
        "Inativo"
        if _normalize_sidebar_section_status_v5(raw_status) == "inativo"
        else "Ativo"
    )


def _build_sidebar_section_payload(
    section_key: str,
    section_label: str,
    visibility_scopes: Any,
    status: Any = "ativo",
) -> dict[str, Any]:
    normalized_scopes = _normalize_sidebar_section_visibility_scopes(visibility_scopes)
    visibility_scope_mode = _resolve_visibility_scope_mode_from_scopes(
        normalized_scopes
    )
    normalized_status = _normalize_sidebar_section_status_v5(status)

    return {
        "key": section_key,
        "label": section_label,
        "visibility_scopes": normalized_scopes,
        "visibility_scope_mode": visibility_scope_mode,
        "visibility_scope_label": _resolve_visibility_scope_label_from_mode(
            visibility_scope_mode
        ),
        "status": normalized_status,
        "is_active": normalized_status == "ativo",
        "status_label": _sidebar_section_status_label_v5(normalized_status),
        "can_delete": not _is_sidebar_section_delete_protected(section_key),
    }


def _is_sidebar_section_delete_protected(section_key: Any) -> bool:
    clean_section_key = _normalize_sidebar_section_key(section_key)
    return clean_section_key in SIDEBAR_SECTION_DELETE_PROTECTED_KEYS


def normalize_sidebar_sections(raw_sections: Any) -> list[dict[str, Any]]:
    if isinstance(raw_sections, str):
        normalized = normalize_sidebar_sections(
            [
                chunk
                for chunk in re.split(r"[,;\n\r]+", raw_sections)
                if str(chunk or "").strip()
            ]
        )
        return normalized

    normalized_sections: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    raw_items = raw_sections if isinstance(raw_sections, (list, tuple, set)) else []
    for raw_item in raw_items:
        if isinstance(raw_item, dict):
            clean_label = _normalize_sidebar_section_label(raw_item.get("label"))
            clean_key = _normalize_sidebar_section_key(raw_item.get("key"))
            clean_visibility_scopes = get_sidebar_section_visibility_scopes(raw_item)
            clean_status = raw_item.get("status", raw_item.get("is_active", "ativo"))
        else:
            clean_label = _normalize_sidebar_section_label(raw_item)
            clean_key = ""
            clean_visibility_scopes = list(MENU_VISIBILITY_SCOPES)
            clean_status = "ativo"
        if not clean_label:
            continue
        if not clean_key:
            clean_key = _build_sidebar_section_key_from_label(clean_label)
        if not clean_key:
            continue
        if clean_key in seen_keys:
            continue
        seen_keys.add(clean_key)
        normalized_sections.append(
            _build_sidebar_section_payload(
                clean_key, clean_label, clean_visibility_scopes, clean_status
            )
        )

    for default_item in SIDEBAR_SECTION_DEFAULTS:
        default_key = _normalize_sidebar_section_key(default_item.get("key"))
        if not default_key or default_key in seen_keys:
            continue
        seen_keys.add(default_key)
        default_label = _normalize_sidebar_section_label(
            default_item.get("label") or default_key
        )
        normalized_sections.append(
            _build_sidebar_section_payload(
                default_key,
                default_label or default_key,
                default_item.get("visibility_scopes"),
            )
        )

    if normalized_sections:
        return normalized_sections
    return [
        _build_sidebar_section_payload(
            _normalize_sidebar_section_key(item.get("key")),
            _normalize_sidebar_section_label(item.get("label") or ""),
            item.get("visibility_scopes"),
        )
        for item in SIDEBAR_SECTION_DEFAULTS
        if _normalize_sidebar_section_key(item.get("key"))
    ]


def _resolve_default_sidebar_section_key(
    menu_key: str, section_keys: set[str], ordered_section_keys: list[str]
) -> str:
    if not ordered_section_keys:
        return ""

    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    preferred_section_key = MENU_SECTION_BY_SYSTEM_MENU_KEY.get(clean_menu_key, "")

    if preferred_section_key in section_keys:
        return preferred_section_key

    if clean_menu_key in {"home", "administrativo"} and "geral" in section_keys:
        return "geral"

    if clean_menu_key not in {"home", "administrativo"} and "igreja" in section_keys:
        return "igreja"

    return ordered_section_keys[0]


def resolve_menu_sidebar_section_key(
    menu_key: Any,
    menu_config: dict[str, Any] | None,
    valid_section_keys: set[str],
    ordered_section_keys: list[str],
) -> str:
    clean_menu_config = menu_config if isinstance(menu_config, dict) else {}

    raw_sidebar_section_key = clean_menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY)
    clean_sidebar_section_key = _normalize_sidebar_section_key(raw_sidebar_section_key)
    if clean_sidebar_section_key in valid_section_keys:
        return clean_sidebar_section_key

    legacy_section_key = (
        clean_menu_config.get("menu_section")
        or clean_menu_config.get("section_key")
        or clean_menu_config.get("section")
    )
    clean_legacy_section_key = _normalize_sidebar_section_key(legacy_section_key)
    if clean_legacy_section_key in valid_section_keys:
        return clean_legacy_section_key

    normalized_legacy_section_key = normalize_menu_section_key(
        legacy_section_key, menu_key
    )
    if normalized_legacy_section_key in valid_section_keys:
        return normalized_legacy_section_key

    return _resolve_default_sidebar_section_key(
        _resolve_legacy_menu_alias(menu_key),
        valid_section_keys,
        ordered_section_keys,
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


def _build_admin_subprocess_sidebar_metadata(menu_key: str) -> dict[str, Any]:
    config = get_admin_subprocess_config(menu_key)
    if config is None or not config.enabled:
        return {}

    return {
        "admin_subprocess_key": config.key,
        "admin_subprocess_label": config.label,
        "admin_subprocess_singular_label": config.singular_label,
        "admin_subprocess_plural_label": config.plural_label,
        "admin_subprocess_default_target": f"#{config.default_target}".replace(
            "##", "#"
        ),
        "admin_subprocess_edit_target": f"#{config.edit_target}".replace("##", "#"),
        "admin_subprocess_edit_param": config.edit_param,
    }


def ensure_sidebar_menu_settings_defaults(session: Session) -> None:
    existing_rows = session.execute(
        text("SELECT menu_key FROM sidebar_menu_settings")
    ).all()
    existing_keys = {_normalize_menu_key(row.menu_key) for row in existing_rows}
    changed = False

    if MENU_MEU_PERFIL_LEGACY_KEY in existing_keys:
        if MENU_MEU_PERFIL_KEY not in existing_keys:
            session.execute(
                text(
                    """
                    UPDATE sidebar_menu_settings
                    SET menu_key = :canonical_key,
                        menu_label = CASE
                            WHEN trim(menu_label) = '' OR trim(menu_label) = 'Documentos'
                            THEN 'Meus dados'
                            ELSE menu_label
                        END
                    WHERE lower(trim(menu_key)) = :legacy_key
                    """
                ),
                {
                    "canonical_key": MENU_MEU_PERFIL_KEY,
                    "legacy_key": MENU_MEU_PERFIL_LEGACY_KEY,
                },
            )
            existing_keys.discard(MENU_MEU_PERFIL_LEGACY_KEY)
            existing_keys.add(MENU_MEU_PERFIL_KEY)
            changed = True
        else:
            session.execute(
                text(
                    """
                    UPDATE sidebar_menu_settings AS canonical
                    SET menu_label = CASE
                            WHEN trim(legacy.menu_label) = '' OR trim(legacy.menu_label) = 'Documentos'
                            THEN canonical.menu_label
                            ELSE legacy.menu_label
                        END,
                        is_active = legacy.is_active,
                        is_deleted = legacy.is_deleted,
                        menu_config = COALESCE(NULLIF(legacy.menu_config, ''), canonical.menu_config)
                    FROM sidebar_menu_settings AS legacy
                    WHERE lower(trim(canonical.menu_key)) = :canonical_key
                      AND lower(trim(legacy.menu_key)) = :legacy_key
                    """
                ),
                {
                    "canonical_key": MENU_MEU_PERFIL_KEY,
                    "legacy_key": MENU_MEU_PERFIL_LEGACY_KEY,
                },
            )
            session.execute(
                text(
                    """
                    DELETE FROM sidebar_menu_settings
                    WHERE lower(trim(menu_key)) = :legacy_key
                    """
                ),
                {"legacy_key": MENU_MEU_PERFIL_LEGACY_KEY},
            )
            existing_keys.discard(MENU_MEU_PERFIL_LEGACY_KEY)
            changed = True

    default_entity_id = _resolve_sidebar_menu_settings_entity_id(session)

    for item in SIDEBAR_MENU_DEFAULTS:
        menu_key = str(item["key"])
        if menu_key in existing_keys:
            continue
        session.execute(
            text(
                """
                INSERT INTO sidebar_menu_settings (entity_id, menu_key, menu_label, is_active, is_deleted)
                VALUES (:entity_id, :menu_key, :menu_label, :is_active, :is_deleted)
                """
            ),
            {
                "entity_id": default_entity_id,
                "menu_key": menu_key,
                "menu_label": str(item["label"]),
                "is_active": True,
                "is_deleted": False,
            },
        )
        changed = True

    meu_perfil_label = session.execute(
        text(
            """
            SELECT menu_label
            FROM sidebar_menu_settings
            WHERE menu_key = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": MENU_MEU_PERFIL_KEY},
    ).scalar_one_or_none()
    if isinstance(meu_perfil_label, str) and meu_perfil_label.strip() == "Documentos":
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_label = :menu_label
                WHERE menu_key = :menu_key
                """
            ),
            {"menu_key": MENU_MEU_PERFIL_KEY, "menu_label": "Meus dados"},
        )
        changed = True

    administrativo_config_raw = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE menu_key = 'administrativo'
            LIMIT 1
            """
        )
    ).scalar_one_or_none()
    administrativo_config = _parse_menu_config(administrativo_config_raw)
    normalized_sidebar_sections = normalize_sidebar_sections(
        administrativo_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )
    if (
        administrativo_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
        != normalized_sidebar_sections
    ):
        administrativo_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = (
            normalized_sidebar_sections
        )
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE menu_key = 'administrativo'
                """
            ),
            {"menu_config": json.dumps(administrativo_config, ensure_ascii=False)},
        )
        changed = True

    if changed:
        session.commit()


def _load_menu_config(session: Session, menu_key: str) -> dict[str, Any]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    raw_menu_config = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": clean_menu_key},
    ).scalar_one_or_none()
    return _parse_menu_config(raw_menu_config)


def _normalize_additional_field_type(raw_type: Any) -> str:
    clean_value = str(raw_type or "").strip().lower()
    if clean_value in ADDITIONAL_FIELD_TYPE_KEYS:
        return clean_value
    return ADDITIONAL_FIELD_DEFAULT_TYPE
