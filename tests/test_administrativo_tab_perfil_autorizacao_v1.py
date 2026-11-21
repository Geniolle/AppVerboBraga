from appgenesis.admin_subprocesses.registry import get_admin_subprocess_config
from appgenesis.services.process_tabs import resolve_process_tabs_v1


def test_administrativo_has_perfil_de_autorizacao_tab_after_fixed_tabs():
    tabs = resolve_process_tabs_v1("administrativo", [])
    assert [tab.key for tab in tabs] == ["entidade", "utilizador", "perfil_de_autorizacao", "funcoes_administrativas"]
    assert tabs[2].label == "Perfil de autorização"
    assert tabs[2].target == "#auth-profile-card"
    assert tabs[3].label == "Funções Administrativas"
    assert tabs[3].target == "#funcoes-administrativas-card"


def test_auth_profile_card_is_visible_in_administrativo_scope():
    scope = get_admin_subprocess_config("perfil_de_autorizacao").menu_scope
    assert "administrativo" in scope.split(",")
    assert "perfil_de_autorizacao" in scope.split(",")
