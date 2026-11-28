"""entity_menu_data: dados por entidade dentro do menu compartilhado (sem sobrescrever outra entidade)."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from appgenesis.services.entity_menu_data import (
    ENTITY_MENU_DATA_TABLE_SQL,
    get_entity_menu_data,
    set_entity_menu_data,
)


def _session():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(ENTITY_MENU_DATA_TABLE_SQL))
    return sessionmaker(bind=engine)()


def test_get_returns_default_when_missing():
    session = _session()
    assert get_entity_menu_data(session, 1, "administrativo", "authorization_functions", []) == []


def test_each_entity_keeps_its_own_value():
    session = _session()
    set_entity_menu_data(session, 1, "administrativo", "authorization_functions", [{"key": "a"}])
    set_entity_menu_data(session, 2, "administrativo", "authorization_functions", [{"key": "b"}])
    assert get_entity_menu_data(session, 1, "administrativo", "authorization_functions") == [{"key": "a"}]
    assert get_entity_menu_data(session, 2, "administrativo", "authorization_functions") == [{"key": "b"}]


def test_set_overwrites_only_same_entity_and_key():
    session = _session()
    set_entity_menu_data(session, 1, "administrativo", "authorization_functions", ["x"])
    set_entity_menu_data(session, 1, "administrativo", "authorization_functions", ["y"])
    set_entity_menu_data(session, 1, "administrativo", "authorization_profile_fields", "z")
    assert get_entity_menu_data(session, 1, "administrativo", "authorization_functions") == ["y"]
    assert get_entity_menu_data(session, 1, "administrativo", "authorization_profile_fields") == "z"


def test_entity_menu_data_is_in_metadata_so_autogenerate_never_drops_it():
    from appgenesis.models import Base

    table = Base.metadata.tables["entity_menu_data"]
    assert [c.name for c in table.primary_key.columns] == ["entity_id", "menu_key", "data_key"]
