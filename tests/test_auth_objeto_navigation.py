from pathlib import Path

from appgenesis.routes.profile.page_handler import (
    _normalize_authorization_profile_target_v1,
    _resolve_active_tab_index_v1,
    _resolve_initial_menu_target,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) TARGET INICIAL DO PERFIL DE AUTORIZACAO
####################################################################################


def test_resolve_initial_menu_target_auth_objeto_edit_keeps_objeto_context() -> None:
    target, dynamic_section = _resolve_initial_menu_target(
        resolved_menu="perfil_de_autorizacao",
        resolved_profile_tab="pessoal",
        resolved_admin_tab="entidade",
        settings_edit_key="",
        can_manage_tenant_structure=True,
        sidebar_menu_settings=[],
        query_edit_params={
            "auth_objeto_edit_key": "obj-123",
            "auth_profile_edit_key": "",
        },
    )

    assert target == "#auth-objeto-form-card"
    assert dynamic_section == ""


def test_resolve_initial_menu_target_auth_profile_edit_keeps_profile_context() -> None:
    target, dynamic_section = _resolve_initial_menu_target(
        resolved_menu="perfil_de_autorizacao",
        resolved_profile_tab="pessoal",
        resolved_admin_tab="entidade",
        settings_edit_key="",
        can_manage_tenant_structure=True,
        sidebar_menu_settings=[],
        query_edit_params={
            "auth_objeto_edit_key": "",
            "auth_profile_edit_key": "perfil-123",
        },
    )

    assert target == "#auth-profile-form-card"
    assert dynamic_section == ""


####################################################################################
# (2) NORMALIZACAO DE TARGETS DO PERFIL DE AUTORIZACAO
####################################################################################


def test_normalize_authorization_profile_target_backend_variants() -> None:
    expected_targets = {
        "#auth-profile-card": [
            "#auth-profile",
            "#auth-profile-card",
            "#auth-profile-active-card",
            "#auth-profile-inactive-card",
            "#auth-profile-form-card",
        ],
        "#auth-objeto-card": [
            "#auth-objeto",
            "#auth-objeto-card",
            "#auth-objeto-active-card",
            "#auth-objeto-inactive-card",
            "#auth-objeto-form-card",
        ],
    }

    for expected_target, aliases in expected_targets.items():
        for alias in aliases:
            assert _normalize_authorization_profile_target_v1(alias) == expected_target


def test_resolve_active_tab_index_auth_objeto_form_stays_on_objeto_tab() -> None:
    active_tab_index = _resolve_active_tab_index_v1(
        menu_key="perfil_de_autorizacao",
        initial_menu_tabs=[
            {"key": "perfis", "target": "#auth-profile-card", "dynamic_process_section": ""},
            {"key": "objetos", "target": "#auth-objeto-card", "dynamic_process_section": ""},
        ],
        initial_menu_target="#auth-objeto-form-card",
        initial_dynamic_process_section="",
    )

    assert active_tab_index == 1


def test_resolve_active_tab_index_auth_profile_form_stays_on_profile_tab() -> None:
    active_tab_index = _resolve_active_tab_index_v1(
        menu_key="perfil_de_autorizacao",
        initial_menu_tabs=[
            {"key": "perfis", "target": "#auth-profile-card", "dynamic_process_section": ""},
            {"key": "objetos", "target": "#auth-objeto-card", "dynamic_process_section": ""},
        ],
        initial_menu_target="#auth-profile-form-card",
        initial_dynamic_process_section="",
    )

    assert active_tab_index == 0


def test_new_user_js_exposes_authorization_profile_target_normalization() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(
        encoding="utf-8"
    )
    registry_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "admin_target_registry_v1.js"
    ).read_text(encoding="utf-8")

    assert "function normalizeAuthorizationProfileTargetV1(value)" in script_text
    assert "function authorizationProfileTargetsMatchV1(leftTarget, rightTarget)" in script_text
    assert "return appGenesisAdminTargetRegistryV1.normalizeAuthorizationProfileTarget(value);" in script_text
    assert "return appGenesisAdminTargetRegistryV1.authorizationProfileTargetsMatch(leftTarget, rightTarget);" in script_text
    assert '"#auth-profile-form-card": "#auth-profile-card"' in registry_text
    assert '"#auth-profile-active-card": "#auth-profile-card"' in registry_text
    assert '"#auth-objeto-form-card": "#auth-objeto-card"' in registry_text
    assert '"#auth-objeto-inactive-card": "#auth-objeto-card"' in registry_text
    assert "function appendAuthObjetoDebugParamV1(rawUrl)" not in script_text
    assert "debug_auth_objeto_nav" not in script_text


def test_page_handler_removes_temporary_auth_objeto_debug_hooks() -> None:
    handler_text = (
        PROJECT_ROOT / "appgenesis" / "routes" / "profile" / "page_handler.py"
    ).read_text(encoding="utf-8")

    assert "def _normalize_authorization_profile_target_v1" in handler_text
    assert "def _resolve_active_tab_index_v1" in handler_text
    assert "def _debug_auth_objeto_nav_enabled_v1" not in handler_text
    assert "_log_auth_objeto_nav_v1(" not in handler_text
    assert "debug_auth_objeto_nav" not in handler_text
