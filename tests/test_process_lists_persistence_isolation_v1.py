import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from appgenesis.menu_settings import (
    get_sidebar_menu_settings,
    update_sidebar_menu_process_lists,
)
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
    assert ".configurable-items-responsive-wrap-v1" in css_text
    assert ".configurable-items-responsive-table-v1" in css_text
    assert ".configurable-items-responsive-hidden-v1" in css_text
    assert (
        "grid-template-columns: repeat(3, minmax(0, 1fr));"
        in css_text
    )
    assert "grid-column: 1 / -1;" in css_text
    assert "@media (max-width: 1100px)" in css_text
    assert "@media (max-width: 768px)" in css_text


def test_process_lists_template_uses_current_css_and_scoped_editor_markup():
    template_text = Path("templates/new_user.html").read_text(encoding="utf-8")

    assert (
        "/static/css/modules/configurable_items_manager_v1.css"
        "?v=20260717-process-lists-responsive-partition-v2"
        in template_text
    )
    assert "data-process-list-reusable-manager" in template_text
    assert "data-process-list-reusable-editor-block" in template_text
    assert "process-lists-editor-grid-v1" in template_text
    assert "data-process-list-editor-source-subprocess" in template_text
    assert "data-process-list-source-subprocess-map" in template_text


def _extract_lista_tab_html() -> str:
    template_text = Path("templates/new_user.html").read_text(encoding="utf-8")
    start = template_text.index('id="settings-tab-lista"')
    end = template_text.index('id="settings-tab-campos-subsequentes"', start)
    return template_text[start:end]


def test_process_lists_entity_field_uses_entity_number_not_entity_name():
    lista_tab_html = _extract_lista_tab_html()

    assert "selected_entity_number" in lista_tab_html
    assert "current_user_entity_name" not in lista_tab_html
    assert 'value="{{ selected_entity_number }}"' in lista_tab_html
    assert 'data-entity-number="{{ selected_entity_number }}"' in lista_tab_html


def test_process_lists_columns_section_is_not_rendered_in_lista_tab():
    lista_tab_html = _extract_lista_tab_html()

    assert "data-process-list-columns-manager" not in lista_tab_html
    assert "Colunas da listagem do processo" not in lista_tab_html


def test_process_lists_columns_configured_hidden_input_is_not_forced_to_one():
    lista_tab_html = _extract_lista_tab_html()

    assert 'name="process_list_columns_configured" value="1"' not in lista_tab_html
    assert 'name="process_list_columns_configured" value="0"' in lista_tab_html


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
        menu_config={"sidebar_section": "sistema"},
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
            "source_session_key": "sistema",
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
        menu_key="administrativo",
        entity_id=1,
        menu_config={
            "sidebar_sections": [
                {"key": "sistema", "label": "Sistema", "status": "ativo"},
                {"key": "definicoes", "label": "Definições", "status": "inativo"},
            ]
        },
    )
    _seed_menu(
        SessionLocal,
        menu_key="perfil_de_autorizacao",
        entity_id=1,
        menu_config={"sidebar_section": "sistema"},
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
            "source_session_key": "sistema",
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
    assert config["process_lists"][0]["source_session_key"] == "sistema"
    assert config["process_lists"][0]["source_menu_key"] == "perfil_de_autorizacao"
    assert config["process_lists"][0]["source_subprocess_key"] == "perfis"


def test_update_process_lists_automatic_rejects_inactive_source_session():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="administrativo",
        entity_id=1,
        menu_config={
            "sidebar_sections": [
                {"key": "sistema", "label": "Sistema", "status": "ativo"},
                {"key": "definicoes", "label": "Definições", "status": "inativo"},
            ]
        },
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo",
        entity_id=1,
        menu_config={"process_lists": []},
    )
    _seed_menu(
        SessionLocal,
        menu_key="perfil_de_autorizacao",
        entity_id=1,
        menu_config={"sidebar_section": "definicoes"},
    )

    session = SessionLocal()
    ok, error = update_sidebar_menu_process_lists(
        session,
        "processo",
        raw_lists=[{
            "key": "auto",
            "label": "Auto",
            "field_type": "automatic",
            "source_session_key": "definicoes",
            "source_menu_key": "perfil_de_autorizacao",
        }],
        raw_columns=None,
        active_entity_id=1,
    )
    session.close()

    assert ok is False
    assert error == "A sessão selecionada não está disponível."


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

    menu_keys = [row["menu_key"] for row in rows]
    assert "menu_ativo" in menu_keys
    assert "menu_inativo" not in menu_keys
    assert "menu_eliminado" not in menu_keys
    assert "menu_outra_entidade" not in menu_keys


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


# ###################################################################################
# ROOT CAUSE B - LEITURA DE get_sidebar_menu_settings ISOLADA POR ENTIDADE ATIVA
# ###################################################################################


def test_get_sidebar_menu_settings_isolates_process_lists_by_entity():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_isolado",
        entity_id=1,
        menu_config={
            "process_lists": [
                {"key": "list_a", "label": "Lista A", "field_type": "manual", "items": ["1"]}
            ]
        },
    )
    _seed_menu(
        SessionLocal,
        menu_key="processo_isolado",
        entity_id=2,
        menu_config={
            "process_lists": [
                {"key": "list_b", "label": "Lista B", "field_type": "manual", "items": ["2"]}
            ]
        },
    )

    with SessionLocal() as session:
        settings_entity_1 = get_sidebar_menu_settings(session, active_entity_id=1)
    with SessionLocal() as session:
        settings_entity_2 = get_sidebar_menu_settings(session, active_entity_id=2)

    item_1 = next(row for row in settings_entity_1 if row["key"] == "processo_isolado")
    item_2 = next(row for row in settings_entity_2 if row["key"] == "processo_isolado")

    assert [entry["key"] for entry in item_1["process_lists"]] == ["list_a"]
    assert [entry["key"] for entry in item_2["process_lists"]] == ["list_b"]


def test_get_sidebar_menu_settings_isolates_is_active_and_is_deleted_by_entity():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_estado", entity_id=1, menu_config={})
    _seed_menu(SessionLocal, menu_key="processo_estado", entity_id=2, menu_config={})

    with SessionLocal() as session:
        session.execute(
            SidebarMenuSetting.__table__.update()
            .where(
                SidebarMenuSetting.menu_key == "processo_estado",
                SidebarMenuSetting.entity_id == 1,
            )
            .values(is_active=False)
        )
        session.commit()

    with SessionLocal() as session:
        settings_entity_1 = get_sidebar_menu_settings(session, active_entity_id=1)
    with SessionLocal() as session:
        settings_entity_2 = get_sidebar_menu_settings(session, active_entity_id=2)

    item_1 = next(row for row in settings_entity_1 if row["key"] == "processo_estado")
    item_2 = next(row for row in settings_entity_2 if row["key"] == "processo_estado")

    assert item_1["is_active"] is False
    assert item_2["is_active"] is True


def test_get_sidebar_menu_settings_reflects_freshly_saved_list_for_same_entity():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"process_lists": []},
    )

    with SessionLocal() as session:
        update_sidebar_menu_process_lists(
            session,
            "processo_teste_a",
            raw_lists=[
                {"key": "nova", "label": "Lista Nova", "field_type": "manual", "items": ["1", "2"]}
            ],
            raw_columns=None,
            active_entity_id=1,
        )

    with SessionLocal() as session:
        settings = get_sidebar_menu_settings(session, active_entity_id=1)

    item = next(row for row in settings if row["key"] == "processo_teste_a")
    assert [entry["label"] for entry in item["process_lists"]] == ["Lista nova"]


def test_get_sidebar_menu_settings_defaults_to_resolved_entity_when_not_specified():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={
            "process_lists": [
                {"key": "list_x", "label": "X", "field_type": "manual", "items": ["1"]}
            ]
        },
    )

    with SessionLocal() as session:
        settings = get_sidebar_menu_settings(session)

    item = next(row for row in settings if row["key"] == "processo_teste_a")
    assert [entry["key"] for entry in item["process_lists"]] == ["list_x"]


def test_update_process_lists_menu_missing_for_active_entity_returns_error():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_teste_a",
        entity_id=1,
        menu_config={"process_lists": []},
    )

    with SessionLocal() as session:
        ok, error = update_sidebar_menu_process_lists(
            session,
            "processo_teste_a",
            raw_lists=[
                {"key": "x", "label": "X", "field_type": "manual", "items": ["1"]}
            ],
            raw_columns=None,
            active_entity_id=2,
        )

    assert ok is False
    assert error == "Menu não encontrado."
