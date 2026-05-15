from __future__ import annotations

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.repositories.user_repository import UserAdminRepository
from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG
from appverbo.models import UserAccountStatus


# ###################################################################################
# (1) DEFAULTS DE EDICAO
# ###################################################################################

def get_user_edit_defaults_v1() -> dict[str, str]:
    return {
        "id": "",
        "full_name": "",
        "primary_phone": "",
        "email": "",
        "entity_id": "",
        "entity_name": "",
        "account_status": UserAccountStatus.ACTIVE.value,
        "profile_id": "",
    }


# ###################################################################################
# (2) USE CASE DE DADOS PARA FORMULARIO DE EDICAO
# ###################################################################################

def execute_get_user_edit_v1(
    *,
    session: Session,
    user_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, str]:
    repository = UserAdminRepository(UTILIZADOR_CONFIG)

    data = repository.get_user_form_data(
        session=session,
        user_id=user_id,
        allowed_entity_ids=allowed_entity_ids,
    )

    if not data.get("id"):
        return get_user_edit_defaults_v1()

    return data

