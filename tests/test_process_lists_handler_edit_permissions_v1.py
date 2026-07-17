import json
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

import appgenesis.routes.profile.process_settings.list_handlers as settings_handlers_module
from appgenesis.models import Base, Entity, SidebarMenuSetting


MENU_KEY = "processo_teste_permissoes"


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


def _seed_menu(SessionLocal, *, menu_config, entity_id=1, menu_key=MENU_KEY):
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


def _load_config(SessionLocal):
    session = SessionLocal()
    row = session.execute(
        select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == MENU_KEY)
    ).scalar_one()
    config = json.loads(row.menu_config)
    session.close()
    return config


def _build_request() -> Request:
    return Request(
        {"type": "http", "method": "POST", "path": "/users/new", "headers": []}
    )


def _call_handler(
    SessionLocal,
    current_user,
    is_admin,
    permissions,
    *,
    session_entity_id=1,
    **form_overrides,
):
    form = dict(
        menu_key=MENU_KEY,
        process_list_key=[],
        process_list_label=[],
        process_list_items_csv=[],
        process_list_field_type=[],
        process_list_source_menu_key=[],
        process_list_source_subprocess_key=[],
        process_list_status=[],
        process_list_column_key=[],
        process_list_column_label=[],
        process_list_column_field_key=[],
        process_list_column_source_kind=[],
        process_list_column_always_visible=[],
        process_list_column_responsive_priority=[],
        process_list_columns_configured="",
        redirect_menu="administrativo",
        redirect_target="#settings-menu-edit-card",
        return_url="",
    )
    form.update(form_overrides)

    with (
        patch.object(settings_handlers_module, "SessionLocal", SessionLocal),
        patch.object(
            settings_handlers_module, "get_current_user", return_value=current_user
        ),
        patch.object(settings_handlers_module, "is_admin_user", return_value=is_admin),
        patch.object(
            settings_handlers_module,
            "get_session_entity_id",
            return_value=session_entity_id,
        ),
        patch.object(
            settings_handlers_module,
            "get_user_entity_permissions",
            return_value=permissions,
        ),
    ):
        return settings_handlers_module.edit_sidebar_menu_process_lists_handler(
            request=_build_request(), **form
        )


def test_edit_process_lists_requires_login():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"process_lists": []})
    response = _call_handler(
        SessionLocal, current_user=None, is_admin=False, permissions={}
    )

    assert response.status_code == 302
    assert (
        response.headers["location"]
        == "/login?error=Efetue%20login%20para%20continuar."
    )
    assert _load_config(SessionLocal)["process_lists"] == []


def test_edit_process_lists_blocks_non_admin():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"process_lists": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "user@example.com"},
        is_admin=False,
        permissions={},
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert (
        "Apenas%20administradores%20podem%20alterar%20listas%20do%20processo."
        in location
    )
    assert "settings_tab=lista" in location
    assert _load_config(SessionLocal)["process_lists"] == []


def test_edit_process_lists_blocks_admin_non_owner():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"process_lists": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "admin@example.com"},
        is_admin=True,
        permissions={
            "can_manage_tenant_structure": False,
            "can_manage_all_entities": False,
        },
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20Owner%20pode%20configurar%20listas%20do%20processo." in location
    assert "settings_tab=lista" in location
    assert _load_config(SessionLocal)["process_lists"] == []


def test_edit_process_lists_uses_session_entity_id_not_form_value():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"process_lists": []}, entity_id=1)
    _seed_menu(SessionLocal, menu_config={"process_lists": []}, entity_id=2)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        session_entity_id=2,
        process_list_key=["a"],
        process_list_label=["Lista A"],
        process_list_items_csv=["1,2"],
        process_list_field_type=["manual"],
    )

    assert response.status_code == 303
    entity_1_session = SessionLocal()
    entity_1_row = entity_1_session.execute(
        select(SidebarMenuSetting).where(
            SidebarMenuSetting.menu_key == MENU_KEY,
            SidebarMenuSetting.entity_id == 1,
        )
    ).scalar_one()
    entity_2_row = entity_1_session.execute(
        select(SidebarMenuSetting).where(
            SidebarMenuSetting.menu_key == MENU_KEY,
            SidebarMenuSetting.entity_id == 2,
        )
    ).scalar_one()
    entity_1_config = json.loads(entity_1_row.menu_config)
    entity_2_config = json.loads(entity_2_row.menu_config)
    entity_1_session.close()

    assert entity_1_config["process_lists"] == []
    assert entity_2_config["process_lists"][0]["label"] == "Lista a"


def test_edit_process_lists_owner_success_creates_and_edits_lists():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"process_lists": []})
    _seed_menu(
        SessionLocal,
        menu_config={"process_lists": [], "sidebar_section": "sistema"},
        menu_key="menu_origem",
    )

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        process_list_key=["a", "b"],
        process_list_label=["Lista A", "Lista B"],
        process_list_items_csv=["1,2", ""],
        process_list_field_type=["manual", "automatic"],
        process_list_source_session_key=["", "sistema"],
        process_list_source_menu_key=["", "menu_origem"],
        process_list_source_subprocess_key=["", ""],
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "target=settings-menu-edit-card" in location
    assert "appgenesis_after_save=1" in location
    assert "settings_tab=lista" in location
    assert "settings_edit_key=" in location
    assert "settings_action=edit" in location
    assert "Listas%20do%20processo%20atualizadas%20com%20sucesso." in location

    process_lists = _load_config(SessionLocal)["process_lists"]
    assert [item["label"] for item in process_lists] == ["Lista a", "Lista b"]
    assert [item["field_type"] for item in process_lists] == ["manual", "automatic"]
    assert process_lists[0]["items"] == ["1", "2"]
    assert process_lists[1]["items"] == []
    assert process_lists[1]["source_session_key"] == "sistema"
    assert process_lists[1]["source_menu_key"] == "menu_origem"
    assert process_lists[1]["source_subprocess_key"] == ""


def test_edit_process_lists_removal_via_blank_rows():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_config={
            "process_lists": [
                {
                    "key": "list_existente",
                    "label": "Existente",
                    "field_type": "manual",
                    "items": ["X"],
                }
            ]
        },
    )

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        process_list_key=[""],
        process_list_label=[""],
        process_list_items_csv=[""],
        process_list_field_type=["manual"],
    )

    assert response.status_code == 303
    assert _load_config(SessionLocal)["process_lists"] == []


def test_edit_process_lists_columns_configured_zero_preserves_legacy_columns():
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
        menu_config={"process_lists": [], "process_list_columns": existing_columns},
    )

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        process_list_key=["a"],
        process_list_label=["Lista A"],
        process_list_items_csv=["1,2"],
        process_list_field_type=["manual"],
        process_list_columns_configured="0",
    )

    assert response.status_code == 303
    assert _load_config(SessionLocal)["process_list_columns"] == existing_columns


def test_edit_process_lists_invalid_field_type_normalized_to_manual():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"process_lists": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        process_list_key=["x"],
        process_list_label=["X"],
        process_list_items_csv=["A"],
        process_list_field_type=["bogus"],
    )

    assert response.status_code == 303
    process_lists = _load_config(SessionLocal)["process_lists"]
    assert process_lists[0]["field_type"] == "manual"
    assert process_lists[0]["items"] == ["A"]
