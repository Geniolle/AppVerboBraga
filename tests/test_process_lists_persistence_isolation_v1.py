import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.menu_settings import update_sidebar_menu_process_lists
from appgenesis.models import Base, Entity, SidebarMenuSetting


def _build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[Entity.__table__, SidebarMenuSetting.__table__],
    )
    return sessionmaker(bind=engine, future=True)


def _seed_menu(SessionLocal, *, menu_key, entity_id, menu_config):
    session = SessionLocal()
    row = SidebarMenuSetting(
        entity_id=entity_id,
        menu_key=menu_key,
        menu_label=menu_key,
        menu_config=json.dumps(menu_config),
    )
    session.add(row)
    session.commit()
    session.close()


def _load_config(SessionLocal, menu_key):
    session = SessionLocal()
    row = session.execute(
        select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == menu_key)
    ).scalar_one()
    config = json.loads(row.menu_config)
    entity_id = row.entity_id
    session.close()
    return config, entity_id


def test_update_process_lists_ignores_entity_id_column_by_design():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=999,
        menu_config={"process_lists": []},
    )

    session = SessionLocal()
    update_sidebar_menu_process_lists(
        session,
        "processo_teste_a",
        raw_lists=[{"key": "x", "label": "X", "field_type": "manual", "items": ["1"]}],
        raw_columns=None,
    )
    session.close()

    config, entity_id = _load_config(SessionLocal, "processo_teste_a")
    assert entity_id == 999
    assert config["process_lists"][0]["key"] == "list_x"


def test_update_process_lists_isolated_between_menu_keys():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"process_lists": []},
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_b",
        entity_id=1,
        menu_config={
            "process_lists": [
                {
                    "key": "list_preexistente",
                    "label": "Preexistente",
                    "field_type": "manual",
                    "items": ["Z"],
                }
            ]
        },
    )

    session = SessionLocal()
    update_sidebar_menu_process_lists(
        session,
        "processo_teste_a",
        raw_lists=[{"key": "novo", "label": "Novo", "field_type": "manual", "items": ["A"]}],
        raw_columns=None,
    )
    session.close()

    config_a, _ = _load_config(SessionLocal, "processo_teste_a")
    config_b, _ = _load_config(SessionLocal, "processo_teste_b")

    assert [item["key"] for item in config_a["process_lists"]] == ["list_novo"]
    assert [item["key"] for item in config_b["process_lists"]] == ["list_preexistente"]


def test_update_process_lists_preserves_unrelated_menu_config_sections():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={
            "process_lists": [],
            "visibility_scope": ["owner", "legado"],
            "additional_fields": [{"key": "campo_extra", "label": "Campo Extra"}],
        },
    )

    session = SessionLocal()
    update_sidebar_menu_process_lists(
        session,
        "processo_teste_a",
        raw_lists=[{"key": "x", "label": "X", "field_type": "manual", "items": ["1"]}],
        raw_columns=None,
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")

    assert config["visibility_scope"] == ["owner", "legado"]
    assert config["additional_fields"] == [{"key": "campo_extra", "label": "Campo Extra"}]
    assert config["process_lists"][0]["key"] == "list_x"


def test_update_process_lists_legacy_rows_without_field_type_assumed_manual():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"process_lists": []},
    )

    session = SessionLocal()
    update_sidebar_menu_process_lists(
        session,
        "processo_teste_a",
        raw_lists=[{"key": "legado", "label": "Legado", "items": ["Um"]}],
        raw_columns=None,
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")

    assert config["process_lists"][0]["field_type"] == "manual"
    assert config["process_lists"][0]["items"] == ["Um"]


def test_update_process_lists_automatic_allows_empty_items():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"process_lists": []},
    )

    session = SessionLocal()
    update_sidebar_menu_process_lists(
        session,
        "processo_teste_a",
        raw_lists=[{"key": "auto", "label": "Auto", "field_type": "automatic"}],
        raw_columns=None,
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")

    assert config["process_lists"][0]["field_type"] == "automatic"
    assert config["process_lists"][0]["items"] == []
