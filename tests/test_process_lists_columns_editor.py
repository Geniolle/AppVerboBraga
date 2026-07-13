import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.menu_settings import update_sidebar_menu_process_lists
from appgenesis.models import Base, Entity, SidebarMenuSetting


####################################################################################
# (1) PERSISTENCIA COMPATIVEL DE LISTAS E COLUNAS
####################################################################################


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


def test_process_lists_save_preserves_reusable_lists_and_columns(monkeypatch) -> None:
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="perfil_de_autorizacao",
        entity_id=1,
        menu_config={"process_lists": [], "process_list_config": {"columns": []}},
    )
    session = SessionLocal()
    menu_config = {
        "additional_fields": [
            {"key": "perfil", "label": "Perfil", "field_type": "text"},
            {
                "key": "nome_do_perfil",
                "label": "Nome do perfil",
                "field_type": "text",
            },
        ],
        "process_list_config": {"columns": []},
    }
    monkeypatch.setattr("appgenesis.menu_settings._menu_exists", lambda *_args: True)
    monkeypatch.setattr(
        "appgenesis.menu_settings._load_menu_config",
        lambda *_args: dict(menu_config),
    )
    monkeypatch.setattr(
        "appgenesis.menu_settings.get_menu_process_selectable_field_options",
        lambda *_args: [
            {"key": "perfil", "label": "Perfil"},
            {"key": "nome_do_perfil", "label": "Nome do perfil"},
        ],
    )

    ok, error = update_sidebar_menu_process_lists(
        session=session,
        menu_key="perfil_de_autorizacao",
        raw_lists=[
            {"key": "estados", "label": "Estados", "items_csv": "Ativo,Inativo"}
        ],
        raw_columns=[
            {
                "key": "perfil",
                "label": "Perfil",
                "field_key": "perfil",
                "source_kind": "field",
                "always_visible": "1",
                "responsive_priority": "2",
            }
        ],
        active_entity_id=1,
    )

    assert ok is True
    assert error == ""
    stored = json.loads(
        session.execute(
            select(SidebarMenuSetting.menu_config).where(
                SidebarMenuSetting.menu_key == "perfil_de_autorizacao",
                SidebarMenuSetting.entity_id == 1,
            )
        ).scalar_one()
    )
    session.close()
    assert stored["process_lists"][0]["label"] == "Estados"
    assert stored["process_list_columns"] == stored["process_list_config"]["columns"]
    assert stored["process_list_columns"][0] == {
        "key": "perfil",
        "label": "Perfil",
        "source_kind": "field",
        "field_key": "perfil",
        "always_visible": True,
        "responsive_priority": 2,
    }


def test_legacy_process_lists_client_does_not_erase_existing_columns(monkeypatch) -> None:
    SessionLocal = _build_session_factory()
    existing_columns = [
        {
            "key": "perfil",
            "label": "Perfil",
            "source_kind": "field",
            "field_key": "perfil",
            "always_visible": True,
            "responsive_priority": 1,
        }
    ]
    _seed_menu(
        SessionLocal,
        menu_key="perfil_de_autorizacao",
        entity_id=1,
        menu_config={"process_lists": [], "process_list_columns": existing_columns},
    )
    session = SessionLocal()

    ok, _error = update_sidebar_menu_process_lists(
        session=session,
        menu_key="perfil_de_autorizacao",
        raw_lists=[{"key": "estados", "label": "Estados", "items_csv": "Ativo"}],
        active_entity_id=1,
    )

    assert ok is True
    stored = json.loads(
        session.execute(
            select(SidebarMenuSetting.menu_config).where(
                SidebarMenuSetting.menu_key == "perfil_de_autorizacao",
                SidebarMenuSetting.entity_id == 1,
            )
        ).scalar_one()
    )
    session.close()
    assert stored["process_list_columns"] == existing_columns
