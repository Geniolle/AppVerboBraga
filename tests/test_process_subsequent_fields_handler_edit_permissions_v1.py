import json
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

import appgenesis.routes.profile.process_settings.subsequent_field_handlers as settings_handlers_module
from appgenesis.models import Base, Entity, SidebarMenuSetting


MENU_KEY = "processo_teste_permissoes_subsequentes"


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


def _seed_menu(SessionLocal, *, menu_config):
    session = SessionLocal()
    row = SidebarMenuSetting(
        entity_id=1,
        menu_key=MENU_KEY,
        menu_label=MENU_KEY,
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
    return Request({"type": "http", "method": "POST", "path": "/users/new", "headers": []})


def _call_handler(SessionLocal, current_user, is_admin, permissions, **form_overrides):
    form = dict(
        menu_key=MENU_KEY,
        subsequent_field_key=[],
        subsequent_trigger_field=[],
        subsequent_field=[],
        subsequent_operator=[],
        subsequent_trigger_value=[],
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
        return settings_handlers_module.edit_sidebar_menu_process_subsequent_fields_handler(
            request=_build_request(), **form
        )


def test_edit_subsequent_fields_requires_login():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"subsequent_fields": []})

    response = _call_handler(SessionLocal, current_user=None, is_admin=False, permissions={})

    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=Efetue%20login%20para%20continuar."
    assert _load_config(SessionLocal)["subsequent_fields"] == []


def test_edit_subsequent_fields_blocks_non_admin():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"subsequent_fields": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "user@example.com"},
        is_admin=False,
        permissions={},
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20administradores%20podem%20alterar%20campos%20subsequentes." in location
    # Comportamento existente (nao corrigido nesta fase): o redirect de erro usa
    # underscore ("campos_subsequentes"), diferente do redirect de sucesso, que usa
    # hifen ("campos-subsequentes"). Ver testes de regressao_hyphen_underscore abaixo.
    assert "settings_tab=campos_subsequentes" in location
    assert _load_config(SessionLocal)["subsequent_fields"] == []


def test_edit_subsequent_fields_blocks_admin_non_owner():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"subsequent_fields": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "admin@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": False, "can_manage_all_entities": False},
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20Owner%20pode%20configurar%20campos%20subsequentes." in location
    assert "settings_tab=campos_subsequentes" in location
    assert _load_config(SessionLocal)["subsequent_fields"] == []


def test_edit_subsequent_fields_owner_success_creates_and_edits_rows():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"subsequent_fields": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        subsequent_field_key=["", ""],
        subsequent_trigger_field=["estado", "tipo"],
        subsequent_field=["motivo", "detalhe"],
        subsequent_operator=["equals", "is_not_empty"],
        subsequent_trigger_value=["inativo", ""],
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "target=settings-menu-edit-card" in location
    # Comportamento existente: o redirect de SUCESSO usa hifen, ao contrario dos
    # redirects de erro desta mesma aba (ver testes acima e abaixo).
    assert "settings_tab=campos-subsequentes" in location
    assert f"settings_edit_key={MENU_KEY}" in location
    assert "Campos%20subsequentes%20atualizados%20com%20sucesso." in location

    subsequent_fields = _load_config(SessionLocal)["subsequent_fields"]
    assert [item["trigger_field"] for item in subsequent_fields] == ["estado", "tipo"]
    assert [item["operator"] for item in subsequent_fields] == ["equals", "is_not_empty"]
    assert subsequent_fields[0]["trigger_value"] == "inativo"
    assert subsequent_fields[1]["trigger_value"] == ""


def test_edit_subsequent_fields_removal_via_blank_rows():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_config={
            "subsequent_fields": [
                {
                    "key": "subseq_existente",
                    "trigger_field": "estado",
                    "field_key": "motivo",
                    "operator": "equals",
                    "trigger_value": "inativo",
                }
            ]
        },
    )

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        subsequent_field_key=[""],
        subsequent_trigger_field=[""],
        subsequent_field=[""],
        subsequent_operator=[""],
        subsequent_trigger_value=[""],
    )

    assert response.status_code == 303
    # A linha em branco e' enviada ao handler (que apenas verifica a EXISTENCIA do
    # indice, nao o conteudo) e so e' descartada dentro da normalizacao, por faltar
    # trigger_field_key/subsequent_field_key -- mecanismo diferente do usado em Listas,
    # onde o proprio handler ja descarta a linha em branco antes de persistir.
    assert _load_config(SessionLocal)["subsequent_fields"] == []


def test_edit_subsequent_fields_invalid_operator_normalized_to_is_empty():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"subsequent_fields": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        subsequent_field_key=[""],
        subsequent_trigger_field=["estado"],
        subsequent_field=["motivo"],
        subsequent_operator=["bogus"],
        subsequent_trigger_value=["x"],
    )

    assert response.status_code == 303
    subsequent_fields = _load_config(SessionLocal)["subsequent_fields"]
    assert subsequent_fields[0]["operator"] == "is_empty"
    assert subsequent_fields[0]["trigger_value"] == ""


def test_edit_subsequent_fields_update_failure_redirect_uses_underscore_tab():
    SessionLocal = _build_session_factory()
    # Menu inexistente: update_sidebar_menu_subsequent_fields devolve
    # ok=False, "Menu não encontrado.".
    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        subsequent_field_key=[""],
        subsequent_trigger_field=["estado"],
        subsequent_field=["motivo"],
        subsequent_operator=["equals"],
        subsequent_trigger_value=["x"],
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Menu%20n%C3%A3o%20encontrado." in location
    assert "settings_tab=campos_subsequentes" in location


def test_regression_hyphen_underscore_settings_tab_inconsistency_is_locked():
    """
    Documenta comportamento estranho pre-existente (nao corrigido nesta fase,
    por instrucao explicita): os 3 redirects de ERRO desta aba usam
    settings_tab="campos_subsequentes" (underscore), enquanto o unico redirect
    de SUCESSO usa settings_tab="campos-subsequentes" (hifen). Todas as outras
    abas usam hifen de forma consistente em todos os redirects. Este teste
    trava o estado atual; qualquer mudanca aqui deve ser deliberada.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"subsequent_fields": []})

    error_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "user@example.com"},
        is_admin=False,
        permissions={},
    )
    assert "settings_tab=campos_subsequentes" in error_response.headers["location"]
    assert "settings_tab=campos-subsequentes" not in error_response.headers["location"]

    success_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
    )
    assert "settings_tab=campos-subsequentes" in success_response.headers["location"]
    assert "settings_tab=campos_subsequentes" not in success_response.headers["location"]
