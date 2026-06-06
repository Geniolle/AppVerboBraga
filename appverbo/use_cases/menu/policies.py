from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.menu_settings import (
    SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS,
    SIDEBAR_MENU_DELETE_PROTECTED_KEYS,
    SIDEBAR_MENU_PROTECTED_KEYS,
)
from appverbo.services.auth import is_admin_user


# ###################################################################################
# (1) POLÍTICAS DE PERMISSÃO E ESCOPO
# ###################################################################################


def ensure_actor_can_manage_menu_v1(
    *,
    session: Session,
    actor_user: dict[str, Any],
) -> str:
    actor_id = int(actor_user["id"])
    actor_login_email = str(actor_user["login_email"] or "")

    if is_admin_user(session, actor_id, actor_login_email):
        return ""

    return "Apenas administradores podem gerir o menu."


def ensure_actor_is_owner_for_menu_v1(
    *,
    permissions: dict[str, Any],
) -> str:
    if permissions.get("can_manage_all_entities"):
        return ""

    return "Apenas Owner pode alterar definições do menu."


def ensure_menu_in_scope_v1(
    *,
    permissions: dict[str, Any],
) -> str:
    if permissions.get("can_manage_all_entities"):
        return ""

    return "Sem permissão para gerir o menu neste escopo."


# ###################################################################################
# (2) POLÍTICAS DE MENU
# ###################################################################################


def ensure_menu_exists_v1(
    *,
    repository: Any,
    session: Session,
    menu_key: str,
) -> str:
    if repository.get_for_edit(session=session, edit_key=menu_key) is not None:
        return ""

    return "Menu não encontrado."


def ensure_menu_can_be_hidden_v1(
    *,
    menu_key: str,
) -> str:
    clean_key = str(menu_key or "").strip().lower()

    if clean_key in SIDEBAR_MENU_PROTECTED_KEYS:
        return "Não é permitido ocultar este menu."

    return ""


def ensure_menu_can_be_deleted_v1(
    *,
    repository: Any,
    session: Session,
    menu_key: str,
) -> str:
    row = repository.get_for_edit(session=session, edit_key=menu_key)

    if row is None:
        return "Menu não encontrado para eliminar."

    clean_key = str(row.get("key") or "").strip().lower()

    if clean_key in SIDEBAR_MENU_DELETE_PROTECTED_KEYS:
        return "Não é permitido eliminar este menu."

    if not bool(row.get("can_delete")):
        return "Não é permitido eliminar este menu."

    return ""


def ensure_menu_can_edit_additional_fields_v1(
    *,
    menu_key: str,
) -> str:
    clean_key = str(menu_key or "").strip().lower()

    if clean_key in SIDEBAR_MENU_ADDITIONAL_FIELDS_PROTECTED_KEYS:
        return "Este menu não permite campos adicionais."

    return ""


def ensure_menu_additional_fields_owner_scope_v1(
    *,
    can_edit: bool,
) -> str:
    if can_edit:
        return ""

    return "Campos adicionais deste processo só podem ser editados na entidade Owner."
