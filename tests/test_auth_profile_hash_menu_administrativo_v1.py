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


def test_admin_tab_perfil_de_autorizacao_is_allowed_on_server():
    source = (RUNTIME_JS.parents[3] / "appgenesis" / "routes" / "profile" / "page_handler.py").read_text(encoding="utf-8")

    # Sem esta entrada na allowlist, o reload forca admin_tab=entidade e o separador fica vazio.
    assert '"sessoes", "perfil_de_autorizacao"}' in source
    assert 'if resolved_admin_tab == "perfil_de_autorizacao":\n            return "#auth-profile-card", ""' in source


def test_auth_profile_targets_are_native_admin_targets():
    source = (RUNTIME_JS.parent / "admin_target_registry_v1.js").read_text(encoding="utf-8")
    block = source[source.index("NATIVE_ADMIN_TARGETS_V1 = new Set(") :]
    block = block[: block.index("]);")]

    # Sem estes alvos no conjunto nativo, o reload de #auth-profile-card cai em #dynamic-process-card.
    assert '"#auth-profile-card"' in block
    assert '"#auth-profile-active-card"' in block


def test_auth_profile_edit_key_honored_on_administrativo():
    source = (RUNTIME_JS.parents[3] / "appgenesis" / "routes" / "profile" / "page_handler.py").read_text(encoding="utf-8")

    # Sem isto, o link Editar (menu=administrativo) ignora auth_profile_edit_key e abre em modo create.
    assert 'if resolved_menu in {"perfil_de_autorizacao", "administrativo"}' in source
    assert 'menu_key="administrativo" if resolved_menu == "administrativo"' in source


def test_auth_profile_return_target_is_list_after_save():
    source = (RUNTIME_JS.parents[3] / "appgenesis" / "routes" / "profile" / "page_handler.py").read_text(encoding="utf-8")

    # Depois de gravar (criar ou editar) o redirect volta a lista, nao ao formulario de edicao.
    assert 'auth_profile_return_target_v1 = "#auth-profile-card"' in source
    assert '"#auth-profile-form-card"\n                    if clean_auth_profile_edit_key_v1' not in source
