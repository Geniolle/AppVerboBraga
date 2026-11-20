from pathlib import Path

RUNTIME_JS = Path(__file__).resolve().parents[1] / "static" / "js" / "modules" / "process_menu_runtime_v1.js"


def test_auth_profile_hash_respects_administrativo_url_menu():
    source = RUNTIME_JS.read_text(encoding="utf-8")

    # Retorno apos gravar perfil usa menu=administrativo + hash #auth-profile-card;
    # o hash nao pode desviar para o menu perfil_de_autorizacao nesse caso.
    assert 'urlMenuKey !== "administrativo" && state.normalizeAuthorizationProfileTarget' in source
    assert '"#auth-profile-card": "administrativo"' in source
    assert '"#auth-profile-form-card": "administrativo"' in source


def test_admin_tab_perfil_de_autorizacao_resolves_to_auth_profile_card():
    source = (RUNTIME_JS.parent / "process_navigation_state_v1.js").read_text(encoding="utf-8")

    # admin_tab=perfil_de_autorizacao sem target deixava o separador vazio (#dynamic-process-card).
    assert 'cleanTab === "perfil_de_autorizacao"' in source
    assert 'return "#auth-profile-card";' in source
