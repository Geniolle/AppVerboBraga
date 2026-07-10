import json
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
import pytest
from starlette.requests import Request

import appgenesis.routes.profile.settings_handlers as settings_handlers_module
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


def _seed_menu(SessionLocal, *, menu_key, entity_id=1, menu_label=None, menu_config=None, is_active=True, is_deleted=False):
    session = SessionLocal()
    row = SidebarMenuSetting(
        entity_id=entity_id,
        menu_key=menu_key,
        menu_label=menu_label if menu_label is not None else menu_key,
        menu_config=json.dumps(menu_config if menu_config is not None else {}),
        is_active=is_active,
        is_deleted=is_deleted,
    )
    session.add(row)
    session.commit()
    session.close()


def _load_row(SessionLocal, menu_key):
    session = SessionLocal()
    row = session.execute(
        select(SidebarMenuSetting).where(SidebarMenuSetting.menu_key == menu_key)
    ).scalar_one_or_none()
    if row is None:
        session.close()
        return None
    data = {
        "menu_label": row.menu_label,
        "is_active": row.is_active,
        "is_deleted": row.is_deleted,
        "config": json.loads(row.menu_config) if row.menu_config else {},
    }
    session.close()
    return data


def _build_request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/users/new", "headers": []})


def _call(handler_name, SessionLocal, current_user, is_admin, permissions, **form):
    with patch.object(settings_handlers_module, "SessionLocal", SessionLocal), patch.object(
        settings_handlers_module, "get_current_user", return_value=current_user
    ), patch.object(
        settings_handlers_module, "is_admin_user", return_value=is_admin
    ), patch.object(
        settings_handlers_module, "get_session_entity_id", return_value=1
    ), patch.object(
        settings_handlers_module, "get_user_entity_permissions", return_value=permissions
    ):
        handler = getattr(settings_handlers_module, handler_name)
        return handler(request=_build_request(), **form)


def _edit_form(**overrides):
    form = dict(
        menu_key="processo_a",
        menu_label="Processo A",
        menu_status="ativo",
        menu_visibility_scope="all",
        menu_sidebar_section="",
        redirect_menu="administrativo",
        redirect_target="#settings-menu-edit-card",
        return_url="",
    )
    form.update(overrides)
    return form


def _create_form(**overrides):
    form = dict(
        menu_label="Processo Novo",
        menu_visibility_scope="all",
        redirect_menu="administrativo",
        redirect_target="#admin-account-status-card",
        return_url="",
    )
    form.update(overrides)
    return form


def _move_form(**overrides):
    form = dict(
        menu_key="processo_a",
        direction="up",
        redirect_menu="administrativo",
        redirect_target="#admin-account-status-card",
        return_url="",
    )
    form.update(overrides)
    return form


def _delete_form(**overrides):
    form = dict(
        menu_key="processo_a",
        redirect_menu="administrativo",
        redirect_target="#admin-account-status-card",
    )
    form.update(overrides)
    return form


OWNER = {"id": 1, "login_email": "owner@example.com"}
ADMIN_NON_OWNER = {"id": 1, "login_email": "admin@example.com"}
REGULAR_USER = {"id": 1, "login_email": "user@example.com"}
OWNER_PERMISSIONS = {"can_manage_tenant_structure": True}
NON_OWNER_PERMISSIONS = {"can_manage_tenant_structure": False, "can_manage_all_entities": False}


####################################################################################
# (1) EDIT: permissoes -- login obrigatorio, bloqueio nao-admin, bloqueio admin
# sem Owner (mensagem GENERICA do helper partilhado _require_menu_settings_owner_v1),
# sucesso do Owner. O handler de edicao e' o UNICO dos 4 que passa
# settings_action/settings_tab corretamente em TODOS os seus redirects (bloqueio,
# falha de validacao e sucesso) -- sem fuga de default.
####################################################################################

def test_edit_requires_login():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    response = _call(
        "edit_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=None, is_admin=False, permissions={},
        **_edit_form(),
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=Efetue%20login%20para%20continuar."


def test_edit_blocks_non_admin_with_correct_action_and_tab():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    response = _call(
        "edit_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=REGULAR_USER, is_admin=False, permissions={},
        **_edit_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20administradores%20podem%20alterar%20defini%C3%A7%C3%B5es%20do%20menu." in location
    assert "settings_tab=geral" in location
    assert "settings_action=edit" in location
    assert "settings_edit_key=processo_a" in location


def test_edit_blocks_admin_non_owner_with_generic_shared_message():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    response = _call(
        "edit_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=ADMIN_NON_OWNER, is_admin=True, permissions=NON_OWNER_PERMISSIONS,
        **_edit_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20Owner%20pode%20alterar%20defini%C3%A7%C3%B5es%20do%20menu." in location
    assert "settings_tab=geral" in location


def test_edit_owner_success():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    response = _call(
        "edit_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_edit_form(menu_label="Processo A Editado"),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Menu%20atualizado%20com%20sucesso." in location
    assert "settings_tab=geral" in location
    assert "settings_action=edit" in location
    assert "settings_edit_key=processo_a" in location
    assert "target=settings-menu-edit-card" in location

    row = _load_row(SessionLocal, "processo_a")
    assert row["menu_label"] == "Processo A Editado"


def test_edit_success_redirect_always_targets_editor_card_ignoring_form_redirect_target():
    """
    Comportamento estranho documentado (nao corrigido): o redirect de sucesso usa
    _build_settings_editor_stay_redirect_url_v1, que fixa internamente
    redirect_target="#settings-menu-edit-card" -- o valor de redirect_target vindo
    do formulario e' ignorado no caminho de sucesso (mas e' respeitado nos
    caminhos de erro).
    """
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    response = _call(
        "edit_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_edit_form(redirect_target="#admin-account-status-card"),
    )

    assert response.status_code == 303
    assert "target=settings-menu-edit-card" in response.headers["location"]


def test_edit_menu_not_found_redirect():
    SessionLocal = _build_session_factory()

    response = _call(
        "edit_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_edit_form(menu_key="processo_inexistente"),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Menu%20inv%C3%A1lido." in location
    assert "settings_tab=geral" in location


def test_edit_blocks_hiding_protected_key_before_label_update():
    SessionLocal = _build_session_factory()

    response = _call(
        "edit_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_edit_form(menu_key="administrativo", menu_label="Outro Nome", menu_status="inativo"),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "N%C3%A3o%20%C3%A9%20permitido%20ocultar%20este%20menu." in location
    row = _load_row(SessionLocal, "administrativo")
    assert row["menu_label"] != "Outro Nome"


####################################################################################
# (2) EDIT: comportamento estranho -- reativacao de menu soft-deleted atraves do
# fluxo normal de edicao (menu_status="ativo" default), consequencia de
# _menu_exists/_load_menu_config nao filtrarem is_deleted e de
# set_sidebar_menu_visibility forcar is_deleted=False sempre que make_visible=True.
####################################################################################

def test_edit_reactivates_a_soft_deleted_menu_via_normal_edit_flow():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_a",
        menu_label="Processo A",
        is_active=False,
        is_deleted=True,
    )

    response = _call(
        "edit_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_edit_form(),
    )

    assert response.status_code == 303
    row = _load_row(SessionLocal, "processo_a")
    assert row["is_active"] is True
    assert row["is_deleted"] is False


####################################################################################
# (3) CREATE: permissoes. settings_action="create" e' passado ao bloqueio, mas o
# valor de settings_tab usado no redirect de bloqueio vem do DEFAULT do helper
# partilhado ("geral") por coincidencia -- create_sidebar_menu_setting_handler_v1
# nunca passa settings_tab explicitamente ao helper.
####################################################################################

def test_create_requires_login():
    SessionLocal = _build_session_factory()

    response = _call(
        "create_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=None, is_admin=False, permissions={},
        **_create_form(),
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=Efetue%20login%20para%20continuar."


def test_create_blocks_non_admin_with_action_create_and_default_tab_geral():
    SessionLocal = _build_session_factory()

    response = _call(
        "create_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=REGULAR_USER, is_admin=False, permissions={},
        **_create_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20administradores%20podem%20alterar%20defini%C3%A7%C3%B5es%20do%20menu." in location
    assert "settings_action=create" in location
    assert "settings_tab=geral" in location


def test_create_blocks_admin_non_owner():
    SessionLocal = _build_session_factory()

    response = _call(
        "create_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=ADMIN_NON_OWNER, is_admin=True, permissions=NON_OWNER_PERMISSIONS,
        **_create_form(),
    )

    assert response.status_code == 303
    assert "Apenas%20Owner%20pode%20alterar%20defini%C3%A7%C3%B5es%20do%20menu." in response.headers["location"]


####################################################################################
# (4) CREATE: comportamento estranho confirmado -- fuga de settings_action/
# settings_tab. O erro de validacao NAO carrega nenhum dos dois (ambos ficam de
# fora do redirect); o sucesso so' os inclui quando redirect_target e'
# especificamente "#settings-menu-edit-card".
####################################################################################

def test_create_validation_error_redirect_has_no_settings_action_or_tab():
    SessionLocal = _build_session_factory()

    response = _call(
        "create_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_create_form(menu_label="   "),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Informe%20o%20nome%20da%20pasta." in location
    assert "settings_action=" not in location
    assert "settings_tab=" not in location


def test_create_success_with_default_redirect_target_has_no_settings_action_or_tab():
    """
    Usa reativacao de uma pasta soft-deleted (em vez de criacao genuina) para
    alcancar o caminho de sucesso sem disparar o bug de entity_id documentado em
    (5) -- apenas pastas genuinamente novas atingem o INSERT que falha.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_novo",
        menu_label="Processo Novo",
        is_active=False,
        is_deleted=True,
    )

    response = _call(
        "create_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_create_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Pasta%20criada%20com%20sucesso." in location
    assert "settings_action=" not in location
    assert "settings_tab=" not in location
    assert "settings_edit_key=" not in location


def test_create_success_with_editor_stay_target_includes_settings_action_and_tab():
    """
    Usa reativacao de uma pasta soft-deleted pelo mesmo motivo do teste anterior.
    """
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_novo",
        menu_label="Processo Novo",
        is_active=False,
        is_deleted=True,
    )

    response = _call(
        "create_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_create_form(redirect_target="#settings-menu-edit-card"),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "settings_action=edit" in location
    assert "settings_tab=geral" in location
    assert "settings_edit_key=processo_novo" in location


####################################################################################
# (5) CREATE: comportamento estranho confirmado empiricamente -- o handler NAO
# captura IntegrityError. Criar uma pasta genuinamente nova (sem nenhuma linha
# existente com a mesma chave/rotulo) propaga a excecao ate' ao chamador em vez
# de devolver um redirect de erro, porque create_sidebar_menu_setting (resolvido
# para a v2 via alias de modulo) executa um INSERT que nunca fornece entity_id
# (coluna nullable=False sem default). Em producao isto significa que criar um
# novo processo atraves desta rota deveria falhar com erro 500, nao com uma
# mensagem de validacao amigavel.
####################################################################################

def test_create_owner_raises_integrity_error_for_a_genuinely_new_process():
    SessionLocal = _build_session_factory()
    session = SessionLocal()
    session.add(Entity(id=1, name="Entidade Teste"))
    session.commit()
    session.close()

    with pytest.raises(IntegrityError, match="entity_id"):
        _call(
            "create_sidebar_menu_setting_handler_v1",
            SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
            **_create_form(),
        )


def test_create_owner_reactivates_soft_deleted_menu_without_hitting_entity_id_bug():
    SessionLocal = _build_session_factory()
    _seed_menu(
        SessionLocal,
        menu_key="processo_novo",
        menu_label="Processo Novo",
        is_active=False,
        is_deleted=True,
    )

    response = _call(
        "create_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_create_form(),
    )

    assert response.status_code == 303
    assert "Pasta%20criada%20com%20sucesso." in response.headers["location"]
    row = _load_row(SessionLocal, "processo_novo")
    assert row["is_active"] is True
    assert row["is_deleted"] is False


####################################################################################
# (6) MOVE: comportamento estranho confirmado -- move_sidebar_menu_setting_handler_v1
# nunca passa settings_action nem settings_tab ao helper partilhado, portanto o
# redirect de bloqueio de permissao usa os DEFAULTS do helper ("edit"/"geral"),
# rotulando incorretamente uma acao que na realidade e' "move". Os redirects de
# erro de validacao e de sucesso proprios do handler tambem nunca incluem
# settings_action/settings_tab (ficam sempre em branco).
####################################################################################

def test_move_requires_login():
    SessionLocal = _build_session_factory()

    response = _call(
        "move_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=None, is_admin=False, permissions={},
        **_move_form(),
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=Efetue%20login%20para%20continuar."


def test_move_blocks_non_admin_with_leaked_default_action_and_tab():
    SessionLocal = _build_session_factory()

    response = _call(
        "move_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=REGULAR_USER, is_admin=False, permissions={},
        **_move_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20administradores%20podem%20alterar%20defini%C3%A7%C3%B5es%20do%20menu." in location
    assert "settings_action=edit" in location
    assert "settings_tab=geral" in location


def test_move_blocks_admin_non_owner_with_leaked_default_action_and_tab():
    SessionLocal = _build_session_factory()

    response = _call(
        "move_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=ADMIN_NON_OWNER, is_admin=True, permissions=NON_OWNER_PERMISSIONS,
        **_move_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20Owner%20pode%20alterar%20defini%C3%A7%C3%B5es%20do%20menu." in location
    assert "settings_action=edit" in location
    assert "settings_tab=geral" in location


def test_move_owner_success_has_no_settings_action_or_tab():
    SessionLocal = _build_session_factory()

    response = _call(
        "move_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_move_form(menu_key="empresa", direction="up"),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Ordem%20da%20pasta%20atualizada%20com%20sucesso." in location
    assert "settings_action=" not in location
    assert "settings_tab=" not in location


def test_move_blocks_moving_top_item_up_with_no_settings_action_or_tab():
    SessionLocal = _build_session_factory()

    response = _call(
        "move_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_move_form(menu_key="home", direction="up"),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Esta%20pasta%20j%C3%A1%20est%C3%A1%20no%20topo." in location
    assert "settings_action=" not in location
    assert "settings_tab=" not in location


def test_move_invalid_menu_key():
    SessionLocal = _build_session_factory()

    response = _call(
        "move_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_move_form(menu_key="processo_inexistente"),
    )

    assert response.status_code == 303
    assert "Menu%20inv%C3%A1lido." in response.headers["location"]


####################################################################################
# (7) DELETE: mesmo padrao de fuga de settings_action/settings_tab do MOVE.
# delete_sidebar_menu_setting_handler_v1 nao tem sequer parametro return_url.
####################################################################################

def test_delete_requires_login():
    SessionLocal = _build_session_factory()

    response = _call(
        "delete_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=None, is_admin=False, permissions={},
        **_delete_form(),
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/login?error=Efetue%20login%20para%20continuar."


def test_delete_blocks_non_admin_with_leaked_default_action_and_tab():
    SessionLocal = _build_session_factory()

    response = _call(
        "delete_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=REGULAR_USER, is_admin=False, permissions={},
        **_delete_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Apenas%20administradores%20podem%20alterar%20defini%C3%A7%C3%B5es%20do%20menu." in location
    assert "settings_action=edit" in location
    assert "settings_tab=geral" in location


def test_delete_blocks_admin_non_owner_with_leaked_default_action_and_tab():
    SessionLocal = _build_session_factory()

    response = _call(
        "delete_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=ADMIN_NON_OWNER, is_admin=True, permissions=NON_OWNER_PERMISSIONS,
        **_delete_form(),
    )

    assert response.status_code == 303
    assert "settings_action=edit" in response.headers["location"]
    assert "settings_tab=geral" in response.headers["location"]


def test_delete_owner_success():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_a", menu_label="Processo A")

    response = _call(
        "delete_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_delete_form(),
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "Pasta%20eliminada%20com%20sucesso." in location
    assert "settings_action=" not in location
    assert "settings_tab=" not in location

    row = _load_row(SessionLocal, "processo_a")
    assert row["is_deleted"] is True


def test_delete_rejects_protected_key():
    SessionLocal = _build_session_factory()

    response = _call(
        "delete_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_delete_form(menu_key="administrativo"),
    )

    assert response.status_code == 303
    assert "N%C3%A3o%20%C3%A9%20permitido%20excluir%20este%20menu." in response.headers["location"]


def test_delete_rejects_label_based_protection_regardless_of_key():
    SessionLocal = _build_session_factory()
    _seed_menu(SessionLocal, menu_key="processo_configuracao", menu_label="Configuração")

    response = _call(
        "delete_sidebar_menu_setting_handler_v1",
        SessionLocal, current_user=OWNER, is_admin=True, permissions=OWNER_PERMISSIONS,
        **_delete_form(menu_key="processo_configuracao"),
    )

    assert response.status_code == 303
    assert "N%C3%A3o%20%C3%A9%20permitido%20excluir%20este%20menu." in response.headers["location"]
