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


def test_sanitize_users_new_settings_return_url_clears_stale_identity_params_when_empty() -> None:
    # O return_url capturado no submit ainda tem settings_edit_key/settings_action/
    # settings_tab preenchidos (URL do proprio editor). Ao sair com sucesso, o chamador
    # passa "" para esses campos e eles TEM de ser removidos, nao herdados do return_url.
    result = _sanitize_users_new_settings_return_url_v1(
        "/users/new?menu=sessoes&admin_tab=contas&settings_action=edit"
        "&target=settings-menu-edit-card&settings_edit_key=calendario"
        "&settings_tab=campos-config#settings-menu-edit-card",
        {
            "success": "Processo atualizado com sucesso.",
            "menu": "sessoes",
            "target": "menu-subprocess-card-active",
            "settings_edit_key": "",
            "settings_action": "",
            "settings_tab": "",
            "appgenesis_after_save": "1",
        },
    )

    parsed = urlsplit(result)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))

    assert parsed.fragment == "menu-subprocess-card-active"
    assert params["admin_tab"] == "contas"
    assert "settings_edit_key" not in params
    assert "settings_action" not in params
    assert "settings_tab" not in params


def test_build_settings_redirect_url_always_marks_appgenesis_after_save() -> None:
    # return_after_save.js so evita a navegacao corretiva (heuristica de sessionStorage)
    # quando ve appgenesis_after_save=1 na URL atual -- esse marcador tem de estar SEMPRE
    # presente nos redirects genericos do editor de processo, com ou sem return_url.
    with_return_url = _build_settings_redirect_url(
        success_message="ok",
        redirect_menu="sessoes",
        redirect_target="#menu-subprocess-card-active",
        return_url="/users/new?menu=sessoes&admin_tab=contas#settings-menu-edit-card",
    )
    without_return_url = _build_settings_redirect_url(
        success_message="ok",
        redirect_menu="sessoes",
        redirect_target="#menu-subprocess-card-active",
    )

    assert dict(parse_qsl(urlsplit(with_return_url).query))["appgenesis_after_save"] == "1"
    assert dict(parse_qsl(urlsplit(without_return_url).query))["appgenesis_after_save"] == "1"


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
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_cards_visibility_v1.js"
    ).read_text(encoding="utf-8")

    assert 'currentUrl.searchParams.delete("dynamic_process_section");' in js_text
    assert 'currentUrl.searchParams.delete("section_key");' in js_text
    assert 'targetSelector !== "#settings-menu-edit-card"' in module_text


def test_estruturas_settings_editor_belongs_to_menu_tab() -> None:
    assert _targets_match_for_menu_v1(
        "sessoes",
        "#menu-subprocess-card-active",
        "#settings-menu-edit-card",
    )


####################################################################################
# (2) return_after_save.js SO POSSUI UM UNICO PONTO DE ESCAPE (appgenesis_after_save=1)
# E TEM DE RESPEITA-LO ANTES DE QUALQUER TENTATIVA DE NAVEGACAO CORRETIVA VIA
# sessionStorage -- caso contrario volta a reabrir o editor com a URL antiga do submit.
####################################################################################


def test_return_after_save_js_skips_correction_when_backend_already_returned_final_url() -> None:
    js_text = (PROJECT_ROOT / "static" / "js" / "modules" / "return_after_save.js").read_text(
        encoding="utf-8"
    )

    escape_hatch_index = js_text.index("function isBackendPostSaveReturnUrl")
    restore_index = js_text.index("function restoreAfterSave")
    skip_check_index = js_text.index("if (isBackendPostSaveReturnUrl(currentUrl))", restore_index)
    saved_url_check_index = js_text.index('sessionStorage.getItem(STORAGE_KEY)', restore_index)

    assert 'searchParams.get("appgenesis_after_save") === "1"' in js_text[
        escape_hatch_index : escape_hatch_index + 400
    ]
    # O escape hatch tem de ser verificado ANTES de qualquer comparacao com a URL salva no
    # sessionStorage, senao o marcador do backend nao tem efeito pratico.
    assert saved_url_check_index < skip_check_index


def test_settings_menu_editor_backend_marker_matches_return_after_save_escape_hatch() -> None:
    handlers_text = (
        PROJECT_ROOT
        / "appgenesis"
        / "routes"
        / "profile"
        / "process_settings"
        / "common.py"
    ).read_text(encoding="utf-8")
    js_text = (PROJECT_ROOT / "static" / "js" / "modules" / "return_after_save.js").read_text(
        encoding="utf-8"
    )

    assert '"appgenesis_after_save": "1"' in handlers_text
    assert 'appgenesis_after_save=1' in handlers_text
    assert 'searchParams.get("appgenesis_after_save")' in js_text


def test_appgenesis_cancel_controller_remains_the_single_cancel_entry_point() -> None:
    cancel_controller_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "appgenesis_cancel_controller_v1.js"
    ).read_text(encoding="utf-8")
    new_user_js_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")
    return_after_save_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "return_after_save.js"
    ).read_text(encoding="utf-8")

    assert "window.AppGenesisCancelControllerV1" in cancel_controller_text
    # Nem new_user.js nem return_after_save.js podem definir seu proprio tratamento de
    # clique em "Cancelar" -- toda logica de saida do editor passa pelo controller global.
    assert "data-appgenesis-cancel" not in new_user_js_text
    assert "data-appgenesis-cancel" not in return_after_save_text


def test_template_marks_requested_settings_tab_active_server_side() -> None:
    html_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    assert "{% set settings_edit_active_tab = settings_tab|default('geral') %}" in html_text
    assert "process-edit-pane {% if settings_edit_active_tab == 'campos-config' %}active{% endif %}" in html_text
    assert (
        "{% if initial_menu not in ['administrativo', 'sessoes'] or initial_menu_target != '#settings-menu-edit-card' %}"
        in html_text
    )
