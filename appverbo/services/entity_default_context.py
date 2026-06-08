from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from appverbo.models import Entity


def empty_entity_default_context_v1() -> dict[str, str]:
    return {
        "entity_id": "",
        "numero_entidade": "",
        "entity_name": "",
    }


def get_entity_default_context_v1(
    session: Session,
    selected_entity_id: int | None,
) -> dict[str, str]:
    """
    Regra default de entidade.

    Toda criação de dado de processo deve receber o Nº Entidade da entidade
    atualmente selecionada/logada.

    O valor visualizado como "Nº Entidade" é o internal_number da tabela Entity,
    o mesmo número apresentado como "Nº Cliente" na gestão de entidades.
    """
    if selected_entity_id is None:
        return empty_entity_default_context_v1()

    row = session.execute(
        select(
            Entity.id,
            Entity.internal_number,
            Entity.name,
        )
        .where(Entity.id == selected_entity_id)
        .limit(1)
    ).one_or_none()

    if row is None:
        return empty_entity_default_context_v1()

    return {
        "entity_id": str(row.id or "").strip(),
        "numero_entidade": str(row.internal_number or "").strip(),
        "entity_name": str(row.name or "").strip(),
    }


__all__ = [
    "empty_entity_default_context_v1",
    "get_entity_default_context_v1",
]
