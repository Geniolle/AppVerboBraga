from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from appgenesis.domains.modules.repositories import (
    find_app_module_by_key,
    find_entity_module_entitlement,
)


@dataclass(frozen=True)
class ModuleAccessDenied:
    reason: str


@dataclass(frozen=True)
class ModuleAccessGranted:
    module_key: str


ModuleAccessResult = ModuleAccessGranted | ModuleAccessDenied


def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def resolve_module_access(
    session: Session, entity_id: int, module_key: str
) -> ModuleAccessResult:
    module = find_app_module_by_key(session, module_key)
    if module is None or not module.is_active:
        return ModuleAccessDenied(reason="Módulo inexistente ou inativo.")

    if module.is_core:
        return ModuleAccessGranted(module_key=module_key)

    entitlement = find_entity_module_entitlement(session, entity_id, module_key)
    if entitlement is None or entitlement.status != "active":
        return ModuleAccessDenied(reason="Entidade não tem acesso ativo a este módulo.")

    now = _as_naive_utc(datetime.now(timezone.utc))
    if entitlement.starts_at is not None and _as_naive_utc(entitlement.starts_at) > now:
        return ModuleAccessDenied(reason="Acesso ao módulo ainda não foi iniciado.")
    if entitlement.expires_at is not None and _as_naive_utc(entitlement.expires_at) < now:
        return ModuleAccessDenied(reason="Acesso ao módulo expirou.")

    return ModuleAccessGranted(module_key=module_key)
