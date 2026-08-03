from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O MENU DA URL ATUAL TEM PRIORIDADE SOBRE redirect_menu/menu_key NO POST-SAVE
####################################################################################

def test_post_save_context_prioritizes_current_url_menu_over_form_fields() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "new_user.js"
    script_text = script_path.read_text(encoding="utf-8")

    function_start = script_text.index("function currentMenuFromUrlOrBootstrapPostSaveV3")
    function_end = script_text.index("\n  }\n", function_start)
    function_body = script_text[function_start:function_end]

    url_menu_index = function_body.index('currentUrl.searchParams.get("menu")')
    fallback_menu_index = function_body.index('"redirect_menu",')
    menu_key_index = function_body.index('"menu_key",')

    # O menu da URL atual (contexto onde o formulario foi aberto) tem de ser lido antes dos
    # campos "redirect_menu"/"menu_key" do formulario, que podem estar desatualizados
    # (redirect_menu fixo no template) ou identificar o item editado, nao o menu de navegacao.
    assert url_menu_index < fallback_menu_index
    assert url_menu_index < menu_key_index
    assert fallback_menu_index < menu_key_index
