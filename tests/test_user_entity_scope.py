from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.models import Base, Entity
from appgenesis.services.user_entity_scope import get_entities_for_user_edit_form_v1


def _build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=[Entity.__table__])
    return sessionmaker(bind=engine, future=True)


def test_get_entities_for_user_edit_form_filters_active_entities_and_orders_by_number() -> None:
    SessionLocal = _build_session_factory()

    with SessionLocal() as session:
        entity_b = Entity(name="Entidade B", entity_number=1001, is_active=True)
        entity_a = Entity(name="Entidade A", entity_number=1000, is_active=True)
        entity_without_number = Entity(name="Sem Numero", entity_number=None, is_active=True)
        inactive_entity = Entity(name="Inativa", entity_number=999, is_active=False)
        session.add_all([entity_b, entity_a, entity_without_number, inactive_entity])
        session.commit()

        rows = get_entities_for_user_edit_form_v1(
            session,
            {
                "can_manage_all_entities": True,
                "allowed_entity_ids": {
                    entity_b.id,
                    entity_a.id,
                    entity_without_number.id,
                    inactive_entity.id,
                },
            },
        )

    assert [row["entity_number"] for row in rows] == [1000, 1001]
    assert [row["id"] for row in rows] == [entity_a.id, entity_b.id]
