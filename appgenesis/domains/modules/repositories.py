from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from appgenesis.models.modules import AppModule, EntityModuleEntitlement


def find_app_module_by_key(session: Session, module_key: str) -> AppModule | None:
    return session.execute(
        select(AppModule).where(AppModule.module_key == module_key)
    ).scalar_one_or_none()


def find_entity_module_entitlement(
    session: Session, entity_id: int, module_key: str
) -> EntityModuleEntitlement | None:
    return session.execute(
        select(EntityModuleEntitlement).where(
            EntityModuleEntitlement.entity_id == entity_id,
            EntityModuleEntitlement.module_key == module_key,
        )
    ).scalar_one_or_none()
