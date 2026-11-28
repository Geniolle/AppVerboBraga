from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

from appgenesis.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appgenesis.models.department import Department, DepartmentMembership

DEPARTMENT_STATUS_ACTIVE = "ativo"
DEPARTMENT_STATUS_INACTIVE = "inativo"


def _entity_id_from_context(context: dict[str, Any] | None) -> int | None:
    raw_value = (context or {}).get("entity_id")
    try:
        return int(raw_value) if raw_value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _normalize_status(raw_value: Any) -> str:
    clean_value = str(raw_value or "").strip().lower()
    if clean_value in {"inativo", "inactive", "0", "false", "off", "no", "nao"}:
        return DEPARTMENT_STATUS_INACTIVE
    return DEPARTMENT_STATUS_ACTIVE


class DepartmentsAdminRepository(BaseAdminSubprocessRepository):
    """Departamentos da entidade (tabela departments). Multi-tenant: filtra sempre por entity_id."""

    def _build_row(self, department: Department) -> dict[str, Any]:
        status_value = DEPARTMENT_STATUS_ACTIVE if department.is_active else DEPARTMENT_STATUS_INACTIVE
        label = str(department.name or "").strip()
        description = str(department.description or "").strip()
        return {
            "key": str(department.id),
            "label": label,
            "status": status_value,
            "status_label": "Ativo" if status_value == DEPARTMENT_STATUS_ACTIVE else "Inativo",
            "description": description,
            "values": {
                "label": label,
                "description": description,
                "status": status_value,
            },
        }

    def list_rows(self, session: Any, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        entity_id = _entity_id_from_context(context)
        if entity_id is None:
            return []
        rows = session.execute(
            select(Department)
            .where(Department.entity_id == entity_id)
            .order_by(Department.name)
        ).scalars().all()
        return [self._build_row(row) for row in rows]

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_key = str(edit_key or "").strip()
        for row in self.list_rows(session, context):
            if row.get("key") == clean_key:
                return row
        return None

    def save_row(
        self,
        session: Any,
        payload: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        edit_key: str = "",
    ) -> tuple[bool, str, str]:
        entity_id = _entity_id_from_context(context)
        if entity_id is None:
            return False, "menu_not_found", ""
        name = str(payload.get("label") or "").strip()
        if not name:
            return False, "label_required", ""
        description = str(payload.get("description") or "").strip()
        is_active = _normalize_status(payload.get("status")) == DEPARTMENT_STATUS_ACTIVE

        duplicate_query = select(Department.id).where(
            Department.entity_id == entity_id,
            func.lower(Department.name) == name.lower(),
        )
        clean_edit_key = str(edit_key or "").strip()
        if clean_edit_key:
            if not clean_edit_key.isdigit():
                return False, "not_found", ""
            department = session.execute(
                select(Department).where(
                    Department.entity_id == entity_id,
                    Department.id == int(clean_edit_key),
                )
            ).scalars().first()
            if department is None:
                return False, "not_found", ""
            if session.execute(duplicate_query.where(Department.id != department.id)).first() is not None:
                return False, "duplicate_name", ""
            department.name = name
            department.description = description or None
            department.is_active = is_active
            session.flush()
            return True, "saved", str(department.id)

        if session.execute(duplicate_query).first() is not None:
            return False, "duplicate_name", ""
        department = Department(
            entity_id=entity_id,
            name=name,
            description=description or None,
            is_active=is_active,
        )
        session.add(department)
        session.flush()
        return True, "saved", str(department.id)

    def delete_row(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        entity_id = _entity_id_from_context(context)
        clean_key = str(edit_key or "").strip()
        if entity_id is None or not clean_key.isdigit():
            return False, "not_found"
        department = session.execute(
            select(Department).where(
                Department.entity_id == entity_id,
                Department.id == int(clean_key),
            )
        ).scalars().first()
        if department is None:
            return False, "not_found"
        if department.is_active:
            return False, "active_department"
        in_use = session.execute(
            select(DepartmentMembership.id).where(DepartmentMembership.department_id == department.id).limit(1)
        ).first()
        if in_use is not None:
            return False, "in_use"
        session.delete(department)
        session.flush()
        return True, "deleted"


__all__ = ["DepartmentsAdminRepository"]
