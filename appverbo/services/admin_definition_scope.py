from __future__ import annotations

from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from appverbo.models import AdminDefinition
from appverbo.services.entity_scope import coerce_entity_scope_id_v1


# ###################################################################################
# (1) LEITURA DAS DEFINICOES NO ESCOPO DA ENTIDADE
# ###################################################################################


def list_admin_definitions_in_scope_v1(
    session: Session,
    *,
    selected_entity_id: object,
) -> list[AdminDefinition]:
    parsed_selected_entity_id = coerce_entity_scope_id_v1(selected_entity_id)

    if parsed_selected_entity_id is None:
        stmt = (
            select(AdminDefinition)
            .where(AdminDefinition.entity_id.is_(None))
            .order_by(AdminDefinition.id.desc())
        )
        return list(session.execute(stmt).scalars().all())

    stmt = (
        select(AdminDefinition)
        .where(
            or_(
                AdminDefinition.entity_id.is_(None),
                AdminDefinition.entity_id == parsed_selected_entity_id,
            )
        )
        .order_by(
            case(
                (AdminDefinition.entity_id == parsed_selected_entity_id, 0),
                else_=1,
            ),
            AdminDefinition.id.desc(),
        )
    )
    return list(session.execute(stmt).scalars().all())
