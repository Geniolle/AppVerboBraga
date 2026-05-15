from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import exists, func, or_, select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.admin_subprocesses.utilizador.urls import (
    montar_url_editar_utilizador_v1,
    montar_url_exibir_utilizador_v1,
    montar_url_fechar_utilizador_v1,
)
from appverbo.core import ENTITY_SUPERUSER_PROFILE_NAME
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    Profile,
    User,
    UserProfile,
)
from appverbo.repositories.member_entity_repository import (
    get_active_entity_ids_for_member,
    replace_active_member_entity_link,
)
from appverbo.repositories.user_profile_repository import (
    delete_user_profiles,
    replace_user_profile,
)
from appverbo.repositories.user_repository import null_created_by_for_deleted_user
from appverbo.services.auth import is_admin_user
from appverbo.services.user_status import (
    USER_ACCOUNT_STATUS_ACTIVE_V1,
    USER_ACCOUNT_STATUS_BLOCKED_V1,
    USER_ACCOUNT_STATUS_INACTIVE_V1,
    USER_ACCOUNT_STATUS_PENDING_V1,
    is_user_account_status_active_v1,
    is_user_account_status_blocked_v1,
    is_user_account_status_inactive_v1,
    is_user_account_status_pending_v1,
    normalize_user_account_status_v1,
    user_account_status_label_pt_v1,
)


USER_LIST_ALLOWED_STATUS_VALUES_V1 = frozenset(
    {
        USER_ACCOUNT_STATUS_ACTIVE_V1,
        USER_ACCOUNT_STATUS_INACTIVE_V1,
        USER_ACCOUNT_STATUS_PENDING_V1,
        USER_ACCOUNT_STATUS_BLOCKED_V1,
    }
)


# ###################################################################################
# (1) FILTROS DE LISTAGEM
# ###################################################################################

@dataclass(frozen=True)
class UserListFilters:
    entity_id: int | None = None
    profile_id: int | None = None
    status_values: tuple[str, ...] = ()
    search_text: str = ""
    page: int = 1
    page_size: int = 5000


# ###################################################################################
# (2) REPOSITORY NATIVA DO SUBPROCESSO UTILIZADOR
# ###################################################################################

class UserAdminRepository(BaseAdminSubprocessRepository):
    def _coerce_int(self, raw_value: Any) -> int | None:
        clean_value = str(raw_value or "").strip()

        if not clean_value.isdigit():
            return None

        return int(clean_value)

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
    ) -> UserListFilters:
        raw_context = context or {}

        parsed_entity_id = self._coerce_int(raw_context.get("entity_id"))
        parsed_profile_id = self._coerce_int(raw_context.get("profile_id"))

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

        clean_search = str(raw_context.get("q") or raw_context.get("search") or "").strip()

        parsed_page = self._coerce_int(raw_context.get("page")) or 1
        parsed_page_size = self._coerce_int(raw_context.get("page_size")) or 5000

        if parsed_page < 1:
            parsed_page = 1

        if parsed_page_size < 1:
            parsed_page_size = 1

        if parsed_page_size > 5000:
            parsed_page_size = 5000

        return UserListFilters(
            entity_id=parsed_entity_id,
            profile_id=parsed_profile_id,
            status_values=status_values,
            search_text=clean_search,
            page=parsed_page,
            page_size=parsed_page_size,
        )

    def _normalize_status_values_v1(
        self,
        raw_status_values: tuple[str, ...],
    ) -> tuple[str, ...]:
        normalized_values: list[str] = []
        seen_values: set[str] = set()

        for raw_status in raw_status_values:
            normalized_status = normalize_user_account_status_v1(raw_status)

            if normalized_status not in USER_LIST_ALLOWED_STATUS_VALUES_V1:
                continue

            if normalized_status in seen_values:
                continue

            seen_values.add(normalized_status)
            normalized_values.append(normalized_status)

        return tuple(normalized_values)

    def _resolve_scoped_member_ids(
        self,
        *,
        session: Any,
        allowed_entity_ids: set[int] | None,
        entity_id: int | None = None,
    ) -> set[int] | None:
        has_entity_filter = entity_id is not None
        has_scope_filter = allowed_entity_ids is not None

        if not has_entity_filter and not has_scope_filter:
            return None

        if has_scope_filter and not allowed_entity_ids:
            return set()

        stmt = select(MemberEntity.member_id).where(
            MemberEntity.status == MemberEntityStatus.ACTIVE.value
        )

        if has_scope_filter:
            stmt = stmt.where(MemberEntity.entity_id.in_(sorted(allowed_entity_ids or set())))

        if has_entity_filter:
            stmt = stmt.where(MemberEntity.entity_id == int(entity_id))

        member_ids = session.execute(stmt.distinct()).scalars().all()

        return {
            int(member_id)
            for member_id in member_ids
            if member_id is not None
        }

    def _build_base_stmt(self):
        return (
            select(
                User.id.label("id"),
                User.member_id.label("member_id"),
                Member.full_name.label("full_name"),
                Member.primary_phone.label("primary_phone"),
                User.login_email.label("login_email"),
                User.account_status.label("account_status"),
                User.created_at.label("created_at"),
            )
            .join(Member, Member.id == User.member_id)
        )

    def _apply_user_filters(
        self,
        *,
        stmt: Any,
        member_ids: set[int] | None,
        filters: UserListFilters,
    ) -> Any:
        if member_ids is not None:
            if not member_ids:
                return stmt.where(User.id == -1)

            stmt = stmt.where(User.member_id.in_(sorted(member_ids)))

        if filters.status_values:
            stmt = stmt.where(func.lower(User.account_status).in_(filters.status_values))

        if filters.profile_id is not None:
            stmt = stmt.where(
                exists(
                    select(UserProfile.id).where(
                        UserProfile.user_id == User.id,
                        UserProfile.is_active.is_(True),
                        UserProfile.profile_id == int(filters.profile_id),
                    )
                )
            )

        if filters.search_text:
            query_pattern = f"%{filters.search_text}%"
            stmt = stmt.where(
                or_(
                    Member.full_name.ilike(query_pattern),
                    User.login_email.ilike(query_pattern),
                    Member.primary_phone.ilike(query_pattern),
                )
            )

        return stmt

    def _format_datetime_label(self, raw_value: Any) -> str:
        if raw_value is None:
            return "-"

        if isinstance(raw_value, datetime):
            return raw_value.strftime("%Y-%m-%d %H:%M")

        value = str(raw_value or "").strip()

        if not value:
            return "-"

        return value[:16]

    def _build_entity_map_by_member_id(
        self,
        *,
        session: Any,
        member_ids: set[int],
        allowed_entity_ids: set[int] | None,
        selected_entity_id: int | None,
    ) -> tuple[dict[int, int], dict[int, str]]:
        if not member_ids:
            return {}, {}

        stmt = (
            select(
                MemberEntity.member_id.label("member_id"),
                MemberEntity.entity_id.label("entity_id"),
                Entity.name.label("entity_name"),
                MemberEntity.id.label("member_entity_id"),
            )
            .join(Entity, Entity.id == MemberEntity.entity_id)
            .where(
                MemberEntity.member_id.in_(sorted(member_ids)),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
            .order_by(MemberEntity.member_id.asc(), MemberEntity.id.desc())
        )

        if allowed_entity_ids is not None:
            if allowed_entity_ids:
                stmt = stmt.where(MemberEntity.entity_id.in_(sorted(allowed_entity_ids)))
            else:
                stmt = stmt.where(MemberEntity.entity_id == -1)

        if selected_entity_id is not None:
            stmt = stmt.where(MemberEntity.entity_id == int(selected_entity_id))

        entity_id_by_member_id: dict[int, int] = {}
        entity_name_by_member_id: dict[int, str] = {}

        for row in session.execute(stmt).all():
            member_id = int(row.member_id)

            if member_id in entity_id_by_member_id:
                continue

            entity_id_by_member_id[member_id] = int(row.entity_id)
            entity_name_by_member_id[member_id] = str(row.entity_name or "-")

        return entity_id_by_member_id, entity_name_by_member_id

    def _build_profile_name_map_by_user_id(
        self,
        *,
        session: Any,
        user_ids: set[int],
    ) -> dict[int, str]:
        if not user_ids:
            return {}

        stmt = (
            select(
                UserProfile.user_id.label("user_id"),
                Profile.name.label("profile_name"),
            )
            .join(Profile, Profile.id == UserProfile.profile_id)
            .where(
                UserProfile.user_id.in_(sorted(user_ids)),
                UserProfile.is_active.is_(True),
            )
            .order_by(UserProfile.user_id.asc(), UserProfile.id.asc())
        )

        names_by_user_id: dict[int, str] = {}

        for row in session.execute(stmt).all():
            user_id = int(row.user_id)

            if user_id in names_by_user_id:
                continue

            names_by_user_id[user_id] = str(row.profile_name or "-")

        return names_by_user_id

    def _build_superuser_user_ids(
        self,
        *,
        session: Any,
        user_ids: set[int],
    ) -> set[int]:
        if not user_ids:
            return set()

        stmt = (
            select(UserProfile.user_id)
            .join(Profile, Profile.id == UserProfile.profile_id)
            .where(
                UserProfile.user_id.in_(sorted(user_ids)),
                UserProfile.is_active.is_(True),
                Profile.is_active.is_(True),
                func.lower(Profile.name) == ENTITY_SUPERUSER_PROFILE_NAME.lower(),
            )
        )

        return {
            int(user_id)
            for user_id in session.execute(stmt).scalars().all()
            if user_id is not None
        }

    def _to_row(
        self,
        *,
        row: Any,
        entity_id_by_member_id: dict[int, int],
        entity_name_by_member_id: dict[int, str],
        profile_name_by_user_id: dict[int, str],
        superuser_user_ids: set[int],
    ) -> dict[str, Any]:
        user_id = int(row.id)
        member_id = int(row.member_id)
        clean_status = normalize_user_account_status_v1(row.account_status)

        return {
            "id": user_id,
            "key": str(user_id),
            "member_id": member_id,
            "full_name": str(row.full_name or "").strip(),
            "name": str(row.full_name or "").strip(),
            "label": str(row.full_name or "").strip() or str(row.login_email or "").strip(),
            "login_email": str(row.login_email or "").strip().lower(),
            "email": str(row.login_email or "").strip().lower(),
            "primary_phone": str(row.primary_phone or "-").strip() or "-",
            "phone": str(row.primary_phone or "-").strip() or "-",
            "account_status": clean_status,
            "status": clean_status,
            "account_status_label": user_account_status_label_pt_v1(clean_status),
            "status_label": user_account_status_label_pt_v1(clean_status),
            "account_status_is_active": is_user_account_status_active_v1(clean_status),
            "account_status_is_pending": is_user_account_status_pending_v1(clean_status),
            "account_status_is_inactive": is_user_account_status_inactive_v1(clean_status),
            "account_status_is_blocked": is_user_account_status_blocked_v1(clean_status),
            "is_active": is_user_account_status_active_v1(clean_status),
            "entity_id": entity_id_by_member_id.get(member_id),
            "entity_name": entity_name_by_member_id.get(member_id, "-"),
            "profile_name": profile_name_by_user_id.get(user_id, "-"),
            "is_entity_superuser": user_id in superuser_user_ids,
            "created_at": self._format_datetime_label(row.created_at),
            "created_at_label": self._format_datetime_label(row.created_at),
            "view_url": montar_url_exibir_utilizador_v1(user_id),
            "edit_url": montar_url_editar_utilizador_v1(user_id),
            "close_url": montar_url_fechar_utilizador_v1(),
        }

    def list_users(
        self,
        *,
        session: Any,
        allowed_entity_ids: set[int] | None = None,
        filters: UserListFilters | None = None,
    ) -> dict[str, Any]:
        resolved_filters = filters or UserListFilters()
        normalized_status_values = self._normalize_status_values_v1(
            tuple(resolved_filters.status_values or ())
        )

        if normalized_status_values != tuple(resolved_filters.status_values or ()):
            resolved_filters = UserListFilters(
                entity_id=resolved_filters.entity_id,
                profile_id=resolved_filters.profile_id,
                status_values=normalized_status_values,
                search_text=resolved_filters.search_text,
                page=resolved_filters.page,
                page_size=resolved_filters.page_size,
            )

        scoped_member_ids = self._resolve_scoped_member_ids(
            session=session,
            allowed_entity_ids=allowed_entity_ids,
            entity_id=resolved_filters.entity_id,
        )

        filtered_stmt = self._apply_user_filters(
            stmt=self._build_base_stmt(),
            member_ids=scoped_member_ids,
            filters=resolved_filters,
        )

        count_stmt = select(func.count()).select_from(filtered_stmt.subquery())
        total_rows = int(session.scalar(count_stmt) or 0)

        row_stmt = filtered_stmt.order_by(User.id.desc()).offset(
            (resolved_filters.page - 1) * resolved_filters.page_size
        ).limit(resolved_filters.page_size)

        raw_rows = session.execute(row_stmt).all()

        member_ids = {
            int(row.member_id)
            for row in raw_rows
            if row.member_id is not None
        }
        user_ids = {
            int(row.id)
            for row in raw_rows
            if row.id is not None
        }

        entity_id_by_member_id, entity_name_by_member_id = self._build_entity_map_by_member_id(
            session=session,
            member_ids=member_ids,
            allowed_entity_ids=allowed_entity_ids,
            selected_entity_id=resolved_filters.entity_id,
        )
        profile_name_by_user_id = self._build_profile_name_map_by_user_id(
            session=session,
            user_ids=user_ids,
        )
        superuser_user_ids = self._build_superuser_user_ids(
            session=session,
            user_ids=user_ids,
        )

        rows = [
            self._to_row(
                row=row,
                entity_id_by_member_id=entity_id_by_member_id,
                entity_name_by_member_id=entity_name_by_member_id,
                profile_name_by_user_id=profile_name_by_user_id,
                superuser_user_ids=superuser_user_ids,
            )
            for row in raw_rows
        ]

        return {
            "rows": rows,
            "total": total_rows,
            "page": resolved_filters.page,
            "page_size": resolved_filters.page_size,
            "has_next": (resolved_filters.page * resolved_filters.page_size) < total_rows,
        }

    def list_rows(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        filters = self._normalize_filters_from_context(context)
        allowed_entity_ids = self._resolve_allowed_entity_ids(context)

        result = self.list_users(
            session=session,
            allowed_entity_ids=allowed_entity_ids,
            filters=filters,
        )

        return list(result.get("rows", []))

    def get_user_form_data(
        self,
        *,
        session: Any,
        user_id: int | None,
        allowed_entity_ids: set[int] | None = None,
    ) -> dict[str, str]:
        defaults = {
            "id": "",
            "full_name": "",
            "primary_phone": "",
            "email": "",
            "entity_id": "",
            "entity_name": "",
            "account_status": "active",
            "profile_id": "",
        }

        if user_id is None:
            return defaults

        row = session.execute(
            select(
                User.id.label("id"),
                User.member_id.label("member_id"),
                Member.full_name.label("full_name"),
                Member.primary_phone.label("primary_phone"),
                User.login_email.label("login_email"),
                User.account_status.label("account_status"),
            )
            .join(Member, Member.id == User.member_id)
            .where(User.id == int(user_id))
            .limit(1)
        ).one_or_none()

        if row is None:
            return defaults

        member_entity_stmt = (
            select(MemberEntity.entity_id)
            .where(
                MemberEntity.member_id == int(row.member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
            .order_by(MemberEntity.id.desc())
        )

        if allowed_entity_ids is not None:
            if allowed_entity_ids:
                member_entity_stmt = member_entity_stmt.where(
                    MemberEntity.entity_id.in_(sorted(allowed_entity_ids))
                )
            else:
                return defaults

        member_entity_id = session.scalar(member_entity_stmt.limit(1))

        if allowed_entity_ids is not None and member_entity_id is None:
            return defaults

        profile_id = session.scalar(
            select(UserProfile.profile_id)
            .where(
                UserProfile.user_id == int(row.id),
                UserProfile.is_active.is_(True),
            )
            .order_by(UserProfile.id.asc())
            .limit(1)
        )

        entity_name = ""

        if member_entity_id is not None:
            entity_name = str(
                session.scalar(
                    select(Entity.name).where(Entity.id == int(member_entity_id)).limit(1)
                )
                or ""
            )

        return {
            "id": str(row.id),
            "full_name": str(row.full_name or ""),
            "primary_phone": str(row.primary_phone or ""),
            "email": str(row.login_email or ""),
            "entity_id": str(member_entity_id) if member_entity_id is not None else "",
            "entity_name": entity_name,
            "account_status": normalize_user_account_status_v1(row.account_status),
            "profile_id": str(profile_id) if profile_id is not None else "",
        }

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        parsed_user_id = self._coerce_int(edit_key)

        if parsed_user_id is None:
            return None

        allowed_entity_ids = self._resolve_allowed_entity_ids(context)
        form_data = self.get_user_form_data(
            session=session,
            user_id=parsed_user_id,
            allowed_entity_ids=allowed_entity_ids,
        )

        if not form_data.get("id"):
            return None

        return form_data

    def get_user_and_member(
        self,
        *,
        session: Any,
        user_id: int,
    ) -> tuple[User | None, Member | None]:
        user = session.get(User, int(user_id))

        if user is None:
            return None, None

        member = session.get(Member, int(user.member_id))

        if member is None:
            return user, None

        return user, member

    def get_profile_by_id(
        self,
        *,
        session: Any,
        profile_id: int,
    ) -> Profile | None:
        return session.get(Profile, int(profile_id))

    def find_duplicate_member_id_by_email(
        self,
        *,
        session: Any,
        email: str,
        excluded_member_id: int | None = None,
    ) -> int | None:
        clean_email = str(email or "").strip().lower()

        if not clean_email:
            return None

        stmt = select(Member.id).where(func.lower(Member.email) == clean_email)

        if excluded_member_id is not None:
            stmt = stmt.where(Member.id != int(excluded_member_id))

        duplicate_id = session.scalar(stmt.limit(1))
        return int(duplicate_id) if duplicate_id is not None else None

    def find_duplicate_user_id_by_email(
        self,
        *,
        session: Any,
        login_email: str,
        excluded_user_id: int | None = None,
    ) -> int | None:
        clean_email = str(login_email or "").strip().lower()

        if not clean_email:
            return None

        stmt = select(User.id).where(func.lower(User.login_email) == clean_email)

        if excluded_user_id is not None:
            stmt = stmt.where(User.id != int(excluded_user_id))

        duplicate_id = session.scalar(stmt.limit(1))
        return int(duplicate_id) if duplicate_id is not None else None

    def member_is_within_allowed_entities(
        self,
        *,
        session: Any,
        member_id: int,
        allowed_entity_ids: set[int],
    ) -> bool:
        if not allowed_entity_ids:
            return False

        scoped_link_id = session.scalar(
            select(MemberEntity.id)
            .where(
                MemberEntity.member_id == int(member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                MemberEntity.entity_id.in_(sorted(allowed_entity_ids)),
            )
            .limit(1)
        )

        return scoped_link_id is not None

    def list_active_entity_ids_for_member(
        self,
        *,
        session: Any,
        member_id: int,
    ) -> list[int]:
        return list(get_active_entity_ids_for_member(session, int(member_id)))

    def has_other_active_admin_for_entity(
        self,
        *,
        session: Any,
        entity_id: int,
        excluded_user_id: int,
    ) -> bool:
        rows = session.execute(
            select(User.id, User.login_email)
            .join(MemberEntity, MemberEntity.member_id == User.member_id)
            .where(
                MemberEntity.entity_id == int(entity_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                User.id != int(excluded_user_id),
                User.account_status == "active",
            )
            .order_by(User.id.asc())
        ).all()

        for row in rows:
            if is_admin_user(session, int(row.id), str(row.login_email or "")):
                return True

        return False

    def get_entity_name_by_id(
        self,
        *,
        session: Any,
        entity_id: int,
    ) -> str:
        return str(
            session.scalar(
                select(Entity.name).where(Entity.id == int(entity_id)).limit(1)
            )
            or ""
        )

    def resolve_edit_entity(
        self,
        *,
        session: Any,
        email: str,
        explicit_entity_id: str,
        member_id: int,
        permissions: dict[str, Any],
    ) -> tuple[Entity | None, str]:
        clean_email = str(email or "").strip().lower()
        allowed_entity_ids = {
            int(raw_id)
            for raw_id in (permissions.get("allowed_entity_ids") or set())
            if str(raw_id).strip().isdigit()
        }
        can_manage_all_entities = bool(permissions.get("can_manage_all_entities"))

        # ###################################################################################
        # (1) LISTA DE ENTIDADES NO ESCOPO DO ATOR
        # ###################################################################################
        entities_stmt = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())

        if not can_manage_all_entities:
            if not allowed_entity_ids:
                return None, "Sem entidades disponíveis para este utilizador."

            entities_stmt = entities_stmt.where(Entity.id.in_(sorted(allowed_entity_ids)))

        scoped_entities = list(session.execute(entities_stmt).scalars().all())

        # ###################################################################################
        # (2) PRIORIDADE: ENTIDADE EXPLICITA DO FORMULARIO DE EDICAO
        # ###################################################################################
        parsed_entity_id = self._coerce_int(explicit_entity_id)

        if parsed_entity_id is not None:
            explicit_entity = session.get(Entity, parsed_entity_id)

            if explicit_entity is not None and explicit_entity.is_active:
                if can_manage_all_entities:
                    return explicit_entity, ""

                if parsed_entity_id in allowed_entity_ids:
                    return explicit_entity, ""

        # ###################################################################################
        # (3) FALLBACK: ENTIDADE ATUAL DO MEMBRO
        # ###################################################################################
        current_entity_stmt = (
            select(Entity)
            .join(MemberEntity, MemberEntity.entity_id == Entity.id)
            .where(
                MemberEntity.member_id == int(member_id),
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
            .order_by(MemberEntity.id.asc())
        )

        if not can_manage_all_entities:
            if not allowed_entity_ids:
                return None, "Sem permissão para usar a entidade atual deste utilizador."

            current_entity_stmt = current_entity_stmt.where(
                Entity.id.in_(sorted(allowed_entity_ids))
            )

        current_entity = session.execute(current_entity_stmt.limit(1)).scalar_one_or_none()

        if current_entity is not None:
            return current_entity, ""

        # ###################################################################################
        # (4) FALLBACK POR EMAIL/DOMINIO (SEM BLOQUEAR EDICAO COM AMBIGUIDADE)
        # ###################################################################################
        resolution_error = ""

        if clean_email and "@" in clean_email:
            exact_matches = [
                entity
                for entity in scoped_entities
                if str(entity.email or "").strip().lower() == clean_email
            ]

            if len(exact_matches) == 1:
                return exact_matches[0], ""

            if len(exact_matches) > 1:
                resolution_error = "Existem múltiplas entidades com o mesmo email."

            _, _, email_domain = clean_email.partition("@")
            clean_email_domain = email_domain.strip().lower()

            if clean_email_domain:
                domain_matches = [
                    entity
                    for entity in scoped_entities
                    if str(entity.email or "").strip().lower().endswith(f"@{clean_email_domain}")
                ]

                if len(domain_matches) == 1:
                    return domain_matches[0], ""

                if len(domain_matches) > 1 and not resolution_error:
                    resolution_error = "Existem múltiplas entidades com este domínio de email."

        # ###################################################################################
        # (5) ULTIMO FALLBACK COMPATIVEL
        # ###################################################################################
        if scoped_entities:
            return scoped_entities[0], ""

        if resolution_error:
            return None, resolution_error

        return None, "Não foi possível determinar a entidade ativa para este utilizador."

    def apply_user_update(
        self,
        *,
        session: Any,
        user: User,
        member: Member,
        full_name: str,
        primary_phone: str,
        login_email: str,
        account_status: str,
        selected_entity: Entity | None,
        selected_profile: Profile,
    ) -> None:
        member.full_name = str(full_name or "").strip()
        member.primary_phone = str(primary_phone or "").strip()
        member.email = str(login_email or "").strip().lower()

        user.login_email = str(login_email or "").strip().lower()
        user.account_status = str(account_status or "").strip().lower()

        if selected_entity is not None:
            replace_active_member_entity_link(
                session=session,
                member_id=int(member.id),
                entity_id=int(selected_entity.id),
            )

        replace_user_profile(
            session=session,
            user_id=int(user.id),
            profile_id=int(selected_profile.id),
            is_active=True,
        )

    def delete_inactive_user(
        self,
        *,
        session: Any,
        user: User,
    ) -> None:
        null_created_by_for_deleted_user(session, int(user.id))
        delete_user_profiles(session, int(user.id))
        session.delete(user)
