import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.menu_settings import update_sidebar_menu_process_lists
from appgenesis.models import Base, Entity, SidebarMenuSetting
from appgenesis.services.process_settings.list_service import (
    get_process_list_source_menus_v1,
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
    entity_id = row.entity_id
    session.close()
    return config, entity_id


def test_update_process_lists_isolated_by_active_entity_id():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"process_lists": []},
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=2,
        menu_config={"process_lists": []},
    )

    session = SessionLocal()
    update_sidebar_menu_process_lists(
        session,
        "processo_teste_a",
        raw_lists=[{"key": "x", "label": "X", "field_type": "manual", "items": ["1"]}],
        raw_columns=None,
        active_entity_id=2,
    )
    session.close()

    config_entity_1, entity_id_1 = _load_config(
        SessionLocal, "processo_teste_a", entity_id=1
    )
    config_entity_2, entity_id_2 = _load_config(
        SessionLocal, "processo_teste_a", entity_id=2
    )
    assert entity_id_1 == 1
    assert entity_id_2 == 2
    assert config_entity_1["process_lists"] == []
    assert config_entity_2["process_lists"][0]["key"] == "list_x"


def test_process_lists_css_is_scoped_to_the_reusable_editor():
    css_text = Path("static/css/modules/configurable_items_manager_v1.css").read_text(
        encoding="utf-8"
    )

    assert "[data-process-list-reusable-manager]" in css_text
    assert "[data-process-list-reusable-editor-block]" in css_text
    assert ".process-lists-editor-grid-v1" in css_text
    assert (
        "grid-template-columns: minmax(220px, 1fr) minmax(180px, 0.55fr) minmax(300px, 1.5fr);"
        in css_text
    )
    assert '[data-process-list-reusable-manager][data-has-source-subprocess="1"]' in css_text
    assert "grid-column: 1 / -1;" in css_text
    assert "@media (max-width: 1100px)" in css_text
    assert "@media (max-width: 768px)" in css_text


def test_process_lists_template_uses_current_css_and_scoped_editor_markup():
    template_text = Path("templates/new_user.html").read_text(encoding="utf-8")

    assert (
        "/static/css/modules/configurable_items_manager_v1.css"
        "?v=20260712-process-lists-source-subprocess-v1"
        in template_text
    )
    assert "data-process-list-reusable-manager" in template_text
    assert "data-process-list-reusable-editor-block" in template_text
    assert "process-lists-editor-grid-v1" in template_text
    assert "data-process-list-editor-source-subprocess" in template_text
    assert "data-process-list-source-subprocess-map" in template_text


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
        raw_lists=[
            {"key": "novo", "label": "Novo", "field_type": "manual", "items": ["A"]}
        ],
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
    assert config["additional_fields"] == [
        {"key": "campo_extra", "label": "Campo Extra"}
    ]
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


def test_update_process_lists_automatic_requires_source_menu():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"process_lists": []},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_lists(
        session,
        "processo_teste_a",
        raw_lists=[{"key": "auto", "label": "Auto", "field_type": "automatic"}],
        raw_columns=None,
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo_teste_a")

    assert ok is False
    assert error == "Selecione o menu de origem da lista automática."
    assert config["process_lists"] == []


def test_update_process_lists_rejects_inactive_target_menu():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"process_lists": []},
    )

    with SessionLocal() as session:
        session.execute(
            SidebarMenuSetting.__table__.update()
            .where(SidebarMenuSetting.menu_key == "processo_teste_a")
            .values(is_active=False)
        )
        session.commit()
        ok, error = update_sidebar_menu_process_lists(
            session,
            "processo_teste_a",
            raw_lists=[{"key": "auto", "label": "Auto", "field_type": "manual", "items": ["1"]}],
            raw_columns=None,
            active_entity_id=1,
        )

    assert ok is False
    assert error == "Menu não encontrado."


def test_update_process_lists_automatic_rejects_invalid_source_subprocess():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="perfil_de_autorizacao",
        entity_id=1,
        menu_config={},
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo",
        entity_id=1,
        menu_config={"process_lists": []},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_lists(
        session,
        "processo",
        raw_lists=[{
            "key": "auto",
            "label": "Auto",
            "field_type": "automatic",
            "source_menu_key": "perfil_de_autorizacao",
            "source_subprocess_key": "inexistente",
        }],
        raw_columns=None,
        active_entity_id=1,
    )
    session.close()

    assert ok is False
    assert error == "O subprocesso selecionado não pertence ao menu de origem."


def test_update_process_lists_automatic_stores_source_subprocess():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="perfil_de_autorizacao",
        entity_id=1,
        menu_config={},
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo",
        entity_id=1,
        menu_config={"process_lists": []},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_lists(
        session,
        "processo",
        raw_lists=[{
            "key": "auto",
            "label": "Auto",
            "field_type": "automatic",
            "source_menu_key": "perfil_de_autorizacao",
            "source_subprocess_key": "perfis",
        }],
        raw_columns=None,
        active_entity_id=1,
    )
    session.close()

    config, _ = _load_config(SessionLocal, "processo")

    assert ok is True
    assert error == ""
    assert config["process_lists"][0]["source_menu_key"] == "perfil_de_autorizacao"
    assert config["process_lists"][0]["source_subprocess_key"] == "perfis"


def test_update_process_lists_preserves_existing_entity_and_state_flags():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=4,
        menu_config={"process_lists": [], "other_section": {"keep": True}},
    )

    session = SessionLocal()
    row = session.execute(
        select(SidebarMenuSetting).where(
            SidebarMenuSetting.menu_key == "processo_teste_a",
            SidebarMenuSetting.entity_id == 4,
        )
    ).scalar_one()
    row.is_deleted = False
    session.commit()

    update_sidebar_menu_process_lists(
        session,
        "processo_teste_a",
        raw_lists=[{"key": "estado", "label": "Estado", "field_type": "manual", "items": ["1"]}],
        raw_columns=None,
        active_entity_id=4,
    )

    updated_row = session.execute(
        select(SidebarMenuSetting).where(
            SidebarMenuSetting.menu_key == "processo_teste_a",
            SidebarMenuSetting.entity_id == 4,
        )
    ).scalar_one()
    updated_config = json.loads(updated_row.menu_config)
    session.close()

    assert updated_row.entity_id == 4
    assert updated_row.is_active is True
    assert updated_row.is_deleted is False
    assert updated_config["other_section"] == {"keep": True}
    assert updated_config["process_lists"][0]["key"] == "list_estado"


def test_source_menus_are_active_and_isolated_by_entity():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="menu_ativo", entity_id=1, menu_config={})
    _seed_menu(SessionLocal, menu_key="menu_outra_entidade", entity_id=2, menu_config={})
    _seed_menu(SessionLocal, menu_key="menu_inativo", entity_id=1, menu_config={})
    _seed_menu(SessionLocal, menu_key="menu_eliminado", entity_id=1, menu_config={})

    with SessionLocal() as session:
        session.execute(
            SidebarMenuSetting.__table__.update()
            .where(SidebarMenuSetting.menu_key == "menu_inativo")
            .values(is_active=False)
        )
        session.execute(
            SidebarMenuSetting.__table__.update()
            .where(SidebarMenuSetting.menu_key == "menu_eliminado")
            .values(is_deleted=True)
        )
        session.commit()
        rows = get_process_list_source_menus_v1(session, 1)

    assert [row["menu_key"] for row in rows] == ["menu_ativo"]


def test_automatic_list_rejects_source_menu_from_other_entity():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo", entity_id=1, menu_config={"process_lists": []})
    _seed_menu(SessionLocal, menu_key="origem", entity_id=2, menu_config={})

    with SessionLocal() as session:
        ok, error = update_sidebar_menu_process_lists(
            session,
            "processo",
            raw_lists=[{
                "key": "auto",
                "label": "Auto",
                "field_type": "automatic",
                "source_menu_key": "origem",
            }],
            active_entity_id=1,
        )

    assert ok is False
    assert error == "O menu de origem selecionado não está disponível."


def test_legacy_automatic_without_source_is_preserved_on_general_submit():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo",
        entity_id=1,
        menu_config={
            "process_lists": [{
                "key": "list_legada",
                "label": "Legada",
                "field_type": "automatic",
                "items": [],
            }],
            "other_section": {"keep": True},
        },
    )

    with SessionLocal() as session:
        ok, error = update_sidebar_menu_process_lists(
            session,
            "processo",
            raw_lists=[{
                "key": "list_legada",
                "label": "Legada",
                "field_type": "automatic",
                "source_menu_key": "",
            }],
            active_entity_id=1,
        )

    config, _ = _load_config(SessionLocal, "processo", entity_id=1)
    assert (ok, error) == (True, "")
    assert config["process_lists"][0]["source_menu_key"] == ""
    assert config["process_lists"][0]["source_subprocess_key"] == ""
    assert config["other_section"] == {"keep": True}
