import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.menu_settings import update_sidebar_menu_subsequent_fields
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


def test_update_subsequent_fields_ignores_entity_id_column_by_design():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=999,
        menu_config={"subsequent_fields": []},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_subsequent_fields(
        session,
        "processo_teste_a",
        raw_fields=[
            {
                "trigger_field": "estado",
                "field_key": "motivo",
                "operator": "equals",
                "trigger_value": "inativo",
            }
        ],
    )
    session.close()

    assert ok is True
    assert error == ""
    config, entity_id = _load_config(SessionLocal, "processo_teste_a")
    assert entity_id == 999
    assert config["subsequent_fields"][0]["trigger_field"] == "estado"


def test_update_subsequent_fields_isolated_between_menu_keys():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"subsequent_fields": []},
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_b",
        entity_id=1,
        menu_config={
            "subsequent_fields": [
                {
                    "key": "subseq_preexistente",
                    "trigger_field": "estado",
                    "field_key": "motivo",
                    "operator": "equals",
                    "trigger_value": "inativo",
                }
            ]
        },
    )

    session = SessionLocal()
    update_sidebar_menu_subsequent_fields(
        session,
        "processo_teste_a",
        raw_fields=[
            {
                "trigger_field": "tipo",
                "field_key": "detalhe",
                "operator": "is_not_empty",
            }
        ],
    )
    session.close()

    config_a, _ = _load_config(SessionLocal, "processo_teste_a")
    config_b, _ = _load_config(SessionLocal, "processo_teste_b")

    assert [item["trigger_field"] for item in config_a["subsequent_fields"]] == ["tipo"]
    assert [item["key"] for item in config_b["subsequent_fields"]] == ["subseq_preexistente"]


def test_update_subsequent_fields_preserves_unrelated_menu_config_sections():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={
            "subsequent_fields": [],
            "process_lists": [{"key": "list_x", "label": "X"}],
            "visibility_scope": ["owner", "legado"],
        },
    )

    session = SessionLocal()
    update_sidebar_menu_subsequent_fields(
        session,
        "processo_teste_a",
        raw_fields=[
            {"trigger_field": "estado", "field_key": "motivo", "operator": "equals", "trigger_value": "x"}
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")

    assert config["process_lists"] == [{"key": "list_x", "label": "X"}]
    assert config["visibility_scope"] == ["owner", "legado"]
    assert len(config["subsequent_fields"]) == 1


def test_update_subsequent_fields_dedup_identical_signature_rows():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"subsequent_fields": []},
    )

    session = SessionLocal()
    update_sidebar_menu_subsequent_fields(
        session,
        "processo_teste_a",
        raw_fields=[
            {"trigger_field": "estado", "field_key": "motivo", "operator": "equals", "trigger_value": "inativo"},
            {"trigger_field": "estado", "field_key": "motivo", "operator": "equals", "trigger_value": "inativo"},
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")

    assert len(config["subsequent_fields"]) == 1


def test_update_subsequent_fields_rows_missing_trigger_or_field_are_filtered_out():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"subsequent_fields": []},
    )

    session = SessionLocal()
    update_sidebar_menu_subsequent_fields(
        session,
        "processo_teste_a",
        raw_fields=[
            {"trigger_field": "", "field_key": "", "operator": "equals", "trigger_value": ""},
            {"trigger_field": "estado", "field_key": "", "operator": "equals", "trigger_value": "x"},
            {"trigger_field": "", "field_key": "motivo", "operator": "equals", "trigger_value": "x"},
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")

    assert config["subsequent_fields"] == []


def test_update_subsequent_fields_invalid_operator_normalized_to_is_empty():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"subsequent_fields": []},
    )

    session = SessionLocal()
    update_sidebar_menu_subsequent_fields(
        session,
        "processo_teste_a",
        raw_fields=[
            {"trigger_field": "estado", "field_key": "motivo", "operator": "bogus", "trigger_value": "x"}
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")

    assert config["subsequent_fields"][0]["operator"] == "is_empty"
    assert config["subsequent_fields"][0]["trigger_value"] == ""


def test_update_subsequent_fields_equals_without_trigger_value_falls_back_to_is_empty():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"subsequent_fields": []},
    )

    session = SessionLocal()
    update_sidebar_menu_subsequent_fields(
        session,
        "processo_teste_a",
        raw_fields=[
            {"trigger_field": "estado", "field_key": "motivo", "operator": "equals", "trigger_value": ""}
        ],
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")

    assert config["subsequent_fields"][0]["operator"] == "is_empty"


def test_update_subsequent_fields_protected_menu_key_home_is_blocked():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="home",
        entity_id=1,
        menu_config={"subsequent_fields": []},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_subsequent_fields(
        session,
        "home",
        raw_fields=[
            {"trigger_field": "estado", "field_key": "motivo", "operator": "equals", "trigger_value": "x"}
        ],
    )
    session.close()

    assert ok is False
    assert error == "Este processo não permite campos subsequentes."
    config, _ = _load_config(SessionLocal, "home")
    assert config["subsequent_fields"] == []


def test_update_subsequent_fields_menu_not_found_returns_error():
    SessionLocal = _build_session_factory()

    session = SessionLocal()
    ok, error = update_sidebar_menu_subsequent_fields(
        session,
        "processo_inexistente",
        raw_fields=[
            {"trigger_field": "estado", "field_key": "motivo", "operator": "equals", "trigger_value": "x"}
        ],
    )
    session.close()

    assert ok is False
    assert error == "Menu não encontrado."
