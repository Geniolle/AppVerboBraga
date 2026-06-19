from __future__ import annotations

from typing import Any

from sqlalchemy import select

from appverbo.admin_subprocesses.repositories.base import BaseAdminSubprocessRepository
from appverbo.models import Member, MemberEntity, MemberEntityStatus, User
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

    Esta primeira versão é propositalmente segura:
    - lista utilizadores;
    - separa ativos/inativos através de is_active;
    - localiza dados para edição;
    - não altera ainda o fluxo legado de criação/edição.
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

        return {int(member_id) for member_id in rows if member_id is not None}

    def _to_row(self, user: User) -> dict[str, Any]:
        member = user.member
        normalized_status = normalize_user_account_status_v1(user.account_status)
        is_active = is_user_account_status_active_v1(normalized_status)

        full_name = ""
        primary_phone = ""

        if member is not None:
            full_name = str(member.full_name or "").strip()
            primary_phone = str(member.primary_phone or "").strip()

        login_email = str(user.login_email or "").strip().lower()

        return {
            "id": user.id,
            "key": str(user.id or ""),
            "member_id": user.member_id,
            "full_name": full_name,
            "name": full_name,
            "label": full_name or login_email,
            "login_email": login_email,
            "email": login_email,
            "primary_phone": primary_phone,
            "phone": primary_phone,
            "account_status": normalized_status,
            "status": normalized_status,
            "status_label": user_account_status_label_pt_v1(normalized_status),
            "is_active": is_active,
            "created_at": user.created_at,
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

        stmt = (
            select(User)
            .join(Member, Member.id == User.member_id)
            .order_by(User.id.desc())
        )

        if scoped_member_ids is not None:
            if not scoped_member_ids:
                return []

            stmt = stmt.where(User.member_id.in_(scoped_member_ids))

        users = session.execute(stmt).scalars().all()

        return [self._to_row(user) for user in users]

    def get_for_edit(
        self,
        session: Any,
        edit_key: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        clean_edit_key = str(edit_key or "").strip()

        if not clean_edit_key.isdigit():
            return None

        user = session.get(User, int(clean_edit_key))

        if user is None:
            return None

        allowed_entity_ids = self._resolve_allowed_entity_ids(context)
        scoped_member_ids = self._resolve_scoped_member_ids(
            session,
            allowed_entity_ids,
        )

        if scoped_member_ids is not None and int(user.member_id) not in scoped_member_ids:
            return None

        return self._to_row(user)
