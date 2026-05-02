from appverbo.process_settings import (
    ADMIN_MENU_ORIGIN,
    build_admin_process_settings_context_v1,
    get_admin_process_settings_tabs_v1,
    is_admin_menu_process_v1,
    resolve_admin_process_settings_tab_v1,
)


####################################################################################
# (1) TESTAR ABAS PADRAO
####################################################################################

def test_get_admin_process_settings_tabs_v1():
    tabs = get_admin_process_settings_tabs_v1()

    assert [tab["key"] for tab in tabs] == [
        "geral",
        "configuracao_campos",
        "campos_adicionais",
        "campos_quantidade",
        "lista",
        "campos_subsequentes",
    ]


####################################################################################
# (2) TESTAR RESOLUCAO DA ABA ATIVA
####################################################################################

def test_resolve_admin_process_settings_tab_v1():
    assert resolve_admin_process_settings_tab_v1("geral") == "geral"
    assert resolve_admin_process_settings_tab_v1("configuracao-campos") == "configuracao_campos"
    assert resolve_admin_process_settings_tab_v1("campos_adicionais") == "campos_adicionais"
    assert resolve_admin_process_settings_tab_v1("campos-quantidade") == "campos_quantidade"
    assert resolve_admin_process_settings_tab_v1("invalida") == "geral"


####################################################################################
# (3) TESTAR IDENTIFICACAO PELO CONTEXTO ADMINISTRATIVO -> MENU
####################################################################################

def test_is_admin_menu_process_by_source_context_v1():
    assert is_admin_menu_process_v1(
        menu_key="empresa",
        menu_config={},
        source_context=ADMIN_MENU_ORIGIN,
    ) is True


####################################################################################
# (4) TESTAR IDENTIFICACAO PELO menu_config
####################################################################################

def test_is_admin_menu_process_by_menu_config_v1():
    assert is_admin_menu_process_v1(
        menu_key="empresa",
        menu_config={"created_from": ADMIN_MENU_ORIGIN},
    ) is True

    assert is_admin_menu_process_v1(
        menu_key="empresa",
        menu_config={"settings_tabs_enabled": True},
    ) is True


####################################################################################
# (5) TESTAR CONTEXTO FINAL PARA TEMPLATE/FRONTEND
####################################################################################

def test_build_admin_process_settings_context_v1():
    context = build_admin_process_settings_context_v1(
        menu_key="empresa",
        menu_config={},
        raw_settings_tab="campos-adicionais",
        source_context=ADMIN_MENU_ORIGIN,
    )

    assert context["settings_tabs_enabled"] is True
    assert context["settings_tab"] == "campos_adicionais"
    assert len(context["settings_tabs"]) == 6
