from unittest.mock import patch
from urllib.parse import unquote_plus

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

import appverbo.routes.users.update_handler as update_user_module
from appverbo.models import Base, Entity, Member, MemberEntity, MemberEntityStatus, User, UserAccountStatus


def _build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[
            Entity.__table__,
            Member.__table__,
            MemberEntity.__table__,
            User.__table__,
        ],
    )
    return sessionmaker(bind=engine, future=True)


def _build_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/users/update",
            "headers": [],
        }
    )


def test_update_user_persists_explicit_active_entity_and_deduplicates_same_entity_links() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        source_entity = Entity(name="Origem", entity_number=1001, is_active=True)
        target_entity = Entity(name="Destino", entity_number=1000, is_active=True)
        member = Member(
            full_name="Utilizador Base",
            primary_phone="913000111",
            email="utilizador@example.com",
        )
        user = User(
            member=member,
            login_email="utilizador@example.com",
            password_hash="hash",
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="owner",
        )
        session.add_all([source_entity, target_entity, member, user])
        session.flush()
        session.add_all(
            [
                MemberEntity(
                    member_id=member.id,
                    entity_id=source_entity.id,
                    status=MemberEntityStatus.ACTIVE.value,
                ),
                MemberEntity(
                    member_id=member.id,
                    entity_id=target_entity.id,
                    status=MemberEntityStatus.ACTIVE.value,
                ),
            ]
        )
        session.commit()
        user_id = user.id
        member_id = member.id
        source_entity_id = source_entity.id
        target_entity_id = target_entity.id

    with patch.object(update_user_module, "SessionLocal", SessionLocal), patch.object(
        update_user_module,
        "get_current_user",
        return_value={"id": 999, "login_email": "admin@example.com"},
    ), patch.object(
        update_user_module,
        "get_session_entity_id",
        return_value=source_entity_id,
    ), patch.object(
        update_user_module,
        "is_admin_user",
        return_value=True,
    ), patch.object(
        update_user_module,
        "get_user_entity_permissions",
        return_value={
            "can_manage_all_entities": True,
            "allowed_entity_ids": {source_entity_id, target_entity_id},
        },
    ), patch.object(
        update_user_module,
        "_member_is_within_permissions",
        return_value=True,
    ), patch.object(
        update_user_module,
        "_ensure_not_last_active_admin_for_member",
        return_value=(True, ""),
    ):
        response = update_user_module.update_user(
            request=_build_request(),
            user_id=str(user_id),
            full_name="Utilizador Atualizado",
            primary_phone="913999888",
            email="utilizador.atualizado@example.com",
            entity_id=str(target_entity_id),
            account_status=UserAccountStatus.ACTIVE.value,
            return_menu="administrativo",
            return_admin_tab="utilizador",
            return_target="#edit-user-card",
        )

    assert response.status_code == 303

    with SessionLocal() as session:
        stored_user = session.get(User, user_id)
        stored_member = session.get(Member, member_id)
        member_links = session.execute(
            select(MemberEntity)
            .where(MemberEntity.member_id == member_id)
            .order_by(MemberEntity.id.asc())
        ).scalars().all()

    assert stored_user is not None
    assert stored_member is not None
    assert stored_user.login_email == "utilizador.atualizado@example.com"
    assert stored_user.system_type == "owner"
    assert stored_member.email == "utilizador.atualizado@example.com"
    assert member_links[0].entity_id == target_entity_id
    assert member_links[0].status == MemberEntityStatus.ACTIVE.value
    assert member_links[1].entity_id == target_entity_id
    assert member_links[1].status == MemberEntityStatus.INACTIVE.value


def test_update_user_rejects_entity_outside_allowed_scope() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        allowed_entity = Entity(name="Permitida", entity_number=1000, is_active=True)
        forbidden_entity = Entity(name="Fora do Escopo", entity_number=1001, is_active=True)
        member = Member(
            full_name="Utilizador Base",
            primary_phone="913000111",
            email="utilizador@example.com",
        )
        user = User(
            member=member,
            login_email="utilizador@example.com",
            password_hash="hash",
            account_status=UserAccountStatus.ACTIVE.value,
            system_type="default",
        )
        session.add_all([allowed_entity, forbidden_entity, member, user])
        session.flush()
        session.add(
            MemberEntity(
                member_id=member.id,
                entity_id=allowed_entity.id,
                status=MemberEntityStatus.ACTIVE.value,
            )
        )
        session.commit()
        user_id = user.id
        member_id = member.id
        allowed_entity_id = allowed_entity.id
        forbidden_entity_id = forbidden_entity.id

    with patch.object(update_user_module, "SessionLocal", SessionLocal), patch.object(
        update_user_module,
        "get_current_user",
        return_value={"id": 999, "login_email": "admin@example.com"},
    ), patch.object(
        update_user_module,
        "get_session_entity_id",
        return_value=allowed_entity_id,
    ), patch.object(
        update_user_module,
        "is_admin_user",
        return_value=True,
    ), patch.object(
        update_user_module,
        "get_user_entity_permissions",
        return_value={
            "can_manage_all_entities": False,
            "allowed_entity_ids": {allowed_entity_id},
        },
    ), patch.object(
        update_user_module,
        "_member_is_within_permissions",
        return_value=True,
    ), patch.object(
        update_user_module,
        "_ensure_not_last_active_admin_for_member",
        return_value=(True, ""),
    ):
        response = update_user_module.update_user(
            request=_build_request(),
            user_id=str(user_id),
            full_name="Utilizador Atualizado",
            primary_phone="913999888",
            email="utilizador.atualizado@example.com",
            entity_id=str(forbidden_entity_id),
            account_status=UserAccountStatus.ACTIVE.value,
            return_menu="administrativo",
            return_admin_tab="utilizador",
            return_target="#edit-user-card",
        )

    assert response.status_code == 303
    assert "Não tem permissão para associar utilizador a esta entidade." in unquote_plus(
        response.headers["location"]
    )

    with SessionLocal() as session:
        stored_user = session.get(User, user_id)
        member_links = session.execute(
            select(MemberEntity)
            .where(MemberEntity.member_id == member_id)
            .order_by(MemberEntity.id.asc())
        ).scalars().all()

    assert stored_user is not None
    assert stored_user.login_email == "utilizador@example.com"
    assert member_links[0].entity_id == allowed_entity_id
    assert member_links[0].status == MemberEntityStatus.ACTIVE.value
