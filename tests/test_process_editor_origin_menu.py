from pathlib import Path

from appgenesis.routes.profile.page_handler import (
    ESTRUTURAS_MENU_KEY_V1,
    _resolve_settings_edit_origin_menu_v1,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O REDIRECT_MENU DO EDITOR DE PROCESSO USA O MENU REAL DO PEDIDO (settings_edit_
# request_origin_menu), NAO UM VALOR FIXO — CAUSA RAIZ DA NAVEGACAO INTERMEDIA AO GUARDAR.
####################################################################################

def test_resolve_settings_edit_origin_menu_preserves_administrativo() -> None:
    # Link real de "Editar" na tabela Menu usa menu=administrativo; o backend nao deve trocar
    # isso por "sessoes" so porque a pagina tambem esta a editar um item de Estruturas > Menu.
    assert _resolve_settings_edit_origin_menu_v1("administrativo") == "administrativo"


def test_resolve_settings_edit_origin_menu_preserves_estruturas_key() -> None:
    assert _resolve_settings_edit_origin_menu_v1(ESTRUTURAS_MENU_KEY_V1) == ESTRUTURAS_MENU_KEY_V1


def test_resolve_settings_edit_origin_menu_falls_back_for_unrelated_menu() -> None:
    # Qualquer menu fora do escopo aceite pelo card do editor (administrativo/sessoes) cai no
    # padrao historico, sem quebrar a visibilidade de #settings-menu-edit-card.
    assert _resolve_settings_edit_origin_menu_v1("home") == ESTRUTURAS_MENU_KEY_V1
    assert _resolve_settings_edit_origin_menu_v1("calendario") == ESTRUTURAS_MENU_KEY_V1
    assert _resolve_settings_edit_origin_menu_v1("extrato") == ESTRUTURAS_MENU_KEY_V1


####################################################################################
# (2) O TEMPLATE USA O VALOR DINAMICO DO BACKEND, NAO O LITERAL "sessoes" HARDCODED
####################################################################################

def test_template_uses_dynamic_origin_menu_not_hardcoded_literal() -> None:
    html_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    assert '{% set settings_edit_origin_menu = settings_edit_request_origin_menu|default("sessoes") %}' in html_text
    assert '{% set settings_edit_origin_menu = "sessoes" %}' not in html_text


def test_page_handler_exposes_origin_menu_in_template_context() -> None:
    handler_text = (PROJECT_ROOT / "appgenesis" / "routes" / "profile" / "page_handler.py").read_text(
        encoding="utf-8"
    )

    assert '"settings_edit_request_origin_menu": settings_edit_request_origin_menu_v1' in handler_text
    # Capturado ANTES de _resolve_estruturas_navigation_context_v1, para nao herdar a reescrita
    # feita so para efeitos de titulo/breadcrumb.
    capture_index = handler_text.index("settings_edit_request_origin_menu_v1 = _resolve_settings_edit_origin_menu_v1")
    rewrite_call_index = handler_text.index(
        "resolved_menu, resolved_admin_tab = _resolve_estruturas_navigation_context_v1("
    )
    assert capture_index < rewrite_call_index
