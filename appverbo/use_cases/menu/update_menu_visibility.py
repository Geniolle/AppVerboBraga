from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.menu.configuracao import MENU_CONFIG
from appverbo.admin_subprocesses.repositories.menu_repository import MenuAdminRepository
from appverbo.use_cases.menu.policies import (
    ensure_menu_can_be_hidden_v1,
    ensure_menu_exists_v1,
)


# ###################################################################################
# (1) MODELO DE ENTRADA
# ###################################################################################


@dataclass(frozen=True)
class UpdateMenuVisibilityInput:
    menu_key: str
    make_visible: bool


def normalize_update_menu_visibility_input_v1(
    *,
    menu_key: str,
    menu_status: str,
) -> UpdateMenuVisibilityInput:
    clean_status = str(menu_status or "").strip().lower()
    make_visible = clean_status not in {
        "inativo",
        "inactive",
        "0",
        "false",
        "no",
        "nao",
        "não",
        "off",
    }

    return UpdateMenuVisibilityInput(
        menu_key=str(menu_key or "").strip().lower(),
        make_visible=make_visible,
    )


# ###################################################################################
# (2) USE CASE
# ###################################################################################


def execute_update_menu_visibility_v1(
    *,
    session: Session,
    payload: UpdateMenuVisibilityInput,
) -> tuple[bool, str]:
    repository = MenuAdminRepository(MENU_CONFIG)

    policy_error = ensure_menu_exists_v1(
        repository=repository,
        session=session,
        menu_key=payload.menu_key,
    )
    if policy_error:
        return False, policy_error

    if not payload.make_visible:
        policy_error = ensure_menu_can_be_hidden_v1(menu_key=payload.menu_key)
        if policy_error:
            return False, policy_error

    ok, error_message = repository.update_menu_visibility(
        session=session,
        menu_key=payload.menu_key,
        make_visible=payload.make_visible,
    )

    if not ok:
        return False, error_message or "Não foi possível atualizar o estado do menu."

    return True, ""
