from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appverbo.models import (
    Base,
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    Profile,
    User,
    UserAccountStatus,
    UserProfile,
)
from appverbo.admin_subprocesses.repositories.user_repository import UserAdminRepository
from appverbo.admin_subprocesses.utilizador.configuracao import UTILIZADOR_CONFIG
from appverbo.services.auth import (
    build_user_invite_token,
    ensure_user_for_member,
    get_signup_country_options,
    hash_password,
    parse_user_invite_token,
    upsert_user_by_email,
    validate_signup_phone_country,
    verify_password,
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


def test_hash_password_and_verify() -> None:
    raw_password = "SenhaForte123!"
    stored_hash = hash_password(raw_password)
    assert stored_hash.startswith("pbkdf2_sha256$")
    assert verify_password(raw_password, stored_hash)
    assert not verify_password("SenhaErrada", stored_hash)


def test_user_invite_token_roundtrip() -> None:
    token = build_user_invite_token(10, "user@example.com", 42)
    payload = parse_user_invite_token(token)
    assert payload is not None
    assert payload["uid"] == 10
    assert payload["email"] == "user@example.com"
    assert payload["entity_id"] == 42


def test_signup_country_options_include_supported_codes() -> None:
    options = get_signup_country_options()

    assert {
        "value": "PT",
        "label": "Portugal",
        "calling_code": "+351",
        "placeholder": "+351 910 000 000",
    } in options
    assert {
        "value": "BR",
        "label": "Brasil",
        "calling_code": "+55",
        "placeholder": "+55 11 99999-9999",
    } in options


def test_validate_signup_phone_country_accepts_matching_calling_code() -> None:
    assert validate_signup_phone_country("PT", "+351 912 345 678") == ""
    assert validate_signup_phone_country("BR", "+55 11 99999-9999") == ""


def test_validate_signup_phone_country_rejects_wrong_calling_code() -> None:
    assert (
        validate_signup_phone_country("PT", "+55 11 99999-9999")
        == "Telefone inválido para Portugal. Use o código +351."
    )
    assert (
        validate_signup_phone_country("BR", "+351 912 345 678")
        == "Telefone inválido para Brasil. Use o código +55."
    )


def test_ensure_user_for_member_creates_and_reuses_user() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        member = Member(
            full_name="Ana Silva",
            primary_phone="912345678",
            email="Ana.Silva@Example.com",
            member_status=MemberStatus.ACTIVE.value,
        )
        session.add(member)
        session.flush()

        created_user = ensure_user_for_member(
            session,
            member,
            status=UserAccountStatus.PENDING.value,
            created_by_user_id=77,
        )
        session.commit()

        assert created_user.member_id == member.id
        assert created_user.login_email == "ana.silva@example.com"
        assert created_user.account_status == UserAccountStatus.PENDING.value
        assert created_user.created_by_user_id == 77
        assert created_user.password_hash.startswith("pbkdf2_sha256$")

        reused_user = ensure_user_for_member(
            session,
            member,
            status=UserAccountStatus.ACTIVE.value,
            created_by_user_id=99,
        )
        session.commit()

        assert reused_user.id == created_user.id
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_upsert_user_by_email_creates_user_for_existing_member_without_account() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        entity = Entity(
            internal_number=1,
            name="Igreja Central",
            is_active=True,
        )
        session.add(entity)
        session.flush()

        member = Member(
            full_name="Joao Pereira",
            primary_phone="912000111",
            email="joao@example.com",
            member_status=MemberStatus.ACTIVE.value,
        )
        session.add(member)
        session.flush()
        session.commit()

        user = upsert_user_by_email(
            session=session,
            email="JOAO@example.com",
            full_name="Joao Pereira",
            primary_phone="912000111",
            entity_id=entity.id,
        )
        session.commit()

        assert user.member_id == member.id
        assert user.login_email == "joao@example.com"
        assert user.account_status == UserAccountStatus.ACTIVE.value
        assert user.password_hash.startswith("pbkdf2_sha256$")
        assert session.scalar(select(func.count()).select_from(User)) == 1
        assert session.scalar(select(func.count()).select_from(MemberEntity)) == 1

        link = session.execute(
            select(MemberEntity).where(
                MemberEntity.member_id == member.id,
                MemberEntity.entity_id == entity.id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()
        assert link is not None


def test_delete_inactive_user_physically_removes_user_and_profiles() -> None:
    SessionLocal = _build_session_factory()
    repository = UserAdminRepository(UTILIZADOR_CONFIG)

    with SessionLocal() as session:
        member = Member(
            full_name="Ana Lopes",
            primary_phone="912333444",
            email="ana.lopes@example.com",
            member_status=MemberStatus.ACTIVE.value,
        )
        profile = Profile(
            name="Admin",
            is_active=True,
        )
        session.add_all([member, profile])
        session.flush()

        user = User(
            member_id=member.id,
            login_email="ana.lopes@example.com",
            password_hash=hash_password("SenhaForte123!"),
            account_status=UserAccountStatus.INACTIVE.value,
        )
        session.add(user)
        session.flush()

        session.add(
            UserProfile(
                user_id=user.id,
                profile_id=profile.id,
                is_active=True,
            )
        )
        session.commit()

        repository.delete_inactive_user(session=session, user=user)
        session.commit()

        assert session.get(User, user.id) is None
        assert session.scalar(select(func.count()).select_from(UserProfile)) == 0
        assert session.get(Member, member.id) is not None
