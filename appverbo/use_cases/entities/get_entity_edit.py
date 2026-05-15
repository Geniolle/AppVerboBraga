from __future__ import annotations

from sqlalchemy.orm import Session

from appverbo.admin_subprocesses.entidade.configuracao import ENTIDADE_CONFIG
from appverbo.admin_subprocesses.repositories.entity_repository import EntityAdminRepository
from appverbo.core import ENTITY_PROFILE_SCOPE_LEGADO


# ###################################################################################
# (1) DEFAULTS DE EDIÇÃO
# ###################################################################################

def get_entity_edit_defaults_v1() -> dict[str, str]:
    return {
        "id": "",
        "internal_number": "-",
        "name": "",
        "acronym": "",
        "tax_id": "",
        "email": "",
        "responsible_name": "",
        "door_number": "",
        "address": "",
        "city": "",
        "freguesia": "",
        "postal_code": "",
        "country": "",
        "phone": "",
        "description": "",
        "profile_scope": ENTITY_PROFILE_SCOPE_LEGADO,
        "created_at": "",
        "logo_url": "",
        "status": "active",
    }


# ###################################################################################
# (2) USE CASE DE DADOS PARA FORMULÁRIO DE EDIÇÃO
# ###################################################################################

def execute_get_entity_edit_v1(
    *,
    session: Session,
    entity_id: int | None,
    allowed_entity_ids: set[int] | None = None,
) -> dict[str, str]:
    repository = EntityAdminRepository(ENTIDADE_CONFIG)

    data = repository.get_for_edit_data(
        session=session,
        entity_id=entity_id,
        allowed_entity_ids=allowed_entity_ids,
    )

    if not data or not data.get("id"):
        return get_entity_edit_defaults_v1()

    return data

