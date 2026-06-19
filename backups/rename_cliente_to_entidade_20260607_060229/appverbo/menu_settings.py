from __future__ import annotations

import json
import re
import unicodedata
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from appverbo.menu_config_scope import (
    MENU_CONFIG_SCOPE_MENU_LABEL_KEY_V1,
    apply_entity_scoped_menu_config_updates_v1,
    build_effective_menu_config_v1,
    build_effective_menu_label_v1,
    get_menu_entity_scope_overrides_v1,
)

MENU_MEU_PERFIL_KEY = "meu_perfil"
MENU_MEU_PERFIL_LEGACY_KEY = "documentos"
MENU_SESSOES_KEY = "sessoes"

SIDEBAR_MENU_DEFAULTS: tuple[dict[str, Any], ...] = (
    {"key": "home", "label": "Home", "requires_admin": False},
    {"key": "administrativo", "label": "Administrativo", "requires_admin": True},
    {"key": MENU_SESSOES_KEY, "label": "Estruturas", "requires_admin": True},
    {"key": MENU_MEU_PERFIL_KEY, "label": "Meu perfil", "requires_admin": True},
    {"key": "funcionarios", "label": "Funcionarios", "requires_admin": True},
    {"key": "financeiro", "label": "Financeiro", "requires_admin": True},
    {"key": "relatorios", "label": "Relatorios", "requires_admin": True},
    {"key": "links", "label": "Links", "requires_admin": False},
    {"key": "contato", "label": "Contacto", "requires_admin": False},
    {"key": "tutorial", "label": "Tutorial", "requires_admin": False},
)

SIDEBAR_MENU_KEYS = {item["key"] for item in SIDEBAR_MENU_DEFAULTS}
SIDEBAR_MENU_PROTECTED_KEYS = {"home", "administrativo", MENU_SESSOES_KEY}
SIDEBAR_MENU_DELETE_PROTECTED_KEYS = {"home", "administrativo", MENU_SESSOES_KEY}
SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS = {"home"}
SIDEBAR_MENU_GLOBAL_SCOPE_KEYS = frozenset({MENU_SESSOES_KEY})
SIDEBAR_MENU_ENTITY_LABEL_DEFAULT_KEYS = frozenset(
    {
        "home",
        "administrativo",
        MENU_SESSOES_KEY,
        "empresa",
        "contacto_geral",
    }
)
SIDEBAR_MENU_ENTITY_LABEL_OWNER_KEYS = frozenset(
    {
        MENU_MEU_PERFIL_KEY,
        "departamentos",
        "adicionar_musica",
        "ensaio",
        "contactos",
    }
)
MENU_PROCESS_ADDITIONAL_PRIORITY_EXCLUDED_KEYS = {"home", "administrativo", MENU_MEU_PERFIL_KEY}
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
MENU_SECTION_LABELS = {
    item["key"]: item["label"] for item in MENU_SECTION_OPTIONS
}
MENU_SECTION_BY_SYSTEM_MENU_KEY = {
    "administrativo": "sistema",
    "sessoes": "sistema",
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
SIDEBAR_ICON_DEFAULT_KEY = "circle"
SIDEBAR_ICON_ALIAS_MAP: dict[str, str] = {
    "settings": "settings",
    "setting": "settings",
    "gear": "settings",
    "admin": "settings",
    "home": "home",
    "house": "home",
    "empresa": "building",
    "building": "building",
    "office": "building",
    "departamentos": "departments",
    "departamento": "departments",
    "department": "departments",
    "departments": "departments",
    "music": "music",
    "musica": "music",
    "musicas": "music",
    "nota": "music",
    "user": "user",
    "perfil": "user",
    "profile": "user",
    "users": "users",
    "usuarios": "users",
    "utilizador": "users",
    "utilizadores": "users",
    "funcionario": "users",
    "funcionarios": "users",
    "team": "users",
    "wallet": "wallet",
    "finance": "wallet",
    "financeiro": "wallet",
    "tesouraria": "wallet",
    "money": "wallet",
    "chart": "chart",
    "report": "chart",
    "reports": "chart",
    "relatorio": "chart",
    "relatorios": "chart",
    "graph": "chart",
    "link": "link",
    "links": "link",
    "mail": "mail",
    "email": "mail",
    "contact": "mail",
    "contacto": "mail",
    "contato": "mail",
    "book": "book",
    "tutorial": "book",
    "help": "book",
    "manual": "book",
    "circle": "circle",
    "default": "circle",
}
MENU_CONFIG_SIDEBAR_SECTION_KEY = "sidebar_section"
MENU_CONFIG_SIDEBAR_SECTIONS_KEY = "sidebar_sections"
MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY = "sidebar_global_refresh_version"
MENU_CONFIG_SIDEBAR_ICON_KEY = "sidebar_icon"
MENU_CONFIG_MEU_PERFIL_HEADERS_AUTO_REPAIRED_V1_KEY = "meu_perfil_headers_auto_repaired_v1"
MENU_CONFIG_MEU_PERFIL_DEPARTMENT_MEMBERSHIP_FIELDS_AUTO_SEEDED_V1_KEY = (
    "meu_perfil_department_membership_fields_auto_seeded_v1"
)
MENU_CONFIG_MEU_PERFIL_DEPARTMENT_ROLES_OPERATIONS_MOVED_V1_KEY = (
    "meu_perfil_department_roles_operations_moved_v1"
)
MENU_CONFIG_DEPARTAMENTOS_ROLES_OPERATIONS_FIELDS_AUTO_SEEDED_V1_KEY = (
    "departamentos_roles_operations_fields_auto_seeded_v1"
)
MENU_CONFIG_PROCESS_FIELDS_SEEDED_ALL_V1_KEY = "process_fields_seeded_all_v1"
MENU_DEPARTAMENTOS_KEY = "departamentos"
MENU_LEGACY_KEY_ALIAS = {
    "configuracao": "administrativo",
    MENU_MEU_PERFIL_LEGACY_KEY: MENU_MEU_PERFIL_KEY,
}
SIDEBAR_SECTION_DEFAULTS: tuple[dict[str, Any], ...] = (
    {"key": "sistema", "label": "Sistema", "visibility_scopes": ["owner", "legado"]},
    {"key": "geral", "label": "Geral", "visibility_scopes": ["owner", "legado"]},
    {"key": "dados_gerais", "label": "Dados gerais", "visibility_scopes": ["owner", "legado"]},
    {"key": "igreja", "label": "Igreja", "visibility_scopes": ["owner", "legado"]},
    {"key": "tesouraria", "label": "Tesouraria", "visibility_scopes": ["owner", "legado"]},
)
SIDEBAR_SECTION_DEFAULTS_BY_KEY = {
    str(item["key"]).strip().lower(): str(item["label"])
    for item in SIDEBAR_SECTION_DEFAULTS
}
ADDITIONAL_FIELD_TEXTUAL_TYPES = {"text", "textarea", "email", "phone", "number", "link"}
ADDITIONAL_FIELD_TYPES: tuple[dict[str, str], ...] = (
    {"key": "text", "label": "Texto"},
    {"key": "textarea", "label": "Texto longo"},
    {"key": "number", "label": "Número"},
    {"key": "email", "label": "Email"},
    {"key": "phone", "label": "Telefone"},
    {"key": "link", "label": "Link"},
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
    ),
    "sessoes": (
        {"key": "perfil_de_autorizacao", "label": "Perfil de autorização"},
        {"key": "sessoes", "label": "Sessões"},
        {"key": "menu", "label": "Menu"},
        {"key": "definicoes", "label": "Definições"},
    ),
    MENU_MEU_PERFIL_KEY: (
        {"key": "nome", "label": "Nome"},
        {"key": "telefone", "label": "Telefone"},
        {"key": "email", "label": "Email"},
        {"key": "pais", "label": "País"},
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
    "administrativo": ["entidade", "utilizador"],
    "sessoes": ["perfil_de_autorizacao", "sessoes", "menu", "definicoes"],
    MENU_MEU_PERFIL_KEY: ["nome", "email", "telefone", "pais"],
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
MENU_MEU_PERFIL_FIELD_KEYS = tuple(item["key"] for item in MENU_MEU_PERFIL_FIELD_OPTIONS)
MENU_MEU_PERFIL_FIELD_LABELS = {
    item["key"]: item["label"] for item in MENU_MEU_PERFIL_FIELD_OPTIONS
}
MENU_MEU_PERFIL_FIELDS_DEFAULT = ["nome", "email", "telefone", "pais"]
MENU_MEU_PERFIL_DEPARTMENT_MEMBERSHIP_FIELDS_V1: tuple[dict[str, Any], ...] = (
    {
        "key": "custom_dados_de_departamento",
        "label": "Dados de departamento",
        "field_type": "header",
        "is_required": False,
    },
    {
        "key": "custom_departamento_nome",
        "label": "Departamento",
        "field_type": "text",
        "is_required": True,
        "size": 120,
        "header_key": "custom_dados_de_departamento",
    },
    {
        "key": "custom_departamento_estado",
        "label": "Estado no departamento",
        "field_type": "text",
        "is_required": True,
        "size": 30,
        "header_key": "custom_dados_de_departamento",
    },
    {
        "key": "custom_departamento_data_entrada",
        "label": "Data de entrada",
        "field_type": "date",
        "is_required": True,
        "header_key": "custom_dados_de_departamento",
    },
    {
        "key": "custom_departamento_data_saida",
        "label": "Data de saida",
        "field_type": "date",
        "is_required": False,
        "header_key": "custom_dados_de_departamento",
    },
    {
        "key": "custom_departamento_motivo_saida",
        "label": "Motivo de saida",
        "field_type": "text",
        "is_required": False,
        "size": 255,
        "header_key": "custom_dados_de_departamento",
    },
    {
        "key": "custom_departamento_supervisor_direto",
        "label": "Supervisor direto",
        "field_type": "text",
        "is_required": False,
        "size": 150,
        "header_key": "custom_dados_de_departamento",
    },
    {
        "key": "custom_departamento_observacoes",
        "label": "Observacoes",
        "field_type": "text",
        "is_required": False,
        "size": 255,
        "header_key": "custom_dados_de_departamento",
    },
    {
        "key": "custom_funcoes_no_departamento",
        "label": "Funcoes no departamento",
        "field_type": "header",
        "is_required": False,
    },
    {
        "key": "custom_funcao_no_departamento",
        "label": "Funcao no departamento",
        "field_type": "text",
        "is_required": False,
        "size": 120,
        "header_key": "custom_funcoes_no_departamento",
    },
    {
        "key": "custom_funcao_principal_departamento",
        "label": "Funcao principal",
        "field_type": "flag",
        "is_required": False,
        "header_key": "custom_funcoes_no_departamento",
    },
    {
        "key": "custom_funcao_ativa_departamento",
        "label": "Funcao ativa",
        "field_type": "flag",
        "is_required": False,
        "header_key": "custom_funcoes_no_departamento",
    },
    {
        "key": "custom_incluir_funcao_na_escala",
        "label": "Incluir funcao na escala",
        "field_type": "flag",
        "is_required": False,
        "header_key": "custom_funcoes_no_departamento",
    },
    {
        "key": "custom_limite_mensal_funcao",
        "label": "Limite mensal da funcao",
        "field_type": "number",
        "is_required": False,
        "size": 10,
        "header_key": "custom_funcoes_no_departamento",
    },
    {
        "key": "custom_data_inicio_funcao",
        "label": "Data inicio da funcao",
        "field_type": "date",
        "is_required": False,
        "header_key": "custom_funcoes_no_departamento",
    },
    {
        "key": "custom_data_fim_funcao",
        "label": "Data fim da funcao",
        "field_type": "date",
        "is_required": False,
        "header_key": "custom_funcoes_no_departamento",
    },
    {
        "key": "custom_operacao_de_escala",
        "label": "Operacao de escala",
        "field_type": "header",
        "is_required": False,
    },
    {
        "key": "custom_escala_prioridade_interna",
        "label": "Prioridade interna",
        "field_type": "number",
        "is_required": False,
        "size": 10,
        "header_key": "custom_operacao_de_escala",
    },
    {
        "key": "custom_escala_elegivel_automatica",
        "label": "Elegivel para escala automatica",
        "field_type": "flag",
        "is_required": False,
        "header_key": "custom_operacao_de_escala",
    },
    {
        "key": "custom_escala_ultima_data",
        "label": "Ultima escala",
        "field_type": "date",
        "is_required": False,
        "header_key": "custom_operacao_de_escala",
    },
    {
        "key": "custom_escala_limite_mensal",
        "label": "Limite mensal de escalas",
        "field_type": "number",
        "is_required": False,
        "size": 10,
        "header_key": "custom_operacao_de_escala",
    },
    {
        "key": "custom_escala_permitir_mesmo_dia",
        "label": "Permitir escala no mesmo dia",
        "field_type": "flag",
        "is_required": False,
        "header_key": "custom_operacao_de_escala",
    },
    {
        "key": "custom_escala_bloqueio_temporario",
        "label": "Bloqueado temporariamente para escala",
        "field_type": "flag",
        "is_required": False,
        "header_key": "custom_operacao_de_escala",
    },
    {
        "key": "custom_escala_motivo_bloqueio",
        "label": "Motivo do bloqueio",
        "field_type": "text",
        "is_required": False,
        "size": 255,
        "header_key": "custom_operacao_de_escala",
    },
)
MENU_DEPARTMENT_ROLES_OPERATIONS_MOVE_KEYS_V1: set[str] = {
    "custom_funcoes_no_departamento",
    "custom_funcao_no_departamento",
    "custom_funcao_principal_departamento",
    "custom_funcao_ativa_departamento",
    "custom_incluir_funcao_na_escala",
    "custom_limite_mensal_funcao",
    "custom_data_inicio_funcao",
    "custom_data_fim_funcao",
    "custom_operacao_de_escala",
    "custom_escala_prioridade_interna",
    "custom_escala_elegivel_automatica",
    "custom_escala_ultima_data",
    "custom_escala_limite_mensal",
    "custom_escala_permitir_mesmo_dia",
    "custom_escala_bloqueio_temporario",
    "custom_escala_motivo_bloqueio",
}
MENU_DEPARTMENT_ROLES_OPERATIONS_MOVE_HEADERS_V1: set[str] = {
    "custom_funcoes_no_departamento",
    "custom_operacao_de_escala",
}
MENU_DEPARTAMENTOS_MEMBERSHIP_HEADERS_V1: set[str] = {
    "custom_dados_de_departamento",
    *MENU_DEPARTMENT_ROLES_OPERATIONS_MOVE_HEADERS_V1,
}
MENU_DEPARTMENT_MEMBERSHIP_DATA_KEYS_V1: set[str] = {
    "custom_dados_de_departamento",
    "custom_departamento_nome",
    "custom_departamento_estado",
    "custom_departamento_data_entrada",
    "custom_departamento_data_saida",
    "custom_departamento_motivo_saida",
    "custom_departamento_supervisor_direto",
    "custom_departamento_observacoes",
}
MENU_DEPARTAMENTOS_FIELDS_SEED_KEYS_V1: set[str] = (
    set(MENU_DEPARTMENT_MEMBERSHIP_DATA_KEYS_V1)
    | set(MENU_DEPARTMENT_ROLES_OPERATIONS_MOVE_KEYS_V1)
)


def _sidebar_menu_defaults_by_key() -> dict[str, dict[str, Any]]:
    return {item["key"]: dict(item) for item in SIDEBAR_MENU_DEFAULTS}


def _normalize_menu_key(menu_key: Any) -> str:
    return str(menu_key or "").strip().lower()


def _resolve_legacy_menu_alias(menu_key: Any) -> str:
    clean_menu_key = _normalize_menu_key(menu_key)
    return MENU_LEGACY_KEY_ALIAS.get(clean_menu_key, clean_menu_key)


def resolve_menu_key_alias(menu_key: Any) -> str:
    return _resolve_legacy_menu_alias(menu_key)


# ###################################################################################
# (0A) ESCOPO GLOBAL DE MENUS CORE
# ###################################################################################


def is_global_scope_menu_v1(menu_key: Any) -> bool:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    return clean_menu_key in SIDEBAR_MENU_GLOBAL_SCOPE_KEYS


def resolve_menu_selected_entity_scope_id_v1(
    menu_key: Any,
    selected_entity_id: object = None,
) -> object:
    if is_global_scope_menu_v1(menu_key):
        return None
    return selected_entity_id


def _coerce_menu_entity_scope_id_v1(value: object) -> int | None:
    clean_value = str(value or "").strip()

    if not clean_value.isdigit():
        return None

    parsed_value = int(clean_value)
    if parsed_value <= 0:
        return None

    return parsed_value


def is_sidebar_menu_entity_scope_visible_v1(
    *,
    record_entity_id: object,
    selected_entity_id: object,
) -> bool:
    parsed_record_entity_id = _coerce_menu_entity_scope_id_v1(record_entity_id)
    parsed_selected_entity_id = _coerce_menu_entity_scope_id_v1(selected_entity_id)

    if parsed_record_entity_id is None:
        return True

    if parsed_selected_entity_id is None:
        return False

    return parsed_record_entity_id == parsed_selected_entity_id


def resolve_menu_entity_label_scope_id_v1(
    menu_key: Any,
    selected_entity_id: object = None,
    *,
    owner_entity_id: object = None,
    has_entity_scope_overrides: bool = False,
) -> object:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if clean_menu_key in SIDEBAR_MENU_ENTITY_LABEL_DEFAULT_KEYS:
        return None

    if clean_menu_key in SIDEBAR_MENU_ENTITY_LABEL_OWNER_KEYS:
        return owner_entity_id

    if has_entity_scope_overrides:
        return selected_entity_id

    return None


def get_owner_entity_scope_id_v1(session: Session) -> int | None:
    from appverbo.services.entities import get_existing_owner_entity_id_v1

    return get_existing_owner_entity_id_v1(session=session)


def resolve_menu_entity_scope_id_v1(
    menu_key: Any,
    *,
    selected_entity_id: object = None,
    owner_entity_id: object = None,
    menu_config: dict[str, Any] | None = None,
) -> object:
    effective_selected_entity_id = resolve_menu_selected_entity_scope_id_v1(
        menu_key,
        selected_entity_id,
    )
    entity_scope_overrides = get_menu_entity_scope_overrides_v1(
        menu_config,
        selected_entity_id=effective_selected_entity_id,
    )

    return resolve_menu_entity_label_scope_id_v1(
        menu_key,
        effective_selected_entity_id,
        owner_entity_id=owner_entity_id,
        has_entity_scope_overrides=bool(entity_scope_overrides),
    )


def resolve_menu_effective_config_scope_id_v1(
    menu_key: Any,
    *,
    selected_entity_id: object = None,
    owner_entity_id: object = None,
    menu_config: dict[str, Any] | None = None,
) -> object:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if clean_menu_key in SIDEBAR_MENU_GLOBAL_SCOPE_KEYS:
        return None

    if clean_menu_key in SIDEBAR_MENU_ENTITY_LABEL_DEFAULT_KEYS:
        owner_scope_overrides = get_menu_entity_scope_overrides_v1(
            menu_config,
            selected_entity_id=owner_entity_id,
        )
        if owner_scope_overrides:
            return owner_entity_id
        return None

    return resolve_menu_selected_entity_scope_id_v1(
        clean_menu_key,
        selected_entity_id,
    )


def _is_menu_delete_protected(menu_key: Any, menu_label: Any = "") -> bool:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
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
    return _resolve_visibility_scope_label_from_mode(get_menu_visibility_scope_mode(menu_config))



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
    return MENU_SECTION_LABELS.get(clean_section, MENU_SECTION_LABELS[MENU_SECTION_DEFAULT_KEY])


def normalize_sidebar_icon_key(raw_icon_key: Any) -> str:
    clean_value = str(raw_icon_key or "").strip().lower()
    clean_value = clean_value.replace("-", "_").replace(" ", "_")
    clean_value = re.sub(r"[^a-z0-9_]+", "", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")

    if not clean_value:
        return SIDEBAR_ICON_DEFAULT_KEY

    alias_key = clean_value.replace("_", "")
    if clean_value in SIDEBAR_ICON_ALIAS_MAP:
        return SIDEBAR_ICON_ALIAS_MAP[clean_value]
    if alias_key in SIDEBAR_ICON_ALIAS_MAP:
        return SIDEBAR_ICON_ALIAS_MAP[alias_key]

    return SIDEBAR_ICON_DEFAULT_KEY


def infer_sidebar_icon_key(
    menu_key: Any = "",
    menu_label: Any = "",
    menu_section: Any = "",
) -> str:
    candidate_values = (
        str(menu_key or "").strip().lower(),
        str(menu_label or "").strip().lower(),
        str(menu_section or "").strip().lower(),
    )
    joined = " ".join(value for value in candidate_values if value)

    if "music" in joined or "musica" in joined:
        return "music"
    if "depart" in joined:
        return "departments"
    if "admin" in joined or "defin" in joined or "config" in joined:
        return "settings"
    if "home" in joined or "inicio" in joined:
        return "home"
    if "empresa" in joined or "entidade" in joined or "building" in joined:
        return "building"
    if "perfil" in joined or "profile" in joined:
        return "user"
    if (
        "funcion" in joined
        or "utilizador" in joined
        or "usuario" in joined
        or "users" in joined
    ):
        return "users"
    if "tesour" in joined or "finance" in joined or "money" in joined:
        return "wallet"
    if "relat" in joined or "report" in joined or "graf" in joined:
        return "chart"
    if "link" in joined:
        return "link"
    if "contat" in joined or "contact" in joined or "mail" in joined:
        return "mail"
    if "tutorial" in joined or "ajuda" in joined or "manual" in joined:
        return "book"

    return SIDEBAR_ICON_DEFAULT_KEY


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


# ###################################################################################
# (MUSICAS) NORMALIZACAO DE CONFIGURACAO DO PROCESSO
# ###################################################################################

def _normalize_music_lookup_text_v1(raw_value: Any) -> str:
    normalized = (
        unicodedata.normalize("NFKD", str(raw_value or ""))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    return " ".join(normalized.split())


def _is_music_menu_v1(menu_key: Any, menu_label: Any = "") -> bool:
    joined = " ".join(
        part
        for part in (
            _normalize_music_lookup_text_v1(menu_key),
            _normalize_music_lookup_text_v1(menu_label),
        )
        if part
    )
    return "musica" in joined


def _resolve_music_field_role_v1(field_key: Any, field_label: Any, field_type: Any) -> str:
    clean_field_type = str(field_type or "").strip().lower()
    lookup = " ".join(
        part
        for part in (
            _normalize_music_lookup_text_v1(field_key),
            _normalize_music_lookup_text_v1(field_label),
        )
        if part
    )
    if not lookup:
        return ""
    if clean_field_type == "header":
        return "header"
    if "nome" in lookup and "musica" in lookup:
        return "name"
    if "versao" in lookup:
        return "version"
    if ("youtube" in lookup) or ("url" in lookup) or ("link" in lookup):
        return "youtube_url"
    if "fonte" in lookup and "letra" in lookup:
        return "lyrics_source"
    if "estado" in lookup and "letra" in lookup:
        return "lyrics_status"
    if "letra" in lookup:
        return "lyrics"
    return ""


def _normalize_music_process_lists_v1(raw_lists: Any) -> list[dict[str, Any]]:
    normalized_lists: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for list_key, list_label, list_items in (
        (
            "list_fonte_da_letra",
            "Fonte da letra",
            ["manual", "youtube_transcript", "audio_transcription", "imported"],
        ),
        (
            "list_estado_da_letra",
            "Estado da letra",
            ["rascunho", "revista", "aprovada"],
        ),
    ):
        normalized_lists.append(
            {
                "key": list_key,
                "label": list_label,
                "items": list(list_items),
                "items_csv": ", ".join(list_items),
                "source_key": "manual",
                "source_label": "Manual",
            }
        )
        seen_keys.add(list_key)

    if isinstance(raw_lists, list):
        for raw_item in raw_lists:
            if not isinstance(raw_item, dict):
                continue
            clean_key = str(raw_item.get("key") or "").strip().lower()
            if not clean_key or clean_key in seen_keys:
                continue
            normalized_lists.append(dict(raw_item))
            seen_keys.add(clean_key)

    return normalized_lists


def _normalize_music_menu_config_v1(
    menu_key: Any,
    menu_label: Any,
    raw_menu_config: dict[str, Any] | None,
) -> dict[str, Any]:
    menu_config = dict(raw_menu_config or {})
    if not _is_music_menu_v1(menu_key, menu_label):
        return menu_config

    additional_fields = normalize_menu_process_additional_fields(
        menu_config.get("additional_fields")
    )
    preferred_fields_by_role: dict[str, dict[str, Any]] = {}
    used_field_keys: set[str] = set()

    for field in additional_fields:
        clean_field_key = str(field.get("key") or "").strip().lower()
        clean_field_type = str(field.get("field_type") or "text").strip().lower()
        field_role = _resolve_music_field_role_v1(
            clean_field_key,
            field.get("label"),
            clean_field_type,
        )
        if not field_role:
            continue
        current_field = preferred_fields_by_role.get(field_role)
        if current_field is None:
            preferred_fields_by_role[field_role] = dict(field)
            continue
        current_type = str(current_field.get("field_type") or "").strip().lower()
        if field_role in {"lyrics_source", "lyrics_status"} and current_type != "list" and clean_field_type == "list":
            preferred_fields_by_role[field_role] = dict(field)

    default_field_specs = (
        {
            "role": "header",
            "default_key": "custom_adicionar_musica",
            "label": "Adicionar música",
            "field_type": "header",
            "is_required": False,
        },
        {
            "role": "name",
            "default_key": "custom_nome_da_musica",
            "label": "Nome da música",
            "field_type": "text",
            "is_required": True,
            "size": 255,
        },
        {
            "role": "version",
            "default_key": "custom_versao",
            "label": "Versão",
            "field_type": "text",
            "is_required": True,
            "size": 255,
        },
        {
            "role": "youtube_url",
            "default_key": "custom_url",
            "label": "URL do YouTube",
            "field_type": "link",
            "is_required": True,
            "size": 255,
        },
        {
            "role": "lyrics",
            "default_key": "custom_letra",
            "label": "Letra",
            "field_type": "textarea",
            "is_required": True,
            "size": 4000,
        },
        {
            "role": "lyrics_source",
            "default_key": "custom_fonte_da_letra",
            "label": "Fonte da letra",
            "field_type": "list",
            "is_required": True,
            "list_key": "list_fonte_da_letra",
            "shared_value_key": "list_fonte_da_letra",
        },
        {
            "role": "lyrics_status",
            "default_key": "custom_estado_da_letra",
            "label": "Estado da letra",
            "field_type": "list",
            "is_required": True,
            "list_key": "list_estado_da_letra",
            "shared_value_key": "list_estado_da_letra",
        },
    )

    normalized_music_fields: list[dict[str, Any]] = []
    for field_spec in default_field_specs:
        existing_field = preferred_fields_by_role.get(field_spec["role"])
        field_data = dict(existing_field or {})
        clean_field_key = str(field_data.get("key") or "").strip().lower()
        if not clean_field_key:
            clean_field_key = str(field_spec["default_key"])
        clean_field_key = _normalize_custom_field_key(clean_field_key)
        field_data["key"] = clean_field_key
        field_data["label"] = str(field_spec["label"])
        field_data["field_type"] = str(field_spec["field_type"])
        field_data["is_required"] = bool(field_spec.get("is_required", False))
        if "size" in field_spec:
            field_data["size"] = int(field_spec["size"])
        else:
            field_data.pop("size", None)
        if "list_key" in field_spec:
            field_data["list_key"] = str(field_spec["list_key"])
            field_data["shared_value_key"] = str(field_spec["shared_value_key"])
        else:
            field_data.pop("list_key", None)
            field_data.pop("shared_value_key", None)
        normalized_music_fields.append(field_data)
        used_field_keys.add(clean_field_key)

    extra_fields: list[dict[str, Any]] = []
    for field in additional_fields:
        clean_field_key = str(field.get("key") or "").strip().lower()
        if not clean_field_key or clean_field_key in used_field_keys:
            continue
        extra_fields.append(dict(field))

    header_key = str(normalized_music_fields[0].get("key") or "").strip().lower()
    visible_field_keys = [
        str(field.get("key") or "").strip().lower()
        for field in normalized_music_fields
        if str(field.get("field_type") or "").strip().lower() != "header"
    ]
    header_map = {
        field_key: header_key
        for field_key in visible_field_keys
    }
    menu_config["additional_fields"] = normalized_music_fields + extra_fields
    menu_config["process_lists"] = _normalize_music_process_lists_v1(
        menu_config.get("process_lists")
    )
    menu_config["visible_fields"] = [header_key] + visible_field_keys
    menu_config["process_visible_fields"] = [header_key] + visible_field_keys
    menu_config["visible_field_headers"] = dict(header_map)
    menu_config["process_visible_field_header_map"] = dict(header_map)
    menu_config["process_visible_field_rows"] = [
        {
            "field_key": field_key,
            "header_key": header_key,
        }
        for field_key in visible_field_keys
    ]
    menu_config["process_visible_fields_configured"] = True
    return menu_config


def _normalize_core_sidebar_menu_config_v1(
    menu_key: Any,
    raw_menu_config: dict[str, Any] | None,
) -> dict[str, Any]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    menu_config = dict(raw_menu_config or {})

    if clean_menu_key not in SIDEBAR_MENU_GLOBAL_SCOPE_KEYS:
        return menu_config

    menu_config["requires_admin"] = True
    menu_config["visibility_scopes"] = list(MENU_VISIBILITY_SCOPES)

    if not str(menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY) or "").strip():
        menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = MENU_SECTION_BY_SYSTEM_MENU_KEY.get(
            clean_menu_key,
            MENU_SECTION_DEFAULT_KEY,
        )

    return menu_config


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


def get_sidebar_section_visibility_scopes(section_config: dict[str, Any] | None) -> list[str]:
    if not isinstance(section_config, dict):
        return list(MENU_VISIBILITY_SCOPES)
    if "visibility_scopes" in section_config:
        return _normalize_sidebar_section_visibility_scopes(section_config.get("visibility_scopes"))
    raw_scope_mode = (
        section_config.get("visibility_scope_mode")
        or section_config.get("scope_mode")
        or section_config.get("scope")
    )
    if raw_scope_mode:
        return _visibility_scope_mode_to_scopes(raw_scope_mode)
    return list(MENU_VISIBILITY_SCOPES)


def get_sidebar_section_visibility_scope_mode(section_config: dict[str, Any] | None) -> str:
    scopes = get_sidebar_section_visibility_scopes(section_config)
    return _resolve_visibility_scope_mode_from_scopes(scopes)


def get_sidebar_section_visibility_scope_label(section_config: dict[str, Any] | None) -> str:
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
    return "Inativo" if _normalize_sidebar_section_status_v5(raw_status) == "inativo" else "Ativo"


def is_sidebar_menu_section_visible_v1(
    menu_row: dict[str, Any] | None,
    current_entity_scope: str | None = None,
) -> bool:
    if not isinstance(menu_row, dict):
        return True

    clean_section_key = _normalize_sidebar_section_key(menu_row.get("sidebar_section_key"))
    if not clean_section_key:
        return True

    raw_section_status = menu_row.get("sidebar_section_status")
    if raw_section_status is None:
        raw_section_status = menu_row.get("sidebar_section_is_active")
    if _normalize_sidebar_section_status_v5(raw_section_status) != "ativo":
        return False

    clean_entity_scope = _normalize_menu_visibility_scope_value(current_entity_scope)
    sidebar_section_visibility_scopes = (
        menu_row.get("sidebar_section_visibility_scopes")
        if menu_row.get("sidebar_section_visibility_scopes") is not None
        else menu_row.get("sidebar_section_visibility_scope_mode")
    )
    visibility_scopes = _normalize_sidebar_section_visibility_scopes(
        sidebar_section_visibility_scopes
    )
    if clean_entity_scope and clean_entity_scope not in visibility_scopes:
        return False

    return True


def _build_sidebar_section_payload(
    section_key: str,
    section_label: str,
    visibility_scopes: Any,
    status: Any = "ativo",
) -> dict[str, Any]:
    normalized_scopes = _normalize_sidebar_section_visibility_scopes(visibility_scopes)
    visibility_scope_mode = _resolve_visibility_scope_mode_from_scopes(normalized_scopes)
    normalized_status = _normalize_sidebar_section_status_v5(status)

    return {
        "key": section_key,
        "label": section_label,
        "visibility_scopes": normalized_scopes,
        "visibility_scope_mode": visibility_scope_mode,
        "visibility_scope_label": _resolve_visibility_scope_label_from_mode(visibility_scope_mode),
        "status": normalized_status,
        "is_active": normalized_status == "ativo",
        "status_label": _sidebar_section_status_label_v5(normalized_status),
    }


def normalize_sidebar_sections(raw_sections: Any) -> list[dict[str, Any]]:
    if isinstance(raw_sections, str):
        normalized = normalize_sidebar_sections(
            [chunk for chunk in re.split(r"[,;\n\r]+", raw_sections) if str(chunk or "").strip()]
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
            _build_sidebar_section_payload(clean_key, clean_label, clean_visibility_scopes, clean_status)
        )

    for default_item in SIDEBAR_SECTION_DEFAULTS:
        default_key = _normalize_sidebar_section_key(default_item.get("key"))
        if not default_key or default_key in seen_keys:
            continue
        seen_keys.add(default_key)
        default_label = _normalize_sidebar_section_label(default_item.get("label") or default_key)
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


def _resolve_default_sidebar_section_key(menu_key: str, section_keys: set[str], ordered_section_keys: list[str]) -> str:
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
    clean_menu_label = _normalize_sentence_case_text(menu_label)
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
    max_size = 4000 if field_type == "textarea" else ADDITIONAL_FIELD_MAX_SIZE
    default_size = 4000 if field_type == "textarea" else ADDITIONAL_FIELD_DEFAULT_SIZE
    try:
        parsed_size = int(str(raw_size or "").strip())
    except (TypeError, ValueError):
        parsed_size = default_size
    parsed_size = max(1, min(parsed_size, max_size))
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
    allowed_operators = {"equals", "not_equals", "is_empty", "is_not_empty"}
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
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
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



def get_menu_process_default_visible_fields_v4(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    # APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_DEFAULTS_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    clean_menu_config = menu_config if isinstance(menu_config, dict) else {}

    selectable_options = get_menu_process_selectable_field_options(
        clean_menu_key,
        clean_menu_config,
    )

    selectable_keys = [
        str(item.get("key") or "").strip().lower()
        for item in selectable_options
        if str(item.get("key") or "").strip()
    ]

    if not selectable_keys:
        return []

    allowed_keys = set(selectable_keys)
    configured_defaults = MENU_PROCESS_DEFAULT_VISIBLE_FIELDS_BY_KEY.get(
        clean_menu_key,
        [],
    )

    normalized_defaults: list[str] = []
    seen_keys: set[str] = set()

    for raw_key in configured_defaults:
        field_key = str(raw_key or "").strip().lower()

        if not field_key:
            continue

        if field_key in seen_keys:
            continue

        if field_key not in allowed_keys:
            continue

        seen_keys.add(field_key)
        normalized_defaults.append(field_key)

    if normalized_defaults:
        return normalized_defaults

    return [selectable_keys[0]]
    # APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_DEFAULTS_END


def get_menu_process_default_visible_fields(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    return get_menu_process_default_visible_fields_v4(
        menu_key,
        menu_config,
    )


def normalize_menu_process_visible_fields_v4(
    menu_key: str,
    raw_fields: Any = None,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    # APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_NORMALIZE_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    if isinstance(raw_fields, dict) and menu_config is None:
        clean_menu_config = raw_fields
        raw_visible_fields = clean_menu_config.get("process_visible_fields")
    else:
        clean_menu_config = menu_config if isinstance(menu_config, dict) else {}
        raw_visible_fields = raw_fields

    if raw_visible_fields is None:
        raw_visible_fields = clean_menu_config.get("process_visible_fields")

    selectable_options = get_menu_process_selectable_field_options(
        clean_menu_key,
        clean_menu_config,
    )

    allowed_field_keys = {
        str(item.get("key") or "").strip().lower()
        for item in selectable_options
        if str(item.get("key") or "").strip()
    }

    if not allowed_field_keys:
        return []

    has_explicit_config = (
        isinstance(clean_menu_config, dict)
        and (
            "process_visible_fields" in clean_menu_config
            or bool(clean_menu_config.get("process_visible_fields_configured"))
        )
    )

    if isinstance(raw_visible_fields, str):
        raw_items = [
            chunk
            for chunk in re.split(r"[,;\n\r]+", raw_visible_fields)
            if str(chunk or "").strip()
        ]
    elif isinstance(raw_visible_fields, (list, tuple, set)):
        raw_items = list(raw_visible_fields)
    else:
        raw_items = []

    normalized_fields: list[str] = []
    seen_fields: set[str] = set()

    for raw_field in raw_items:
        field_key = str(raw_field or "").strip().lower()

        if not field_key:
            continue

        if field_key in seen_fields:
            continue

        if field_key not in allowed_field_keys:
            continue

        seen_fields.add(field_key)
        normalized_fields.append(field_key)

    if normalized_fields:
        return normalized_fields

    if has_explicit_config and clean_menu_key != "administrativo":
        return []

    return get_menu_process_default_visible_fields(
        clean_menu_key,
        clean_menu_config,
    )
    # APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_NORMALIZE_END


def normalize_menu_process_visible_fields(
    menu_key: str,
    raw_fields: Any = None,
    menu_config: dict[str, Any] | None = None,
) -> list[str]:
    return normalize_menu_process_visible_fields_v4(
        menu_key,
        raw_fields,
        menu_config,
    )

def normalize_meu_perfil_visible_fields(raw_fields: Any) -> list[str]:
    return normalize_menu_process_visible_fields(MENU_MEU_PERFIL_KEY, raw_fields)


def get_menu_process_visible_field_header_map(
    menu_key: str,
    menu_config: dict[str, Any] | None = None,
) -> dict[str, str]:
    if not isinstance(menu_config, dict):
        return {}

    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
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
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
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

    has_explicit_config = False
    if isinstance(menu_config, dict):
        has_explicit_config = bool(menu_config.get("process_visible_fields_configured"))

    if has_explicit_config and clean_menu_key != "administrativo":
        return []

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


# ###################################################################################
# (MEU_PERFIL) REPARO AUTOMATICO DE HEADERS VISIVEIS
# ###################################################################################

def _build_legacy_visible_fields_from_rows_v1(
    rows: list[dict[str, str]],
) -> list[str]:
    legacy_visible_fields: list[str] = []
    emitted_legacy_keys: set[str] = set()
    active_header_key = ""

    for row in rows:
        field_key = str(row.get("field_key") or "").strip().lower()
        header_key = str(row.get("header_key") or "").strip().lower()

        if not field_key:
            continue

        if header_key and header_key != active_header_key:
            if header_key not in emitted_legacy_keys:
                legacy_visible_fields.append(header_key)
                emitted_legacy_keys.add(header_key)

            active_header_key = header_key

        if not header_key:
            active_header_key = ""

        if field_key in emitted_legacy_keys:
            continue

        legacy_visible_fields.append(field_key)
        emitted_legacy_keys.add(field_key)

    return legacy_visible_fields


# ###################################################################################
# (MEU_PERFIL) AUTO-SEED DE CAMPOS DEPARTMENT_MEMBERSHIP_*
# ###################################################################################

def _normalize_seed_required_flag_v1(raw_value: Any) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value or "").strip().lower() in {"1", "true", "sim", "yes", "on"}

def _normalize_seed_toggle_flag_v1(raw_value: Any) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value or "").strip().lower() in {"1", "true", "sim", "yes", "on"}


def _ensure_meu_perfil_department_membership_fields_v1(
    menu_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    if not isinstance(menu_config, dict):
        return {}, False

    updated_menu_config = dict(menu_config)

    additional_fields = normalize_menu_process_additional_fields(
        updated_menu_config.get("additional_fields")
    )

    additional_fields_by_key: dict[str, dict[str, Any]] = {}
    for field in additional_fields:
        clean_key = str(field.get("key") or "").strip().lower()
        if clean_key and clean_key not in additional_fields_by_key:
            additional_fields_by_key[clean_key] = field

    changed = False
    auto_seed_already_applied = _normalize_seed_toggle_flag_v1(
        updated_menu_config.get(
            MENU_CONFIG_MEU_PERFIL_DEPARTMENT_MEMBERSHIP_FIELDS_AUTO_SEEDED_V1_KEY
        )
    )
    process_fields_already_configured = bool(
        updated_menu_config.get("process_visible_fields_configured")
    )
    should_auto_seed_visibility = (
        not auto_seed_already_applied and not process_fields_already_configured
    )

    for raw_seed_field in MENU_MEU_PERFIL_DEPARTMENT_MEMBERSHIP_FIELDS_V1:
        seed_key = _normalize_custom_field_key(raw_seed_field.get("key"))
        seed_label = _normalize_additional_field_label(raw_seed_field.get("label"))
        seed_type = _normalize_additional_field_type(raw_seed_field.get("field_type"))
        seed_size = _normalize_additional_field_size(raw_seed_field.get("size"), seed_type)
        seed_required = _normalize_seed_required_flag_v1(raw_seed_field.get("is_required"))

        if not seed_key or not seed_label:
            continue

        if seed_key in additional_fields_by_key:
            continue

        seed_field_payload: dict[str, Any] = {
            "key": seed_key,
            "label": seed_label,
            "field_type": seed_type,
            "is_required": bool(seed_required and seed_type != "header"),
        }

        if seed_size is not None:
            seed_field_payload["size"] = seed_size

        additional_fields.append(seed_field_payload)
        additional_fields_by_key[seed_key] = seed_field_payload
        changed = True

    updated_menu_config["additional_fields"] = additional_fields

    header_keys = {
        str(field.get("key") or "").strip().lower()
        for field in additional_fields
        if str(field.get("field_type") or "").strip().lower() == "header"
        and str(field.get("key") or "").strip()
    }

    existing_visible_fields: list[str] = []
    seen_visible_fields: set[str] = set()
    for raw_key in (updated_menu_config.get("process_visible_fields") or []):
        field_key = str(raw_key or "").strip().lower()
        if not field_key or field_key in seen_visible_fields:
            continue
        seen_visible_fields.add(field_key)
        existing_visible_fields.append(field_key)

    if not existing_visible_fields:
        for raw_row in (updated_menu_config.get("process_visible_field_rows") or []):
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            if not field_key or field_key in seen_visible_fields:
                continue
            seen_visible_fields.add(field_key)
            existing_visible_fields.append(field_key)

    header_map: dict[str, str] = {}
    for raw_source_map in (
        updated_menu_config.get("process_visible_field_header_map"),
        updated_menu_config.get("visible_field_headers"),
    ):
        if not isinstance(raw_source_map, dict):
            continue
        for raw_field_key, raw_header_key in raw_source_map.items():
            field_key = str(raw_field_key or "").strip().lower()
            header_key = str(raw_header_key or "").strip().lower()
            if not field_key or not header_key:
                continue
            if header_key not in header_keys:
                continue
            header_map[field_key] = header_key

    for raw_row in (updated_menu_config.get("process_visible_field_rows") or []):
        if not isinstance(raw_row, dict):
            continue
        field_key = str(raw_row.get("field_key") or "").strip().lower()
        header_key = str(raw_row.get("header_key") or "").strip().lower()
        if not field_key or not header_key:
            continue
        if header_key not in header_keys:
            continue
        header_map[field_key] = header_key

    if should_auto_seed_visibility:
        seeded_rows: list[dict[str, str]] = []
        for raw_seed_field in MENU_MEU_PERFIL_DEPARTMENT_MEMBERSHIP_FIELDS_V1:
            seed_type = _normalize_additional_field_type(raw_seed_field.get("field_type"))
            if seed_type == "header":
                continue
            field_key = _normalize_custom_field_key(raw_seed_field.get("key"))
            header_key = _normalize_custom_field_key(raw_seed_field.get("header_key"))
            if not field_key:
                continue
            if header_key not in header_keys:
                header_key = ""
            seeded_rows.append({"field_key": field_key, "header_key": header_key})

        for seeded_row in seeded_rows:
            field_key = seeded_row["field_key"]
            header_key = seeded_row["header_key"]
            if field_key not in seen_visible_fields:
                existing_visible_fields.append(field_key)
                seen_visible_fields.add(field_key)
                changed = True
            if header_key and field_key not in header_map:
                header_map[field_key] = header_key
                changed = True

    if not auto_seed_already_applied:
        updated_menu_config[
            MENU_CONFIG_MEU_PERFIL_DEPARTMENT_MEMBERSHIP_FIELDS_AUTO_SEEDED_V1_KEY
        ] = True
        changed = True

    if not changed:
        return dict(menu_config), False

    normalized_rows: list[dict[str, str]] = []
    for field_key in existing_visible_fields:
        normalized_rows.append(
            {
                "field_key": field_key,
                "header_key": str(header_map.get(field_key) or "").strip().lower(),
            }
        )

    process_visible_field_header_map = {
        row["field_key"]: row["header_key"]
        for row in normalized_rows
        if row.get("header_key")
    }

    process_visible_headers: list[str] = []
    seen_headers: set[str] = set()
    for row in normalized_rows:
        header_key = str(row.get("header_key") or "").strip().lower()
        if not header_key or header_key in seen_headers:
            continue
        seen_headers.add(header_key)
        process_visible_headers.append(header_key)

    refresh_token = str(uuid4())
    updated_menu_config["process_visible_fields"] = [
        str(row.get("field_key") or "").strip().lower()
        for row in normalized_rows
        if str(row.get("field_key") or "").strip()
    ]
    updated_menu_config["process_visible_field_header_map"] = process_visible_field_header_map
    updated_menu_config["process_visible_field_rows"] = normalized_rows
    updated_menu_config["process_visible_headers"] = process_visible_headers
    updated_menu_config["process_visible_fields_configured"] = True
    updated_menu_config["process_visible_fields_refresh_version"] = refresh_token
    updated_menu_config["visible_fields"] = _build_legacy_visible_fields_from_rows_v1(
        normalized_rows
    )
    updated_menu_config["visible_field_headers"] = process_visible_field_header_map
    updated_menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = refresh_token
    updated_menu_config[
        MENU_CONFIG_MEU_PERFIL_DEPARTMENT_MEMBERSHIP_FIELDS_AUTO_SEEDED_V1_KEY
    ] = True

    return updated_menu_config, True


# ###################################################################################
# (MEU_PERFIL) COMPAT - MANTER CAMPOS NO PROPRIO PROCESSO
# ###################################################################################

def _migrate_meu_perfil_department_roles_operations_out_v1(
    menu_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    if not isinstance(menu_config, dict):
        return {}, False
    return dict(menu_config), False


# ###################################################################################
# (DEPARTAMENTOS) LIMPEZA DE CAMPOS DEPARTMENT_MEMBERSHIP_*
# ###################################################################################

def _ensure_departamentos_roles_operations_fields_v1(
    menu_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    if not isinstance(menu_config, dict):
        return {}, False

    updated_menu_config = dict(menu_config)

    changed = False

    additional_fields = normalize_menu_process_additional_fields(
        updated_menu_config.get("additional_fields")
    )
    filtered_additional_fields: list[dict[str, Any]] = []
    for raw_field in additional_fields:
        field_key = str(raw_field.get("key") or "").strip().lower()
        if field_key in MENU_DEPARTAMENTOS_FIELDS_SEED_KEYS_V1:
            changed = True
            continue
        filtered_additional_fields.append(raw_field)
    updated_menu_config["additional_fields"] = filtered_additional_fields

    visible_fields: list[str] = []
    seen_visible_fields: set[str] = set()
    for raw_key in (updated_menu_config.get("process_visible_fields") or []):
        field_key = str(raw_key or "").strip().lower()
        if not field_key or field_key in seen_visible_fields:
            continue
        seen_visible_fields.add(field_key)
        if field_key in MENU_DEPARTAMENTOS_FIELDS_SEED_KEYS_V1:
            changed = True
            continue
        visible_fields.append(field_key)

    visible_field_header_map: dict[str, str] = {}
    for raw_map in (
        updated_menu_config.get("process_visible_field_header_map"),
        updated_menu_config.get("visible_field_headers"),
    ):
        if not isinstance(raw_map, dict):
            continue
        for raw_field_key, raw_header_key in raw_map.items():
            field_key = str(raw_field_key or "").strip().lower()
            header_key = str(raw_header_key or "").strip().lower()
            if not field_key:
                continue
            if (
                field_key in MENU_DEPARTAMENTOS_FIELDS_SEED_KEYS_V1
                or header_key in MENU_DEPARTAMENTOS_MEMBERSHIP_HEADERS_V1
            ):
                changed = True
                continue
            visible_field_header_map[field_key] = header_key

    normalized_rows: list[dict[str, str]] = []
    raw_rows = updated_menu_config.get("process_visible_field_rows")
    if isinstance(raw_rows, list):
        for raw_row in raw_rows:
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            header_key = str(raw_row.get("header_key") or "").strip().lower()
            if not field_key:
                continue
            if (
                field_key in MENU_DEPARTAMENTOS_FIELDS_SEED_KEYS_V1
                or header_key in MENU_DEPARTAMENTOS_MEMBERSHIP_HEADERS_V1
            ):
                changed = True
                continue
            normalized_rows.append({"field_key": field_key, "header_key": header_key})
            visible_field_header_map[field_key] = header_key

    if not normalized_rows:
        for field_key in visible_fields:
            normalized_rows.append(
                {
                    "field_key": field_key,
                    "header_key": str(visible_field_header_map.get(field_key) or "").strip().lower(),
                }
            )

    process_visible_field_header_map = {
        row["field_key"]: row["header_key"]
        for row in normalized_rows
        if row.get("header_key")
    }
    process_visible_fields = [
        str(row.get("field_key") or "").strip().lower()
        for row in normalized_rows
        if str(row.get("field_key") or "").strip()
    ]
    process_visible_headers: list[str] = []
    seen_headers: set[str] = set()
    for row in normalized_rows:
        header_key = str(row.get("header_key") or "").strip().lower()
        if (
            not header_key
            or header_key in seen_headers
            or header_key in MENU_DEPARTAMENTOS_MEMBERSHIP_HEADERS_V1
        ):
            continue
        seen_headers.add(header_key)
        process_visible_headers.append(header_key)

    legacy_visible_fields: list[str] = []
    seen_legacy_visible_fields: set[str] = set()
    for raw_key in (updated_menu_config.get("visible_fields") or []):
        field_key = str(raw_key or "").strip().lower()
        if not field_key or field_key in seen_legacy_visible_fields:
            continue
        if (
            field_key in MENU_DEPARTAMENTOS_FIELDS_SEED_KEYS_V1
            or field_key in MENU_DEPARTAMENTOS_MEMBERSHIP_HEADERS_V1
        ):
            changed = True
            continue
        seen_legacy_visible_fields.add(field_key)
        legacy_visible_fields.append(field_key)

    if not changed:
        return dict(menu_config), False

    refresh_token = str(uuid4())
    updated_menu_config["process_visible_fields"] = process_visible_fields
    updated_menu_config["process_visible_field_rows"] = normalized_rows
    updated_menu_config["process_visible_field_header_map"] = process_visible_field_header_map
    updated_menu_config["process_visible_headers"] = process_visible_headers
    updated_menu_config["visible_field_headers"] = process_visible_field_header_map
    updated_menu_config["visible_fields"] = legacy_visible_fields
    updated_menu_config["process_visible_fields_configured"] = True
    updated_menu_config["process_visible_fields_refresh_version"] = refresh_token
    updated_menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = refresh_token
    updated_menu_config[
        MENU_CONFIG_DEPARTAMENTOS_ROLES_OPERATIONS_FIELDS_AUTO_SEEDED_V1_KEY
    ] = True

    return updated_menu_config, True


def _repair_meu_perfil_process_headers_v1(
    menu_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    if not isinstance(menu_config, dict):
        return {}, False

    if bool(menu_config.get(MENU_CONFIG_MEU_PERFIL_HEADERS_AUTO_REPAIRED_V1_KEY)):
        return dict(menu_config), False

    normalized_fields = normalize_menu_process_additional_fields_v1(
        menu_config.get("additional_fields")
    )

    header_order: list[str] = []
    header_label_map: dict[str, str] = {}
    for item in normalized_fields:
        field_type = str(item.get("field_type") or "").strip().lower()
        field_key = str(item.get("key") or "").strip().lower()
        if field_type != "header" or not field_key:
            continue
        header_order.append(field_key)
        header_label_map[field_key] = str(item.get("label") or "").strip()

    if not header_order:
        updated_menu_config = dict(menu_config)
        updated_menu_config[MENU_CONFIG_MEU_PERFIL_HEADERS_AUTO_REPAIRED_V1_KEY] = True
        return updated_menu_config, True

    selectable_keys = {
        str(item.get("key") or "").strip().lower()
        for item in get_menu_process_selectable_field_options(
            MENU_MEU_PERFIL_KEY,
            menu_config,
        )
        if str(item.get("key") or "").strip()
    }
    if not selectable_keys:
        updated_menu_config = dict(menu_config)
        updated_menu_config[MENU_CONFIG_MEU_PERFIL_HEADERS_AUTO_REPAIRED_V1_KEY] = True
        return updated_menu_config, True

    visible_fields_raw = normalize_menu_process_visible_fields(
        MENU_MEU_PERFIL_KEY,
        menu_config.get("visible_fields"),
        menu_config,
    )
    visible_fields: list[str] = []
    seen_visible_fields: set[str] = set()
    for raw_field_key in visible_fields_raw:
        field_key = str(raw_field_key or "").strip().lower()
        if not field_key or field_key in seen_visible_fields:
            continue
        if field_key not in selectable_keys:
            continue
        seen_visible_fields.add(field_key)
        visible_fields.append(field_key)

    if not visible_fields:
        return dict(menu_config), False

    current_header_map = get_menu_process_visible_field_header_map(
        MENU_MEU_PERFIL_KEY,
        menu_config,
    )
    visible_field_headers: dict[str, str] = {}
    for field_key, header_key in current_header_map.items():
        clean_field_key = str(field_key or "").strip().lower()
        clean_header_key = str(header_key or "").strip().lower()
        if not clean_field_key or not clean_header_key:
            continue
        if clean_field_key not in selectable_keys:
            continue
        if clean_header_key not in header_order:
            continue
        visible_field_headers[clean_field_key] = clean_header_key

    used_headers = {
        str(visible_field_headers.get(field_key) or "").strip().lower()
        for field_key in visible_fields
        if str(visible_field_headers.get(field_key) or "").strip()
    }
    missing_headers = [header_key for header_key in header_order if header_key not in used_headers]

    if not missing_headers:
        updated_menu_config = dict(menu_config)
        updated_menu_config[MENU_CONFIG_MEU_PERFIL_HEADERS_AUTO_REPAIRED_V1_KEY] = True
        return updated_menu_config, True

    changed = False
    default_candidate_order = ["nome", "telefone", "email", "pais"]
    morada_candidate_order = ["pais", "telefone", "email", "nome"]
    already_mapped_fields = set(visible_field_headers.keys())

    def resolve_insert_index_v1(target_header_key: str) -> int:
        first_field_index_by_header: dict[str, int] = {}
        for field_index, field_key in enumerate(visible_fields):
            header_key = str(visible_field_headers.get(field_key) or "").strip().lower()
            if not header_key:
                continue
            if header_key not in first_field_index_by_header:
                first_field_index_by_header[header_key] = field_index

        if target_header_key not in header_order:
            return len(visible_fields)

        target_index = header_order.index(target_header_key)
        for next_header_key in header_order[target_index + 1:]:
            if next_header_key in first_field_index_by_header:
                return first_field_index_by_header[next_header_key]

        return len(visible_fields)

    for missing_header_key in missing_headers:
        label_text = str(header_label_map.get(missing_header_key) or "").strip().lower()
        if "morada" in label_text:
            candidate_order = morada_candidate_order
        else:
            candidate_order = default_candidate_order

        target_field_key = ""
        for candidate_key in candidate_order:
            clean_candidate_key = str(candidate_key or "").strip().lower()
            if clean_candidate_key not in selectable_keys:
                continue
            if clean_candidate_key in already_mapped_fields:
                continue
            target_field_key = clean_candidate_key
            break

        if not target_field_key:
            continue

        visible_field_headers[target_field_key] = missing_header_key
        already_mapped_fields.add(target_field_key)
        changed = True

        if target_field_key not in visible_fields:
            insert_index = resolve_insert_index_v1(missing_header_key)
            visible_fields.insert(max(0, min(insert_index, len(visible_fields))), target_field_key)

    if not changed:
        updated_menu_config = dict(menu_config)
        updated_menu_config[MENU_CONFIG_MEU_PERFIL_HEADERS_AUTO_REPAIRED_V1_KEY] = True
        return updated_menu_config, True

    normalized_rows = [
        {
            "field_key": field_key,
            "header_key": str(visible_field_headers.get(field_key) or "").strip().lower(),
        }
        for field_key in visible_fields
    ]

    repaired_header_map = {
        row["field_key"]: row["header_key"]
        for row in normalized_rows
        if row.get("header_key")
    }

    process_visible_headers: list[str] = []
    seen_headers: set[str] = set()
    for row in normalized_rows:
        header_key = str(row.get("header_key") or "").strip().lower()
        if not header_key or header_key in seen_headers:
            continue
        seen_headers.add(header_key)
        process_visible_headers.append(header_key)

    refresh_token = str(uuid4())
    updated_menu_config = dict(menu_config)
    updated_menu_config["process_visible_fields"] = list(visible_fields)
    updated_menu_config["process_visible_field_header_map"] = repaired_header_map
    updated_menu_config["process_visible_field_rows"] = normalized_rows
    updated_menu_config["process_visible_headers"] = process_visible_headers
    updated_menu_config["process_visible_fields_configured"] = True
    updated_menu_config["process_visible_fields_refresh_version"] = refresh_token
    updated_menu_config["visible_fields"] = _build_legacy_visible_fields_from_rows_v1(normalized_rows)
    updated_menu_config["visible_field_headers"] = repaired_header_map
    updated_menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = refresh_token
    updated_menu_config[MENU_CONFIG_MEU_PERFIL_HEADERS_AUTO_REPAIRED_V1_KEY] = True

    return updated_menu_config, True


def _seed_process_fields_all_visible_once_v1(
    menu_key: Any,
    menu_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    if not isinstance(menu_config, dict):
        return {}, False

    if bool(menu_config.get(MENU_CONFIG_PROCESS_FIELDS_SEEDED_ALL_V1_KEY)):
        return dict(menu_config), False

    clean_menu_key = _resolve_legacy_menu_alias(menu_key)

    selectable_options = get_menu_process_selectable_field_options(
        clean_menu_key,
        menu_config,
    )
    selectable_keys_order: list[str] = []
    seen_selectable_keys: set[str] = set()
    for option in selectable_options:
        field_key = str(option.get("key") or "").strip().lower()
        if not field_key or field_key in seen_selectable_keys:
            continue
        seen_selectable_keys.add(field_key)
        selectable_keys_order.append(field_key)

    updated_menu_config = dict(menu_config)

    if not selectable_keys_order:
        updated_menu_config[MENU_CONFIG_PROCESS_FIELDS_SEEDED_ALL_V1_KEY] = True
        return updated_menu_config, True

    header_options = get_menu_process_header_options(clean_menu_key, menu_config)
    header_order: list[str] = []
    header_keys: set[str] = set()
    for option in header_options:
        header_key = str(option.get("key") or "").strip().lower()
        if not header_key or header_key in header_keys:
            continue
        header_keys.add(header_key)
        header_order.append(header_key)

    existing_header_map: dict[str, str] = {}
    for raw_map in (
        menu_config.get("process_visible_field_header_map"),
        menu_config.get("visible_field_headers"),
    ):
        if not isinstance(raw_map, dict):
            continue
        for raw_field_key, raw_header_key in raw_map.items():
            field_key = str(raw_field_key or "").strip().lower()
            header_key = str(raw_header_key or "").strip().lower()
            if field_key in seen_selectable_keys and header_key in header_keys:
                existing_header_map[field_key] = header_key

    process_visible_rows = menu_config.get("process_visible_field_rows")
    if isinstance(process_visible_rows, list):
        for raw_row in process_visible_rows:
            if not isinstance(raw_row, dict):
                continue
            field_key = str(raw_row.get("field_key") or "").strip().lower()
            header_key = str(raw_row.get("header_key") or "").strip().lower()
            if field_key in seen_selectable_keys and header_key in header_keys:
                existing_header_map[field_key] = header_key

    inferred_header_map: dict[str, str] = {}
    additional_fields = normalize_menu_process_additional_fields_v1(
        menu_config.get("additional_fields")
    )
    active_header_key = ""
    for raw_item in additional_fields:
        if not isinstance(raw_item, dict):
            continue
        item_key = str(raw_item.get("key") or "").strip().lower()
        item_type = str(raw_item.get("field_type") or "").strip().lower()
        if item_type == "header":
            active_header_key = item_key if item_key in header_keys else ""
            continue
        if item_key in seen_selectable_keys and active_header_key and item_key not in inferred_header_map:
            inferred_header_map[item_key] = active_header_key

    rows: list[dict[str, str]] = []
    for field_key in selectable_keys_order:
        header_key = str(existing_header_map.get(field_key) or inferred_header_map.get(field_key) or "").strip().lower()
        if header_key not in header_keys:
            header_key = ""
        rows.append({"field_key": field_key, "header_key": header_key})

    if clean_menu_key == MENU_MEU_PERFIL_KEY:
        for row in rows:
            field_key = row["field_key"]
            if row.get("header_key"):
                continue
            if field_key in {"nome", "telefone", "email"} and "custom_dados_pessoais" in header_keys:
                row["header_key"] = "custom_dados_pessoais"
            if field_key == "pais" and "custom_dados_de_morada" in header_keys:
                row["header_key"] = "custom_dados_de_morada"

    used_headers = {
        str(row.get("header_key") or "").strip().lower()
        for row in rows
        if str(row.get("header_key") or "").strip()
    }
    missing_headers = [header_key for header_key in header_order if header_key not in used_headers]
    if missing_headers:
        empty_indexes = [
            index
            for index, row in enumerate(rows)
            if not str(row.get("header_key") or "").strip()
        ]
        for missing_header_key in missing_headers:
            if not empty_indexes:
                break
            chosen_index: int | None = None
            if clean_menu_key == MENU_MEU_PERFIL_KEY and "morada" in missing_header_key:
                for index, row in enumerate(rows):
                    if row["field_key"] == "pais":
                        chosen_index = index
                        break
            if chosen_index is None:
                chosen_index = empty_indexes[0]
            rows[chosen_index]["header_key"] = missing_header_key
            empty_indexes = [
                index
                for index, row in enumerate(rows)
                if not str(row.get("header_key") or "").strip()
            ]

    process_visible_field_header_map = {
        str(row["field_key"]): str(row["header_key"])
        for row in rows
        if str(row.get("header_key") or "").strip()
    }

    process_visible_headers: list[str] = []
    seen_headers: set[str] = set()
    for row in rows:
        header_key = str(row.get("header_key") or "").strip().lower()
        if not header_key or header_key in seen_headers:
            continue
        seen_headers.add(header_key)
        process_visible_headers.append(header_key)

    refresh_token = str(uuid4())
    updated_menu_config["process_visible_fields"] = [str(row["field_key"]) for row in rows]
    updated_menu_config["process_visible_field_rows"] = rows
    updated_menu_config["process_visible_field_header_map"] = process_visible_field_header_map
    updated_menu_config["process_visible_headers"] = process_visible_headers
    updated_menu_config["process_visible_fields_configured"] = True
    updated_menu_config["process_visible_fields_refresh_version"] = refresh_token
    updated_menu_config["visible_fields"] = _build_legacy_visible_fields_from_rows_v1(rows)
    updated_menu_config["visible_field_headers"] = process_visible_field_header_map
    updated_menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = refresh_token
    updated_menu_config[MENU_CONFIG_PROCESS_FIELDS_SEEDED_ALL_V1_KEY] = True

    return updated_menu_config, True


def ensure_sidebar_menu_settings_defaults(session: Session) -> None:
    existing_rows = session.execute(text("SELECT menu_key FROM sidebar_menu_settings")).all()
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
                            THEN 'Meu perfil'
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

    sessoes_menu_label = _normalize_system_menu_label(MENU_SESSOES_KEY, "Estruturas")
    sessoes_row = session.execute(
        text(
            """
            SELECT menu_label, is_active, is_deleted, menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": MENU_SESSOES_KEY},
    ).mappings().first()

    if sessoes_row is not None:
        current_sessoes_config = _parse_menu_config(sessoes_row.get("menu_config"))
        normalized_sessoes_config = _normalize_core_sidebar_menu_config_v1(
            MENU_SESSOES_KEY,
            current_sessoes_config,
        )
        current_sessoes_label = _normalize_system_menu_label(
            MENU_SESSOES_KEY,
            sessoes_row.get("menu_label") or "",
        )
        needs_sessoes_update = (
            not bool(sessoes_row.get("is_active"))
            or bool(sessoes_row.get("is_deleted"))
            or current_sessoes_label in {"", "Sessões", "Sessoes"}
            or json.dumps(current_sessoes_config, ensure_ascii=False, sort_keys=True)
            != json.dumps(normalized_sessoes_config, ensure_ascii=False, sort_keys=True)
        )

        if needs_sessoes_update:
            session.execute(
                text(
                    """
                    UPDATE sidebar_menu_settings
                    SET menu_label = :menu_label,
                        is_active = TRUE,
                        is_deleted = FALSE,
                        menu_config = :menu_config
                    WHERE lower(trim(menu_key)) = :menu_key
                    """
                ),
                {
                    "menu_key": MENU_SESSOES_KEY,
                    "menu_label": sessoes_menu_label,
                    "menu_config": json.dumps(normalized_sessoes_config, ensure_ascii=False),
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
            {"menu_key": MENU_MEU_PERFIL_KEY, "menu_label": "Meu perfil"},
        )
        changed = True

    meu_perfil_config_raw = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE menu_key = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": MENU_MEU_PERFIL_KEY},
    ).scalar_one_or_none()
    meu_perfil_config = _parse_menu_config(meu_perfil_config_raw)
    working_meu_perfil_config, meu_perfil_headers_repaired = _repair_meu_perfil_process_headers_v1(
        meu_perfil_config
    )
    working_meu_perfil_config, meu_perfil_department_fields_seeded = (
        _ensure_meu_perfil_department_membership_fields_v1(
            working_meu_perfil_config
        )
    )
    working_meu_perfil_config, meu_perfil_roles_operations_moved = (
        _migrate_meu_perfil_department_roles_operations_out_v1(
            working_meu_perfil_config
        )
    )
    if (
        meu_perfil_headers_repaired
        or meu_perfil_department_fields_seeded
        or meu_perfil_roles_operations_moved
    ):
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE menu_key = :menu_key
                """
            ),
            {
                "menu_key": MENU_MEU_PERFIL_KEY,
                "menu_config": json.dumps(working_meu_perfil_config, ensure_ascii=False),
            },
        )
        changed = True

    departamentos_row = session.execute(
        text(
            """
            SELECT id, menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": MENU_DEPARTAMENTOS_KEY},
    ).mappings().first()
    if departamentos_row is not None:
        departamentos_config = _parse_menu_config(departamentos_row.get("menu_config"))
        updated_departamentos_config, departamentos_fields_seeded = (
            _ensure_departamentos_roles_operations_fields_v1(
                departamentos_config
            )
        )
        if departamentos_fields_seeded:
            session.execute(
                text(
                    """
                    UPDATE sidebar_menu_settings
                    SET menu_config = :menu_config
                    WHERE lower(trim(menu_key)) = :menu_key
                    """
                ),
                {
                    "menu_key": MENU_DEPARTAMENTOS_KEY,
                    "menu_config": json.dumps(updated_departamentos_config, ensure_ascii=False),
                },
            )
            changed = True

    process_config_rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()
    for process_config_row in process_config_rows:
        clean_menu_key = _resolve_legacy_menu_alias(process_config_row.menu_key)
        if not clean_menu_key:
            continue
        current_menu_config = _parse_menu_config(process_config_row.menu_config)
        seeded_menu_config, seeded_changed = _seed_process_fields_all_visible_once_v1(
            clean_menu_key,
            current_menu_config,
        )
        if not seeded_changed:
            continue
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
                "menu_config": json.dumps(seeded_menu_config, ensure_ascii=False),
            },
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
    if administrativo_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY) != normalized_sidebar_sections:
        administrativo_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = normalized_sidebar_sections
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


# ###################################################################################
# (1.5) INJEÇÃO DINÂMICA DO CAMPO Nº CLIENTE PARA CONTACTO GERAL
# ###################################################################################

def _inject_contacto_geral_n_cliente_config_v1(
    menu_key: str,
    menu_config: dict[str, Any],
    entity_internal_number: object = None,
) -> dict[str, Any]:
    if menu_key != "contacto_geral" or not isinstance(menu_config, dict):
        return menu_config

    updated = dict(menu_config)

    # 1. Inject custom_n_cliente into additional_fields
    add_fields = [dict(f) for f in (updated.get("additional_fields") or [])]
    found_n = False
    for f in add_fields:
        if str(f.get("key") or "").strip().lower() == "custom_n_cliente":
            if entity_internal_number is not None:
                f["value"] = str(entity_internal_number)
            found_n = True
            break

    if not found_n:
        h_idx = -1
        for idx, f in enumerate(add_fields):
            if str(f.get("key") or "").strip().lower() == "custom_dados_membresia":
                h_idx = idx
                break
        n_field = {
            "key": "custom_n_cliente",
            "label": "Nº cliente",
            "field_type": "text",
            "is_required": False,
            "size": 255
        }
        if entity_internal_number is not None:
            n_field["value"] = str(entity_internal_number)
        if h_idx != -1:
            add_fields.insert(h_idx + 1, n_field)
        else:
            add_fields.append(n_field)
    updated["additional_fields"] = add_fields

    # 2. Inject custom_n_cliente into visible_fields
    vis_fields = list(updated.get("visible_fields") or [])
    if "custom_n_cliente" not in vis_fields:
        if "custom_dados_membresia" in vis_fields:
            vis_fields.insert(vis_fields.index("custom_dados_membresia") + 1, "custom_n_cliente")
        else:
            vis_fields.append("custom_n_cliente")
        updated["visible_fields"] = vis_fields

    # 3. Inject into visible_field_headers
    vfh = dict(updated.get("visible_field_headers") or {})
    if "custom_n_cliente" not in vfh:
        vfh["custom_n_cliente"] = "custom_dados_membresia"
        updated["visible_field_headers"] = vfh

    # 4. Inject into process_visible_fields
    pvf = list(updated.get("process_visible_fields") or [])
    if "custom_n_cliente" not in pvf:
        if "custom_dados_membresia" in pvf:
            pvf.insert(pvf.index("custom_dados_membresia") + 1, "custom_n_cliente")
        else:
            pvf.append("custom_n_cliente")
        updated["process_visible_fields"] = pvf

    # 5. Inject into process_visible_field_header_map
    pvfhm = dict(updated.get("process_visible_field_header_map") or {})
    if "custom_n_cliente" not in pvfhm:
        pvfhm["custom_n_cliente"] = "custom_dados_membresia"
        updated["process_visible_field_header_map"] = pvfhm

    # 6. Inject into process_visible_field_rows
    pvfr = list(updated.get("process_visible_field_rows") or [])
    if not any(str(r.get("field_key") or "").strip().lower() == "custom_n_cliente" for r in pvfr):
        target_idx = -1
        for idx, r in enumerate(pvfr):
            if str(r.get("field_key") or "").strip().lower() == "custom_dados_membresia":
                target_idx = idx
                break
        n_row = {
            "field_key": "custom_n_cliente",
            "header_key": "custom_dados_membresia"
        }
        if target_idx != -1:
            pvfr.insert(target_idx + 1, n_row)
        else:
            pvfr.append(n_row)
        updated["process_visible_field_rows"] = pvfr

    return updated


def get_sidebar_menu_settings(
    session: Session,
    selected_entity_id: object = None,
) -> list[dict[str, Any]]:
    ensure_sidebar_menu_settings_defaults(session)
    active_entity_internal_number = None
    if selected_entity_id is not None:
        from appverbo.models.entity import Entity as _Entity
        from sqlalchemy import select
        active_entity_internal_number = session.scalar(
            select(_Entity.internal_number).where(_Entity.id == selected_entity_id)
        )
        if active_entity_internal_number is not None:
            active_entity_internal_number = str(active_entity_internal_number).strip()
    owner_entity_id = get_owner_entity_scope_id_v1(session)
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

        raw_menu_config = _normalize_core_sidebar_menu_config_v1(
            menu_key,
            _normalize_music_menu_config_v1(
                menu_key,
                menu_label,
                _parse_menu_config(None if row is None else row.menu_config),
            ),
        )
        effective_menu_config_scope_id = resolve_menu_effective_config_scope_id_v1(
            menu_key,
            selected_entity_id=selected_entity_id,
            owner_entity_id=owner_entity_id,
            menu_config=raw_menu_config,
        )
        effective_menu_label = build_effective_menu_label_v1(
            menu_label,
            raw_menu_config,
            selected_entity_id=effective_menu_config_scope_id,
        ) or menu_label
        entity_scope_entity_id = resolve_menu_entity_scope_id_v1(
            menu_key,
            selected_entity_id=selected_entity_id,
            owner_entity_id=owner_entity_id,
            menu_config=raw_menu_config,
        )
        menu_config = _normalize_core_sidebar_menu_config_v1(
            menu_key,
            _normalize_music_menu_config_v1(
                menu_key,
                effective_menu_label,
                build_effective_menu_config_v1(
                    raw_menu_config,
                    selected_entity_id=effective_menu_config_scope_id,
                ),
            ),
        )
        menu_config = _inject_contacto_geral_n_cliente_config_v1(menu_key, menu_config, active_entity_internal_number)
        process_additional_fields = get_menu_process_additional_fields(menu_config)
        process_subsequent_fields = menu_config.get("subsequent_fields", [])
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
                "label": effective_menu_label,
                "default_label": _normalize_system_menu_label(
                    menu_key,
                    defaults_by_key[menu_key]["label"],
                ),
                "requires_admin": bool(item["requires_admin"]),
                "is_active": bool(is_active),
                "is_deleted": bool(is_deleted),
                "can_delete": not _is_menu_delete_protected(menu_key, effective_menu_label),
                "menu_config": menu_config,
                "visibility_scopes": get_menu_visibility_scopes(menu_config),
                "visibility_scope_mode": get_menu_visibility_scope_mode(menu_config),
                "visibility_scope_label": get_menu_visibility_scope_label(menu_config),
                "entity_scope_entity_id": entity_scope_entity_id,
                "process_additional_fields": process_additional_fields,
                "process_subsequent_fields": process_subsequent_fields,
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
        raw_menu_config = _normalize_core_sidebar_menu_config_v1(
            menu_key,
            _normalize_music_menu_config_v1(
                menu_key,
                menu_label,
                _parse_menu_config(row.menu_config),
            ),
        )
        effective_menu_config_scope_id = resolve_menu_effective_config_scope_id_v1(
            menu_key,
            selected_entity_id=selected_entity_id,
            owner_entity_id=owner_entity_id,
            menu_config=raw_menu_config,
        )
        effective_menu_label = build_effective_menu_label_v1(
            menu_label,
            raw_menu_config,
            selected_entity_id=effective_menu_config_scope_id,
        ) or menu_label
        entity_scope_entity_id = resolve_menu_entity_scope_id_v1(
            menu_key,
            selected_entity_id=selected_entity_id,
            owner_entity_id=owner_entity_id,
            menu_config=raw_menu_config,
        )
        menu_config = _normalize_core_sidebar_menu_config_v1(
            menu_key,
            _normalize_music_menu_config_v1(
                menu_key,
                effective_menu_label,
                build_effective_menu_config_v1(
                    raw_menu_config,
                    selected_entity_id=effective_menu_config_scope_id,
                ),
            ),
        )
        menu_config = _inject_contacto_geral_n_cliente_config_v1(menu_key, menu_config, active_entity_internal_number)
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
                "label": effective_menu_label,
                "default_label": menu_label,
                "requires_admin": requires_admin,
                "is_active": is_active,
                "is_deleted": is_deleted,
                "can_delete": not _is_menu_delete_protected(menu_key, effective_menu_label),
                "menu_config": menu_config,
                "visibility_scopes": get_menu_visibility_scopes(menu_config),
                "visibility_scope_mode": get_menu_visibility_scope_mode(menu_config),
                "visibility_scope_label": get_menu_visibility_scope_label(menu_config),
                "entity_scope_entity_id": entity_scope_entity_id,
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

    administrativo_row = next(
        (row for row in settings if str(row.get("key") or "").strip().lower() == "administrativo"),
        None,
    )
    sidebar_section_options = normalize_sidebar_sections(
        (administrativo_row or {}).get("menu_config", {}).get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )
    sidebar_section_keys = [
        str(item.get("key") or "").strip().lower()
        for item in sidebar_section_options
        if str(item.get("key") or "").strip()
    ]
    sidebar_section_keys_set = set(sidebar_section_keys)
    sidebar_section_labels_by_key = {
        str(item.get("key") or "").strip().lower(): str(item.get("label") or "").strip()
        for item in sidebar_section_options
        if str(item.get("key") or "").strip()
    }
    sidebar_section_visibility_scopes_by_key = {
        str(item.get("key") or "").strip().lower(): normalize_menu_visibility_scopes(
            item.get("visibility_scopes")
        )
        for item in sidebar_section_options
        if str(item.get("key") or "").strip()
    }
    sidebar_section_visibility_scope_mode_by_key = {
        str(item.get("key") or "").strip().lower(): get_sidebar_section_visibility_scope_mode(
            item
        )
        for item in sidebar_section_options
        if str(item.get("key") or "").strip()
    }
    sidebar_section_visibility_scope_label_by_key = {
        str(item.get("key") or "").strip().lower(): get_sidebar_section_visibility_scope_label(
            item
        )
        for item in sidebar_section_options
        if str(item.get("key") or "").strip()
    }
    sidebar_section_status_by_key = {
        str(item.get("key") or "").strip().lower(): _normalize_sidebar_section_status_v5(
            item.get("status") if item.get("status") is not None else item.get("is_active")
        )
        for item in sidebar_section_options
        if str(item.get("key") or "").strip()
    }
    for setting_row in settings:
        clean_menu_key = str(setting_row.get("key") or "").strip().lower()
        menu_config = setting_row.get("menu_config")
        if isinstance(menu_config, dict):
            configured_section_key = _normalize_sidebar_section_key(
                menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY)
            )
        else:
            configured_section_key = ""
        if configured_section_key not in sidebar_section_keys_set:
            configured_section_key = _resolve_default_sidebar_section_key(
                clean_menu_key,
                sidebar_section_keys_set,
                sidebar_section_keys,
            )
        setting_row["sidebar_section_key"] = configured_section_key
        sidebar_section_status = sidebar_section_status_by_key.get(configured_section_key, "ativo")
        setting_row["sidebar_section_label"] = (
            sidebar_section_labels_by_key.get(configured_section_key)
            or SIDEBAR_SECTION_DEFAULTS_BY_KEY.get(configured_section_key)
            or configured_section_key
        )
        setting_row["sidebar_section_visibility_scopes"] = list(
            sidebar_section_visibility_scopes_by_key.get(
                configured_section_key,
                list(MENU_VISIBILITY_SCOPES),
            )
        )
        setting_row["sidebar_section_visibility_scope_mode"] = (
            sidebar_section_visibility_scope_mode_by_key.get(configured_section_key)
            or MENU_VISIBILITY_SCOPE_ALL
        )
        setting_row["sidebar_section_visibility_scope_label"] = (
            sidebar_section_visibility_scope_label_by_key.get(configured_section_key)
            or _resolve_visibility_scope_label_from_mode(MENU_VISIBILITY_SCOPE_ALL)
        )
        setting_row["sidebar_section_status"] = sidebar_section_status
        setting_row["sidebar_section_is_active"] = sidebar_section_status == "ativo"

    for setting in settings:
        clean_setting_key = _normalize_menu_key(setting.get("key"))
        setting_row = db_by_key.get(clean_setting_key)
        section_config = _parse_menu_config(None if setting_row is None else setting_row.menu_config)

        # Prioriza o mapeamento atual por secao do sidebar para manter coerencia
        # entre o formulario de edicao e a listagem de menus.
        sidebar_section_key = _normalize_sidebar_section_key(setting.get("sidebar_section_key"))
        sidebar_section_label = str(setting.get("sidebar_section_label") or "").strip()

        if sidebar_section_key:
            setting["menu_section"] = sidebar_section_key
            setting["menu_section_label"] = sidebar_section_label or get_menu_section_label(
                sidebar_section_key
            )
            continue

        # Fallback legado: usa o menu_section historico quando nao existir secao.
        section_key = normalize_menu_section_key(
            section_config.get("menu_section"),
            clean_setting_key,
        )
        setting["menu_section"] = section_key
        setting["menu_section_label"] = get_menu_section_label(section_key)


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
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
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
    selected_entity_id: object = None,
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
        if not is_sidebar_menu_section_visible_v1(
            item,
            current_entity_scope=clean_entity_scope,
        ):
            continue
        if not is_sidebar_menu_entity_scope_visible_v1(
            record_entity_id=item.get("entity_scope_entity_id"),
            selected_entity_id=selected_entity_id,
        ):
            continue
        visible_keys.add(str(item["key"]))
    if "home" not in visible_keys:
        visible_keys.add("home")
    return visible_keys


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
    return _normalize_core_sidebar_menu_config_v1(
        clean_menu_key,
        _parse_menu_config(raw_menu_config),
    )


def _persist_menu_config(session: Session, menu_key: str, menu_config: dict[str, Any]) -> None:
    session.execute(
        text(
            """
            UPDATE sidebar_menu_settings
            SET menu_config = :menu_config
            WHERE lower(trim(menu_key)) = :menu_key
            """
        ),
        {
            "menu_key": menu_key,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )


def set_sidebar_menu_visibility(session: Session, menu_key: str, make_visible: bool) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
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
    sidebar_section_key: str | None = None,
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    clean_menu_label = _normalize_sentence_case_text(menu_label)
    ensure_sidebar_menu_settings_defaults(session)
    if not _menu_exists(session, clean_menu_key):
        return False, "Menu inválido."
    if not clean_menu_label:
        return False, "Nome do menu é obrigatório."

    menu_config = _load_menu_config(session, clean_menu_key)
    selected_entity_id = resolve_menu_effective_config_scope_id_v1(
        clean_menu_key,
        selected_entity_id=selected_entity_id,
        owner_entity_id=get_owner_entity_scope_id_v1(session),
        menu_config=menu_config,
    )
    effective_menu_config = build_effective_menu_config_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
    )
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

    administrative_config = _load_menu_config(session, "administrativo")
    section_options = normalize_sidebar_sections(
        administrative_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )
    section_keys = [
        str(item.get("key") or "").strip().lower()
        for item in section_options
        if str(item.get("key") or "").strip()
    ]
    section_keys_set = set(section_keys)
    requested_section_key = _normalize_sidebar_section_key(sidebar_section_key)
    if requested_section_key:
        if requested_section_key not in section_keys_set:
            return False, "Sessão inválida."
        resolved_section_key = requested_section_key
    elif section_keys:
        current_section_key = _normalize_sidebar_section_key(
            effective_menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY)
        )
        if current_section_key not in section_keys_set:
            resolved_section_key = _resolve_default_sidebar_section_key(
                clean_menu_key,
                section_keys_set,
                section_keys,
            )
        else:
            resolved_section_key = current_section_key

    if not section_keys:
        resolved_section_key = ""

    if selected_entity_id is None:
        if resolved_section_key:
            menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = resolved_section_key
        _persist_menu_config(session, clean_menu_key, menu_config)
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_label = :menu_label
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": clean_menu_key,
                "menu_label": clean_menu_label,
            },
        )
    else:
        scoped_updates: dict[str, Any] = {
            MENU_CONFIG_SCOPE_MENU_LABEL_KEY_V1: clean_menu_label,
        }
        if resolved_section_key:
            scoped_updates[MENU_CONFIG_SIDEBAR_SECTION_KEY] = resolved_section_key

        menu_config = apply_entity_scoped_menu_config_updates_v1(
            menu_config,
            selected_entity_id=selected_entity_id,
            updates=scoped_updates,
        )
        _persist_menu_config(session, clean_menu_key, menu_config)

    session.commit()
    return True, ""


def update_sidebar_menu_sidebar_sections(
    session: Session,
    sidebar_sections: list[Any] | tuple[Any, ...] | set[Any] | str,
    menu_section_map: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    ensure_sidebar_menu_settings_defaults(session)
    normalized_sidebar_sections = normalize_sidebar_sections(sidebar_sections)
    section_keys = [
        str(item.get("key") or "").strip().lower()
        for item in normalized_sidebar_sections
        if str(item.get("key") or "").strip()
    ]
    section_keys_set = set(section_keys)
    if not section_keys:
        return False, "Defina ao menos uma sessão do sidebar."

    normalized_section_map: dict[str, str] = {}
    if isinstance(menu_section_map, dict):
        for raw_menu_key, raw_section_key in menu_section_map.items():
            clean_menu_key = _normalize_menu_key(raw_menu_key)
            clean_section_key = _normalize_sidebar_section_key(raw_section_key)
            if not clean_menu_key:
                continue
            normalized_section_map[clean_menu_key] = clean_section_key

    settings = get_sidebar_menu_settings(session)
    changed = False

    administrativo_config = _load_menu_config(session, "administrativo")
    if administrativo_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY) != normalized_sidebar_sections:
        administrativo_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = normalized_sidebar_sections
        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_config = :menu_config
                WHERE lower(trim(menu_key)) = 'administrativo'
                """
            ),
            {"menu_config": json.dumps(administrativo_config, ensure_ascii=False)},
        )
        changed = True

    # When no explicit menu->section mapping is sent, this operation manages only
    # the session definitions and must not reassign menus.
    should_update_menu_mapping = bool(normalized_section_map)

    if should_update_menu_mapping:
        for setting_row in settings:
            clean_menu_key = _normalize_menu_key(setting_row.get("key"))
            if not clean_menu_key:
                continue
            desired_section_key = _normalize_sidebar_section_key(
                normalized_section_map.get(clean_menu_key)
            )
            if desired_section_key not in section_keys_set:
                desired_section_key = _resolve_default_sidebar_section_key(
                    clean_menu_key,
                    section_keys_set,
                    section_keys,
                )
            if not desired_section_key:
                continue

            menu_config = _load_menu_config(session, clean_menu_key)
            current_section_key = _normalize_sidebar_section_key(
                menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY)
            )
            if current_section_key == desired_section_key:
                continue

            menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = desired_section_key
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
    return True, ""




def update_sidebar_menu_process_fields_v4(
    session: Session,
    menu_key: str,
    visible_fields: list[str] | tuple[str, ...] | set[str],
    visible_headers: list[str] | tuple[str, ...] | set[str] | None = None,
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    # APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_PROCESS_FIELDS_SAVE_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    selected_entity_id = resolve_menu_selected_entity_scope_id_v1(
        clean_menu_key,
        selected_entity_id,
    )

    if not clean_menu_key:
        return False, "Menu inválido."


    ensure_sidebar_menu_settings_defaults(session)

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    menu_config = _load_menu_config(session, clean_menu_key)
    effective_menu_config = build_effective_menu_config_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
    )

    selectable_options = get_menu_process_selectable_field_options(
        clean_menu_key,
        effective_menu_config,
    )
    header_options = get_menu_process_header_options(
        clean_menu_key,
        effective_menu_config,
    )

    selectable_keys = {
        str(item.get("key") or "").strip().lower()
        for item in selectable_options
        if str(item.get("key") or "").strip()
    }
    header_keys = {
        str(item.get("key") or "").strip().lower()
        for item in header_options
        if str(item.get("key") or "").strip()
    }

    if not selectable_keys and not header_keys:
        return False, "Este processo não possui campos configuráveis."

    raw_visible_fields = (
        list(visible_fields)
        if isinstance(visible_fields, (list, tuple, set))
        else []
    )
    raw_visible_headers = (
        list(visible_headers)
        if isinstance(visible_headers, (list, tuple, set))
        else []
    )

    # APPVERBO_PROCESS_FIELDS_PRESERVE_HEADERS_V13_START
    existing_header_map: dict[str, str] = {}

    existing_rows = effective_menu_config.get("process_visible_field_rows")
    if isinstance(existing_rows, list):
        for existing_row in existing_rows:
            if not isinstance(existing_row, dict):
                continue

            existing_field_key = str(existing_row.get("field_key") or "").strip().lower()
            existing_header_key = str(existing_row.get("header_key") or "").strip().lower()

            if existing_field_key and existing_header_key:
                existing_header_map[existing_field_key] = existing_header_key

    existing_process_header_map = effective_menu_config.get("process_visible_field_header_map")
    if isinstance(existing_process_header_map, dict):
        for raw_field_key, raw_header_key in existing_process_header_map.items():
            existing_field_key = str(raw_field_key or "").strip().lower()
            existing_header_key = str(raw_header_key or "").strip().lower()

            if existing_field_key and existing_header_key:
                existing_header_map[existing_field_key] = existing_header_key

    existing_legacy_header_map = effective_menu_config.get("visible_field_headers")
    if isinstance(existing_legacy_header_map, dict):
        for raw_field_key, raw_header_key in existing_legacy_header_map.items():
            existing_field_key = str(raw_field_key or "").strip().lower()
            existing_header_key = str(raw_header_key or "").strip().lower()

            if existing_field_key and existing_header_key:
                existing_header_map[existing_field_key] = existing_header_key

    incoming_has_any_header = any(
        str(raw_header_key or "").strip()
        for raw_header_key in raw_visible_headers
    )

    should_preserve_existing_headers = (
        not incoming_has_any_header
        and bool(existing_header_map)
    )
    # APPVERBO_PROCESS_FIELDS_PRESERVE_HEADERS_V13_END

    normalized_rows: list[dict[str, str]] = []
    seen_fields: set[str] = set()

    for row_index, raw_field in enumerate(raw_visible_fields):
        field_key = str(raw_field or "").strip().lower()

        if not field_key:
            continue

        if field_key in seen_fields:
            continue

        if field_key not in selectable_keys:
            continue

        header_key = (
            str(raw_visible_headers[row_index] if row_index < len(raw_visible_headers) else "")
            .strip()
            .lower()
        )

        if header_key not in header_keys:
            header_key = ""

        # APPVERBO_PROCESS_FIELDS_RESTORE_HEADER_ON_BLANK_SUBMIT_V13_START
        if not header_key and should_preserve_existing_headers:
            header_key = existing_header_map.get(field_key, "")

            if header_key not in header_keys:
                header_key = ""
        # APPVERBO_PROCESS_FIELDS_RESTORE_HEADER_ON_BLANK_SUBMIT_V13_END

        seen_fields.add(field_key)
        normalized_rows.append(
            {
                "field_key": field_key,
                "header_key": header_key,
            }
        )

    process_visible_fields = [
        row["field_key"]
        for row in normalized_rows
    ]

    process_visible_field_header_map = {
        row["field_key"]: row["header_key"]
        for row in normalized_rows
        if row.get("header_key")
    }

    legacy_visible_fields: list[str] = []
    emitted_legacy_keys: set[str] = set()
    active_header_key = ""

    for row in normalized_rows:
        field_key = row["field_key"]
        header_key = row["header_key"]

        if header_key and header_key != active_header_key:
            if header_key not in emitted_legacy_keys:
                legacy_visible_fields.append(header_key)
                emitted_legacy_keys.add(header_key)

            active_header_key = header_key

        if not header_key:
            active_header_key = ""

        if field_key in emitted_legacy_keys:
            continue

        legacy_visible_fields.append(field_key)
        emitted_legacy_keys.add(field_key)

    refresh_token = str(uuid4())

    menu_config = apply_entity_scoped_menu_config_updates_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
        updates={
            "process_visible_fields": process_visible_fields,
            "process_visible_field_header_map": process_visible_field_header_map,
            "process_visible_field_rows": normalized_rows,
            "process_visible_fields_configured": True,
            "process_visible_fields_refresh_version": refresh_token,
            "visible_fields": legacy_visible_fields,
            "visible_field_headers": process_visible_field_header_map,
            MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY: refresh_token,
        },
    )

    if selected_entity_id is not None:
        menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = refresh_token

    _persist_menu_config(session, clean_menu_key, menu_config)
    session.commit()

    return True, ""
    # APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_PROCESS_FIELDS_SAVE_END


def update_sidebar_menu_process_fields(
    session: Session,
    menu_key: str,
    visible_fields: list[str] | tuple[str, ...] | set[str],
    visible_headers: list[str] | tuple[str, ...] | set[str] | None = None,
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    return update_sidebar_menu_process_fields_v4(
        session,
        menu_key,
        visible_fields,
        visible_headers,
        selected_entity_id,
    )

def update_sidebar_menu_process_lists(
    session: Session,
    menu_key: str,
    raw_lists: Any,
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    selected_entity_id = resolve_menu_selected_entity_scope_id_v1(
        clean_menu_key,
        selected_entity_id,
    )

    if not clean_menu_key:
        return False, "Menu inválido."

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    menu_config = _load_menu_config(session, clean_menu_key)
    normalized_lists = normalize_menu_process_lists_v3(raw_lists)
    menu_config = apply_entity_scoped_menu_config_updates_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
        updates={"process_lists": normalized_lists},
    )
    _persist_menu_config(session, clean_menu_key, menu_config)
    session.commit()
    return True, ""


def update_sidebar_menu_additional_fields(
    session: Session,
    menu_key: str,
    additional_fields: list[dict[str, Any]] | tuple[dict[str, Any], ...] | set[Any] | list[str] | tuple[str, ...],
) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
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

    clean_menu_key = _resolve_legacy_menu_alias(_build_menu_key_from_label(clean_menu_label))
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
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
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


####################################################################################
# HOTFIX V2 - CRIACAO DE PASTA COM REATIVACAO DE REGISTO ELIMINADO
####################################################################################

def create_sidebar_menu_setting_v2(
    session: Session,
    menu_label: str,
    visibility_scope_mode: str = "all",
) -> tuple[bool, str, str]:
    ####################################################################################
    # (1) NORMALIZAR NOME E CHAVE DA PASTA
    ####################################################################################

    clean_menu_label = _normalize_sentence_case_text(menu_label)
    if not clean_menu_label:
        return False, "Informe o nome da pasta.", ""

    clean_menu_key = _resolve_legacy_menu_alias(_build_menu_key_from_label(clean_menu_label))
    if not clean_menu_key:
        return False, "Informe um nome valido para a pasta.", ""

    ####################################################################################
    # (2) CALCULAR PROXIMA ORDEM DE EXIBICAO
    ####################################################################################

    def _next_display_order_v2() -> int:
        rows = session.execute(
            text(
                """
                SELECT menu_config
                FROM sidebar_menu_settings
                """
            )
        ).all()

        max_display_order = -1
        for row in rows:
            menu_config = _parse_menu_config(row.menu_config)
            display_order = _normalize_menu_display_order(
                menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY)
            )
            if display_order is not None:
                max_display_order = max(max_display_order, display_order)

        return max_display_order + 1

    ####################################################################################
    # (3) MONTAR OU ATUALIZAR CONFIGURACAO DA PASTA
    ####################################################################################

    def _build_menu_config_v2(existing_config: dict[str, Any] | None = None) -> dict[str, Any]:
        menu_config = dict(existing_config or {})

        menu_config["requires_admin"] = True
        menu_config["visibility_scopes"] = normalize_menu_visibility_scopes(
            visibility_scope_mode
        )

        if not isinstance(menu_config.get("additional_fields"), list):
            menu_config["additional_fields"] = []

        if not isinstance(menu_config.get("visible_fields"), list):
            menu_config["visible_fields"] = []

        if not isinstance(menu_config.get("visible_field_headers"), dict):
            menu_config["visible_field_headers"] = {}

        display_order = _normalize_menu_display_order(
            menu_config.get(MENU_CONFIG_DISPLAY_ORDER_KEY)
        )
        if display_order is None:
            menu_config[MENU_CONFIG_DISPLAY_ORDER_KEY] = _next_display_order_v2()

        if not str(menu_config.get("menu_section") or "").strip():
            menu_config["menu_section"] = "igreja"

        if not str(menu_config.get("sidebar_section") or "").strip():
            menu_config["sidebar_section"] = menu_config.get("menu_section") or "igreja"

        return menu_config

    ####################################################################################
    # (4) PROCURAR REGISTO EXISTENTE, INCLUINDO ELIMINADOS
    ####################################################################################

    existing_row = session.execute(
        text(
            """
            SELECT menu_key, menu_label, is_active, is_deleted, menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
               OR lower(trim(menu_label)) = :menu_label
            ORDER BY
                CASE WHEN lower(trim(menu_key)) = :menu_key THEN 0 ELSE 1 END,
                CASE WHEN COALESCE(is_deleted, false) THEN 1 ELSE 0 END
            LIMIT 1
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_label": clean_menu_label.strip().lower(),
        },
    ).mappings().first()

    ####################################################################################
    # (5) SE EXISTE ATIVO, BLOQUEAR
    ####################################################################################

    if existing_row is not None and not bool(existing_row.get("is_deleted")):
        return (
            False,
            "Ja existe uma pasta com este nome.",
            str(existing_row.get("menu_key") or clean_menu_key),
        )

    ####################################################################################
    # (6) SE EXISTE ELIMINADO, REATIVAR
    ####################################################################################

    if existing_row is not None and bool(existing_row.get("is_deleted")):
        existing_menu_key = str(existing_row.get("menu_key") or clean_menu_key).strip().lower()
        existing_config = _parse_menu_config(existing_row.get("menu_config"))
        menu_config = _build_menu_config_v2(existing_config)

        session.execute(
            text(
                """
                UPDATE sidebar_menu_settings
                SET menu_label = :menu_label,
                    is_active = :is_active,
                    is_deleted = :is_deleted,
                    menu_config = :menu_config
                WHERE lower(trim(menu_key)) = :menu_key
                """
            ),
            {
                "menu_key": existing_menu_key,
                "menu_label": clean_menu_label,
                "is_active": True,
                "is_deleted": False,
                "menu_config": json.dumps(menu_config, ensure_ascii=False),
            },
        )
        session.commit()
        return True, "", existing_menu_key

    ####################################################################################
    # (7) SE NAO EXISTE, CRIAR NOVA PASTA
    ####################################################################################

    menu_config = _build_menu_config_v2({})

    session.execute(
        text(
            """
            INSERT INTO sidebar_menu_settings
                (menu_key, menu_label, is_active, is_deleted, menu_config)
            VALUES
                (:menu_key, :menu_label, :is_active, :is_deleted, :menu_config)
            """
        ),
        {
            "menu_key": clean_menu_key,
            "menu_label": clean_menu_label,
            "is_active": True,
            "is_deleted": False,
            "menu_config": json.dumps(menu_config, ensure_ascii=False),
        },
    )
    session.commit()

    return True, "", clean_menu_key


# Mantem compatibilidade com os imports existentes.
create_sidebar_menu_setting = create_sidebar_menu_setting_v2

####################################################################################
# LISTA V1 - LISTAS REUTILIZÁVEIS DO PROCESSO
####################################################################################

def _normalize_process_list_key_v1(raw_key: Any) -> str:
    clean_key = str(raw_key or "").strip().lower()
    clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
    clean_key = re.sub(r"_+", "_", clean_key).strip("_")

    if not clean_key:
        return ""

    if not clean_key.startswith("list_"):
        clean_key = f"list_{clean_key}"

    return clean_key


def _build_process_list_key_from_label_v1(label: str) -> str:
    base_key = _build_menu_key_from_label(label)

    if not base_key:
        base_key = "lista"

    return _normalize_process_list_key_v1(base_key)


def _normalize_process_list_items_csv_v1(raw_items: Any) -> list[str]:
    if isinstance(raw_items, str):
        raw_values = raw_items.split(",")
    elif isinstance(raw_items, (list, tuple, set)):
        raw_values = []
        for item in raw_items:
            if isinstance(item, str) and "," in item:
                raw_values.extend(item.split(","))
            else:
                raw_values.append(item)
    else:
        raw_values = []

    normalized: list[str] = []
    seen: set[str] = set()

    for raw_value in raw_values:
        clean_value = " ".join(str(raw_value or "").strip().split())

        if not clean_value:
            continue

        lookup_key = clean_value.lower()

        if lookup_key in seen:
            continue

        seen.add(lookup_key)
        normalized.append(clean_value)

    return normalized


def normalize_menu_process_lists_v1(raw_lists: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_lists, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_labels: set[str] = set()

    for raw_item in raw_lists:
        if not isinstance(raw_item, dict):
            continue

        label = _normalize_sentence_case_text(raw_item.get("label", raw_item.get("name")))

        if not label:
            continue

        label_lookup = label.lower()

        if label_lookup in seen_labels:
            continue

        seen_labels.add(label_lookup)

        list_key = (
            _normalize_process_list_key_v1(raw_item.get("key"))
            or _build_process_list_key_from_label_v1(label)
        )

        base_key = list_key
        suffix = 2

        while list_key in seen_keys:
            list_key = f"{base_key}_{suffix}"
            suffix += 1

        seen_keys.add(list_key)

        items = _normalize_process_list_items_csv_v1(
            raw_item.get("items_csv", raw_item.get("items"))
        )

        normalized.append(
            {
                "key": list_key,
                "label": label,
                "items": items,
                "items_csv": ", ".join(items),
            }
        )

    return normalized


def get_menu_process_lists_v1(menu_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not isinstance(menu_config, dict):
        return []

    return normalize_menu_process_lists_v1(menu_config.get("process_lists"))


if "_original_normalize_menu_process_additional_fields_for_list_v1" not in globals():
    _original_normalize_menu_process_additional_fields_for_list_v1 = normalize_menu_process_additional_fields


def normalize_menu_process_additional_fields_v2(raw_fields: Any) -> list[dict[str, Any]]:
    normalized = _original_normalize_menu_process_additional_fields_for_list_v1(raw_fields)

    if not isinstance(raw_fields, (list, tuple, set)):
        return normalized

    raw_by_key: dict[str, dict[str, Any]] = {}
    raw_by_label: dict[str, dict[str, Any]] = {}
    raw_by_index: dict[int, dict[str, Any]] = {}

    for index, raw_item in enumerate(raw_fields):
        if not isinstance(raw_item, dict):
            continue

        raw_by_index[index] = raw_item

        raw_key = _normalize_custom_field_key(str(raw_item.get("key") or ""))

        if raw_key:
            raw_by_key[raw_key] = raw_item

        raw_label = _normalize_additional_field_label(raw_item.get("label"))

        if raw_label:
            raw_by_label[raw_label.lower()] = raw_item

    for index, item in enumerate(normalized):
        if str(item.get("field_type") or "").strip().lower() != "list":
            item.pop("list_key", None)
            continue

        item_key = str(item.get("key") or "").strip().lower()
        item_label = str(item.get("label") or "").strip().lower()

        raw_item = (
            raw_by_key.get(item_key)
            or raw_by_label.get(item_label)
            or raw_by_index.get(index)
            or {}
        )

        item["list_key"] = _normalize_process_list_key_v1(
            raw_item.get("list_key", raw_item.get("process_list_key", raw_item.get("lista")))
        )

    return normalized


normalize_menu_process_additional_fields = normalize_menu_process_additional_fields_v2


if "_original_get_sidebar_menu_settings_for_lists_v1" not in globals():
    _original_get_sidebar_menu_settings_for_lists_v1 = get_sidebar_menu_settings


def get_sidebar_menu_settings_v2(
    session: Session,
    selected_entity_id: object = None,
) -> list[dict[str, Any]]:
    settings = _original_get_sidebar_menu_settings_for_lists_v1(
        session,
        selected_entity_id=selected_entity_id,
    )

    rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()

    config_by_key = {
        _normalize_menu_key(row.menu_key): _parse_menu_config(row.menu_config)
        for row in rows
        if _normalize_menu_key(row.menu_key)
    }

    for item in settings:
        clean_key = _normalize_menu_key(item.get("key"))
        menu_config = config_by_key.get(clean_key, {})
        process_lists = get_menu_process_lists_v1(menu_config)
        item["process_lists"] = process_lists
        item["process_list_options"] = [
            {"key": process_list["key"], "label": process_list["label"]}
            for process_list in process_lists
        ]

    return settings


get_sidebar_menu_settings = get_sidebar_menu_settings_v2

####################################################################################
# LISTA V2 - LISTAS REUTILIZÁVEIS DO PROCESSO
####################################################################################

def _normalize_process_list_key_v2(raw_key: Any) -> str:
    clean_key = str(raw_key or "").strip().lower()
    clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
    clean_key = re.sub(r"_+", "_", clean_key).strip("_")

    if not clean_key:
        return ""

    if not clean_key.startswith("list_"):
        clean_key = f"list_{clean_key}"

    return clean_key


def _build_process_list_key_from_label_v2(label: str) -> str:
    base_key = _build_menu_key_from_label(label)

    if not base_key:
        base_key = "lista"

    return _normalize_process_list_key_v2(base_key)


def _normalize_process_list_items_csv_v2(raw_items: Any) -> list[str]:
    if isinstance(raw_items, str):
        raw_values = raw_items.split(",")
    elif isinstance(raw_items, (list, tuple, set)):
        raw_values = []
        for item in raw_items:
            if isinstance(item, str) and "," in item:
                raw_values.extend(item.split(","))
            else:
                raw_values.append(item)
    else:
        raw_values = []

    normalized: list[str] = []
    seen: set[str] = set()

    for raw_value in raw_values:
        clean_value = " ".join(str(raw_value or "").strip().split())

        if not clean_value:
            continue

        lookup_key = clean_value.lower()

        if lookup_key in seen:
            continue

        seen.add(lookup_key)
        normalized.append(clean_value)

    return normalized


def normalize_menu_process_lists_v2(raw_lists: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_lists, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_labels: set[str] = set()

    for raw_item in raw_lists:
        if not isinstance(raw_item, dict):
            continue

        label = _normalize_sentence_case_text(raw_item.get("label", raw_item.get("name")))

        if not label:
            continue

        label_lookup = label.lower()

        if label_lookup in seen_labels:
            continue

        seen_labels.add(label_lookup)

        list_key = (
            _normalize_process_list_key_v2(raw_item.get("key"))
            or _build_process_list_key_from_label_v2(label)
        )

        base_key = list_key
        suffix = 2

        while list_key in seen_keys:
            list_key = f"{base_key}_{suffix}"
            suffix += 1

        seen_keys.add(list_key)

        items = _normalize_process_list_items_csv_v2(
            raw_item.get("items_csv", raw_item.get("items"))
        )

        normalized.append(
            {
                "key": list_key,
                "label": label,
                "items": items,
                "items_csv": ", ".join(items),
            }
        )

    return normalized


def get_menu_process_lists_v2(menu_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not isinstance(menu_config, dict):
        return []

    return normalize_menu_process_lists_v2(menu_config.get("process_lists"))


if "_original_normalize_menu_process_additional_fields_for_list_v2" not in globals():
    _original_normalize_menu_process_additional_fields_for_list_v2 = normalize_menu_process_additional_fields


def normalize_menu_process_additional_fields_v3(raw_fields: Any) -> list[dict[str, Any]]:
    normalized = _original_normalize_menu_process_additional_fields_for_list_v2(raw_fields)

    if not isinstance(raw_fields, (list, tuple, set)):
        return normalized

    raw_by_key: dict[str, dict[str, Any]] = {}
    raw_by_label: dict[str, dict[str, Any]] = {}
    raw_by_index: dict[int, dict[str, Any]] = {}

    for index, raw_item in enumerate(raw_fields):
        if not isinstance(raw_item, dict):
            continue

        raw_by_index[index] = raw_item

        raw_key = _normalize_custom_field_key(str(raw_item.get("key") or ""))

        if raw_key:
            raw_by_key[raw_key] = raw_item

        raw_label = _normalize_additional_field_label(raw_item.get("label"))

        if raw_label:
            raw_by_label[raw_label.lower()] = raw_item

    for index, item in enumerate(normalized):
        if str(item.get("field_type") or "").strip().lower() != "list":
            item.pop("list_key", None)
            continue

        item_key = str(item.get("key") or "").strip().lower()
        item_label = str(item.get("label") or "").strip().lower()

        raw_item = (
            raw_by_key.get(item_key)
            or raw_by_label.get(item_label)
            or raw_by_index.get(index)
            or {}
        )

        item["list_key"] = _normalize_process_list_key_v2(
            raw_item.get("list_key", raw_item.get("process_list_key", raw_item.get("lista")))
        )

    return normalized


normalize_menu_process_additional_fields = normalize_menu_process_additional_fields_v3


if "_original_get_sidebar_menu_settings_for_lists_v2" not in globals():
    _original_get_sidebar_menu_settings_for_lists_v2 = get_sidebar_menu_settings


def get_sidebar_menu_settings_v3(
    session: Session,
    selected_entity_id: object = None,
) -> list[dict[str, Any]]:
    settings = _original_get_sidebar_menu_settings_for_lists_v2(
        session,
        selected_entity_id=selected_entity_id,
    )

    rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()

    config_by_key = {
        _normalize_menu_key(row.menu_key): _parse_menu_config(row.menu_config)
        for row in rows
        if _normalize_menu_key(row.menu_key)
    }

    for item in settings:
        clean_key = _normalize_menu_key(item.get("key"))
        menu_config = config_by_key.get(clean_key, {})
        process_lists = get_menu_process_lists_v2(menu_config)
        item["process_lists"] = process_lists
        item["process_list_options"] = [
            {"key": process_list["key"], "label": process_list["label"]}
            for process_list in process_lists
        ]

    return settings


get_sidebar_menu_settings = get_sidebar_menu_settings_v3

####################################################################################
# LISTA V3 - LISTAS REUTILIZÁVEIS DO PROCESSO
####################################################################################

def _normalize_process_list_key_v3(raw_key: Any) -> str:
    clean_key = str(raw_key or "").strip().lower()
    clean_key = re.sub(r"[^a-z0-9_]+", "_", clean_key)
    clean_key = re.sub(r"_+", "_", clean_key).strip("_")

    if not clean_key:
        return ""

    if not clean_key.startswith("list_"):
        clean_key = f"list_{clean_key}"

    return clean_key


PROCESS_LIST_SOURCE_MANUAL_V1 = "manual"
PROCESS_LIST_SOURCE_USERS_V1 = "users"
PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1 = "sidebar_sections"
PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1 = "sidebar_menus_by_section"
PROCESS_LIST_SOURCE_TABLE_PREFIX_V1 = "table:"
PROCESS_LIST_SOURCE_TABLE_EXCLUDED_KEYS_V1 = frozenset({"alembic_version", "sqlite_sequence"})
PROCESS_LIST_SOURCE_TABLE_KEY_ALIASES_V1 = {
    "user_profiles": "profiles",
}
PROCESS_LIST_SOURCE_LABELS_V1 = {
    PROCESS_LIST_SOURCE_MANUAL_V1: "Manual",
    PROCESS_LIST_SOURCE_USERS_V1: "Utilizador (automático)",
    PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1: "Sessoes (automatico)",
    PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1: "Subprocesso/Menu por sessao (automatico)",
}
PROCESS_LIST_SOURCE_TABLE_LABEL_OVERRIDES_V1 = {
    "profiles": "Perfil",
}
PROCESS_LIST_SOURCE_TABLE_DISPLAY_COLUMN_PRIORITY_V1 = (
    "label",
    "nome",
    "name",
    "title",
    "titulo",
    "descricao",
    "description",
    "full_name",
    "display_name",
    "login_email",
    "email",
    "code",
    "codigo",
    "key",
    "id",
)
PROCESS_LIST_SOURCE_TABLE_STATUS_COLUMN_PRIORITY_V1 = (
    "account_status",
    "status",
    "section_status",
    "record_status",
    "is_active",
)
PROCESS_LIST_SOURCE_TABLE_TEXT_TYPES_V1 = frozenset(
    {
        "character varying",
        "character",
        "text",
        "citext",
        "varchar",
        "bpchar",
    }
)


def _is_process_list_users_source_alias_v1(raw_value: Any) -> bool:
    clean_value = str(raw_value or "").strip().lower()
    clean_value = unicodedata.normalize("NFKD", clean_value).encode("ascii", "ignore").decode("ascii")
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")

    return clean_value in {"users", "user", "utilizador", "utilizadores", "tabela_utilizador", "users_table"}


def _is_process_list_sidebar_sections_source_alias_v1(raw_value: Any) -> bool:
    clean_value = str(raw_value or "").strip().lower()
    clean_value = unicodedata.normalize("NFKD", clean_value).encode("ascii", "ignore").decode("ascii")
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")

    return clean_value in {
        PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1,
        "sessions",
        "session",
        "sessoes",
        "sidebar_sections",
    }


def _is_process_list_sidebar_menus_by_section_source_alias_v1(raw_value: Any) -> bool:
    clean_value = str(raw_value or "").strip().lower()
    clean_value = unicodedata.normalize("NFKD", clean_value).encode("ascii", "ignore").decode("ascii")
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")

    return clean_value in {
        PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1,
        "menus_by_section",
        "menu_by_section",
        "menus_por_sessao",
        "menu_por_sessao",
        "subprocessos_por_sessao",
        "submenu_por_sessao",
    }


def _normalize_process_list_table_key_v1(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    clean_value = unicodedata.normalize("NFKD", clean_value).encode("ascii", "ignore").decode("ascii")
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")
    clean_value = PROCESS_LIST_SOURCE_TABLE_KEY_ALIASES_V1.get(clean_value, clean_value)
    return clean_value


def _build_process_list_table_source_key_v1(table_key: str) -> str:
    clean_table_key = _normalize_process_list_table_key_v1(table_key)
    if not clean_table_key:
        return ""
    return f"{PROCESS_LIST_SOURCE_TABLE_PREFIX_V1}{clean_table_key}"


def _extract_process_list_table_key_from_source_v1(raw_source: Any) -> str:
    clean_source = str(raw_source or "").strip().lower()

    if not clean_source:
        return ""

    if clean_source.startswith(PROCESS_LIST_SOURCE_TABLE_PREFIX_V1):
        return _normalize_process_list_table_key_v1(
            clean_source[len(PROCESS_LIST_SOURCE_TABLE_PREFIX_V1):]
        )

    if clean_source.startswith("table_"):
        return _normalize_process_list_table_key_v1(clean_source[6:])

    return ""


def _format_process_list_table_label_v1(table_key: str) -> str:
    clean_table_key = _normalize_process_list_table_key_v1(table_key)
    if not clean_table_key:
        return "Tabela"
    if clean_table_key in PROCESS_LIST_SOURCE_TABLE_LABEL_OVERRIDES_V1:
        return PROCESS_LIST_SOURCE_TABLE_LABEL_OVERRIDES_V1[clean_table_key]
    return clean_table_key.replace("_", " ").title()


def _is_process_list_source_automatic_v1(source_key: str) -> bool:
    clean_source_key = _normalize_process_list_source_key_v1(source_key)
    return clean_source_key in {
        PROCESS_LIST_SOURCE_USERS_V1,
        PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1,
        PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1,
    } or bool(
        _extract_process_list_table_key_from_source_v1(clean_source_key)
    )


def _normalize_process_list_source_key_v1(raw_source: Any) -> str:
    if _is_process_list_users_source_alias_v1(raw_source):
        return PROCESS_LIST_SOURCE_USERS_V1
    if _is_process_list_sidebar_sections_source_alias_v1(raw_source):
        return PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1
    if _is_process_list_sidebar_menus_by_section_source_alias_v1(raw_source):
        return PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1

    table_key = _extract_process_list_table_key_from_source_v1(raw_source)
    if table_key:
        return _build_process_list_table_source_key_v1(table_key)

    return PROCESS_LIST_SOURCE_MANUAL_V1


def _resolve_process_list_source_label_v1(source_key: str) -> str:
    clean_source_key = _normalize_process_list_source_key_v1(source_key)
    source_table_key = _extract_process_list_table_key_from_source_v1(clean_source_key)
    if source_table_key:
        return f"Tabela: {_format_process_list_table_label_v1(source_table_key)} (automático)"
    return PROCESS_LIST_SOURCE_LABELS_V1.get(
        clean_source_key,
        PROCESS_LIST_SOURCE_LABELS_V1[PROCESS_LIST_SOURCE_MANUAL_V1],
    )


def normalize_menu_process_lists_v3(raw_lists: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_lists, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for raw_item in raw_lists:
        if not isinstance(raw_item, dict):
            continue

        label = _normalize_sentence_case_text(raw_item.get("label", raw_item.get("name")))

        if not label:
            continue

        list_key = _normalize_process_list_key_v3(raw_item.get("key"))

        if not list_key:
            list_key = _normalize_process_list_key_v3(_build_menu_key_from_label(label))

        if not list_key:
            list_key = "list_lista"

        base_key = list_key
        suffix = 2

        while list_key in seen_keys:
            list_key = f"{base_key}_{suffix}"
            suffix += 1

        seen_keys.add(list_key)

        raw_source_key = (
            raw_item.get("source_key")
            or raw_item.get("source")
            or raw_item.get("process_list_source")
            or raw_item.get("data_source")
        )
        source_key = _normalize_process_list_source_key_v1(raw_source_key)

        raw_items = raw_item.get("items_csv", raw_item.get("items"))
        if _is_process_list_source_automatic_v1(source_key):
            raw_values = []
        else:
            if isinstance(raw_items, str):
                raw_values = raw_items.split(",")
            elif isinstance(raw_items, (list, tuple, set)):
                raw_values = raw_items
            else:
                raw_values = []

        items: list[str] = []
        seen_items: set[str] = set()

        for raw_value in raw_values:
            clean_value = " ".join(str(raw_value or "").strip().split())

            if not clean_value:
                continue

            lookup = clean_value.lower()

            if lookup in seen_items:
                continue

            seen_items.add(lookup)
            items.append(clean_value)

        has_explicit_source = bool(str(raw_source_key or "").strip())
        if (
            source_key == PROCESS_LIST_SOURCE_MANUAL_V1
            and not has_explicit_source
            and len(items) == 1
            and _is_process_list_users_source_alias_v1(items[0])
        ):
            source_key = PROCESS_LIST_SOURCE_USERS_V1
            items = []

        normalized.append(
            {
                "key": list_key,
                "label": label,
                "items": items,
                "items_csv": ", ".join(items),
                "source_key": source_key,
                "source_label": _resolve_process_list_source_label_v1(source_key),
            }
        )

    return normalized


def _load_process_list_users_source_items_v1(session: Session) -> list[str]:
    rows = session.execute(
        text(
            """
            SELECT DISTINCT
                trim(coalesce(nullif(m.full_name, ''), nullif(u.login_email, ''))) AS option_label
            FROM users AS u
            JOIN members AS m ON m.id = u.member_id
            WHERE lower(trim(coalesce(u.account_status, ''))) = 'active'
            ORDER BY option_label
            """
        )
    ).mappings().all()

    labels: list[str] = []
    seen_labels: set[str] = set()

    for row in rows:
        option_label = " ".join(str((row or {}).get("option_label") or "").strip().split())

        if not option_label:
            continue

        lookup_label = option_label.lower()
        if lookup_label in seen_labels:
            continue

        seen_labels.add(lookup_label)
        labels.append(option_label)

    return labels


def _normalize_process_list_option_label_v1(raw_value: Any) -> str:
    return " ".join(str(raw_value or "").strip().split())


def _extract_process_list_option_labels_v1(option_rows: list[dict[str, Any]]) -> list[str]:
    labels: list[str] = []
    seen_labels: set[str] = set()

    for row in option_rows:
        option_label = _normalize_process_list_option_label_v1(
            row.get("label") or row.get("value")
        )
        if not option_label:
            continue
        lookup_label = option_label.lower()
        if lookup_label in seen_labels:
            continue
        seen_labels.add(lookup_label)
        labels.append(option_label)

    return labels


def _build_process_list_option_rows_from_labels_v1(labels: list[str]) -> list[dict[str, str]]:
    return [
        {
            "value": option_label,
            "label": option_label,
        }
        for option_label in labels
        if str(option_label or "").strip()
    ]


def _load_process_list_sidebar_sections_source_rows_v1(
    session: Session,
    selected_entity_id: object = None,
) -> list[dict[str, str]]:
    administrativo_config = build_effective_menu_config_v1(
        _load_menu_config(session, "administrativo"),
        selected_entity_id=selected_entity_id,
    )
    section_rows = normalize_sidebar_sections(
        administrativo_config.get(MENU_CONFIG_SIDEBAR_SECTIONS_KEY)
    )

    option_rows: list[dict[str, str]] = []
    seen_section_keys: set[str] = set()

    for section_row in section_rows:
        section_key = _normalize_sidebar_section_key(section_row.get("key"))
        section_label = _normalize_process_list_option_label_v1(section_row.get("label"))
        section_status = _normalize_sidebar_section_status_v5(
            section_row.get("status")
            if section_row.get("status") is not None
            else section_row.get("section_status", section_row.get("is_active"))
        )

        if not section_key or not section_label or section_status != "ativo":
            continue
        if section_key in seen_section_keys:
            continue

        seen_section_keys.add(section_key)
        option_rows.append(
            {
                "value": section_label,
                "label": section_label,
                "section_key": section_key,
                "section_label": section_label,
            }
        )

    return option_rows


def _load_process_list_sidebar_menus_by_section_source_rows_v1(
    session: Session,
    selected_entity_id: object = None,
) -> list[dict[str, str]]:
    base_get_sidebar_menu_settings = globals().get("_original_get_sidebar_menu_settings_for_lists_v3")
    if callable(base_get_sidebar_menu_settings):
        menu_rows = base_get_sidebar_menu_settings(
            session,
            selected_entity_id=selected_entity_id,
        )
    else:
        menu_rows = get_sidebar_menu_settings(
            session,
            selected_entity_id=selected_entity_id,
        )

    option_rows: list[dict[str, str]] = []

    for menu_row in menu_rows:
        if not bool(menu_row.get("is_active")) or bool(menu_row.get("is_deleted")):
            continue

        menu_label = _normalize_process_list_option_label_v1(menu_row.get("label"))
        menu_key = _normalize_menu_key(menu_row.get("key"))
        section_key = _normalize_sidebar_section_key(
            menu_row.get("sidebar_section_key") or menu_row.get("menu_section")
        )
        section_label = _normalize_process_list_option_label_v1(
            menu_row.get("sidebar_section_label") or menu_row.get("menu_section_label")
        )

        if not menu_label or not section_key or not section_label:
            continue

        option_rows.append(
            {
                "value": menu_label,
                "label": menu_label,
                "menu_key": menu_key,
                "section_key": section_key,
                "section_label": section_label,
            }
        )

    return option_rows


def _list_process_source_tables_v1(session: Session) -> list[str]:
    rows = session.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
    ).mappings().all()

    table_keys: list[str] = []
    seen_table_keys: set[str] = set()

    for row in rows:
        table_key = _normalize_process_list_table_key_v1((row or {}).get("table_name"))

        if (
            not table_key
            or table_key in seen_table_keys
            or table_key in PROCESS_LIST_SOURCE_TABLE_EXCLUDED_KEYS_V1
        ):
            continue

        seen_table_keys.add(table_key)
        table_keys.append(table_key)

    return table_keys


def get_process_list_source_options_v1(session: Session) -> list[dict[str, str]]:
    options: list[dict[str, str]] = [
        {"key": PROCESS_LIST_SOURCE_MANUAL_V1, "label": PROCESS_LIST_SOURCE_LABELS_V1[PROCESS_LIST_SOURCE_MANUAL_V1]},
        {"key": PROCESS_LIST_SOURCE_USERS_V1, "label": PROCESS_LIST_SOURCE_LABELS_V1[PROCESS_LIST_SOURCE_USERS_V1]},
        {
            "key": PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1,
            "label": PROCESS_LIST_SOURCE_LABELS_V1[PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1],
        },
        {
            "key": PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1,
            "label": PROCESS_LIST_SOURCE_LABELS_V1[PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1],
        },
    ]

    for table_key in _list_process_source_tables_v1(session):
        if table_key == "users":
            continue
        options.append(
            {
                "key": _build_process_list_table_source_key_v1(table_key),
                "label": _resolve_process_list_source_label_v1(
                    _build_process_list_table_source_key_v1(table_key)
                ),
            }
        )

    return options


def _quote_sql_identifier_v1(raw_identifier: Any) -> str:
    return '"' + str(raw_identifier or "").replace('"', '""') + '"'


def _load_process_source_table_columns_v1(
    session: Session,
    table_key: str,
) -> list[dict[str, str]]:
    clean_table_key = _normalize_process_list_table_key_v1(table_key)
    if not clean_table_key:
        return []

    rows = session.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                udt_name,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
            ORDER BY ordinal_position
            """
        ),
        {"table_name": clean_table_key},
    ).mappings().all()

    normalized_columns: list[dict[str, str]] = []
    for row in rows:
        column_name = _normalize_process_list_table_key_v1((row or {}).get("column_name"))
        if not column_name:
            continue
        normalized_columns.append(
            {
                "column_name": column_name,
                "data_type": str((row or {}).get("data_type") or "").strip().lower(),
                "udt_name": str((row or {}).get("udt_name") or "").strip().lower(),
            }
        )

    return normalized_columns


def _is_process_source_table_text_column_v1(column_meta: dict[str, str]) -> bool:
    return (
        str(column_meta.get("data_type") or "").strip().lower() in PROCESS_LIST_SOURCE_TABLE_TEXT_TYPES_V1
        or str(column_meta.get("udt_name") or "").strip().lower() in PROCESS_LIST_SOURCE_TABLE_TEXT_TYPES_V1
    )


def _resolve_process_source_table_display_column_v1(columns: list[dict[str, str]]) -> str:
    if not columns:
        return ""

    columns_by_name = {
        str(column.get("column_name") or "").strip().lower(): column
        for column in columns
        if str(column.get("column_name") or "").strip()
    }

    for preferred_name in PROCESS_LIST_SOURCE_TABLE_DISPLAY_COLUMN_PRIORITY_V1:
        if preferred_name in columns_by_name:
            return preferred_name

    for column in columns:
        if _is_process_source_table_text_column_v1(column):
            return str(column.get("column_name") or "").strip().lower()

    return str(columns[0].get("column_name") or "").strip().lower()


def _resolve_process_source_table_status_column_v1(columns: list[dict[str, str]]) -> dict[str, str] | None:
    columns_by_name = {
        str(column.get("column_name") or "").strip().lower(): column
        for column in columns
        if str(column.get("column_name") or "").strip()
    }

    for preferred_name in PROCESS_LIST_SOURCE_TABLE_STATUS_COLUMN_PRIORITY_V1:
        if preferred_name in columns_by_name:
            return columns_by_name[preferred_name]

    return None


def _load_process_list_table_source_items_v1(
    session: Session,
    table_key: str,
) -> list[str]:
    clean_table_key = _normalize_process_list_table_key_v1(table_key)
    if not clean_table_key:
        return []

    table_columns = _load_process_source_table_columns_v1(session, clean_table_key)
    display_column = _resolve_process_source_table_display_column_v1(table_columns)
    if not display_column:
        return []

    status_column_meta = _resolve_process_source_table_status_column_v1(table_columns)

    quoted_schema = _quote_sql_identifier_v1("public")
    quoted_table = _quote_sql_identifier_v1(clean_table_key)
    quoted_display_column = _quote_sql_identifier_v1(display_column)
    display_expr = f"trim(coalesce({quoted_display_column}::text, ''))"

    where_parts = [f"{display_expr} <> ''"]

    if status_column_meta:
        quoted_status_column = _quote_sql_identifier_v1(status_column_meta.get("column_name"))
        status_data_type = str(status_column_meta.get("data_type") or "").strip().lower()
        status_udt_name = str(status_column_meta.get("udt_name") or "").strip().lower()

        if status_data_type == "boolean" or status_udt_name == "bool":
            where_parts.append(f"{quoted_status_column} IS TRUE")
        else:
            where_parts.append(
                f"lower(trim(coalesce({quoted_status_column}::text, ''))) = 'active'"
            )

    where_sql = " AND ".join(where_parts)

    rows = session.execute(
        text(
            f"""
            SELECT DISTINCT {display_expr} AS option_label
            FROM {quoted_schema}.{quoted_table}
            WHERE {where_sql}
            ORDER BY option_label
            LIMIT 500
            """
        )
    ).mappings().all()

    items: list[str] = []
    seen_items: set[str] = set()

    for row in rows:
        option_label = " ".join(str((row or {}).get("option_label") or "").strip().split())
        if not option_label:
            continue
        lookup_label = option_label.lower()
        if lookup_label in seen_items:
            continue
        seen_items.add(lookup_label)
        items.append(option_label)

    return items


def _resolve_process_lists_dynamic_sources_v1(
    session: Session,
    process_lists: list[dict[str, Any]],
    selected_entity_id: object = None,
) -> list[dict[str, Any]]:
    if not process_lists:
        return []

    resolved_lists: list[dict[str, Any]] = []
    users_source_items_cache: list[str] | None = None
    table_source_items_cache: dict[str, list[str]] = {}
    sidebar_sections_source_rows_cache: list[dict[str, str]] | None = None
    sidebar_menus_by_section_source_rows_cache: list[dict[str, str]] | None = None

    for raw_process_list in process_lists:
        process_list = dict(raw_process_list or {})
        source_key = _normalize_process_list_source_key_v1(process_list.get("source_key"))
        source_table_key = _extract_process_list_table_key_from_source_v1(source_key)

        process_list["source_key"] = source_key
        process_list["source_label"] = _resolve_process_list_source_label_v1(source_key)

        if source_key == PROCESS_LIST_SOURCE_USERS_V1:
            if users_source_items_cache is None:
                users_source_items_cache = _load_process_list_users_source_items_v1(session)
            process_list["items"] = list(users_source_items_cache)
            process_list["items_csv"] = ", ".join(users_source_items_cache)
            process_list["option_rows"] = _build_process_list_option_rows_from_labels_v1(
                users_source_items_cache
            )
        elif source_key == PROCESS_LIST_SOURCE_SIDEBAR_SECTIONS_V1:
            if sidebar_sections_source_rows_cache is None:
                sidebar_sections_source_rows_cache = _load_process_list_sidebar_sections_source_rows_v1(
                    session,
                    selected_entity_id=selected_entity_id,
                )
            process_list["option_rows"] = list(sidebar_sections_source_rows_cache)
            process_list["items"] = _extract_process_list_option_labels_v1(
                sidebar_sections_source_rows_cache
            )
            process_list["items_csv"] = ", ".join(process_list["items"])
        elif source_key == PROCESS_LIST_SOURCE_SIDEBAR_MENUS_BY_SECTION_V1:
            if sidebar_menus_by_section_source_rows_cache is None:
                sidebar_menus_by_section_source_rows_cache = (
                    _load_process_list_sidebar_menus_by_section_source_rows_v1(
                        session,
                        selected_entity_id=selected_entity_id,
                    )
                )
            process_list["option_rows"] = list(sidebar_menus_by_section_source_rows_cache)
            process_list["items"] = _extract_process_list_option_labels_v1(
                sidebar_menus_by_section_source_rows_cache
            )
            process_list["items_csv"] = ", ".join(process_list["items"])
        elif source_table_key:
            if source_table_key not in table_source_items_cache:
                table_source_items_cache[source_table_key] = _load_process_list_table_source_items_v1(
                    session,
                    source_table_key,
                )
            source_items = table_source_items_cache.get(source_table_key, [])
            process_list["items"] = list(source_items)
            process_list["items_csv"] = ", ".join(source_items)
            process_list["option_rows"] = _build_process_list_option_rows_from_labels_v1(
                source_items
            )
        else:
            process_list["option_rows"] = _build_process_list_option_rows_from_labels_v1(
                list(process_list.get("items") or [])
            )

        resolved_lists.append(process_list)

    return resolved_lists


if "_original_normalize_menu_process_additional_fields_for_list_v3" not in globals():
    _original_normalize_menu_process_additional_fields_for_list_v3 = normalize_menu_process_additional_fields


def normalize_menu_process_additional_fields_v4(raw_fields: Any) -> list[dict[str, Any]]:
    normalized = _original_normalize_menu_process_additional_fields_for_list_v3(raw_fields)

    if not isinstance(raw_fields, (list, tuple, set)):
        return normalized

    raw_by_index: dict[int, dict[str, Any]] = {}

    for index, raw_item in enumerate(raw_fields):
        if isinstance(raw_item, dict):
            raw_by_index[index] = raw_item

    for index, item in enumerate(normalized):
        if str(item.get("field_type") or "").strip().lower() != "list":
            item.pop("list_key", None)
            continue

        raw_item = raw_by_index.get(index, {})
        item["list_key"] = _normalize_process_list_key_v3(
            raw_item.get("list_key", raw_item.get("process_list_key", raw_item.get("lista")))
        )

    return normalized


normalize_menu_process_additional_fields = normalize_menu_process_additional_fields_v4


if "_original_get_sidebar_menu_settings_for_lists_v3" not in globals():
    _original_get_sidebar_menu_settings_for_lists_v3 = get_sidebar_menu_settings


def get_sidebar_menu_settings_v4(
    session: Session,
    selected_entity_id: object = None,
) -> list[dict[str, Any]]:
    settings = _original_get_sidebar_menu_settings_for_lists_v3(
        session,
        selected_entity_id=selected_entity_id,
    )
    process_list_source_options = get_process_list_source_options_v1(session)

    rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).all()

    config_by_key = {
        _normalize_menu_key(row.menu_key): _parse_menu_config(row.menu_config)
        for row in rows
        if _normalize_menu_key(row.menu_key)
    }

    for item in settings:
        clean_key = _normalize_menu_key(item.get("key"))
        raw_menu_config = config_by_key.get(clean_key, {})
        menu_config = _normalize_music_menu_config_v1(
            clean_key,
            item.get("label"),
            item.get("menu_config") if isinstance(item.get("menu_config"), dict) else raw_menu_config,
        )
        process_lists = _resolve_process_lists_dynamic_sources_v1(
            session,
            normalize_menu_process_lists_v3(menu_config.get("process_lists")),
            selected_entity_id=selected_entity_id,
        )
        process_subsequent_fields = normalize_menu_process_subsequent_fields(menu_config.get("subsequent_fields"))
        process_quantity_fields = normalize_menu_process_quantity_fields(
            menu_config.get("process_quantity_fields")
        )
        item["process_lists"] = process_lists
        item["process_subsequent_fields"] = process_subsequent_fields
        item["process_quantity_fields"] = process_quantity_fields
        item["process_list_source_options"] = list(process_list_source_options)
        item["process_list_options"] = [
            {"key": process_list["key"], "label": process_list["label"]}
            for process_list in process_lists
        ]

    return settings


get_sidebar_menu_settings = get_sidebar_menu_settings_v4


def _build_process_quantity_rule_key_v1(rule_label: str, fallback_index: int) -> str:
    clean_key = _normalize_menu_key(rule_label)
    if clean_key:
        return f"qty_{clean_key}"
    return f"qty_regra_{fallback_index + 1}"


def _normalize_process_quantity_max_items_v1(raw_value: Any) -> int:
    try:
        parsed_value = int(str(raw_value or "").strip())
    except (TypeError, ValueError):
        return 1
    return max(1, min(parsed_value, 50))


def normalize_menu_process_quantity_fields(raw_fields: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_fields, (list, tuple, set)):
        return []

    normalized_fields: list[dict[str, Any]] = []
    seen_rule_keys: set[str] = set()

    for row_index, raw_item in enumerate(raw_fields):
        if not isinstance(raw_item, dict):
            continue

        rule_label = _normalize_sentence_case_text(
            raw_item.get("label")
            or raw_item.get("rule_label")
            or raw_item.get("name")
        )
        quantity_field_key = _normalize_custom_field_key(
            raw_item.get("quantity_field_key")
            or raw_item.get("quantityFieldKey")
            or raw_item.get("field_key")
        )
        raw_repeated_field_keys = (
            raw_item.get("repeated_field_keys")
            or raw_item.get("repeatedFieldKeys")
            or raw_item.get("field_keys")
            or []
        )
        if isinstance(raw_repeated_field_keys, str):
            try:
                parsed_repeated_field_keys = json.loads(raw_repeated_field_keys)
            except (TypeError, ValueError, json.JSONDecodeError):
                parsed_repeated_field_keys = [
                    chunk
                    for chunk in re.split(r"[,;\n\r]+", raw_repeated_field_keys)
                    if str(chunk or "").strip()
                ]
        else:
            parsed_repeated_field_keys = raw_repeated_field_keys

        repeated_field_keys: list[str] = []
        seen_repeated_field_keys: set[str] = set()
        if isinstance(parsed_repeated_field_keys, (list, tuple, set)):
            for raw_field_key in parsed_repeated_field_keys:
                clean_field_key = _normalize_custom_field_key(raw_field_key)
                if not clean_field_key or clean_field_key in seen_repeated_field_keys:
                    continue
                seen_repeated_field_keys.add(clean_field_key)
                repeated_field_keys.append(clean_field_key)

        header_key = _normalize_custom_field_key(
            raw_item.get("header_key")
            or raw_item.get("headerKey")
        )
        max_items = _normalize_process_quantity_max_items_v1(
            raw_item.get("max_items")
            or raw_item.get("maxItems")
        )
        item_label = _normalize_sentence_case_text(
            raw_item.get("item_label")
            or raw_item.get("itemLabel")
            or "Item"
        ) or "Item"

        rule_key = _normalize_menu_key(
            raw_item.get("key")
            or raw_item.get("rule_key")
            or raw_item.get("ruleKey")
        )
        if not rule_key:
            rule_key = _build_process_quantity_rule_key_v1(rule_label or item_label, row_index)

        if (
            not rule_label
            or not quantity_field_key
            or not repeated_field_keys
            or rule_key in seen_rule_keys
        ):
            continue

        seen_rule_keys.add(rule_key)
        normalized_fields.append(
            {
                "key": rule_key,
                "label": rule_label,
                "quantity_field_key": quantity_field_key,
                "repeated_field_keys": repeated_field_keys,
                "header_key": header_key,
                "max_items": max_items,
                "item_label": item_label,
            }
        )

    return normalized_fields


def update_sidebar_menu_process_quantity_fields_v1(
    session: Session,
    menu_key: str,
    raw_fields: Any,
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    selected_entity_id = resolve_menu_selected_entity_scope_id_v1(
        clean_menu_key,
        selected_entity_id,
    )

    if not clean_menu_key:
        return False, "Menu inválido."

    if clean_menu_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return False, "Este processo não permite Campos Quantidade."

    ensure_sidebar_menu_settings_defaults(session)

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    menu_config = _load_menu_config(session, clean_menu_key)
    effective_menu_config = build_effective_menu_config_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
    )
    additional_fields = normalize_menu_process_additional_fields(
        effective_menu_config.get("additional_fields")
    )
    additional_fields_by_key = {
        str(field.get("key") or "").strip().lower(): field
        for field in additional_fields
        if str(field.get("key") or "").strip()
    }
    header_keys = {
        field_key
        for field_key, field in additional_fields_by_key.items()
        if str(field.get("field_type") or "").strip().lower() == "header"
    }

    normalized_fields = normalize_menu_process_quantity_fields(raw_fields)
    validated_fields: list[dict[str, Any]] = []
    seen_rule_keys: set[str] = set()

    for row_index, item in enumerate(normalized_fields):
        rule_key = str(item.get("key") or "").strip().lower()
        rule_label = str(item.get("label") or "").strip()
        quantity_field_key = str(item.get("quantity_field_key") or "").strip().lower()
        repeated_field_keys = [
            str(raw_field_key or "").strip().lower()
            for raw_field_key in (item.get("repeated_field_keys") or [])
            if str(raw_field_key or "").strip()
        ]
        header_key = str(item.get("header_key") or "").strip().lower()
        item_label = str(item.get("item_label") or "").strip() or "Item"
        max_items = _normalize_process_quantity_max_items_v1(item.get("max_items"))

        if not rule_label:
            return False, f"Informe o nome da regra na linha {row_index + 1}."

        if not rule_key:
            return False, f"Regra inválida na linha {row_index + 1}."

        if rule_key in seen_rule_keys:
            return False, f"Já existe uma regra com a chave '{rule_key}'."
        seen_rule_keys.add(rule_key)

        quantity_field_meta = additional_fields_by_key.get(quantity_field_key)
        if quantity_field_meta is None:
            return False, f"O campo origem da regra '{rule_label}' deve existir em Campos adicionais."
        if str(quantity_field_meta.get("field_type") or "").strip().lower() != "number":
            return False, f"O campo origem da regra '{rule_label}' deve ser numérico."

        if not repeated_field_keys:
            return False, f"Selecione os campos repetidos da regra '{rule_label}'."

        validated_repeated_field_keys: list[str] = []
        seen_repeated_field_keys: set[str] = set()
        for repeated_field_key in repeated_field_keys:
            repeated_field_meta = additional_fields_by_key.get(repeated_field_key)
            if repeated_field_meta is None:
                return False, f"Os campos repetidos da regra '{rule_label}' devem existir em Campos adicionais."
            repeated_field_type = str(repeated_field_meta.get("field_type") or "").strip().lower()
            if repeated_field_type == "header":
                return False, f"A regra '{rule_label}' não pode repetir cabeçalhos."
            if repeated_field_key == quantity_field_key:
                return False, f"A regra '{rule_label}' não pode repetir o próprio campo de quantidade."
            if repeated_field_key in seen_repeated_field_keys:
                continue
            seen_repeated_field_keys.add(repeated_field_key)
            validated_repeated_field_keys.append(repeated_field_key)

        if header_key and header_key not in header_keys:
            return False, f"O cabeçalho da regra '{rule_label}' deve existir em Campos adicionais."

        validated_fields.append(
            {
                "key": rule_key,
                "label": rule_label,
                "quantity_field_key": quantity_field_key,
                "repeated_field_keys": validated_repeated_field_keys,
                "header_key": header_key,
                "max_items": max_items,
                "item_label": item_label,
            }
        )

    menu_config = apply_entity_scoped_menu_config_updates_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
        updates={"process_quantity_fields": validated_fields},
    )
    _persist_menu_config(session, clean_menu_key, menu_config)
    session.commit()

    return True, ""

# //###################################################################################
# (MENU) HIERARQUIA DOS CAMPOS ADICIONAIS - PATCH SEGURO V2
# //###################################################################################

def normalize_menu_process_additional_fields_v1(raw_fields: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_fields, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for row_index, raw_item in enumerate(raw_fields):
        item_label = ""
        item_key = ""
        item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
        item_size: int | None = None
        item_is_required = False
        item_list_key = ""

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
            item_list_key = _normalize_menu_key(
                raw_item.get("list_key", raw_item.get("listKey", ""))
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
            "display_order": row_index,
        }

        if item_size is not None:
            normalized_item["size"] = item_size

        if item_type == "list" and item_list_key:
            normalized_item["list_key"] = item_list_key

        normalized.append(normalized_item)

    return normalized


def normalize_menu_process_additional_fields(raw_fields: Any) -> list[dict[str, Any]]:
    return normalize_menu_process_additional_fields_v1(raw_fields)


def _rebuild_menu_process_hierarchy_from_additional_fields_v1(
    menu_config: dict[str, Any],
    normalized_fields: list[dict[str, Any]],
) -> dict[str, Any]:
    previous_additional_fields = normalize_menu_process_additional_fields_v1(
        menu_config.get("additional_fields")
    )

    previous_field_keys = {
        str(item.get("key") or "").strip().lower()
        for item in previous_additional_fields
        if str(item.get("key") or "").strip()
    }

    existing_visible_raw = menu_config.get("process_visible_fields")
    has_existing_visible_config = isinstance(existing_visible_raw, list) and bool(existing_visible_raw)

    existing_visible_keys = {
        str(raw_key or "").strip().lower()
        for raw_key in (existing_visible_raw or [])
        if str(raw_key or "").strip()
    }

    visible_order: list[str] = []
    visible_headers: list[str] = []
    visible_rows: list[dict[str, Any]] = []
    field_header_map: dict[str, str] = {}

    active_header_key = ""

    for field_index, field_item in enumerate(normalized_fields):
        field_key = str(field_item.get("key") or "").strip().lower()

        if not field_key:
            continue

        field_type = str(field_item.get("field_type") or "").strip().lower()
        is_new_field = field_key not in previous_field_keys

        should_be_visible = (
            not has_existing_visible_config
            or field_key in existing_visible_keys
            or is_new_field
            or field_type == "header"
        )

        if field_type == "header":
            active_header_key = field_key

            if should_be_visible and field_key not in visible_order:
                visible_order.append(field_key)

            if should_be_visible and field_key not in visible_headers:
                visible_headers.append(field_key)

            continue

        if not should_be_visible:
            continue

        if field_key not in visible_order:
            visible_order.append(field_key)

        if active_header_key:
            field_header_map[field_key] = active_header_key

        visible_rows.append(
            {
                "field_key": field_key,
                "header_key": active_header_key,
                "display_order": field_index,
            }
        )

    used_headers = {
        str(row.get("header_key") or "").strip().lower()
        for row in visible_rows
        if str(row.get("header_key") or "").strip()
    }

    visible_order = [
        field_key
        for field_key in visible_order
        if field_key not in visible_headers or field_key in used_headers
    ]

    visible_headers = [
        header_key
        for header_key in visible_headers
        if header_key in used_headers
    ]

    menu_config["additional_fields"] = normalized_fields
    menu_config["process_visible_fields"] = visible_order
    menu_config["process_visible_headers"] = visible_headers
    menu_config["process_visible_field_rows"] = visible_rows
    menu_config["process_visible_field_header_map"] = field_header_map

    return menu_config



def update_sidebar_menu_additional_fields_v4(
    session: Session,
    menu_key: str,
    fields: list[dict[str, Any]],
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    # APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_ADDITIONAL_FIELDS_SAVE_START
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    selected_entity_id = resolve_menu_selected_entity_scope_id_v1(
        clean_menu_key,
        selected_entity_id,
    )

    if not clean_menu_key:
        return False, "Menu inválido."

    # APPVERBO_PROCESS_CREATE_EDIT_FLOW_V6_PROTECTED_GUARD
    if clean_menu_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return False, "Este processo nao permite campos adicionais."

    ensure_sidebar_menu_settings_defaults(session)

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    menu_config = _load_menu_config(session, clean_menu_key)
    effective_menu_config = build_effective_menu_config_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
    )

    old_header_map: dict[str, str] = {}

    old_rows = effective_menu_config.get("process_visible_field_rows")
    if isinstance(old_rows, list):
        for old_row in old_rows:
            if not isinstance(old_row, dict):
                continue

            field_key = str(old_row.get("field_key") or "").strip().lower()
            header_key = str(old_row.get("header_key") or "").strip().lower()

            if field_key and header_key:
                old_header_map[field_key] = header_key

    legacy_header_map = effective_menu_config.get("visible_field_headers")
    if isinstance(legacy_header_map, dict):
        for raw_field_key, raw_header_key in legacy_header_map.items():
            field_key = str(raw_field_key or "").strip().lower()
            header_key = str(raw_header_key or "").strip().lower()

            if field_key and header_key:
                old_header_map[field_key] = header_key

    normalized_fields = normalize_menu_process_additional_fields(fields)
    effective_menu_config["additional_fields"] = normalized_fields

    selectable_options = get_menu_process_selectable_field_options(
        clean_menu_key,
        effective_menu_config,
    )
    header_options = get_menu_process_header_options(
        clean_menu_key,
        effective_menu_config,
    )

    selectable_keys = {
        str(item.get("key") or "").strip().lower()
        for item in selectable_options
        if str(item.get("key") or "").strip()
    }
    header_keys = {
        str(item.get("key") or "").strip().lower()
        for item in header_options
        if str(item.get("key") or "").strip()
    }

    raw_configured_fields = effective_menu_config.get("process_visible_fields")
    configured_flag = (
        "process_visible_fields" in effective_menu_config
        or bool(effective_menu_config.get("process_visible_fields_configured"))
    )

    if isinstance(raw_configured_fields, (list, tuple, set)):
        raw_visible_fields = list(raw_configured_fields)
    else:
        raw_visible_fields = []

    if not raw_visible_fields:
        raw_rows = effective_menu_config.get("process_visible_field_rows")

        if isinstance(raw_rows, list):
            for raw_row in raw_rows:
                if not isinstance(raw_row, dict):
                    continue

                raw_visible_fields.append(raw_row.get("field_key"))

    clean_visible_fields: list[str] = []
    seen_fields: set[str] = set()

    for raw_field in raw_visible_fields:
        field_key = str(raw_field or "").strip().lower()

        if not field_key:
            continue

        if field_key in seen_fields:
            continue

        if field_key not in selectable_keys:
            continue

        seen_fields.add(field_key)
        clean_visible_fields.append(field_key)

    if clean_menu_key == "administrativo" and not clean_visible_fields:
        default_visible_fields = get_menu_process_default_visible_fields(
            clean_menu_key,
            effective_menu_config,
        )
        for field_key in default_visible_fields:
            clean_field_key = str(field_key or "").strip().lower()
            if not clean_field_key or clean_field_key in seen_fields:
                continue
            if clean_field_key not in selectable_keys:
                continue
            seen_fields.add(clean_field_key)
            clean_visible_fields.append(clean_field_key)

    process_visible_field_rows: list[dict[str, str]] = []
    process_visible_field_header_map: dict[str, str] = {}

    for field_key in clean_visible_fields:
        header_key = old_header_map.get(field_key, "")

        if header_key not in header_keys:
            header_key = ""

        if header_key:
            process_visible_field_header_map[field_key] = header_key

        process_visible_field_rows.append(
            {
                "field_key": field_key,
                "header_key": header_key,
            }
        )

    legacy_visible_fields: list[str] = []
    emitted_legacy_keys: set[str] = set()
    active_header_key = ""

    for row in process_visible_field_rows:
        field_key = row["field_key"]
        header_key = row["header_key"]

        if header_key and header_key != active_header_key:
            if header_key not in emitted_legacy_keys:
                legacy_visible_fields.append(header_key)
                emitted_legacy_keys.add(header_key)

            active_header_key = header_key

        if not header_key:
            active_header_key = ""

        if field_key in emitted_legacy_keys:
            continue

        legacy_visible_fields.append(field_key)
        emitted_legacy_keys.add(field_key)

    refresh_token = str(uuid4())
    scoped_updates: dict[str, Any] = {
        "additional_fields": normalized_fields,
        "process_additional_fields_refresh_version": refresh_token,
        MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY: refresh_token,
    }

    if configured_flag:
        scoped_updates.update(
            {
                "process_visible_fields": clean_visible_fields,
                "process_visible_field_header_map": process_visible_field_header_map,
                "process_visible_field_rows": process_visible_field_rows,
                "process_visible_fields_configured": True,
                "visible_fields": legacy_visible_fields,
                "visible_field_headers": process_visible_field_header_map,
            }
        )

    menu_config = apply_entity_scoped_menu_config_updates_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
        updates=scoped_updates,
    )

    if selected_entity_id is not None:
        menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = refresh_token

    _persist_menu_config(session, clean_menu_key, menu_config)
    session.commit()

    return True, ""
    # APPVERBO_PROCESS_CREATE_EDIT_FLOW_V4_ADDITIONAL_FIELDS_SAVE_END


def update_sidebar_menu_additional_fields_v1(
    session: Session,
    menu_key: str,
    fields: list[dict[str, Any]],
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    return update_sidebar_menu_additional_fields_v4(
        session,
        menu_key,
        fields,
        selected_entity_id,
    )

def update_sidebar_menu_additional_fields(
    session: Session,
    menu_key: str,
    raw_fields: Any,
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    return update_sidebar_menu_additional_fields_v1(
        session=session,
        menu_key=menu_key,
        fields=list(raw_fields or []) if isinstance(raw_fields, (list, tuple, set)) else [],
        selected_entity_id=selected_entity_id,
    )


# //###################################################################################
# (3) CAMPOS SUBSEQUENTES - V1
# //###################################################################################

def normalize_menu_process_subsequent_fields(raw_fields: Any) -> list[dict[str, Any]]:
    """Normaliza campos subsequentes que aparecem após outros campos específicos."""
    if not isinstance(raw_fields, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []

    for raw_item in raw_fields:
        if not isinstance(raw_item, dict):
            continue

        subsequent_key = str(raw_item.get("key") or "").strip().lower()
        trigger_field = str(raw_item.get("trigger_field") or "").strip().lower()
        field_key = str(raw_item.get("field_key") or raw_item.get("subsequent_field") or "").strip().lower()
        operator = str(raw_item.get("operator") or raw_item.get("condition") or "equals").strip().lower()
        trigger_value = str(raw_item.get("trigger_value") or "").strip()
        allowed_operators = {
            "preenchido",
            "vazio",
            "igual",
            "diferente",
            "contem",
            "nao_contem",
            "maior",
            "menor",
            "maior_igual",
            "menor_igual",
        }

        if operator not in allowed_operators:
            operator = "equals"
        if operator in {"is_empty", "is_not_empty"}:
            trigger_value = ""

        if not trigger_field or not field_key:
            continue

        normalized.append({
            "key": subsequent_key or uuid4().hex,
            "trigger_field": trigger_field,
            "field_key": field_key,
            "operator": operator,
            "trigger_value": trigger_value,
        })

    return normalized


def update_sidebar_menu_subsequent_fields(
    session: Session,
    menu_key: str,
    raw_fields: Any,
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    """Atualiza os campos subsequentes de um menu."""
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    selected_entity_id = resolve_menu_selected_entity_scope_id_v1(
        clean_menu_key,
        selected_entity_id,
    )

    if not clean_menu_key:
        return False, "Menu inválido."

    if clean_menu_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return False, "Este processo não permite campos subsequentes."

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    menu_config = _load_menu_config(session, clean_menu_key)
    normalized_fields = normalize_menu_process_subsequent_fields(raw_fields)
    menu_config = apply_entity_scoped_menu_config_updates_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
        updates={"subsequent_fields": normalized_fields},
    )
    _persist_menu_config(session, clean_menu_key, menu_config)
    session.commit()

    return True, ""


# //###################################################################################
# (2) MOVER CAMPO ADICIONAL NO FORMULÁRIO - V1
# //###################################################################################

def move_sidebar_menu_additional_field(
    session: Session,
    menu_key: str,
    field_key: str,
    direction: str,
    selected_entity_id: object = None,
) -> tuple[bool, str]:
    """
    Move um campo adicional para cima ou para baixo no formulário.
    Se o campo for do tipo 'header' (Cabeçalho), move o bloco inteiro junto com os campos abaixo.
    """
    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    selected_entity_id = resolve_menu_selected_entity_scope_id_v1(
        clean_menu_key,
        selected_entity_id,
    )

    if not clean_menu_key:
        return False, "Menu inválido."

    if clean_menu_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return False, "Este processo não permite mover campos."

    clean_direction = str(direction or "").strip().lower()
    if clean_direction not in {"up", "down"}:
        return False, "Direção inválida."

    if not _menu_exists(session, clean_menu_key):
        return False, "Menu não encontrado."

    menu_config = _load_menu_config(session, clean_menu_key)
    effective_menu_config = build_effective_menu_config_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
    )

    normalized_fields = normalize_menu_process_additional_fields_v1(
        effective_menu_config.get("additional_fields")
    )

    if not normalized_fields:
        return False, "Nenhum campo adicional encontrado."

    clean_field_key = str(field_key or "").strip().lower()

    # Encontrar o índice do campo
    field_index = None
    for idx, field in enumerate(normalized_fields):
        if str(field.get("key") or "").strip().lower() == clean_field_key:
            field_index = idx
            break

    if field_index is None:
        return False, "Campo não encontrado."

    field_type = str(normalized_fields[field_index].get("field_type") or "").strip().lower()

    # Determinar o bloco a mover
    if field_type == "header":
        # Se for header, mover o bloco inteiro (header + campos seguintes até próximo header)
        block_start = field_index
        block_end = field_index
        for idx in range(field_index + 1, len(normalized_fields)):
            next_field_type = str(normalized_fields[idx].get("field_type") or "").strip().lower()
            if next_field_type == "header":
                break
            block_end = idx
        block_size = block_end - block_start + 1
    else:
        # Campo normal, mover apenas ele
        block_start = field_index
        block_end = field_index
        block_size = 1

    # Calcular o alvo
    if clean_direction == "up":
        if block_start <= 0:
            return False, "Este campo já está no topo."
        target_index = block_start - 1
    else:
        if block_end >= len(normalized_fields) - 1:
            return False, "Este campo já está no fim."
        target_index = block_end + 1

    # Se o alvo é um header, ajustar
    target_type = str(normalized_fields[target_index].get("field_type") or "").strip().lower()
    if target_type == "header":
        if clean_direction == "up":
            # Mover para antes do header
            target_index = target_index
        else:
            # Mover para depois do bloco do header
            for idx in range(target_index + 1, len(normalized_fields)):
                next_field_type = str(normalized_fields[idx].get("field_type") or "").strip().lower()
                if next_field_type == "header":
                    break
                target_index = idx
            target_index = min(target_index + 1, len(normalized_fields) - 1)

    # Executar a troca
    if clean_direction == "up":
        # Remover bloco atual e inserir antes do alvo
        block = normalized_fields[block_start:block_end + 1]
        normalized_fields = (
            normalized_fields[:target_index] +
            block +
            normalized_fields[target_index:block_start] +
            normalized_fields[block_end + 1:]
        )
    else:
        # Remover bloco atual e inserir depois do alvo
        block = normalized_fields[block_start:block_end + 1]
        normalized_fields = (
            normalized_fields[:block_start] +
            normalized_fields[block_end + 1:target_index + 1] +
            block +
            normalized_fields[target_index + 1:]
        )

    # Reconstruir a hierarquia e salvar
    rebuilt_menu_config = _rebuild_menu_process_hierarchy_from_additional_fields_v1(
        dict(effective_menu_config),
        normalized_fields,
    )
    menu_config = apply_entity_scoped_menu_config_updates_v1(
        menu_config,
        selected_entity_id=selected_entity_id,
        updates={
            "additional_fields": rebuilt_menu_config.get("additional_fields"),
            "process_visible_fields": rebuilt_menu_config.get("process_visible_fields"),
            "process_visible_headers": rebuilt_menu_config.get("process_visible_headers"),
            "process_visible_field_rows": rebuilt_menu_config.get("process_visible_field_rows"),
            "process_visible_field_header_map": rebuilt_menu_config.get("process_visible_field_header_map"),
        },
    )
    _persist_menu_config(session, clean_menu_key, menu_config)
    session.commit()

    return True, ""


####################################################################################
# (CAMPOS SUBSEQUENTES V2) NORMALIZAR CONDICAO DE CAMPOS SUBSEQUENTES
####################################################################################

def _normalize_subsequent_field_operator_v2(raw_operator: Any) -> str:
    clean_operator = str(raw_operator or "").strip().lower()
    clean_operator = clean_operator.replace("-", "_")
    clean_operator = clean_operator.replace(" ", "_")

    operator_aliases = {
        "": "vazio",
        "vazio": "vazio",
        "empty": "vazio",
        "blank": "vazio",
        "is_empty": "vazio",
        "esta_vazio": "vazio",

        "preenchido": "preenchido",
        "not_empty": "preenchido",
        "filled": "preenchido",
        "is_filled": "preenchido",
        "esta_preenchido": "preenchido",

        "igual": "igual",
        "igual_a": "igual",
        "equals": "igual",
        "equal": "igual",
        "eq": "igual",

        "diferente": "diferente",
        "diferente_de": "diferente",
        "not_equal": "diferente",
        "neq": "diferente",

        "contem": "contem",
        "contém": "contem",
        "contains": "contem",

        "nao_contem": "nao_contem",
        "não_contém": "nao_contem",
        "not_contains": "nao_contem",
    }

    return operator_aliases.get(clean_operator, "vazio")


####################################################################################
# (CAMPOS SUBSEQUENTES V2) NORMALIZAR LISTA DE CAMPOS SUBSEQUENTES
####################################################################################

def normalize_menu_process_subsequent_fields(raw_fields: Any) -> list[dict[str, str]]:
    if not isinstance(raw_fields, (list, tuple)):
        return []

    allowed_operators = {
        "vazio",
        "preenchido",
        "igual",
        "diferente",
        "contem",
        "nao_contem",
    }

    normalized_fields: list[dict[str, str]] = []
    seen_fields: set[tuple[str, str, str, str]] = set()

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue

        trigger_field_key = _normalize_menu_key(
            raw_field.get("trigger_field_key")
            or raw_field.get("triggerFieldKey")
            or raw_field.get("field_key")
            or raw_field.get("fieldKey")
            or raw_field.get("campo_acionador")
            or raw_field.get("campoAcionador")
        )

        subsequent_field_key = _normalize_menu_key(
            raw_field.get("subsequent_field_key")
            or raw_field.get("subsequentFieldKey")
            or raw_field.get("target_field_key")
            or raw_field.get("targetFieldKey")
            or raw_field.get("campo_subsequente")
            or raw_field.get("campoSubsequente")
        )

        operator = _normalize_subsequent_field_operator_v2(
            raw_field.get("operator")
            or raw_field.get("condition")
            or raw_field.get("condicao")
            or raw_field.get("condição")
        )

        trigger_value = str(
            raw_field.get("trigger_value")
            or raw_field.get("triggerValue")
            or raw_field.get("value")
            or raw_field.get("valor_acionador")
            or raw_field.get("valorAcionador")
            or ""
        ).strip()

        if operator not in allowed_operators:
            operator = "vazio"

        if operator == "igual" and not trigger_value:
            operator = "vazio"

        if operator in {"vazio", "preenchido"}:
            trigger_value = ""

        if not trigger_field_key or not subsequent_field_key:
            continue

        field_key = (
            trigger_field_key,
            subsequent_field_key,
            operator,
            trigger_value,
        )

        if field_key in seen_fields:
            continue

        seen_fields.add(field_key)

        normalized_fields.append(
            {
                "trigger_field_key": trigger_field_key,
                "subsequent_field_key": subsequent_field_key,
                "operator": operator,
                "condition": operator,
                "trigger_value": trigger_value,
            }
        )

    return normalized_fields


####################################################################################
# (CAMPOS SUBSEQUENTES V3) NORMALIZAR E GRAVAR CAMPOS SUBSEQUENTES
####################################################################################

def _normalize_subsequent_field_operator_v3(raw_operator: Any) -> str:
    clean_operator = str(raw_operator or "").strip().lower()
    clean_operator = clean_operator.replace("-", "_")
    clean_operator = clean_operator.replace(" ", "_")

    operator_aliases = {
        "": "is_empty",

        "vazio": "is_empty",
        "empty": "is_empty",
        "blank": "is_empty",
        "is_empty": "is_empty",
        "esta_vazio": "is_empty",

        "preenchido": "is_not_empty",
        "not_empty": "is_not_empty",
        "filled": "is_not_empty",
        "is_filled": "is_not_empty",
        "is_not_empty": "is_not_empty",
        "esta_preenchido": "is_not_empty",

        "igual": "equals",
        "igual_a": "equals",
        "equals": "equals",
        "equal": "equals",
        "eq": "equals",

        "diferente": "not_equals",
        "diferente_de": "not_equals",
        "not_equal": "not_equals",
        "not_equals": "not_equals",
        "neq": "not_equals",
    }

    return operator_aliases.get(clean_operator, "is_empty")


def _build_subsequent_field_key_v3(
    trigger_field_key: str,
    subsequent_field_key: str,
    operator: str,
    trigger_value: str,
) -> str:
    base_key = "_".join(
        [
            str(trigger_field_key or "").strip().lower(),
            str(subsequent_field_key or "").strip().lower(),
            str(operator or "").strip().lower(),
            str(trigger_value or "").strip().lower(),
        ]
    )
    base_key = re.sub(r"[^a-z0-9_]+", "_", base_key)
    base_key = re.sub(r"_+", "_", base_key).strip("_")

    if not base_key:
        return ""

    return f"subseq_{base_key}"


def normalize_menu_process_subsequent_fields(raw_fields: Any) -> list[dict[str, str]]:
    if not isinstance(raw_fields, (list, tuple)):
        return []

    allowed_operators = {
        "is_empty",
        "is_not_empty",
        "equals",
        "not_equals",
    }

    normalized_fields: list[dict[str, str]] = []
    seen_fields: set[tuple[str, str, str, str]] = set()

    for raw_field in raw_fields:
        if not isinstance(raw_field, dict):
            continue

        trigger_field_key = _normalize_menu_key(
            raw_field.get("trigger_field")
            or raw_field.get("trigger_field_key")
            or raw_field.get("triggerField")
            or raw_field.get("triggerFieldKey")
            or raw_field.get("campo_acionador")
            or raw_field.get("campoAcionador")
        )

        subsequent_field_key = _normalize_menu_key(
            raw_field.get("field_key")
            or raw_field.get("subsequent_field")
            or raw_field.get("subsequent_field_key")
            or raw_field.get("subsequentField")
            or raw_field.get("subsequentFieldKey")
            or raw_field.get("target_field_key")
            or raw_field.get("targetFieldKey")
            or raw_field.get("campo_subsequente")
            or raw_field.get("campoSubsequente")
        )

        operator = _normalize_subsequent_field_operator_v3(
            raw_field.get("operator")
            or raw_field.get("condition")
            or raw_field.get("condicao")
            or raw_field.get("condição")
        )

        trigger_value = str(
            raw_field.get("trigger_value")
            or raw_field.get("triggerValue")
            or raw_field.get("value")
            or raw_field.get("valor_acionador")
            or raw_field.get("valorAcionador")
            or ""
        ).strip()

        if operator not in allowed_operators:
            operator = "is_empty"

        if operator in {"is_empty", "is_not_empty"}:
            trigger_value = ""

        if operator in {"equals", "not_equals"} and not trigger_value:
            operator = "is_empty"
            trigger_value = ""

        if not trigger_field_key or not subsequent_field_key:
            continue

        clean_key = _normalize_menu_key(
            raw_field.get("key")
            or raw_field.get("subsequent_field_key")
            or raw_field.get("id")
        )

        if not clean_key:
            clean_key = _build_subsequent_field_key_v3(
                trigger_field_key,
                subsequent_field_key,
                operator,
                trigger_value,
            )

        field_signature = (
            trigger_field_key,
            subsequent_field_key,
            operator,
            trigger_value,
        )

        if field_signature in seen_fields:
            continue

        seen_fields.add(field_signature)

        normalized_fields.append(
            {
                "key": clean_key,
                "trigger_field": trigger_field_key,
                "trigger_field_key": trigger_field_key,
                "field_key": subsequent_field_key,
                "subsequent_field": subsequent_field_key,
                "subsequent_field_key": subsequent_field_key,
                "operator": operator,
                "condition": operator,
                "trigger_value": trigger_value,
            }
        )

    return normalized_fields


####################################################################################
# (LISTAS V8) PRESERVAR LIST_KEY NOS CAMPOS ADICIONAIS
####################################################################################

def _normalize_process_list_key_v8(raw_key: Any) -> str:
    clean_value = str(raw_key or "").strip().lower()
    clean_value = unicodedata.normalize("NFKD", clean_value).encode("ascii", "ignore").decode("ascii")
    clean_value = re.sub(r"[^a-z0-9_]+", "_", clean_value)
    clean_value = re.sub(r"_+", "_", clean_value).strip("_")
    return clean_value


def normalize_menu_process_additional_fields(raw_fields: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_fields, (list, tuple, set)):
        return []

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for raw_item in raw_fields:
        item_label = ""
        item_key = ""
        item_type = ADDITIONAL_FIELD_DEFAULT_TYPE
        item_size: int | None = None
        item_is_required = False
        item_list_key = ""
        item_shared_value_key = ""

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
            item_list_key = _normalize_process_list_key_v8(
                raw_item.get("list_key")
                or raw_item.get("listKey")
                or raw_item.get("process_list_key")
                or raw_item.get("processListKey")
            )
            item_shared_value_key = _normalize_menu_key(
                raw_item.get("shared_value_key")
                or raw_item.get("sharedValueKey")
                or raw_item.get("value_group_key")
                or raw_item.get("valueGroupKey")
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

        candidate_key = item_key or _build_custom_field_key_from_label(item_label)
        unique_key = candidate_key
        suffix_index = 2

        while unique_key in seen_keys:
            unique_key = f"{candidate_key}_{suffix_index}"
            suffix_index += 1

        seen_keys.add(unique_key)

        if item_type == "list" and not item_list_key:
            item_list_key = _normalize_process_list_key_v8(item_label)
        if item_type == "list" and not item_shared_value_key:
            item_shared_value_key = item_list_key

        normalized_item: dict[str, Any] = {
            "key": unique_key,
            "label": item_label,
            "field_type": item_type,
            "is_required": bool(item_is_required and item_type != "header"),
        }

        if item_size is not None:
            normalized_item["size"] = item_size

        if item_type == "list":
            normalized_item["list_key"] = item_list_key
        if item_shared_value_key:
            normalized_item["shared_value_key"] = item_shared_value_key

        normalized.append(normalized_item)

    return normalized


# ###################################################################################
# (SIDEBAR_GLOBAL_REFRESH_V1) VERSAO GLOBAL PARA REFRESH DOS UTILIZADORES LOGADOS
# ###################################################################################

def build_sidebar_global_refresh_version_v1() -> str:
    from time import time as _appverbo_time

    return str(int(_appverbo_time() * 1000))


def get_sidebar_global_refresh_version_v1(session: Session) -> str:
    row = session.execute(
        text(
            """
            SELECT menu_config
            FROM sidebar_menu_settings
            WHERE lower(trim(menu_key)) = :menu_key
            LIMIT 1
            """
        ),
        {"menu_key": "administrativo"},
    ).mappings().one_or_none()

    if row is None:
        return ""

    try:
        menu_config = json.loads(row.get("menu_config") or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        menu_config = {}

    if not isinstance(menu_config, dict):
        return ""

    return str(menu_config.get(MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY) or "")

# APPVERBO_SIDEBAR_SECTIONS_UPDATE_V2_START

# ###################################################################################
# (SIDEBAR_SECTIONS_UPDATE_V2) GRAVAR SESSOES E PROPAGAR VISIBILIDADE AOS MENUS
# ###################################################################################

def _parse_sidebar_menu_config_v2(raw_menu_config: Any) -> dict[str, Any]:
    try:
        parsed_config = json.loads(raw_menu_config or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed_config = {}

    if not isinstance(parsed_config, dict):
        return {}

    return parsed_config


def _resolve_menu_sidebar_section_key_v2(
    menu_key: Any,
    menu_config: dict[str, Any],
    section_keys: set[str],
    ordered_section_keys: list[str],
) -> str:
    raw_section_key = (
        menu_config.get(MENU_CONFIG_SIDEBAR_SECTION_KEY)
        or menu_config.get("menu_section")
        or menu_config.get("section_key")
        or menu_config.get("section")
    )

    clean_section_key = _normalize_sidebar_section_key(raw_section_key)
    if clean_section_key in section_keys:
        return clean_section_key

    normalized_section_key = normalize_menu_section_key(raw_section_key, menu_key)
    if normalized_section_key in section_keys:
        return normalized_section_key

    clean_menu_key = _resolve_legacy_menu_alias(menu_key)
    default_system_section = MENU_SECTION_BY_SYSTEM_MENU_KEY.get(clean_menu_key, "")

    if default_system_section in section_keys:
        return default_system_section

    return _resolve_default_sidebar_section_key(
        clean_menu_key,
        section_keys,
        ordered_section_keys,
    )


def update_sidebar_sections_v2(
    session: Session,
    raw_sections: list[dict[str, Any]],
) -> tuple[bool, str]:
    payload_sections: list[dict[str, Any]] = []

    for raw_section in raw_sections:
        if not isinstance(raw_section, dict):
            continue

        clean_label = _normalize_sidebar_section_label(raw_section.get("label"))
        if not clean_label:
            continue

        clean_key = _normalize_sidebar_section_key(raw_section.get("key"))
        if not clean_key:
            clean_key = _build_sidebar_section_key_from_label(clean_label)

        if not clean_key:
            continue

        scope_mode = (
            raw_section.get("visibility_scope_mode")
            or raw_section.get("scope_mode")
            or raw_section.get("scope")
            or raw_section.get("visibility")
            or MENU_VISIBILITY_SCOPE_ALL
        )

        payload_sections.append(
            _build_sidebar_section_payload(
                clean_key,
                clean_label,
                _visibility_scope_mode_to_scopes(scope_mode),
            )
        )

    normalized_sections = normalize_sidebar_sections(payload_sections)

    if not normalized_sections:
        return False, "Informe pelo menos uma sessão válida."

    section_keys = {
        str(section.get("key") or "").strip().lower()
        for section in normalized_sections
        if str(section.get("key") or "").strip()
    }
    ordered_section_keys = [
        str(section.get("key") or "").strip().lower()
        for section in normalized_sections
        if str(section.get("key") or "").strip()
    ]
    section_scope_map = {
        str(section.get("key") or "").strip().lower(): normalize_menu_visibility_scopes(
            section.get("visibility_scopes")
        )
        for section in normalized_sections
        if str(section.get("key") or "").strip()
    }

    menu_rows = session.execute(
        text(
            """
            SELECT menu_key, menu_config
            FROM sidebar_menu_settings
            """
        )
    ).mappings().all()

    if not menu_rows:
        return False, "Não existem menus para atualizar."

    updated_menus_count = 0

    for menu_row in menu_rows:
        clean_menu_key = _normalize_menu_key(menu_row.get("menu_key"))
        if not clean_menu_key:
            continue

        menu_config = _parse_sidebar_menu_config_v2(menu_row.get("menu_config"))
        sidebar_section_key = _resolve_menu_sidebar_section_key_v2(
            clean_menu_key,
            menu_config,
            section_keys,
            ordered_section_keys,
        )

        if sidebar_section_key not in section_scope_map:
            continue

        inherited_scopes = normalize_menu_visibility_scopes(
            section_scope_map.get(sidebar_section_key)
        )
        inherited_scope_mode = _resolve_visibility_scope_mode_from_scopes(inherited_scopes)

        menu_config[MENU_CONFIG_SIDEBAR_SECTION_KEY] = sidebar_section_key
        menu_config["visibility_scopes"] = inherited_scopes
        menu_config["visibility_scope_mode"] = inherited_scope_mode
        menu_config["visibility_scope_label"] = _resolve_visibility_scope_label_from_mode(
            inherited_scope_mode
        )

        if clean_menu_key == "administrativo":
            menu_config[MENU_CONFIG_SIDEBAR_SECTIONS_KEY] = normalized_sections
            menu_config[MENU_CONFIG_SIDEBAR_GLOBAL_REFRESH_VERSION_KEY] = build_sidebar_global_refresh_version_v1()

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
        updated_menus_count += 1

    session.commit()

    if updated_menus_count <= 0:
        return False, "Nenhum menu foi atualizado com a visibilidade das sessões."

    return True, ""

# APPVERBO_SIDEBAR_SECTIONS_UPDATE_V2_END
