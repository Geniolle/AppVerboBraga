from pathlib import Path

RUNTIME_JS = Path(__file__).resolve().parents[1] / "static" / "js" / "modules" / "process_menu_runtime_v1.js"


def test_auth_profile_hash_respects_administrativo_url_menu():
    source = RUNTIME_JS.read_text(encoding="utf-8")

    # Retorno apos gravar perfil usa menu=administrativo + hash #auth-profile-card;
    # o hash nao pode desviar para o menu perfil_de_autorizacao nesse caso.
    assert 'urlMenuKey !== "administrativo" && state.normalizeAuthorizationProfileTarget' in source
    assert '"#auth-profile-card": "administrativo"' in source
    assert '"#auth-profile-form-card": "administrativo"' in source
