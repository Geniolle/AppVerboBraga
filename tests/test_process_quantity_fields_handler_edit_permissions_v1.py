import json
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

import appgenesis.routes.profile.process_settings.quantity_field_handlers as settings_handlers_module
import appgenesis.routes.profile.process_settings.common as common_module
from appgenesis.models import Base, Entity, SidebarMenuSetting


MENU_KEY = "processo_teste_permissoes_campos_quantidade"

CUSTOM_ADDITIONAL_FIELDS = [
    {
        "key": "custom_secao_dados",
        "label": "Dados",
        "field_type": "header",
    },
    {
        "key": "custom_quantidade_filhos",
        "label": "Quantidade de filhos",
        "field_type": "number",
    },
    {
        "key": "custom_nome_filho",
        "label": "Nome do filho",
        "field_type": "text",
    },
    {
        "key": "custom_outro_texto",
        "label": "Outro texto",
        "field_type": "text",
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
        quantity_rule_key=[],
        quantity_rule_label=[],
        quantity_field_key=[],
        quantity_repeated_field_keys_json=[],
        quantity_header_key=[],
        quantity_max_items=[],
        quantity_item_label=[],
        redirect_menu="administrativo",
        redirect_target="#settings-menu-edit-card",
        return_url="",
    )
    form.update(form_overrides)

    with patch.object(settings_handlers_module, "SessionLocal", SessionLocal), patch.object(
        common_module, "get_current_user", return_value=current_user
    ), patch.object(
        common_module, "is_admin_user", return_value=is_admin
    ), patch.object(
        common_module, "get_session_entity_id", return_value=1
    ), patch.object(
        common_module, "get_user_entity_permissions", return_value=permissions
    ):
        return settings_handlers_module.edit_sidebar_menu_process_quantity_fields_handler(
            request=_build_request(), **form
        )


def _one_row_form(**overrides):
    row = dict(
        quantity_rule_key=[""],
        quantity_rule_label=["Filhos"],
        quantity_field_key=["custom_quantidade_filhos"],
        quantity_repeated_field_keys_json=[json.dumps(["custom_nome_filho"])],
        quantity_header_key=[""],
        quantity_max_items=["10"],
        quantity_item_label=["Filho"],
    )
    row.update(overrides)
    return row


####################################################################################
# (1) PERMISSOES: login obrigatorio, bloqueio de nao-admin, bloqueio de admin sem
# Owner, sucesso do Owner. Ao contrario das 4 abas ja protegidas (que tem blocos de
# permissao inline duplicados, com mensagens especificas por aba), esta aba usa o
# helper partilhado _require_menu_settings_owner_v1 -- por isso a mensagem de erro
# de "admin sem Owner" e' a mensagem GENERICA "Apenas Owner pode alterar definições
# do menu.", nao uma mensagem especifica de Campos Quantidade.
####################################################################################

def test_edit_quantity_fields_requires_login():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(SessionLocal, current_user=None, is_admin=False, permissions={})

    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=Efetue%20login%20para%20continuar."
    assert "process_quantity_fields" not in _load_config(SessionLocal)


def test_edit_quantity_fields_blocks_non_admin():
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
    assert "settings_tab=campos-quantidade" in location
    assert "process_quantity_fields" not in _load_config(SessionLocal)


def test_edit_quantity_fields_blocks_admin_non_owner_with_generic_shared_message():
    """
    Diferenca confirmada em relacao as 4 abas ja protegidas: a mensagem de bloqueio
    para admin-sem-Owner e' a mensagem GENERICA do helper partilhado
    _require_menu_settings_owner_v1 ("Apenas Owner pode alterar definições do
    menu."), e nao uma mensagem especifica desta aba (ex.: "Apenas Owner pode
    configurar Campos Quantidade.", que nao existe no codigo).
    """
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
    assert "Apenas%20Owner%20pode%20alterar%20defini%C3%A7%C3%B5es%20do%20menu." in location
    assert "settings_tab=campos-quantidade" in location
    assert "process_quantity_fields" not in _load_config(SessionLocal)


def test_edit_quantity_fields_owner_success():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "appgenesis_after_save=1" in location
    assert "settings_tab=" not in location
    assert "settings_edit_key=" not in location
    assert "Campos%20Quantidade%20atualizados%20com%20sucesso." in location

    config = _load_config(SessionLocal)
    assert config["process_quantity_fields"] == [
        {
            "key": "qty_filhos",
            "label": "Filhos",
            "quantity_field_key": "custom_quantidade_filhos",
            "repeated_field_keys": ["custom_nome_filho"],
            "header_key": "",
            "max_items": 10,
            "item_label": "Filho",
        }
    ]


####################################################################################
# (2) DEPENDENCIA POR INDICE (nivel do handler): as 7 listas paralelas do formulario
# sao combinadas por posicao (zip por indice), nao por chave. Se uma lista tiver
# menos elementos que as outras, os campos em falta assumem string vazia -- e' o
# mesmo padrao de risco ja testado ao nivel do handler para Configuração dos campos.
####################################################################################

def test_edit_quantity_fields_handler_level_index_misalignment_regression():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        quantity_rule_key=["", ""],
        quantity_rule_label=["Filhos", "Outra regra"],
        quantity_field_key=["custom_quantidade_filhos", "custom_quantidade_filhos"],
        quantity_repeated_field_keys_json=[json.dumps(["custom_nome_filho"])],
        quantity_header_key=[],
        quantity_max_items=["10", "5"],
        quantity_item_label=["Filho", "Item"],
    )

    assert response.status_code == 303
    config = _load_config(SessionLocal)
    rules = config["process_quantity_fields"]
    # A segunda linha nao tinha repeated_field_keys_json correspondente na lista
    # (indice fora do intervalo) -- resultou em string vazia -> [] apos normalize
    # -> linha inteira descartada por normalize_menu_process_quantity_fields
    # (que exige repeated_field_keys nao vazio). Apenas a primeira linha sobrevive.
    assert [rule["label"] for rule in rules] == ["Filhos"]
    assert rules[0]["repeated_field_keys"] == ["custom_nome_filho"]


####################################################################################
# (3) EDICAO, REMOCAO E PRESERVACAO DE OUTRAS SECCOES (nivel handler completo).
####################################################################################

def test_edit_quantity_fields_owner_can_edit_previously_saved_rule():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(),
    )
    config = _load_config(SessionLocal)
    saved_key = config["process_quantity_fields"][0]["key"]

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(
            quantity_rule_key=[saved_key],
            quantity_rule_label=["Filhos e enteados"],
        ),
    )

    config = _load_config(SessionLocal)
    assert config["process_quantity_fields"][0]["key"] == saved_key
    assert config["process_quantity_fields"][0]["label"] == "Filhos e enteados"


def test_edit_quantity_fields_removal_via_empty_lists():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(),
    )

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
    )

    assert response.status_code == 303
    config = _load_config(SessionLocal)
    assert config["process_quantity_fields"] == []


def test_edit_quantity_fields_preserves_unrelated_menu_config_sections_through_handler():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_config={
            "additional_fields": CUSTOM_ADDITIONAL_FIELDS,
            "process_lists": [{"key": "list_x", "label": "X"}],
            "process_visible_fields": ["custom_nome_filho"],
        },
    )

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(),
    )

    config = _load_config(SessionLocal)
    assert config["process_lists"] == [{"key": "list_x", "label": "X"}]
    assert config["process_visible_fields"] == ["custom_nome_filho"]


####################################################################################
# (4) FALHA DE ATUALIZACAO E MENU INEXISTENTE (nivel handler).
####################################################################################

def test_edit_quantity_fields_menu_not_found_redirect():
    SessionLocal = _build_session_factory()
    # Sem _seed_menu: menu inexistente.

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Menu%20n%C3%A3o%20encontrado." in location
    assert "settings_tab=campos-quantidade" in location


def test_edit_quantity_fields_protected_menu_key_home_redirect():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="home")

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        menu_key="home",
        **_one_row_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Este%20processo%20n%C3%A3o%20permite%20Campos%20Quantidade." in location
    assert "settings_tab=campos-quantidade" in location


def test_edit_quantity_fields_validation_error_redirect_uses_hyphen_tab():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(quantity_field_key=["custom_campo_inexistente"]),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "deve%20existir%20em%20Campos%20adicionais" in location
    assert "settings_tab=campos-quantidade" in location


####################################################################################
# (5) CONSISTENCIA HIFEN: todos os redirects (erro de permissao, erro de validacao,
# sucesso) usam sempre settings_tab="campos-quantidade", nunca "campos_quantidade".
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
    assert "settings_tab=campos-quantidade" in non_admin_response.headers["location"]
    assert "settings_tab=campos_quantidade" not in non_admin_response.headers["location"]

    non_owner_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "admin@example.com"},
        is_admin=True,
        permissions={},
    )
    assert "settings_tab=campos-quantidade" in non_owner_response.headers["location"]
    assert "settings_tab=campos_quantidade" not in non_owner_response.headers["location"]

    success_response = _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(),
    )
    assert "appgenesis_after_save=1" in success_response.headers["location"]
    assert "settings_tab=" not in success_response.headers["location"]
    assert "settings_tab=campos_quantidade" not in success_response.headers["location"]


####################################################################################
# (6) COMPORTAMENTO APOS REFRESH: resubmeter a mesma regra sem alteracoes preserva
# o estado persistido (idempotencia do handler para o mesmo payload).
####################################################################################

def test_edit_quantity_fields_resubmitting_same_state_after_refresh_is_idempotent():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal)

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(),
    )
    config_first = _load_config(SessionLocal)
    saved_key = config_first["process_quantity_fields"][0]["key"]

    _call_handler(
        SessionLocal,
        current_user={"id": 1, "login_email": "owner@example.com"},
        is_admin=True,
        permissions={"can_manage_tenant_structure": True},
        **_one_row_form(quantity_rule_key=[saved_key]),
    )

    config_second = _load_config(SessionLocal)
    assert config_second["process_quantity_fields"] == config_first["process_quantity_fields"]
