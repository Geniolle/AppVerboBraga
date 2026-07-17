import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.menu_settings import (
    PROCESS_LIST_ALL_SESSIONS_KEY,
    normalize_menu_process_lists_v3,
    normalize_menu_process_lists_v4,
    update_sidebar_menu_process_lists,
)
from appgenesis.models import Base, Entity, SidebarMenuSetting
from appgenesis.services.process_settings.list_service import (
    get_process_list_source_menus_v1,
)
from appgenesis.services.process_settings.normalizers import (
    MENU_CONFIG_DISPLAY_ORDER_KEY,
)


def test_manual_default_and_items_dedup():
    raw = [
        {
            "key": "perfil",
            "label": "Perfil",
            "items_csv": "Ativo, Inativo, Ativo, Pendente",
        }
    ]

    normalized = normalize_menu_process_lists_v3(raw)
    assert len(normalized) == 1
    item = normalized[0]
    assert item["key"] == "list_perfil"
    assert item["label"] == "Perfil"
    assert item["field_type"] == "manual"
    assert item["items"] == ["Ativo", "Inativo", "Pendente"]
    assert item["items_csv"] == "Ativo, Inativo, Pendente"


def test_automatic_allows_empty_items():
    raw = [{"key": "perfil", "label": "Perfil", "field_type": "automatic"}]
    normalized = normalize_menu_process_lists_v3(raw)
    assert len(normalized) == 1
    item = normalized[0]
    assert item["field_type"] == "automatic"
    assert item["items"] == []
    assert item["items_csv"] == ""


def test_invalid_field_type_normalized_to_manual():
    raw = [{"key": "x", "label": "X", "field_type": "unknown", "items": ["A"]}]
    normalized = normalize_menu_process_lists_v3(raw)
    assert normalized[0]["field_type"] == "manual"
    assert normalized[0]["items"] == ["A"]


def test_existing_without_field_type_assumed_manual():
    raw = [{"key": "k1", "label": "K1", "items": ["One"]}]
    normalized = normalize_menu_process_lists_v3(raw)
    assert normalized[0]["field_type"] == "manual"
    assert normalized[0]["items"] == ["One"]


def test_automatic_source_subprocess_is_preserved_in_v4():
    raw = [
        {
            "key": "auto",
            "label": "Auto",
            "field_type": "automatic",
            "source_menu_key": "perfil_de_autorizacao",
            "source_subprocess_key": "perfis",
            "source_session_key": "sistema",
        }
    ]

    normalized = normalize_menu_process_lists_v4(raw)
    assert normalized[0]["source_menu_key"] == "perfil_de_autorizacao"
    assert normalized[0]["source_subprocess_key"] == "perfis"
    assert normalized[0]["source_session_key"] == "sistema"
    assert normalized[0]["source_sidebar_section_key"] == "sistema"
    assert normalized[0]["items"] == []


def test_automatic_all_sessions_clears_menu_and_subprocess_in_v4():
    raw = [
        {
            "key": "auto",
            "label": "Auto",
            "field_type": "automatic",
            "source_session_key": PROCESS_LIST_ALL_SESSIONS_KEY,
            "source_menu_key": "perfil_de_autorizacao",
            "source_subprocess_key": "perfis",
        }
    ]

    normalized = normalize_menu_process_lists_v4(raw)
    assert normalized[0]["source_menu_key"] == ""
    assert normalized[0]["source_subprocess_key"] == ""
    assert normalized[0]["source_session_key"] == PROCESS_LIST_ALL_SESSIONS_KEY
    assert normalized[0]["source_sidebar_section_key"] == PROCESS_LIST_ALL_SESSIONS_KEY


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


def _load_config(SessionLocal, menu_key, *, entity_id=None):
    session = SessionLocal()
    stmt = select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == menu_key)
    if entity_id is not None:
        stmt = stmt.where(SidebarMenuSetting.entity_id == entity_id)
    row = session.execute(stmt).scalar_one()
    config = json.loads(row.menu_config)
    session.close()
    return config


def test_update_process_lists_accepts_all_sessions_and_persists_reserved_key():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="administrativo",
        entity_id=1,
        menu_config={
            "sidebar_sections": [
                {"key": "sistema", "label": "Sistema", "status": "ativo"},
                {"key": "geral", "label": "Geral", "status": "ativo"},
            ]
        },
    )
    _seed_menu(
        SessionLocal,
        menu_key="perfil_de_autorizacao",
        entity_id=1,
        menu_config={
            "sidebar_section": "sistema",
            MENU_CONFIG_DISPLAY_ORDER_KEY: 1,
        },
    )
    _seed_menu(
        SessionLocal,
        menu_key="menu_geral",
        entity_id=1,
        menu_config={
            "sidebar_section": "geral",
            MENU_CONFIG_DISPLAY_ORDER_KEY: 2,
        },
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo",
        entity_id=1,
        menu_config={"process_lists": []},
    )

    with SessionLocal() as session:
        ok, error = update_sidebar_menu_process_lists(
            session,
            "processo",
            raw_lists=[
                {
                    "key": "auto",
                    "label": "Auto",
                    "field_type": "automatic",
                    "source_session_key": PROCESS_LIST_ALL_SESSIONS_KEY,
                    "source_menu_key": "perfil_de_autorizacao",
                    "source_subprocess_key": "perfis",
                }
            ],
            raw_columns=None,
            active_entity_id=1,
        )

    config = _load_config(SessionLocal, "processo")

    assert ok is True
    assert error == ""
    assert config["process_lists"][0]["source_session_key"] == PROCESS_LIST_ALL_SESSIONS_KEY
    assert config["process_lists"][0]["source_sidebar_section_key"] == PROCESS_LIST_ALL_SESSIONS_KEY
    assert config["process_lists"][0]["source_menu_key"] == ""
    assert config["process_lists"][0]["source_subprocess_key"] == ""


def test_get_process_list_source_menus_preserves_structure_order():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="administrativo",
        entity_id=1,
        menu_config={
            "sidebar_sections": [
                {"key": "sistema", "label": "Sistema", "status": "ativo"},
                {"key": "geral", "label": "Geral", "status": "ativo"},
            ]
        },
    )
    _seed_menu(
        SessionLocal,
        menu_key="menu_b",
        entity_id=1,
        menu_config={
            "sidebar_section": "geral",
            MENU_CONFIG_DISPLAY_ORDER_KEY: 2,
        },
    )
    _seed_menu(
        SessionLocal,
        menu_key="menu_a",
        entity_id=1,
        menu_config={
            "sidebar_section": "sistema",
            MENU_CONFIG_DISPLAY_ORDER_KEY: 1,
        },
    )

    with SessionLocal() as session:
        rows = get_process_list_source_menus_v1(session, 1)

    menu_keys = [row["menu_key"] for row in rows]
    assert "menu_a" in menu_keys
    assert "menu_b" in menu_keys
    assert menu_keys.index("menu_a") < menu_keys.index("menu_b")
    assert len({row["menu_key"] for row in rows}) == len(rows)
