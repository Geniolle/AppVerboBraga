from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.domains.modules.permissions import (
    ModuleAccessDenied,
    ModuleAccessGranted,
    resolve_module_access,
)
from appgenesis.models import Base, Entity
from appgenesis.models.modules import AppModule, EntityModuleEntitlement


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
            AppModule.__table__,
            EntityModuleEntitlement.__table__,
        ],
    )
    return sessionmaker(bind=engine, future=True)


def _create_entity(session) -> Entity:
    entity = Entity(name="Igreja Teste", entity_number=1)
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


def test_core_module_is_always_granted_without_entitlement() -> None:
    session_factory = _build_session_factory()
    with session_factory() as session:
        entity = _create_entity(session)
        session.add(
            AppModule(
                module_key="home",
                module_name="Home",
                is_core=True,
                is_active=True,
            )
        )
        session.commit()

        result = resolve_module_access(session, entity.id, "home")

    assert result == ModuleAccessGranted(module_key="home")


def test_paid_module_with_active_entitlement_is_granted() -> None:
    session_factory = _build_session_factory()
    with session_factory() as session:
        entity = _create_entity(session)
        session.add(
            AppModule(
                module_key="tesouraria",
                module_name="Tesouraria",
                is_core=False,
                is_active=True,
            )
        )
        session.commit()
        session.add(
            EntityModuleEntitlement(
                entity_id=entity.id,
                module_key="tesouraria",
                status="active",
            )
        )
        session.commit()

        result = resolve_module_access(session, entity.id, "tesouraria")

    assert result == ModuleAccessGranted(module_key="tesouraria")


def test_paid_module_with_inactive_entitlement_is_denied() -> None:
    session_factory = _build_session_factory()
    with session_factory() as session:
        entity = _create_entity(session)
        session.add(
            AppModule(
                module_key="tesouraria",
                module_name="Tesouraria",
                is_core=False,
                is_active=True,
            )
        )
        session.commit()
        session.add(
            EntityModuleEntitlement(
                entity_id=entity.id,
                module_key="tesouraria",
                status="inactive",
            )
        )
        session.commit()

        result = resolve_module_access(session, entity.id, "tesouraria")

    assert isinstance(result, ModuleAccessDenied)


def test_direct_access_to_unregistered_module_is_denied() -> None:
    session_factory = _build_session_factory()
    with session_factory() as session:
        entity = _create_entity(session)

        result = resolve_module_access(session, entity.id, "modulo_inexistente")

    assert isinstance(result, ModuleAccessDenied)


def test_paid_module_with_expired_entitlement_is_denied() -> None:
    session_factory = _build_session_factory()
    with session_factory() as session:
        entity = _create_entity(session)
        session.add(
            AppModule(
                module_key="tesouraria",
                module_name="Tesouraria",
                is_core=False,
                is_active=True,
            )
        )
        session.commit()
        session.add(
            EntityModuleEntitlement(
                entity_id=entity.id,
                module_key="tesouraria",
                status="active",
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            )
        )
        session.commit()

        result = resolve_module_access(session, entity.id, "tesouraria")

    assert isinstance(result, ModuleAccessDenied)


def test_inactive_module_denies_access_even_when_core() -> None:
    session_factory = _build_session_factory()
    with session_factory() as session:
        entity = _create_entity(session)
        session.add(
            AppModule(
                module_key="home",
                module_name="Home",
                is_core=True,
                is_active=False,
            )
        )
        session.commit()

        result = resolve_module_access(session, entity.id, "home")

    assert isinstance(result, ModuleAccessDenied)
