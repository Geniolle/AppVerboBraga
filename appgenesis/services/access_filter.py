"""Filtro de acesso por funcao administrativa (menus).

Cadeia: perfil no sistema do utilizador -> funcoes ativas com esse perfil ->
perfis de autorizacao dessas funcoes -> menus (menu de origem) desses perfis.

Ativo apenas com APPGENESIS_ACCESS_FILTER_V1=1. Quando inativo, ou para o
utilizador owner, nao ha filtro (devolve None). Sem funcao/perfil, nao ha menus
(nem Home). Os menus nao dependem de requires_admin quando o filtro esta ativo.
"""

from __future__ import annotations

import os
from typing import Any

from sqlalchemy import select

from appgenesis.admin_subprocesses.registry import AUTHORIZATION_PROFILE_CONFIG, FUNCTIONS_ADMIN_CONFIG
from appgenesis.admin_subprocesses.repositories.auth_profile_repository import (
    AuthorizationProfileAdminRepository,
)
from appgenesis.admin_subprocesses.repositories.functions_repository import (
    ALL_PROFILES_VALUE,
    FunctionsAdminRepository,
)
from appgenesis.models import Entity
from appgenesis.services.access_actions import ALL_ACTIONS, normalize_actions

ACCESS_FILTER_ENV_VAR = "APPGENESIS_ACCESS_FILTER_V1"
OWNER_SYSTEM_TYPE = "owner"


def access_filter_enabled() -> bool:
    return os.getenv(ACCESS_FILTER_ENV_VAR, "0").strip().lower() in {"1", "true", "yes", "on"}


def resolve_allowed_menu_keys_v1(
    session: Any,
    *,
    entity_id: int | None,
    user_system_type: str | None,
) -> set[str] | None:
    """Menus permitidos ao utilizador, ou None quando nao ha filtro."""
    if not access_filter_enabled():
        return None
    clean_system_type = str(user_system_type or "").strip().lower()
    if clean_system_type == OWNER_SYSTEM_TYPE:
        return None
    if entity_id is None:
        return set()

    entity_number = session.execute(
        select(Entity.entity_number).where(Entity.id == entity_id).limit(1)
    ).scalar()
    functions = FunctionsAdminRepository(FUNCTIONS_ADMIN_CONFIG).list_rows(
        session, context={"entity_id": entity_id}
    )
    profile_keys: set[str] = set()
    all_profiles = False
    for function_row in functions:
        if function_row.get("status") != "ativo":
            continue
        if str(function_row.get("system_profile") or "") != clean_system_type:
            continue
        for key in function_row.get("authorization_profiles") or []:
            if key == ALL_PROFILES_VALUE:
                all_profiles = True
            else:
                profile_keys.add(str(key).strip().lower())

    if not all_profiles and not profile_keys:
        return set()

    profile_rows = AuthorizationProfileAdminRepository(AUTHORIZATION_PROFILE_CONFIG).list_rows(
        session,
        context={
            "selected_entity_id": entity_id,
            "entity_number": "" if entity_number is None else str(entity_number),
        },
    )
    allowed: set[str] = set()
    for profile_row in profile_rows:
        if profile_row.get("status") != "ativo":
            continue
        if not all_profiles and str(profile_row.get("key") or "").lower() not in profile_keys:
            continue
        menu_origin = str(profile_row.get("menu_origin") or "").strip().lower()
        if menu_origin:
            allowed.add(menu_origin)
    return allowed


def resolve_menu_actions_v1(
    session: Any,
    *,
    entity_id: int | None,
    user_system_type: str | None,
    menu_key: str,
) -> frozenset[str]:
    """Acoes permitidas no menu (exibir, editar, criar, eliminar).

    Sem filtro (flag desligada ou owner) devolve todas as acoes.
    Varios perfis do mesmo menu somam as acoes (uniao).
    """
    if not access_filter_enabled():
        return frozenset(ALL_ACTIONS)
    clean_system_type = str(user_system_type or "").strip().lower()
    if clean_system_type == OWNER_SYSTEM_TYPE:
        return frozenset(ALL_ACTIONS)
    if entity_id is None:
        return frozenset()

    entity_number = session.execute(
        select(Entity.entity_number).where(Entity.id == entity_id).limit(1)
    ).scalar()
    functions = FunctionsAdminRepository(FUNCTIONS_ADMIN_CONFIG).list_rows(
        session, context={"entity_id": entity_id}
    )
    profile_keys: set[str] = set()
    all_profiles = False
    for function_row in functions:
        if function_row.get("status") != "ativo":
            continue
        if str(function_row.get("system_profile") or "") != clean_system_type:
            continue
        for key in function_row.get("authorization_profiles") or []:
            if key == ALL_PROFILES_VALUE:
                all_profiles = True
            else:
                profile_keys.add(str(key).strip().lower())
    if not all_profiles and not profile_keys:
        return frozenset()

    profile_rows = AuthorizationProfileAdminRepository(AUTHORIZATION_PROFILE_CONFIG).list_rows(
        session,
        context={
            "selected_entity_id": entity_id,
            "entity_number": "" if entity_number is None else str(entity_number),
        },
    )
    clean_menu_key = str(menu_key or "").strip().lower()
    actions: set[str] = set()
    for profile_row in profile_rows:
        if profile_row.get("status") != "ativo":
            continue
        if not all_profiles and str(profile_row.get("key") or "").lower() not in profile_keys:
            continue
        if str(profile_row.get("menu_origin") or "").strip().lower() != clean_menu_key:
            continue
        actions.update(normalize_actions(profile_row.get("authorization_level")))
    return frozenset(actions)


def apply_access_filter_to_menu_keys_v1(
    visible_menu_keys: set[str],
    allowed_menu_keys: set[str] | None,
) -> set[str]:
    if allowed_menu_keys is None:
        return visible_menu_keys
    return {key for key in visible_menu_keys if key in allowed_menu_keys}


__all__ = [
    "access_filter_enabled",
    "resolve_menu_actions_v1",
    "apply_access_filter_to_menu_keys_v1",
    "resolve_allowed_menu_keys_v1",
]
