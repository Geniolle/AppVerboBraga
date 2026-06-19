from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.admin_subprocesses.utilizador.urls import (
    montar_url_editar_utilizador_v1,
    montar_url_exibir_utilizador_v1,
    montar_url_fechar_utilizador_v1,
)
from appverbo.models import (
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    Profile,
    User,
    UserProfile,
)
from appverbo.services.user_status import (
    is_user_account_status_active_v1,
    normalize_user_account_status_v1,
    user_account_status_label_pt_v1,
)


####################################################################################
# (1) REPOSITORY NATIVA DO SUBPROCESSO UTILIZADOR
####################################################################################

class UserAdminRepository(BaseAdminSubprocessRepository):
    """
    Repository isolada para o subprocesso Utilizador.

    Regras de performance:
    - SELECT explícito por colunas;
    - evita N+1 para entidades e perfis;
    - respeita escopo de entidades recebido no context;
    - não altera criação, convite, edição ou geração de link legado.
    """

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
            try:
                allowed_entity_ids.add(int(raw_id))
            except (TypeError, ValueError):
                continue

        return allowed_entity_ids

    def _resolve_scoped_member_ids(
        self,
        session: Any,
        allowed_entity_ids: set[int] | None,
    ) -> set[int] | None:
        if allowed_entity_ids is None:
            return None

        if not allowed_entity_ids:
            return set()

        rows = session.execute(
            select(MemberEntity.member_id)
            .where(
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                MemberEntity.entity_id.in_(allowed_entity_ids),
            )
            .distinct()
        ).scalars().all()

        return {
            int(member_id)
            for member_id in rows
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

    def _format_datetime_label(self, raw_value: Any) -> str:
        if raw_value is None:
            return "-"

        if isinstance(raw_value, datetime):
            return raw_value.strftime("%Y-%m-%d %H:%M")

        value = str(raw_value or "").strip()

        if not value:
            return "-"

        return value[:16]

    def _build_entity_names_by_member_id(
        self,
        session: Any,
        member_ids: set[int],
    ) -> dict[int, str]:
        if not member_ids:
            return {}

        rows = session.execute(
            select(
                MemberEntity.member_id.label("member_id"),
                Entity.name.label("entity_name"),
            )
            .join(Entity, Entity.id == MemberEntity.entity_id)
            .where(
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                MemberEntity.member_id.in_(member_ids),
            )
            .order_by(Entity.name.asc())
        ).all()

        names_by_member_id: dict[int, list[str]] = {}

        for row in rows:
            member_id = int(row.member_id)
            entity_name = str(row.entity_name or "").strip()

            if not entity_name:
                continue

            names_by_member_id.setdefault(member_id, [])

            if entity_name not in names_by_member_id[member_id]:
                names_by_member_id[member_id].append(entity_name)

        return {
            member_id: ", ".join(entity_names)
            for member_id, entity_names in names_by_member_id.items()
        }

    def _build_profile_names_by_user_id(
        self,
        session: Any,
        user_ids: set[int],
    ) -> dict[int, str]:
        if not user_ids:
            return {}

        rows = session.execute(
            select(
                UserProfile.user_id.label("user_id"),
                Profile.name.label("profile_name"),
            )
            .join(Profile, Profile.id == UserProfile.profile_id)
            .where(
                UserProfile.is_active.is_(True),
                UserProfile.user_id.in_(user_ids),
            )
            .order_by(Profile.name.asc())
        ).all()

        names_by_user_id: dict[int, list[str]] = {}

        for row in rows:
            user_id = int(row.user_id)
            profile_name = str(row.profile_name or "").strip()

            if not profile_name:
                continue

            names_by_user_id.setdefault(user_id, [])

            if profile_name not in names_by_user_id[user_id]:
                names_by_user_id[user_id].append(profile_name)

        return {
            user_id: ", ".join(profile_names)
            for user_id, profile_names in names_by_user_id.items()
        }

    def _to_row(
        self,
        row: Any,
        entity_names_by_member_id: dict[int, str] | None = None,
        profile_names_by_user_id: dict[int, str] | None = None,
    ) -> dict[str, Any]:
        entity_names_by_member_id = entity_names_by_member_id or {}
        profile_names_by_user_id = profile_names_by_user_id or {}

        normalized_status = normalize_user_account_status_v1(row.account_status)
        is_active = is_user_account_status_active_v1(normalized_status)

        user_id = int(row.id)
        member_id = int(row.member_id)
        full_name = str(row.full_name or "").strip()
        primary_phone = str(row.primary_phone or "").strip()
        login_email = str(row.login_email or "").strip().lower()
        entity_name = entity_names_by_member_id.get(member_id, "-")
        profile_name = profile_names_by_user_id.get(user_id, "-")
        created_at_label = self._format_datetime_label(row.created_at)

        return {
            "id": user_id,
            "key": str(user_id),
            "member_id": member_id,
            "full_name": full_name,
            "name": full_name,
            "label": full_name or login_email,
            "login_email": login_email,
            "email": login_email,
            "primary_phone": primary_phone or "-",
            "phone": primary_phone or "-",
            "entity_name": entity_name,
            "profile_name": profile_name,
            "account_status": normalized_status,
            "status": normalized_status,
            "status_label": user_account_status_label_pt_v1(normalized_status),
            "is_active": is_active,
            "created_at": row.created_at,
            "created_at_label": created_at_label,
            "view_url": montar_url_exibir_utilizador_v1(user_id),
            "edit_url": montar_url_editar_utilizador_v1(user_id),
            "close_url": montar_url_fechar_utilizador_v1(),
        }

    def list_rows(
        self,
        session: Any,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        allowed_entity_ids = self._resolve_allowed_entity_ids(context)
        scoped_member_ids = self._resolve_scoped_member_ids(
            session,
            allowed_entity_ids,
        )

        if scoped_member_ids is not None and not scoped_member_ids:
            return []

        stmt = self._build_base_stmt().order_by(User.id.desc())

        if scoped_member_ids is not None:
            stmt = stmt.where(User.member_id.in_(scoped_member_ids))

        rows = session.execute(stmt).all()

        user_ids = {
            int(row.id)
            for row in rows
            if row.id is not None
        }
        member_ids = {
            int(row.member_id)
            for row in rows
            if row.member_id is not None
        }

        entity_names_by_member_id = self._build_entity_names_by_member_id(
            session,
            member_ids,
        )
        profile_names_by_user_id = self._build_profile_names_by_user_id(
            session,
            user_ids,
        )

        return [
            self._to_row(
                row,
                entity_names_by_member_id=entity_names_by_member_id,
                profile_names_by_user_id=profile_names_by_user_id,
            )
            for row in rows
        ]

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_edit_key = str(edit_key or "").strip()

        if not clean_edit_key.isdigit():
            return None

        allowed_entity_ids = self._resolve_allowed_entity_ids(context)
        scoped_member_ids = self._resolve_scoped_member_ids(
            session,
            allowed_entity_ids,
        )

        if scoped_member_ids is not None and not scoped_member_ids:
            return None

        stmt = self._build_base_stmt().where(User.id == int(clean_edit_key))

        if scoped_member_ids is not None:
            stmt = stmt.where(User.member_id.in_(scoped_member_ids))

        row = session.execute(stmt).one_or_none()

        if row is None:
            return None

        member_ids = {int(row.member_id)}
        user_ids = {int(row.id)}

        entity_names_by_member_id = self._build_entity_names_by_member_id(
            session,
            member_ids,
        )
        profile_names_by_user_id = self._build_profile_names_by_user_id(
            session,
            user_ids,
        )

        return self._to_row(
            row,
            entity_names_by_member_id=entity_names_by_member_id,
            profile_names_by_user_id=profile_names_by_user_id,
        )
