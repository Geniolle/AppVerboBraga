from unittest.mock import patch

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from appverbo.models import (
    Base,
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)
import appverbo.use_cases.users.create_user as create_user_module
from appverbo.use_cases.users.create_user import (
    execute_create_user,
    normalize_create_user_input,
)


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
            Profile.__table__,
            User.__table__,
            UserProfile.__table__,
        ],
    )
    return sessionmaker(bind=engine, future=True)


def _build_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/users/create",
            "headers": [],
        }
    )


def test_normalize_create_user_input_success() -> None:
    payload = normalize_create_user_input(
        full_name="  Joao Silva  ",
        primary_phone=" 912345678 ",
        email="  JOAO@EXAMPLE.COM ",
        profile_id=" 10 ",
        invite_delivery="link",
    )

    assert payload.clean_full_name == "Joao Silva"
    assert payload.clean_primary_phone == "912345678"
    assert payload.clean_email == "joao@example.com"
    assert payload.clean_profile_id == "10"
    assert payload.clean_invite_delivery == "link"
    assert payload.form_data["entity_id"] == ""
    assert payload.form_data["entity_name"] == ""
    assert payload.errors == []


def test_normalize_create_user_input_invalid_delivery_defaults_to_email() -> None:
    payload = normalize_create_user_input(
        full_name="Ana",
        primary_phone="999",
        email="ana@example.com",
        profile_id="",
        invite_delivery="sms",
    )

    assert payload.clean_invite_delivery == "email"


def test_normalize_create_user_input_required_fields() -> None:
    payload = normalize_create_user_input(
        full_name=" ",
        primary_phone=" ",
        email=" ",
        profile_id="",
        invite_delivery="email",
    )

    assert payload.errors == [
        "Nome completo é obrigatório.",
        "Telefone principal é obrigatório.",
        "Email é obrigatório.",
    ]


def test_execute_create_user_creates_member_user_and_profile() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        entity = Entity(entity_number=1, name="Igreja Central", is_active=True)
        profile = Profile(name="USER", is_active=True)
        session.add_all([entity, profile])
        session.commit()

        payload = normalize_create_user_input(
            full_name="Maria Gestora",
            primary_phone="913111222",
            email="maria.gestora@example.com",
            profile_id=str(profile.id),
            invite_delivery="link",
        )

        with patch.object(create_user_module, "is_admin_user", return_value=True), patch.object(
            create_user_module,
            "get_user_entity_permissions",
            return_value={
                "can_manage_all_entities": True,
                "allowed_entity_ids": {entity.id},
            },
        ), patch.object(create_user_module, "get_page_data", return_value={}), patch.object(
            create_user_module, "get_user_personal_data", return_value={}
        ), patch.object(
            create_user_module, "get_next_entity_number", return_value=1
        ), patch.object(
            create_user_module,
            "_resolve_entity_from_user_email_v2",
            return_value=(entity, ""),
        ), patch.object(
            create_user_module,
            "get_or_create_entity_superuser_profile",
            return_value=profile,
        ), patch.object(
            create_user_module,
            "build_user_invite_link",
            return_value="https://app.test/invite",
        ), patch.object(
            create_user_module, "build_users_new_url", return_value="/users/new"
        ):
            outcome = execute_create_user(
                session=session,
                request=_build_request(),
                actor_user={
                    "id": 0,
                    "login_email": "admin@example.com",
                    "full_name": "Administrador",
                },
                selected_entity_id=entity.id,
                payload=payload,
            )

        assert outcome.kind == "redirect"
        assert session.scalar(select(func.count()).select_from(Member)) == 1
        assert session.scalar(select(func.count()).select_from(User)) == 1
        assert session.scalar(select(func.count()).select_from(UserProfile)) == 1

        member = session.execute(select(Member)).scalar_one()
        user = session.execute(select(User)).scalar_one()
        user_profile = session.execute(select(UserProfile)).scalar_one()

        assert member.email == "maria.gestora@example.com"
        assert user.member_id == member.id
        assert user.login_email == "maria.gestora@example.com"
        assert user.account_status == UserAccountStatus.PENDING.value
        assert user_profile.user_id == user.id
        assert user_profile.profile_id == profile.id

        link = session.execute(
            select(MemberEntity).where(
                MemberEntity.member_id == member.id,
                MemberEntity.entity_id == entity.id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()
        assert link is not None


def test_execute_create_user_reuses_existing_member_without_user() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        entity = Entity(entity_number=1, name="Igreja Norte", is_active=True)
        profile = Profile(name="USER", is_active=True)
        member = Member(
            full_name="Carlos Base",
            primary_phone="913333444",
            email="carlos.base@example.com",
        )
        session.add_all([entity, profile, member])
        session.commit()

        payload = normalize_create_user_input(
            full_name="Carlos Atualizado",
            primary_phone="913999888",
            email="CARLOS.BASE@example.com",
            profile_id=str(profile.id),
            invite_delivery="link",
        )

        with patch.object(create_user_module, "is_admin_user", return_value=True), patch.object(
            create_user_module,
            "get_user_entity_permissions",
            return_value={
                "can_manage_all_entities": True,
                "allowed_entity_ids": {entity.id},
            },
        ), patch.object(create_user_module, "get_page_data", return_value={}), patch.object(
            create_user_module, "get_user_personal_data", return_value={}
        ), patch.object(
            create_user_module, "get_next_entity_number", return_value=1
        ), patch.object(
            create_user_module,
            "_resolve_entity_from_user_email_v2",
            return_value=(entity, ""),
        ), patch.object(
            create_user_module,
            "get_or_create_entity_superuser_profile",
            return_value=profile,
        ), patch.object(
            create_user_module,
            "build_user_invite_link",
            return_value="https://app.test/invite",
        ), patch.object(
            create_user_module, "build_users_new_url", return_value="/users/new"
        ):
            outcome = execute_create_user(
                session=session,
                request=_build_request(),
                actor_user={
                    "id": 0,
                    "login_email": "admin@example.com",
                    "full_name": "Administrador",
                },
                selected_entity_id=entity.id,
                payload=payload,
            )

        assert outcome.kind == "redirect"
        assert session.scalar(select(func.count()).select_from(Member)) == 1
        assert session.scalar(select(func.count()).select_from(User)) == 1

        stored_member = session.get(Member, member.id)
        stored_user = session.execute(select(User)).scalar_one()

        assert stored_member is not None
        assert stored_member.full_name == "Carlos Atualizado"
        assert stored_member.primary_phone == "913999888"
        assert stored_member.email == "carlos.base@example.com"
        assert stored_user.member_id == member.id
        assert stored_user.login_email == "carlos.base@example.com"
        assert stored_user.account_status == UserAccountStatus.PENDING.value
