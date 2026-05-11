from __future__ import annotations

####################################################################################
# (1) IMPORTS
####################################################################################

from typing import Any

from appverbo.admin_subprocesses.sessoes.config import SESSOES_CONFIG


####################################################################################
# (2) ACESSO CENTRALIZADO À CONFIGURAÇÃO DO SUBPROCESSO SESSÕES
####################################################################################

def get_sessoes_config_v2() -> Any:
    return SESSOES_CONFIG


def get_sessoes_key_v2() -> str:
    return str(getattr(SESSOES_CONFIG, "key", "sessoes"))


def get_sessoes_title_v2() -> str:
    title = getattr(SESSOES_CONFIG, "title", None)

    if title:
        return str(title)

    label = getattr(SESSOES_CONFIG, "label", None)

    if label:
        return str(label)

    name = getattr(SESSOES_CONFIG, "name", None)

    if name:
        return str(name)

    return "Sessões"


def is_sessoes_config_v2(config: Any) -> bool:
    config_key = str(getattr(config, "key", "") or "")
    return config_key == get_sessoes_key_v2()


####################################################################################
# (3) ACESSO CENTRALIZADO A CAMPOS E COLUNAS
####################################################################################

def get_sessoes_fields_v2() -> list[Any]:
    fields = getattr(SESSOES_CONFIG, "fields", None)

    if not fields:
        return []

    return list(fields)


def get_sessoes_columns_v2() -> list[Any]:
    columns = getattr(SESSOES_CONFIG, "columns", None)

    if not columns:
        return []

    return list(columns)


def get_sessoes_field_keys_v2() -> list[str]:
    field_keys: list[str] = []

    for field in get_sessoes_fields_v2():
        field_key = getattr(field, "key", None)

        if field_key:
            field_keys.append(str(field_key))

    return field_keys


def get_sessoes_column_keys_v2() -> list[str]:
    column_keys: list[str] = []

    for column in get_sessoes_columns_v2():
        column_key = getattr(column, "key", None)

        if column_key:
            column_keys.append(str(column_key))

    return column_keys


####################################################################################
# (4) CONTEXTO SEGURO DO SUBPROCESSO SESSÕES
####################################################################################

def build_sessoes_context_v2(context: dict[str, Any] | None = None) -> dict[str, Any]:
    safe_context = dict(context or {})
    safe_context["subprocess_key"] = get_sessoes_key_v2()
    safe_context["subprocess_title"] = get_sessoes_title_v2()
    safe_context["subprocess_fields"] = get_sessoes_field_keys_v2()
    safe_context["subprocess_columns"] = get_sessoes_column_keys_v2()
    safe_context["uses_generic_v2_crud"] = True
    safe_context["has_custom_create_service"] = False
    safe_context["has_custom_delete_service"] = False
    safe_context["has_custom_resend_service"] = False
    return safe_context


####################################################################################
# (5) COMPATIBILIDADE COM NOMES V1
####################################################################################

def get_sessoes_config_v1() -> Any:
    return get_sessoes_config_v2()


def get_sessoes_key_v1() -> str:
    return get_sessoes_key_v2()


def get_sessoes_title_v1() -> str:
    return get_sessoes_title_v2()


def get_sessoes_fields_v1() -> list[Any]:
    return get_sessoes_fields_v2()


def get_sessoes_columns_v1() -> list[Any]:
    return get_sessoes_columns_v2()


def build_sessoes_context_v1(context: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_sessoes_context_v2(context)
