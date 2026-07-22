from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "configurable_items_manager_core_v1.js"


####################################################################################
# (1) O CONTADOR [ visivel / total ] TEM DE APARECER SEMPRE QUE EXISTAM REGISTOS,
# INDEPENDENTEMENTE DE MAIS/MENOS SEREM MOSTRADOS. A UNICA CONDICAO QUE ESCONDE TUDO
# E totalItems === 0 (showCounter). renderPagination_v1 E O UNICO PONTO QUE DECIDE ISTO
# PARA AS 5 ABAS QUE USAM createConfigurableItemsManager_v1.
####################################################################################

def _read_render_pagination_body() -> str:
    script_text = CORE_PATH.read_text(encoding="utf-8")
    function_start = script_text.index("function renderPagination_v1")
    function_end = script_text.index("\n  }\n", function_start)
    return script_text[function_start:function_end]


def test_render_pagination_hides_everything_only_when_there_are_zero_items() -> None:
    body = _read_render_pagination_body()

    assert "const showMais = currentCount < totalItems;" in body
    assert "const showMenos = manager.state.visibleCount > manager.state.pageSize;" in body
    assert "const showCounter = totalItems > 0;" in body

    hide_branch_start = body.index("if (!showCounter) {")
    hide_branch_end = body.index("return;", hide_branch_start)
    hide_branch = body[hide_branch_start:hide_branch_end]

    # A unica condicao usada para esconder o rodape inteiro deve ser showCounter.
    assert "showMais" not in hide_branch
    assert "showMenos" not in hide_branch


def test_render_pagination_counter_is_not_nested_inside_the_mais_button_block() -> None:
    body = _read_render_pagination_body()

    mais_block_start = body.index("if (showMais) {")
    mais_block_end = body.index("paginationEl.appendChild(moreBtn);", mais_block_start)
    mais_block = body[mais_block_start:mais_block_end]

    counter_index = body.index("appgenesis-load-more-counter-v1")
    # O contador tem de ser criado DEPOIS do bloco do botao Mais terminar, nunca dentro dele,
    # para que apareca mesmo quando showMais for falso.
    assert counter_index > mais_block_end
    assert "appgenesis-load-more-counter-v1" not in mais_block


####################################################################################
# (2) OPCOES DE PAGE SIZE PADRONIZADAS: [5, 10, 20] COM DEFAULT 5, CENTRALIZADAS NO
# CORE COMO CONSTANTES REUTILIZAVEIS EM VEZ DE LITERAIS REPETIDOS EM CADA MANAGER.
####################################################################################

def test_core_exposes_shared_page_size_constants() -> None:
    script_text = CORE_PATH.read_text(encoding="utf-8")

    assert "const DEFAULT_CONFIGURABLE_PAGE_SIZE_V1 = 5;" in script_text
    assert "const DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1 = [5, 10, 20];" in script_text
    assert "namespace.DEFAULT_CONFIGURABLE_PAGE_SIZE_V1 = DEFAULT_CONFIGURABLE_PAGE_SIZE_V1;" in script_text
    assert (
        "namespace.DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1 = DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1;"
        in script_text
    )
    assert "DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1" in script_text
    # Fallback interno da normalizacao tambem usa a constante partilhada, nao um literal solto.
    assert "[5, 10, 25]" not in script_text


def test_all_five_managers_reference_shared_page_size_constants_not_literals() -> None:
    modules_dir = PROJECT_ROOT / "static" / "js" / "modules"
    managers = [
        "process_additional_fields_manager_v3.js",
        "process_fields_config_manager_v7.js",
        "process_lists_manager_v1.js",
        "process_quantity_fields_manager_v1.js",
        "process_subsequent_fields_manager_v1.js",
    ]

    for manager_file in managers:
        manager_text = (modules_dir / manager_file).read_text(encoding="utf-8")
        assert "core.DEFAULT_CONFIGURABLE_PAGE_SIZE_V1" in manager_text, manager_file
        assert "core.DEFAULT_CONFIGURABLE_PAGE_SIZE_OPTIONS_V1" in manager_text, manager_file
        assert "[5, 10, 25]" not in manager_text, manager_file
        assert "pageSizeOptions: [5, 10, 20]" not in manager_text, manager_file


####################################################################################
# (3) A TABELA ESTATICA "CAMPOS DISPONIVEIS" (ABA GERAL) REUTILIZA O CONTROLADOR
# JA EXISTENTE (AppGenesisProcessShell.enhanceLoadMoreTables via .table-limiter),
# EM VEZ DE SE TORNAR UM TERCEIRO SISTEMA DE PAGINACAO OU UM MANAGER EDITAVEL.
####################################################################################

def test_geral_static_fields_table_is_wired_to_the_table_limiter_controller() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    assert 'id="settings-process-fields-table"' in template_text
    assert 'id="settings-process-fields-limiter" class="table-limiter"' in template_text
    # Nao deve existir nenhum manager de itens configuraveis para esta tabela estatica.
    assert "settings-process-fields-manager" not in template_text


####################################################################################
# (4) RODAPE DE PAGINACAO DEDUPLICADO NUM UNICO MACRO REUTILIZADO PELAS 6 ABAS.
####################################################################################

def test_pagination_footer_markup_exists_once_in_the_shared_macro_only() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")
    macro_text = (
        PROJECT_ROOT / "templates" / "macros" / "configurable_items_pagination.html"
    ).read_text(encoding="utf-8")

    assert (
        'from "macros/configurable_items_pagination.html" import '
        "render_configurable_items_pagination_footer" in template_text
    )
    assert template_text.count("render_configurable_items_pagination_footer(") == 6
    assert (
        macro_text.count(
            'class="appgenesis-load-more-footer-v1 configurable-items-pagination-footer-v1"'
        )
        == 1
    )
    # A marcacao bruta do rodape ja nao deve estar repetida diretamente no template.
    assert (
        template_text.count(
            'class="appgenesis-load-more-footer-v1 configurable-items-pagination-footer-v1"'
        )
        == 0
    )


####################################################################################
# (5) TITULO DUPLICADO REMOVIDO DA ABA LISTAS ("Listas" + "Listas reutilizaveis"
# TORNARAM-SE UM UNICO <h3>Listas reutilizaveis</h3>).
####################################################################################

def test_process_lists_tab_heading_is_not_duplicated() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    tab_start = template_text.index('data-process-edit-pane="lista"')
    tab_end = template_text.index('data-process-edit-pane="', tab_start + 1)
    tab_body = template_text[tab_start:tab_end]

    assert tab_body.count("<h3>") == 0
    assert "<h4>Listas reutilizáveis</h4>" not in tab_body
    assert "render_configurable_list_card(" in tab_body
