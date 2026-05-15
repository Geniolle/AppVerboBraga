from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, or_, select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.core import (
    ENTITY_INTERNAL_NUMBER_MAX,
    ENTITY_INTERNAL_NUMBER_MIN,
    ENTITY_PROFILE_SCOPE_LEGADO,
    ENTITY_PROFILE_SCOPE_OWNER,
)
from appverbo.models import Entity, MemberEntity, User
from appverbo.services.entities import apply_entity_form_data_v1, normalize_entity_text_v1


ENTITY_LIST_ALLOWED_STATUS_VALUES_V1 = frozenset({"active", "inactive"})


# ###################################################################################
# (1) FILTROS DE LISTAGEM
# ###################################################################################

@dataclass(frozen=True)
class EntityListFilters:
    entity_id: int | None = None
    status_values: tuple[str, ...] = ()
    search_text: str = ""
    page: int = 1
    page_size: int = 100


# ###################################################################################
# (2) REPOSITÓRIO NATIVO DE ENTIDADE
# ###################################################################################

class EntityAdminRepository(BaseAdminSubprocessRepository):
    def _coerce_int(self, raw_value: Any) -> int | None:
        clean_value = str(raw_value or "").strip()

        if not clean_value.isdigit():
            return None

        return int(clean_value)

    def _normalize_status_values_v1(
        self,
        raw_status_values: tuple[str, ...],
    ) -> tuple[str, ...]:
        normalized_values: list[str] = []
        seen_values: set[str] = set()

        for raw_status in raw_status_values:
            clean_status = str(raw_status or "").strip().lower()

            if clean_status not in ENTITY_LIST_ALLOWED_STATUS_VALUES_V1:
                continue

            if clean_status in seen_values:
                continue

            seen_values.add(clean_status)
            normalized_values.append(clean_status)

        return tuple(normalized_values)

    def _resolve_allowed_entity_ids(
        self,
        context: dict[str, Any] | None,
    ) -> set[int] | None:
        if not isinstance(context, dict):
            return None

        raw_allowed_entity_ids = context.get("allowed_entity_ids")

        if raw_allowed_entity_ids is None:
            return None

        allowed_entity_ids: set[int] = set()

        for raw_id in raw_allowed_entity_ids:
            parsed_id = self._coerce_int(raw_id)

            if parsed_id is None:
                continue

            allowed_entity_ids.add(parsed_id)

        return allowed_entity_ids

    def _normalize_filters_from_context(
        self,
        context: dict[str, Any] | None,
    ) -> EntityListFilters:
        raw_context = context or {}

        parsed_entity_id = self._coerce_int(raw_context.get("entity_id"))
        clean_search = str(raw_context.get("q") or raw_context.get("search") or "").strip()

        raw_status = str(raw_context.get("status") or "").strip().lower()
        raw_status_values = tuple(
            clean_status
            for clean_status in (
                part.strip().lower()
                for part in raw_status.split(",")
            )
            if clean_status
        )
        status_values = self._normalize_status_values_v1(raw_status_values)

        parsed_page = self._coerce_int(raw_context.get("page")) or 1
        parsed_page_size = self._coerce_int(raw_context.get("page_size")) or 100

        if parsed_page < 1:
            parsed_page = 1

        if parsed_page_size < 1:
            parsed_page_size = 1

        if parsed_page_size > 5000:
            parsed_page_size = 5000

        return EntityListFilters(
            entity_id=parsed_entity_id,
            status_values=status_values,
            search_text=clean_search,
            page=parsed_page,
            page_size=parsed_page_size,
        )

    def _build_base_stmt(self) -> Any:
        return select(Entity)

    def _apply_entity_filters(
        self,
        *,
        stmt: Any,
        allowed_entity_ids: set[int] | None,
        filters: EntityListFilters,
    ) -> Any:
        if allowed_entity_ids is not None:
            if not allowed_entity_ids:
                return stmt.where(Entity.id == -1)

            stmt = stmt.where(Entity.id.in_(sorted(allowed_entity_ids)))

        if filters.entity_id is not None:
            stmt = stmt.where(Entity.id == int(filters.entity_id))

        status_values = set(filters.status_values or ())

        if status_values and status_values != ENTITY_LIST_ALLOWED_STATUS_VALUES_V1:
            if status_values == {"active"}:
                stmt = stmt.where(Entity.is_active.is_(True))
            elif status_values == {"inactive"}:
                stmt = stmt.where(Entity.is_active.is_(False))

        if filters.search_text:
            query_pattern = f"%{filters.search_text}%"
            stmt = stmt.where(
                or_(
                    Entity.name.ilike(query_pattern),
                    Entity.acronym.ilike(query_pattern),
                    Entity.tax_id.ilike(query_pattern),
                    Entity.email.ilike(query_pattern),
                    Entity.responsible_name.ilike(query_pattern),
                    Entity.address.ilike(query_pattern),
                    Entity.city.ilike(query_pattern),
                    Entity.freguesia.ilike(query_pattern),
                    Entity.postal_code.ilike(query_pattern),
                    Entity.country.ilike(query_pattern),
                    Entity.phone.ilike(query_pattern),
                )
            )

        return stmt

    def _format_datetime_label(self, raw_value: Any) -> str:
        if raw_value is None:
            return "-"

        if isinstance(raw_value, datetime):
            return raw_value.strftime("%Y-%m-%d %H:%M")

        clean_value = str(raw_value or "").strip()

        if not clean_value:
            return "-"

        return clean_value[:16]

    def _profile_scope_label_v1(self, raw_value: Any) -> str:
        clean_value = str(raw_value or "").strip().lower()

        if clean_value == ENTITY_PROFILE_SCOPE_OWNER:
            return "Owner"

        return "Legado"

    def _to_row_v1(self, entity: Entity) -> dict[str, Any]:
        is_active = bool(entity.is_active)
        status = "active" if is_active else "inactive"

        return {
            "id": int(entity.id),
            "key": str(entity.id),
            "internal_number": (
                int(entity.internal_number)
                if isinstance(entity.internal_number, int)
                else None
            ),
            "name": str(entity.name or "").strip(),
            "label": str(entity.name or "").strip(),
            "acronym": str(entity.acronym or "").strip(),
            "tax_id": str(entity.tax_id or "").strip(),
            "email": str(entity.email or "").strip(),
            "responsible_name": str(entity.responsible_name or "").strip(),
            "door_number": str(entity.door_number or "").strip(),
            "address": str(entity.address or "").strip(),
            "city": str(entity.city or "").strip(),
            "freguesia": str(entity.freguesia or "").strip(),
            "postal_code": str(entity.postal_code or "").strip(),
            "country": str(entity.country or "").strip(),
            "phone": str(entity.phone or "").strip(),
            "description": str(entity.description or "").strip(),
            "profile_scope": str(entity.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO).strip().lower(),
            "profile_scope_label": self._profile_scope_label_v1(entity.profile_scope),
            "logo_url": str(entity.logo_url or "").strip(),
            "is_active": is_active,
            "status": status,
            "status_label": "Ativo" if is_active else "Inativo",
            "created_at": self._format_datetime_label(entity.created_at),
            "created_at_label": self._format_datetime_label(entity.created_at),
        }

    def list_entities(
        self,
        *,
        session: Any,
        allowed_entity_ids: set[int] | None = None,
        filters: EntityListFilters | None = None,
    ) -> dict[str, Any]:
        resolved_filters = filters or EntityListFilters()
        normalized_status_values = self._normalize_status_values_v1(
            tuple(resolved_filters.status_values or ())
        )

        if normalized_status_values != tuple(resolved_filters.status_values or ()):
            resolved_filters = EntityListFilters(
                entity_id=resolved_filters.entity_id,
                status_values=normalized_status_values,
                search_text=resolved_filters.search_text,
                page=resolved_filters.page,
                page_size=resolved_filters.page_size,
            )

        filtered_stmt = self._apply_entity_filters(
            stmt=self._build_base_stmt(),
            allowed_entity_ids=allowed_entity_ids,
            filters=resolved_filters,
        )

        count_stmt = select(func.count()).select_from(filtered_stmt.subquery())
        total_rows = int(session.scalar(count_stmt) or 0)

        row_stmt = (
            filtered_stmt
            .order_by(Entity.id.desc())
            .offset((resolved_filters.page - 1) * resolved_filters.page_size)
            .limit(resolved_filters.page_size)
        )
        rows = session.execute(row_stmt).scalars().all()

        return {
            "rows": [self._to_row_v1(entity) for entity in rows],
            "total": total_rows,
            "page": resolved_filters.page,
            "page_size": resolved_filters.page_size,
            "has_next": (resolved_filters.page * resolved_filters.page_size) < total_rows,
        }

    def list_active(
        self,
        *,
        session: Any,
        allowed_entity_ids: set[int] | None = None,
        filters: EntityListFilters | None = None,
    ) -> list[dict[str, Any]]:
        resolved_filters = filters or EntityListFilters()
        active_filters = EntityListFilters(
            entity_id=resolved_filters.entity_id,
            status_values=("active",),
            search_text=resolved_filters.search_text,
            page=resolved_filters.page,
            page_size=resolved_filters.page_size,
        )
        return self.list_entities(
            session=session,
            allowed_entity_ids=allowed_entity_ids,
            filters=active_filters,
        ).get("rows", [])

    def list_inactive(
        self,
        *,
        session: Any,
        allowed_entity_ids: set[int] | None = None,
        filters: EntityListFilters | None = None,
    ) -> list[dict[str, Any]]:
        resolved_filters = filters or EntityListFilters()
        inactive_filters = EntityListFilters(
            entity_id=resolved_filters.entity_id,
            status_values=("inactive",),
            search_text=resolved_filters.search_text,
            page=resolved_filters.page,
            page_size=resolved_filters.page_size,
        )
        return self.list_entities(
            session=session,
            allowed_entity_ids=allowed_entity_ids,
            filters=inactive_filters,
        ).get("rows", [])

    def list_rows(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        filters = self._normalize_filters_from_context(context)
        allowed_entity_ids = self._resolve_allowed_entity_ids(context)

        result = self.list_entities(
            session=session,
            allowed_entity_ids=allowed_entity_ids,
            filters=filters,
        )

        return list(result.get("rows", []))

    def get_by_id(
        self,
        *,
        session: Any,
        entity_id: int,
    ) -> Entity | None:
        return session.get(Entity, int(entity_id))

    def _to_edit_data_v1(self, entity: Entity) -> dict[str, str]:
        return {
            "id": str(entity.id),
            "internal_number": (
                str(entity.internal_number)
                if entity.internal_number is not None
                else "-"
            ),
            "name": str(entity.name or "").strip(),
            "acronym": str(entity.acronym or "").strip(),
            "tax_id": str(entity.tax_id or "").strip(),
            "email": str(entity.email or "").strip(),
            "responsible_name": str(entity.responsible_name or "").strip(),
            "door_number": str(entity.door_number or "").strip(),
            "address": str(entity.address or "").strip(),
            "city": str(entity.city or "").strip(),
            "freguesia": str(entity.freguesia or "").strip(),
            "postal_code": str(entity.postal_code or "").strip(),
            "country": str(entity.country or "").strip(),
            "phone": str(entity.phone or "").strip(),
            "description": str(entity.description or "").strip(),
            "profile_scope": (
                str(entity.profile_scope or ENTITY_PROFILE_SCOPE_LEGADO).strip().lower()
                or ENTITY_PROFILE_SCOPE_LEGADO
            ),
            "created_at": entity.created_at.strftime("%d/%m/%Y") if entity.created_at else "",
            "logo_url": str(entity.logo_url or "").strip(),
            "status": "active" if bool(entity.is_active) else "inactive",
        }

    def get_for_edit_data(
        self,
        *,
        session: Any,
        entity_id: int | None,
        allowed_entity_ids: set[int] | None = None,
    ) -> dict[str, str] | None:
        if entity_id is None:
            return None

        parsed_entity_id = int(entity_id)

        if allowed_entity_ids is not None and parsed_entity_id not in allowed_entity_ids:
            return None

        entity = self.get_by_id(session=session, entity_id=parsed_entity_id)

        if entity is None:
            return None

        return self._to_edit_data_v1(entity)

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        parsed_entity_id = self._coerce_int(edit_key)

        if parsed_entity_id is None:
            return None

        allowed_entity_ids = self._resolve_allowed_entity_ids(context)

        return self.get_for_edit_data(
            session=session,
            entity_id=parsed_entity_id,
            allowed_entity_ids=allowed_entity_ids,
        )

    def get_next_internal_number(
        self,
        *,
        session: Any,
    ) -> int:
        used_numbers = session.scalars(
            select(Entity.internal_number)
            .where(
                Entity.internal_number.is_not(None),
                Entity.internal_number >= ENTITY_INTERNAL_NUMBER_MIN,
                Entity.internal_number <= ENTITY_INTERNAL_NUMBER_MAX,
            )
            .order_by(Entity.internal_number.asc())
        ).all()

        used_set = {
            int(number)
            for number in used_numbers
            if isinstance(number, int)
        }

        for candidate in range(ENTITY_INTERNAL_NUMBER_MIN, ENTITY_INTERNAL_NUMBER_MAX + 1):
            if candidate not in used_set:
                return candidate

        return ENTITY_INTERNAL_NUMBER_MAX

    def find_duplicate_name_id(
        self,
        *,
        session: Any,
        name: str,
        ignore_entity_id: int | None = None,
    ) -> int | None:
        clean_name = normalize_entity_text_v1(name).lower()

        if not clean_name:
            return None

        stmt = select(Entity.id).where(func.lower(Entity.name) == clean_name)

        if ignore_entity_id is not None:
            stmt = stmt.where(Entity.id != int(ignore_entity_id))

        duplicate_id = session.scalar(stmt.limit(1))

        return int(duplicate_id) if duplicate_id is not None else None

    def find_existing_owner_entity_id(
        self,
        *,
        session: Any,
        ignore_entity_id: int | None = None,
    ) -> int | None:
        stmt = select(Entity.id).where(
            Entity.profile_scope == ENTITY_PROFILE_SCOPE_OWNER
        )

        if ignore_entity_id is not None:
            stmt = stmt.where(Entity.id != int(ignore_entity_id))

        existing_id = session.scalar(stmt.limit(1))

        return int(existing_id) if existing_id is not None else None

    def count_linked_users(
        self,
        *,
        session: Any,
        entity_id: int,
    ) -> int:
        linked_users = session.scalar(
            select(func.count(User.id))
            .join(MemberEntity, MemberEntity.member_id == User.member_id)
            .where(MemberEntity.entity_id == int(entity_id))
        )

        return int(linked_users or 0)

    def create_entity(
        self,
        *,
        session: Any,
        form_data: dict[str, str],
        logo_url: str = "",
        is_active: bool = True,
    ) -> Entity:
        entity = Entity(
            internal_number=self.get_next_internal_number(session=session),
            logo_url=str(logo_url or "").strip() or None,
            is_active=bool(is_active),
        )
        apply_entity_form_data_v1(entity, form_data)
        session.add(entity)
        session.flush()
        return entity

    def update_entity(
        self,
        *,
        session: Any,
        entity: Entity,
        form_data: dict[str, str],
        clean_status: str,
        include_description: bool = True,
    ) -> Entity:
        apply_entity_form_data_v1(
            entity,
            form_data,
            include_description=include_description,
        )
        entity.is_active = str(clean_status or "").strip().lower() == "active"
        session.flush()
        return entity

    def delete_member_entity_links(
        self,
        *,
        session: Any,
        entity_id: int,
    ) -> None:
        session.execute(
            delete(MemberEntity).where(MemberEntity.entity_id == int(entity_id))
        )

    def delete_inactive_entity(
        self,
        *,
        session: Any,
        entity: Entity,
    ) -> None:
        session.delete(entity)

    def create(
        self,
        session: Any,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        form_data = {
            key: str(value or "")
            for key, value in (payload or {}).items()
        }
        self.create_entity(
            session=session,
            form_data=form_data,
            logo_url=str(payload.get("logo_url") or ""),
            is_active=str(payload.get("status") or "active").strip().lower() == "active",
        )
        return True

    def update(
        self,
        session: Any,
        edit_key: str,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> bool:
        parsed_entity_id = self._coerce_int(edit_key)

        if parsed_entity_id is None:
            return False

        entity = self.get_by_id(session=session, entity_id=parsed_entity_id)

        if entity is None:
            return False

        form_data = {
            key: str(value or "")
            for key, value in (payload or {}).items()
        }
        self.update_entity(
            session=session,
            entity=entity,
            form_data=form_data,
            clean_status=str(payload.get("status") or "active"),
            include_description=True,
        )
        return True

    def delete(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        parsed_entity_id = self._coerce_int(edit_key)

        if parsed_entity_id is None:
            return False

        entity = self.get_by_id(session=session, entity_id=parsed_entity_id)

        if entity is None or bool(entity.is_active):
            return False

        if self.count_linked_users(session=session, entity_id=parsed_entity_id) > 0:
            return False

        self.delete_member_entity_links(session=session, entity_id=parsed_entity_id)
        self.delete_inactive_entity(session=session, entity=entity)
        return True
