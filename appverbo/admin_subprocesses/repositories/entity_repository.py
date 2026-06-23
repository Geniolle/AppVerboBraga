
from __future__ import annotations

import importlib
from typing import Any

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository


class EntityAdminRepository(BaseAdminSubprocessRepository):
    def _resolve_entity_model(self) -> type[Any]:
        candidates = (
            "appverbo.models",
            "appverbo.models.entity",
            "appverbo.models.entities",
        )

        for module_name in candidates:
            try:
                module = importlib.import_module(module_name)
            except Exception:
                continue

            entity_model = getattr(module, "Entity", None)

            if entity_model is not None:
                return entity_model

        raise RuntimeError("Modelo Entity não encontrado nos módulos conhecidos.")

    def _to_row(self, entity: Any) -> dict[str, Any]:
        is_active = bool(getattr(entity, "is_active", False))
        entity_number = getattr(entity, "entity_number", None)
        return {
            "id": getattr(entity, "id", None),
            "key": str(getattr(entity, "id", "") or ""),
            "entity_number": entity_number if entity_number is not None else "",
            "name": getattr(entity, "name", "") or getattr(entity, "legal_name", "") or "",
            "label": getattr(entity, "name", "") or getattr(entity, "legal_name", "") or "",
            "status": "active" if is_active else "inactive",
            "status_label": "Ativa" if is_active else "Inativa",
            "is_active": is_active,
        }

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        Entity = self._resolve_entity_model()
        rows = session.query(Entity).order_by(Entity.entity_number.asc(), Entity.id.asc()).all()
        return [self._to_row(row) for row in rows]

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if not str(edit_key or "").isdigit():
            return None

        Entity = self._resolve_entity_model()
        entity = session.get(Entity, int(edit_key))

        if entity is None:
            return None

        return self._to_row(entity)
