from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) ORDEM GLOBAL DOS MENUS DE ACOES: SUBIR/DESCER SEMPRE ANTES DE EDITAR/ELIMINAR.
# createRawActionsContainer_v1 e o UNICO ponto que monta as acoes de linha para as 5 abas
# do editor de processo que usam createConfigurableItemsManager_v1 (Configuracao dos campos,
# Campos adicionais, Campos Quantidade, Listas, Campos Subsequentes).
####################################################################################

def test_configurable_items_actions_move_before_edit_before_remove() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "configurable_items_manager_core_v1.js"
    script_text = script_path.read_text(encoding="utf-8")

    function_start = script_text.index("function createRawActionsContainer_v1")
    function_end = script_text.index("\n    return container;", function_start)
    function_body = script_text[function_start:function_end]

    move_index = function_body.index("manager.config.actions.move")
    edit_index = function_body.index("manager.config.actions.edit")
    remove_index = function_body.index("manager.config.actions.remove")

    assert move_index < edit_index < remove_index


def test_configurable_items_managers_all_share_the_same_actions_helper() -> None:
    modules_dir = PROJECT_ROOT / "static" / "js" / "modules"
    managers_using_shared_helper = [
        "process_additional_fields_manager_v3.js",
        "process_fields_config_manager_v7.js",
        "process_lists_manager_v1.js",
        "process_quantity_fields_manager_v1.js",
        "process_subsequent_fields_manager_v1.js",
    ]

    for manager_file in managers_using_shared_helper:
        manager_text = (modules_dir / manager_file).read_text(encoding="utf-8")
        assert "createConfigurableItemsManager_v1(" in manager_text, (
            f"{manager_file} nao usa o gestor generico de itens configuraveis; "
            "a ordem das acoes teria de ser corrigida separadamente."
        )


####################################################################################
# (2) AS TABELAS JINJA (admin_subprocess) JA SEGUIAM A ORDEM CORRETA — CONFIRMAR QUE
# CONTINUAM ASSIM (regressao / ponto de referencia usado para o padrao global).
####################################################################################

def test_admin_subprocess_row_actions_macro_already_orders_move_before_edit() -> None:
    macro_path = PROJECT_ROOT / "templates" / "macros" / "admin_subprocess.html"
    macro_text = macro_path.read_text(encoding="utf-8")

    macro_start = macro_text.index("{% macro render_admin_subprocess_row_actions")
    macro_end = macro_text.index("{% endmacro %}", macro_start)
    macro_body = macro_text[macro_start:macro_end]

    move_up_index = macro_body.index('title="Subir"')
    edit_index = macro_body.index('title="Editar"')
    delete_index = macro_body.index("state.config.delete_endpoint")

    assert move_up_index < edit_index < delete_index


def test_sidebar_menu_table_already_orders_move_before_edit() -> None:
    html_path = PROJECT_ROOT / "templates" / "new_user.html"
    html_text = html_path.read_text(encoding="utf-8")

    move_up_index = html_text.index('title="Subir pasta"')
    edit_index = html_text.index('title="Editar menu"')

    assert move_up_index < edit_index
