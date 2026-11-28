"""Isolamento multi-tenant da lista de utilizadores (aba Utilizador / Administradores do sistema)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.models import Base, Entity, Member, MemberEntity, MemberEntityStatus, User
from appgenesis.services.page import _resolve_scoped_users


def _session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[Entity.__table__, Member.__table__, MemberEntity.__table__, User.__table__],
    )
    return sessionmaker(bind=engine, future=True)()


def _add_user(session, entity_ids, email, system_type="default"):
    member = Member(full_name=email, primary_phone="900", email=email)
    session.add(member)
    session.flush()
    for entity_id in entity_ids:
        session.add(
            MemberEntity(
                member_id=member.id, entity_id=entity_id, status=MemberEntityStatus.ACTIVE.value
            )
        )
    session.add(
        User(
            member_id=member.id,
            login_email=email,
            password_hash="x",
            account_status="active",
            system_type=system_type,
        )
    )
    session.flush()


def _seed():
    session = _session()
    owner = Entity(entity_number=1000, name="Owner", is_active=True, profile_scope="owner")
    a = Entity(entity_number=1001, name="A", is_active=True, profile_scope="legado")
    b = Entity(entity_number=1002, name="B", is_active=True, profile_scope="legado")
    session.add_all([owner, a, b])
    session.flush()
    _add_user(session, [owner.id], "owner@t.test", "owner")
    _add_user(session, [a.id], "a.user@t.test")
    _add_user(session, [a.id], "a.admin@t.test", "legado")
    _add_user(session, [b.id], "b.user@t.test")
    _add_user(session, [a.id, b.id], "ab@t.test")
    session.commit()
    return session, owner, a, b


def _emails(result):
    return sorted(row["login_email"] for row in result["all_users"])


def test_list_only_has_users_of_session_entity():
    session, _, a, b = _seed()
    # Ator com vinculo em A e B, sessao em A: nao pode ver utilizadores so de B.
    perms = {"selected_entity_id": a.id, "allowed_data_entity_ids": {a.id, b.id}}
    result = _resolve_scoped_users(session, perms, True, [a.id, b.id])
    assert _emails(result) == ["a.admin@t.test", "a.user@t.test", "ab@t.test"]
    assert {row["entity_number"] for row in result["all_users"]} == {1001}


def test_session_entity_without_data_access_returns_nothing():
    session, owner, a, _ = _seed()
    # Owner a olhar para A sem vinculo: dados operacionais de A ficam fechados.
    perms = {"selected_entity_id": a.id, "allowed_data_entity_ids": {owner.id}}
    assert _resolve_scoped_users(session, perms, True, [owner.id, a.id])["all_users"] == []


def test_system_admin_list_filters_types_in_sql():
    session, *_ = _seed()
    result = _resolve_scoped_users(session, {}, False, [], system_types={"legado", "owner"})
    assert _emails(result) == ["a.admin@t.test", "owner@t.test"]
