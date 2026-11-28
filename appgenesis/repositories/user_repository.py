from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from appgenesis.models import Entity, Member, MemberEntity, MemberEntityStatus, User, UserAccountStatus

# Perfis geridos pelo owner na aba "Administradores do sistema", em qualquer entidade.
SYSTEM_ADMIN_TYPES = frozenset({"legado", "owner"})


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, int(user_id))


def get_user_by_email_ci(session: Session, login_email: str) -> User | None:
    clean_email = (login_email or "").strip().lower()
    if not clean_email:
        return None
    return session.execute(
        select(User).where(func.lower(User.login_email) == clean_email)
    ).scalar_one_or_none()


def find_other_user_id_by_email(session: Session, login_email: str, excluded_user_id: int) -> int | None:
    return session.scalar(
        select(User.id).where(
            func.lower(User.login_email) == (login_email or "").strip().lower(),
            User.id != excluded_user_id,
        )
    )


def find_other_member_id_by_email(session: Session, email: str, excluded_member_id: int) -> int | None:
    return session.scalar(
        select(Member.id).where(
            func.lower(Member.email) == (email or "").strip().lower(),
            Member.id != excluded_member_id,
        )
    )


def get_active_entity(session: Session, entity_id: int) -> Entity | None:
    return session.execute(
        select(Entity).where(Entity.id == int(entity_id), Entity.is_active.is_(True))
    ).scalar_one_or_none()


def get_entity_name(session: Session, entity_id: int) -> str | None:
    return session.scalar(select(Entity.name).where(Entity.id == int(entity_id)).limit(1))


def list_active_entities(session: Session, entity_ids: list[int] | None) -> list[Entity]:
    """Entidades ativas por nome; `entity_ids=None` = sem filtro (so para owner)."""
    query = select(Entity).where(Entity.is_active.is_(True)).order_by(Entity.name.asc())
    if entity_ids is not None:
        query = query.where(Entity.id.in_(entity_ids or [-1]))
    return list(session.execute(query).scalars().all())


def get_primary_entity_for_member(session: Session, member_id: int) -> tuple[int | None, str]:
    entity_row = session.execute(
        select(Entity.id, Entity.name)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
        .limit(1)
    ).one_or_none()
    if entity_row is None:
        return None, "-"
    return int(entity_row.id), str(entity_row.name or "-")


def get_first_linked_entity(session: Session, member_id: int, entity_ids: list[int] | None) -> Entity | None:
    """Primeira entidade ligada ao membro (qualquer estado); `entity_ids=None` = sem filtro."""
    stmt = (
        select(Entity)
        .join(MemberEntity, MemberEntity.entity_id == Entity.id)
        .where(MemberEntity.member_id == member_id)
        .order_by(MemberEntity.id.asc())
    )
    if entity_ids is not None:
        stmt = stmt.where(Entity.id.in_(entity_ids or [-1]))
    return session.execute(stmt.limit(1)).scalar_one_or_none()


def get_active_entity_ids_for_member(session: Session, member_id: int) -> list[int]:
    rows = session.scalars(
        select(MemberEntity.entity_id)
        .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
        )
        .order_by(MemberEntity.id.asc())
    ).all()
    return list(dict.fromkeys(int(entity_id) for entity_id in rows if isinstance(entity_id, int)))


def list_active_entity_links(session: Session, member_id: int, entity_ids: list[int] | None) -> list[Any]:
    """(entity_id, name) das entidades ativas com vinculo ativo; `entity_ids=None` = sem filtro."""
    stmt = (
        select(MemberEntity.entity_id, Entity.name)
        .join(Entity, Entity.id == MemberEntity.entity_id)
        .where(
            MemberEntity.member_id == member_id,
            MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            Entity.is_active.is_(True),
        )
        .order_by(MemberEntity.id.asc())
    )
    if entity_ids is not None:
        stmt = stmt.where(MemberEntity.entity_id.in_(entity_ids or [-1]))
    return list(session.execute(stmt).all())


def list_member_links(session: Session, member_id: int) -> list[MemberEntity]:
    return list(
        session.execute(
            select(MemberEntity).where(MemberEntity.member_id == member_id).order_by(MemberEntity.id.asc())
        ).scalars().all()
    )


def list_active_users_in_entity(session: Session, entity_id: int, excluded_user_id: int) -> list[Any]:
    """(id, login_email, system_type) dos utilizadores ativos com vinculo ativo na entidade."""
    return list(
        session.execute(
            select(User.id, User.login_email, User.system_type)
            .join(MemberEntity, MemberEntity.member_id == User.member_id)
            .where(
                MemberEntity.entity_id == entity_id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                User.id != excluded_user_id,
                User.account_status == UserAccountStatus.ACTIVE.value,
            )
            .order_by(User.id.asc())
        ).all()
    )


def member_has_active_link_in(session: Session, member_id: int, entity_ids: list[int]) -> bool:
    if not entity_ids:
        return False
    return (
        session.scalar(
            select(MemberEntity.id)
            .where(
                MemberEntity.member_id == member_id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
                MemberEntity.entity_id.in_(entity_ids),
            )
            .limit(1)
        )
        is not None
    )


def member_is_within_permissions(
    session: Session,
    member_id: int,
    permissions: dict[str, Any],
    system_admin_target: bool = False,
    target_system_type: str = "",
) -> bool:
    """O ator pode gerir este membro?

    - Owner (gestao do tenant): administradores do sistema (`system_admin_target`) de qualquer
      entidade, e os membros das entidades onde ele proprio tem dados (`allowed_data_entity_ids`).
      Nao gere utilizadores comuns das entidades legado.
    - Outros (admin de entidade): so membros ('default', ou sem utilizador) com vinculo ativo
      nas entidades do seu escopo. Nunca outros administradores.
    """
    if permissions.get("can_manage_tenant_structure", permissions.get("can_manage_all_entities")):
        if system_admin_target:
            return True
        return member_has_active_link_in(
            session, member_id, sorted(set(permissions.get("allowed_data_entity_ids") or set()))
        )
    if str(target_system_type or "").strip().lower() not in ("", "default"):
        return False
    return member_has_active_link_in(
        session, member_id, sorted(set(permissions.get("allowed_entity_ids") or set()))
    )


def count_users_for_member(session: Session, member_id: int) -> int:
    return int(session.scalar(select(func.count(User.id)).where(User.member_id == member_id)) or 0)


def delete_member_with_links(session: Session, member_id: int) -> None:
    session.execute(delete(MemberEntity).where(MemberEntity.member_id == member_id))
    member = session.get(Member, member_id)
    if member is not None:
        session.delete(member)
