from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.admin_subprocesses.registry import require_admin_subprocess_config
from appgenesis.admin_subprocesses.repositories.entity_repository import EntityAdminRepository
from appgenesis.models import Base, Entity


def _build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=[Entity.__table__])
    return sessionmaker(bind=engine, future=True)


def test_entity_admin_repository_lists_entity_number_sorted_ascending() -> None:
    SessionLocal = _build_session_factory()
    repository = EntityAdminRepository(require_admin_subprocess_config("entidade"))

    with SessionLocal() as session:
        session.add_all(
            [
                Entity(entity_number=30, name="Entidade C", is_active=True),
                Entity(entity_number=None, name="Sem Numero A", is_active=True),
                Entity(entity_number=7, name="Entidade A", is_active=True),
                Entity(entity_number=None, name="Sem Numero B", is_active=False),
            ]
        )
        session.commit()

        rows = repository.list_rows(session)

    assert [row["entity_number"] for row in rows] == [7, 30, "", ""]
    assert [row["name"] for row in rows] == [
        "Entidade A",
        "Entidade C",
        "Sem Numero A",
        "Sem Numero B",
    ]
    assert rows[2]["id"] < rows[3]["id"]
