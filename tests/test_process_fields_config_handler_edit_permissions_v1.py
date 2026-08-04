import json
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

import appgenesis.routes.profile.process_settings.field_handlers as settings_handlers_module
from appgenesis.models import Base, Entity, SidebarMenuSetting


MENU_KEY = "processo_teste_permissoes_campos_config"

CUSTOM_ADDITIONAL_FIELDS = [
    {
        "key": "custom_secao_dados",
        "label": "Dados",
        "field_type": "header",
        "is_required": False,
    },
    {
        "key": "custom_nome",
        "label": "Nome",
        "field_type": "text",
        "is_required": False,
    },
    {
        "key": "custom_estado",
        "label": "Estado",
        "field_type": "text",
        "is_required": False,
    },
]


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


def _seed_menu(SessionLocal, *, menu_key=MENU_KEY, menu_config=None):
    if menu_config is None:
        menu_config = {"additional_fields": CUSTOM_ADDITIONAL_FIELDS}
    session = SessionLocal()
    row = SidebarMenuSetting(
        entity_id=1,
        menu_key=menu_key,
        menu_label=menu_key,
        menu_config=json.dumps(menu_config),
    )
    session.add(row)
    session.commit()
    session.close()


def _load_config(SessionLocal, menu_key=MENU_KEY):
    session = SessionLocal()
    row = session.execute(
        select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == menu_key)
    ).scalar_one()
    config = json.loads(row.menu_config)
    session.close()
    return config


def _build_request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/users/new", "headers": []})


def _call_handler(SessionLocal, current_user, is_admin, permissions, **form_overrides):
    form = dict(
        menu_key=MENU_KEY,
        visible_fields=[],
        visible_headers=[],
        visible_rows_json="",
        redirect_menu="administrativo",
        redirect_target="#settings-menu-edit-card",
        return_url="",
    )
    form.update(form_overrides)

    with patch.object(settings_handlers_module, "SessionLocal", SessionLocal), patch.object(
        settings_handlers_module, "get_current_user", return_value=current_user
    ), patch.object(
        settings_handlers_module, "is_admin_user", return_value=is_admin
    ), patch.object(
        settings_handlers_module, "get_session_entity_id", return_value=1
    ), patch.object(
        settings_handlers_module, "get_user_entity_permissions", return_value=permissions
    ):
        return settings_handlers_module.edit_sidebar_menu_process_fields_handler(
            request=_build_request(), **form
        )


####################################################################################
# (1) PERMISSOES: login obrigatorio, bloqueio de nao-admin, bloqueio de admin sem
# Owner, sucesso do Owner. Todos os redirects de erro/sucesso usam
# settings_tab="campos-config" com HIFEN de forma consistente (diferente de Campos
# Subsequentes, que tem uma inconsistencia hifen/underscore confirmada).
####################################################################################

def test_edit_process_fields_requires_login():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(SessionLocal, current_user=None, is_admin=False, permissions={})

    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=Efetue%20login%20para%20continuar."
    assert "process_visible_fields" not in _load_config(SessionLocal)


def test_edit_process_fields_blocks_non_admin():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "user@example.com"},
        is_admin=False,
        permissions={},
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20administradores%20podem%20alterar%20defini%C3%A7%C3%B5es%20do%20menu." in location
    assert "settings_tab=campos-config" in location
    assert "process_visible_fields" not in _load_config(SessionLocal)


def test_edit_process_fields_blocks_admin_non_owner():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "admin@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": False, "can_manage_all_entities": False},
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20Owner%20pode%20configurar%20campos%20do%20processo." in location
    assert "settings_tab=campos-config" in location
    assert "process_visible_fields" not in _load_config(SessionLocal)


def test_edit_process_fields_owner_success_via_json_rows():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps(
            [
                {"field_key": "custom_nome", "header_key": "custom_secao_dados"},
                {"field_key": "custom_estado", "header_key": ""},
            ]
        ),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "appgenesis_after_save=1" in location
    assert "settings_tab=" not in location
    assert "settings_edit_key=" not in location
    assert "Configura%C3%A7%C3%A3o%20dos%20campos%20atualizada%20com%20sucesso." in location

    config = _load_config(SessionLocal)
    assert config["process_visible_fields"] == ["custom_nome", "custom_estado"]
    assert config["process_visible_field_header_map"] == {"custom_nome": "custom_secao_dados"}


####################################################################################
# (2) CAMINHOS DE SUBMISSAO: visible_rows_json e' preferencial; o fallback
# posicional (visible_fields/visible_headers) so' e' usado quando o JSON esta vazio
# ou nao produz nenhum campo valido.
####################################################################################

def test_edit_process_fields_legacy_flat_lists_fallback_when_json_is_blank():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json="",
        visible_fields=["custom_nome", "custom_estado"],
        visible_headers=["custom_secao_dados", ""],
    )

    assert response.status_code == 303
    config = _load_config(SessionLocal)
    assert config["process_visible_fields"] == ["custom_nome", "custom_estado"]
    assert config["process_visible_field_header_map"] == {"custom_nome": "custom_secao_dados"}


def test_edit_process_fields_json_rows_take_priority_over_flat_lists():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps([{"field_key": "custom_estado", "header_key": ""}]),
        # Estas listas flat deveriam ser completamente ignoradas, ja que o JSON
        # produziu pelo menos uma linha valida.
        visible_fields=["custom_nome"],
        visible_headers=["custom_secao_dados"],
    )

    assert response.status_code == 303
    config = _load_config(SessionLocal)
    assert config["process_visible_fields"] == ["custom_estado"]


def test_edit_process_fields_invalid_json_rows_falls_back_to_flat_lists():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json="{not valid json",
        visible_fields=["custom_nome"],
        visible_headers=[""],
    )

    assert response.status_code == 303
    config = _load_config(SessionLocal)
    assert config["process_visible_fields"] == ["custom_nome"]


def test_edit_process_fields_handler_level_index_misalignment_regression():
    """
    Trava, ao nivel do handler (nao apenas da persistencia), o mesmo risco de
    dependencia por indice: no caminho de fallback legado, o handler zipa
    visible_fields[i] com visible_headers[i] por posicao. Se a lista de headers
    tiver menos elementos, os campos excedentes ficam sem header, silenciosamente.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json="",
        visible_fields=["custom_nome", "custom_estado"],
        visible_headers=["custom_secao_dados"],
    )

    assert response.status_code == 303
    config = _load_config(SessionLocal)
    assert config["process_visible_field_header_map"] == {"custom_nome": "custom_secao_dados"}


####################################################################################
# (3) EDICAO, REMOCAO E PRESERVACAO DE OUTRAS SECCOES.
####################################################################################

def test_edit_process_fields_owner_can_edit_previously_saved_selection():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps([{"field_key": "custom_nome", "header_key": ""}]),
    )

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps([{"field_key": "custom_estado", "header_key": ""}]),
    )

    config = _load_config(SessionLocal)
    assert config["process_visible_fields"] == ["custom_estado"]


def test_edit_process_fields_removal_via_empty_selection():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps([{"field_key": "custom_nome", "header_key": ""}]),
    )

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json="[]",
    )

    assert response.status_code == 303
    config = _load_config(SessionLocal)
    assert config["process_visible_fields"] == []


def test_edit_process_fields_preserves_unrelated_menu_config_sections_through_handler():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_config={
            "additional_fields": CUSTOM_ADDITIONAL_FIELDS,
            "process_lists": [{"key": "list_x", "label": "X"}],
        },
    )

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps([{"field_key": "custom_nome", "header_key": ""}]),
    )

    config = _load_config(SessionLocal)
    assert config["process_lists"] == [{"key": "list_x", "label": "X"}]


####################################################################################
# (4) FALHA DE ATUALIZACAO E MENU INEXISTENTE.
####################################################################################

def test_edit_process_fields_update_failure_redirect_uses_hyphen_tab_and_default_message():
    SessionLocal = _build_session_factory()
    # Menu inexistente: update_sidebar_menu_process_fields devolve
    # ok=False, "Menu não encontrado.".
    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps([{"field_key": "custom_nome", "header_key": ""}]),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Menu%20n%C3%A3o%20encontrado." in location
    assert "settings_tab=campos-config" in location


def test_edit_process_fields_no_configurable_fields_error_reaches_handler_redirect():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"additional_fields": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps([{"field_key": "custom_nome", "header_key": ""}]),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Este%20processo%20n%C3%A3o%20possui%20campos%20configur%C3%A1veis." in location
    assert "settings_tab=campos-config" in location


####################################################################################
# (5) CONSISTENCIA HIFEN: os 3 redirects (2 de erro de permissao + falha de
# persistencia + sucesso) usam sempre settings_tab="campos-config", nunca
# "campos_config" -- diferenca confirmada em relacao a Campos Subsequentes.
####################################################################################

def test_regression_settings_tab_is_always_hyphenated_never_underscore():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    non_admin_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "user@example.com"},
        is_admin=False,
        permissions={},
    )
    assert "settings_tab=campos-config" in non_admin_response.headers["location"]
    assert "settings_tab=campos_config" not in non_admin_response.headers["location"]

    non_owner_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "admin@example.com"},
        is_admin=True,
        permissions={},
    )
    assert "settings_tab=campos-config" in non_owner_response.headers["location"]
    assert "settings_tab=campos_config" not in non_owner_response.headers["location"]

    success_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps([{"field_key": "custom_nome", "header_key": ""}]),
    )
    assert "appgenesis_after_save=1" in success_response.headers["location"]
    assert "settings_tab=" not in success_response.headers["location"]
    assert "settings_tab=campos_config" not in success_response.headers["location"]


####################################################################################
# (6) COMPORTAMENTO APOS REFRESH: resubmeter o mesmo estado (sem headers) apos um
# refresh de pagina preserva os headers anteriormente configurados, em vez de os
# limpar -- validado tambem ao nivel do handler completo (nao so' da persistencia).
####################################################################################

def test_edit_process_fields_headers_survive_a_refresh_resubmit_without_headers():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json=json.dumps(
            [{"field_key": "custom_nome", "header_key": "custom_secao_dados"}]
        ),
    )

    # Simula um refresh que reenvia o formulario legado sem nenhum header.
    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        visible_rows_json="",
        visible_fields=["custom_nome"],
        visible_headers=[""],
    )

    config = _load_config(SessionLocal)
    assert config["process_visible_field_header_map"] == {"custom_nome": "custom_secao_dados"}
