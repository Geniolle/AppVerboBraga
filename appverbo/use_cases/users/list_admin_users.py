from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.user_repository import UserAdminRepository
from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG


def execute_list_admin_users_v1(
    *,
    session: Session,
    context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    repository = UserAdminRepository(UTILIZADOR_CONFIG)
    return repository.list_rows(session, context or {})


__all__ = ["execute_list_admin_users_v1"]

