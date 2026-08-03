import json
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

import appgenesis.routes.profile.process_settings.additional_field_handlers as settings_handlers_module
from appgenesis.models import Base, Entity, SidebarMenuSetting


MENU_KEY = "processo_teste_permissoes_adicionais"


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


def _seed_menu(SessionLocal, *, menu_config, menu_key=MENU_KEY):
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
        additional_field_key=[],
        additional_field_label=[],
        additional_field_type=[],
        additional_field_required=[],
        additional_field_size=[],
        additional_field_list_key=[],
        additional_field_list_source_type=[],
        additional_field_manual_list_key=[],
        additional_field_manual_list_items=[],
        additional_field_automatic_source_process_key=[],
        additional_field_automatic_source_section_key=[],
        additional_field_automatic_source_field_key=[],
        additional_field_automatic_only_active=[],
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
        return settings_handlers_module.edit_sidebar_menu_process_additional_fields_v1(
            request=_build_request(), **form
        )


def test_edit_additional_fields_requires_login():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"additional_fields": []})

    response = _call_handler(SessionLocal, current_user=None, is_admin=False, permissions={})

    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=Efetue%20login%20para%20continuar."
    assert _load_config(SessionLocal)["additional_fields"] == []


def test_edit_additional_fields_blocks_non_admin():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"additional_fields": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "user@example.com"},
        is_admin=False,
        permissions={},
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20administradores%20podem%20alterar%20defini" in location
    assert "settings_tab=campos-adicionais" in location
    assert _load_config(SessionLocal)["additional_fields"] == []


def test_edit_additional_fields_blocks_admin_non_owner():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"additional_fields": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "admin@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": False, "can_manage_all_entities": False},
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20Owner%20pode%20configurar%20campos%20adicionais%20por%20processo." in location
    assert "settings_tab=campos-adicionais" in location
    assert _load_config(SessionLocal)["additional_fields"] == []


def test_edit_additional_fields_owner_success_creates_rows():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"additional_fields": []})

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        additional_field_key=["", ""],
        additional_field_label=["Estado", "Motivo"],
        additional_field_type=["text", "text"],
        additional_field_required=["on", ""],
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "target=settings-menu-edit-card" in location
    # Ao contrario de Campos Subsequentes (mistura hifen/underscore), esta aba usa
    # hifen de forma consistente em TODOS os redirects (erro e sucesso).
    assert "settings_tab=campos-adicionais" in location
    assert f"settings_edit_key={MENU_KEY}" in location
    assert "sucesso" in location

    additional_fields = _load_config(SessionLocal)["additional_fields"]
    assert [item["label"] for item in additional_fields] == ["Estado", "Motivo"]
    assert additional_fields[0]["is_required"] is True
    assert additional_fields[1]["is_required"] is False


def test_edit_additional_fields_removal_via_blank_rows():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_config={
            "additional_fields": [
                {
                    "key": "custom_existente",
                    "label": "Existente",
                    "field_type": "text",
                    "is_required": False,
                }
            ]
        },
    )

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        additional_field_key=[""],
        additional_field_label=[""],
        additional_field_type=["text"],
    )

    assert response.status_code == 303
    assert _load_config(SessionLocal)["additional_fields"] == []


def test_edit_additional_fields_protected_menu_key_blocks_and_reports_error():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"additional_fields": []}, menu_key="home")

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        menu_key="home",
        additional_field_key=[""],
        additional_field_label=["Estado"],
        additional_field_type=["text"],
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Este%20processo%20nao%20permite%20campos%20adicionais." in location
    assert "settings_tab=campos-adicionais" in location
    assert _load_config(SessionLocal, menu_key="home")["additional_fields"] == []


def test_edit_additional_fields_menu_not_found_error_redirect():
    SessionLocal = _build_session_factory()

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        additional_field_key=[""],
        additional_field_label=["Estado"],
        additional_field_type=["text"],
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Menu%20n%C3%A3o%20encontrado." in location
    assert "settings_tab=campos-adicionais" in location


def test_regression_all_redirects_use_hyphenated_settings_tab_consistently():
    """
    Diferenca em relacao a Campos Subsequentes: naquela aba, os redirects de ERRO
    usam settings_tab="campos_subsequentes" (underscore) e o de SUCESSO usa hifen.
    Em Campos Adicionais, TODOS os redirects (login, permissao admin, permissao
    owner, menu-nao-encontrado, sucesso) usam consistentemente hifen
    ("campos-adicionais"). Este teste protege essa diferenca de comportamento.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"additional_fields": []})

    non_admin_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "user@example.com"},
        is_admin=False,
        permissions={},
    )
    assert "settings_tab=campos-adicionais" in non_admin_response.headers["location"]
    assert "settings_tab=campos_adicionais" not in non_admin_response.headers["location"]

    non_owner_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "admin@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": False},
    )
    assert "settings_tab=campos-adicionais" in non_owner_response.headers["location"]

    success_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
    )
    assert "settings_tab=campos-adicionais" in success_response.headers["location"]


def test_regression_header_restore_after_additional_fields_save_locks_current_behavior():
    """
    Comportamento existente unico desta aba (nao presente em Listas nem em Campos
    Subsequentes): apos a gravacao principal, _restore_menu_header_assignments_
    after_additional_fields_v1 executa uma SEGUNDA gravacao que substitui as
    atribuicoes de cabecalho calculadas nesta submissao pelas atribuicoes
    ANTIGAS (do estado antes desta gravacao), filtradas pelos cabecalhos e campos
    ainda existentes.

    Efeito colateral documentado (nao corrigido nesta fase, por instrucao
    explicita da Fase 0): como o normalizador reordena SEMPRE os cabecalhos para
    o inicio da lista antes da reconstrucao da hierarquia, quando dois ou mais
    cabecalhos sao submetidos na MESMA gravacao, a reconstrucao "ingenua" atribui
    erradamente TODOS os campos normais ao ULTIMO cabecalho da lista. A segunda
    passagem (restore) corrige os campos que ja existiam antes desta gravacao
    (usando a atribuicao antiga), mas um campo NOVO criado na mesma gravacao que
    um cabecalho NOVO fica sem atribuicao de cabecalho (header_key vazio), e o
    cabecalho novo desaparece de process_visible_fields/process_visible_headers.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_config={"additional_fields": []})

    first_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        additional_field_key=["", ""],
        additional_field_label=["Secao 1", "Campo A"],
        additional_field_type=["header", "text"],
    )
    assert first_response.status_code == 303

    config_after_first_save = _load_config(SessionLocal)
    assert config_after_first_save["process_visible_field_header_map"] == {
        "custom_campo_a": "custom_secao_1"
    }

    second_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        additional_field_key=["custom_secao_1", "custom_campo_a", "", ""],
        additional_field_label=["Secao 1", "Campo A", "Secao 2", "Campo B"],
        additional_field_type=["header", "text", "header", "text"],
    )
    assert second_response.status_code == 303

    config_after_second_save = _load_config(SessionLocal)

    # O campo pre-existente mantem a atribuicao ANTIGA (custom_secao_1), mesmo
    # tendo sido submetido, nesta segunda gravacao, apos o cabecalho custom_secao_2.
    assert config_after_second_save["process_visible_field_header_map"].get(
        "custom_campo_a"
    ) == "custom_secao_1"

    # O campo novo (custom_campo_b), criado na mesma gravacao que o cabecalho novo
    # (custom_secao_2), fica SEM atribuicao de cabecalho apos a segunda passagem.
    assert "custom_campo_b" not in config_after_second_save["process_visible_field_header_map"]

    # custom_secao_2 desaparece da lista de cabecalhos visiveis apos a segunda
    # passagem, apesar de ter sido submetido nesta gravacao.
    assert "custom_secao_2" not in config_after_second_save.get("process_visible_headers", [])

    # A definicao do cabecalho custom_secao_2 continua presente em additional_fields
    # (rule 7: nao remover); apenas a sua "visibilidade"/atribuicao e' que se perde.
    additional_field_keys = [
        item["key"] for item in config_after_second_save["additional_fields"]
    ]
    assert "custom_secao_2" in additional_field_keys
    assert "custom_campo_b" in additional_field_keys
