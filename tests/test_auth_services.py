from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appverbo.models import (
    Base,
    Entity,
    Member,
    MemberEntity,
    MemberEntityStatus,
    MemberStatus,
    User,
    UserAccountStatus,
)
from appverbo.routes.users.delete_handler import _inactivate_user_and_member_v1
from appverbo.services.auth import (
    build_user_invite_token,
    get_signup_country_options,
    parse_user_invite_token,
    upsert_user_by_email,
    validate_signup_phone_country,
)
from appverbo.services.passwords import hash_password, verify_password
from appverbo.services.user_member import (
    ensure_user_for_member,
    member_status_for_user_account_status,
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
            User.__table__,
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
        assert member.member_status == MemberStatus.ACTIVE.value

        reused_user = ensure_user_for_member(
            session,
            member,
            status=UserAccountStatus.ACTIVE.value,
            created_by_user_id=99,
        )
        session.commit()

        assert reused_user.id == created_user.id
        assert reused_user.account_status == UserAccountStatus.ACTIVE.value
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_users_member_id_unique_constraint_rejects_second_account() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        member = Member(
            full_name="Conta Unica",
            primary_phone="915111222",
            email="conta.unica@example.com",
        )
        session.add(member)
        session.flush()
        ensure_user_for_member(session, member)
        session.commit()

        session.add(
            User(
                member_id=member.id,
                login_email="segunda.conta@example.com",
                password_hash=hash_password("PasswordSegura123!"),
                account_status=UserAccountStatus.PENDING.value,
            )
        )

        try:
            session.flush()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("users.member_id deveria impedir uma segunda conta.")

        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_users_login_email_unique_constraint_rejects_duplicate() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        first_member = Member(
            full_name="Primeira Conta",
            primary_phone="915333444",
            email="email.unico@example.com",
        )
        second_member = Member(
            full_name="Segunda Conta",
            primary_phone="915555666",
            email="outro.member@example.com",
        )
        session.add_all([first_member, second_member])
        session.flush()
        ensure_user_for_member(session, first_member)
        session.commit()

        session.add(
            User(
                member_id=second_member.id,
                login_email="email.unico@example.com",
                password_hash=hash_password("PasswordSegura123!"),
                account_status=UserAccountStatus.PENDING.value,
            )
        )

        try:
            session.flush()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("users.login_email deveria impedir emails duplicados.")

        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_ensure_user_for_member_fails_if_email_belongs_to_other_member() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        first_member = Member(
            full_name="Primeiro Membro",
            primary_phone="912000111",
            email="partilhado@example.com",
        )
        second_member = Member(
            full_name="Segundo Membro",
            primary_phone="912000222",
            email="segundo@example.com",
        )
        session.add_all([first_member, second_member])
        session.flush()
        first_user = ensure_user_for_member(session, first_member)
        session.commit()

        first_user.login_email = "segundo@example.com"
        session.flush()

        try:
            ensure_user_for_member(session, second_member)
        except ValueError as exc:
            assert "outro utilizador" in str(exc)
        else:
            raise AssertionError("O helper deveria falhar para email ja ligado a outro member.")


def test_ensure_user_for_member_uses_supplied_password() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        member = Member(
            full_name="Joao Costa",
            primary_phone="912111222",
            email="joao.costa@example.com",
            member_status=MemberStatus.ACTIVE.value,
        )
        session.add(member)
        session.flush()

        user = ensure_user_for_member(
            session,
            member,
            status=UserAccountStatus.ACTIVE.value,
            password="SenhaForte123!",
        )
        session.commit()

        assert user.account_status == UserAccountStatus.ACTIVE.value
        assert member.member_status == MemberStatus.ACTIVE.value
        assert verify_password("SenhaForte123!", user.password_hash)
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_upsert_user_by_email_creates_member_and_user_together() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        user = upsert_user_by_email(
            session=session,
            email="novo.utilizador@example.com",
            full_name="Novo Utilizador",
            primary_phone="912555666",
            entity_id=None,
        )
        session.commit()

        member = session.get(Member, user.member_id)

        assert member is not None
        assert member.user_account is not None
        assert member.user_account.id == user.id
        assert session.scalar(select(func.count()).select_from(Member)) == 1
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_upsert_user_by_email_creates_user_for_existing_member_without_account() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        entity = Entity(
            entity_number=1,
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
        assert member.member_status == MemberStatus.ACTIVE.value

        link = session.execute(
            select(MemberEntity).where(
                MemberEntity.member_id == member.id,
                MemberEntity.entity_id == entity.id,
                MemberEntity.status == MemberEntityStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()
        assert link is not None


def test_inactivate_user_and_member_keeps_user_linked() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        member = Member(
            full_name="Ana Lopes",
            primary_phone="912333444",
            email="ana.lopes@example.com",
            member_status=MemberStatus.ACTIVE.value,
        )
        session.add(member)
        session.flush()

        user = ensure_user_for_member(
            session,
            member,
            status=UserAccountStatus.ACTIVE.value,
            password="SenhaForte123!",
        )
        session.commit()

        _inactivate_user_and_member_v1(session, user)
        session.commit()

        stored_user = session.get(User, user.id)
        stored_member = session.get(Member, member.id)

        assert stored_user is not None
        assert stored_user.account_status == UserAccountStatus.INACTIVE.value
        assert stored_member is not None
        assert stored_member.member_status == MemberStatus.INACTIVE.value
        assert stored_member.user_account is not None
        assert stored_member.user_account.id == user.id


def test_member_status_mapping_for_account_status() -> None:
    assert (
        member_status_for_user_account_status(UserAccountStatus.ACTIVE.value)
        == MemberStatus.ACTIVE.value
    )
    assert (
        member_status_for_user_account_status(UserAccountStatus.PENDING.value)
        == MemberStatus.ACTIVE.value
    )
    assert (
        member_status_for_user_account_status(UserAccountStatus.INACTIVE.value)
        == MemberStatus.INACTIVE.value
    )
    assert (
        member_status_for_user_account_status(UserAccountStatus.BLOCKED.value)
        == MemberStatus.INACTIVE.value
    )


def test_login_password_flow_still_valid_after_activation() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        user = upsert_user_by_email(
            session=session,
            email="login.utilizador@example.com",
            full_name="Login Utilizador",
            primary_phone="913000111",
            entity_id=None,
        )
        user.password_hash = hash_password("LoginSeguro123!")
        user.account_status = UserAccountStatus.ACTIVE.value
        session.commit()

        stored_user = session.execute(
            select(User).where(func.lower(User.login_email) == "login.utilizador@example.com")
        ).scalar_one()

        assert stored_user.member_id == user.member_id
        assert verify_password("LoginSeguro123!", stored_user.password_hash)


def test_pending_user_invite_token_keeps_member_user_identity() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        member = Member(
            full_name="Marta Convite",
            primary_phone="913222333",
            email="marta.convite@example.com",
        )
        session.add(member)
        session.flush()
        user = ensure_user_for_member(session, member)
        session.commit()

        token = build_user_invite_token(user.id, user.login_email, 15)
        payload = parse_user_invite_token(token)

        assert payload is not None
        assert payload["uid"] == user.id
        assert payload["email"] == user.login_email
        assert payload["entity_id"] == 15
        assert user.account_status == UserAccountStatus.PENDING.value
        assert member.user_account.id == user.id

        activated_user = ensure_user_for_member(
            session,
            member,
            status=UserAccountStatus.ACTIVE.value,
            password="ConviteSeguro123!",
        )
        session.commit()

        assert activated_user.id == user.id
        assert verify_password("ConviteSeguro123!", activated_user.password_hash)
        assert activated_user.account_status == UserAccountStatus.ACTIVE.value
        assert member.member_status == MemberStatus.ACTIVE.value
        assert session.scalar(select(func.count()).select_from(User)) == 1
