from urllib.parse import parse_qsl, urlsplit
from pathlib import Path

from appgenesis.routes.profile.page_handler import _targets_match_for_menu_v1
from appgenesis.routes.profile.settings_handlers import (
    _build_settings_redirect_url,
    _sanitize_users_new_settings_return_url_v1,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O REDIRECT DO EDITOR DE PROCESSO TEM DE REAPROVEITAR O RETURN_URL COMPLETO DO
# SUBMIT, PARA O PRIMEIRO 303 JA VIR COM admin_tab=contas E SEM NAVEGACAO CORRETIVA.
####################################################################################


def test_sanitize_users_new_settings_return_url_preserves_existing_context() -> None:
    result = _sanitize_users_new_settings_return_url_v1(
        "/users/new?menu=sessoes&admin_tab=contas&settings_action=edit"
        "&target=settings-menu-edit-card&settings_edit_key=calendario"
        "&settings_tab=campos-config#settings-menu-edit-card",
        {
            "success": "Configuração dos campos atualizada com sucesso.",
            "menu": "sessoes",
            "target": "settings-menu-edit-card",
            "settings_edit_key": "calendario",
            "settings_action": "edit",
            "settings_tab": "campos-config",
        },
    )

    parsed = urlsplit(result)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))

    assert parsed.path == "/users/new"
    assert parsed.fragment == "settings-menu-edit-card"
    assert params["menu"] == "sessoes"
    assert params["admin_tab"] == "contas"
    assert params["settings_edit_key"] == "calendario"
    assert params["settings_action"] == "edit"
    assert params["settings_tab"] == "campos-config"
    assert params["success"] == "Configuração dos campos atualizada com sucesso."


def test_sanitize_users_new_settings_return_url_rejects_external_urls() -> None:
    result = _sanitize_users_new_settings_return_url_v1(
        "https://example.com/users/new?menu=sessoes",
        {"success": "ok"},
    )

    assert result == ""


def test_build_settings_redirect_url_uses_return_url_when_available() -> None:
    result = _build_settings_redirect_url(
        success_message="Configuração dos campos atualizada com sucesso.",
        redirect_menu="sessoes",
        redirect_target="#settings-menu-edit-card",
        settings_edit_key="calendario",
        settings_action="edit",
        settings_tab="campos-config",
        return_url=(
            "/users/new?menu=sessoes&admin_tab=contas&settings_action=edit"
            "&target=settings-menu-edit-card&settings_edit_key=calendario"
            "&settings_tab=campos-config&appgenesis_after_save=1#settings-menu-edit-card"
        ),
    )

    parsed = urlsplit(result)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))

    assert parsed.fragment == "settings-menu-edit-card"
    assert params["menu"] == "sessoes"
    assert params["admin_tab"] == "contas"
    assert params["settings_action"] == "edit"
    assert params["settings_edit_key"] == "calendario"
    assert params["settings_tab"] == "campos-config"
    assert params["success"] == "Configuração dos campos atualizada com sucesso."


def test_post_save_context_does_not_reinject_dynamic_section_for_settings_editor() -> None:
    js_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert 'currentUrl.searchParams.delete("dynamic_process_section");' in js_text
    assert 'currentUrl.searchParams.delete("section_key");' in js_text
    assert 'targetSelector !== "#settings-menu-edit-card"' in js_text


def test_estruturas_settings_editor_belongs_to_menu_tab() -> None:
    assert _targets_match_for_menu_v1(
        "sessoes",
        "#menu-subprocess-card-active",
        "#settings-menu-edit-card",
    )


def test_template_marks_requested_settings_tab_active_server_side() -> None:
    html_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    assert "{% set settings_edit_active_tab = settings_tab|default('geral') %}" in html_text
    assert "process-edit-pane {% if settings_edit_active_tab == 'campos-config' %}active{% endif %}" in html_text
    assert "{% if admin_subprocess_menu_state and initial_menu_target != '#settings-menu-edit-card' %}" in html_text
