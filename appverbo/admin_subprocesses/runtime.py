from __future__ import annotations

import importlib
from typing import Any

from appverbo.admin_subprocesses.models import (
    AdminSubprocessConfig,
    AdminSubprocessState,
)
from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.admin_subprocesses.service import build_admin_subprocess_state


####################################################################################
# (1) CARREGAMENTO ISOLADO DO REPOSITORIO DO SUBPROCESSO
####################################################################################

def load_admin_subprocess_repository(
    config: AdminSubprocessConfig,
) -> BaseAdminSubprocessRepository | None:
    repository_class_path = str(config.repository_class or "").strip()

    if not repository_class_path:
        return None

    module_name, separator, class_name = repository_class_path.rpartition(".")

    if not separator or not module_name or not class_name:
        raise RuntimeError(
            f"repository_class invalido para subprocesso {config.key}: "
            f"{repository_class_path}"
        )

    module = importlib.import_module(module_name)
    repository_class = getattr(module, class_name, None)

    if repository_class is None:
        raise RuntimeError(
            f"Classe de repository nao encontrada para subprocesso {config.key}: "
            f"{repository_class_path}"
        )

    try:
        repository = repository_class(config)
    except TypeError:
        repository = repository_class()

    if not isinstance(repository, BaseAdminSubprocessRepository):
        raise RuntimeError(
            f"Repository do subprocesso {config.key} nao herda "
            "BaseAdminSubprocessRepository."
        )

    return repository


####################################################################################
# (2) CONSTRUCAO UNICA DO STATE DO SUBPROCESSO
####################################################################################

def build_admin_subprocess_state_from_repository(
    *,
    config: AdminSubprocessConfig,
    session: Any,
    edit_key: str = "",
    create_data: dict[str, Any] | None = None,
    success: str = "",
    error: str = "",
    return_url: str = "",
    context: dict[str, Any] | None = None,
) -> AdminSubprocessState | None:
    if not config.enabled:
        return None

    repository = load_admin_subprocess_repository(config)

    if repository is None:
        return None

    rows = repository.list_rows(session, context or {})
    edit_data = None

    if str(edit_key or "").strip():
        edit_data = repository.get_for_edit(
            session,
            edit_key,
            context or {},
        )

    return build_admin_subprocess_state(
        config=config,
        rows=rows,
        edit_key=edit_key,
        edit_data=edit_data,
        create_data=create_data,
        success=success,
        error=error,
        return_url=return_url,
    )
