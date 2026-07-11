import inspect
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) GERACAO UNICA CONFIRMADA: apos a consolidacao estrutural desta fase,
# create_sidebar_menu_setting tem exatamente UMA definicao em menu_settings.py --
# a v1 morta e o alias de modulo "create_sidebar_menu_setting = create_sidebar_menu_setting_v2"
# foram removidos. entity_id passou a ser o segundo parametro posicional,
# obrigatorio.
####################################################################################

def test_menu_settings_has_exactly_one_create_sidebar_menu_setting_definition() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    lines = menu_settings_path.read_text(encoding="utf-8").splitlines()

    definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def create_sidebar_menu_setting(")
    ]

    assert len(definition_line_numbers) == 1


def test_menu_settings_has_no_create_sidebar_menu_setting_v2_definition() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    menu_settings_text = menu_settings_path.read_text(encoding="utf-8")

    assert "def create_sidebar_menu_setting_v2(" not in menu_settings_text


def test_menu_settings_has_no_module_level_alias_for_create_sidebar_menu_setting() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    menu_settings_text = menu_settings_path.read_text(encoding="utf-8")

    assert "create_sidebar_menu_setting = create_sidebar_menu_setting_v2" not in menu_settings_text


def test_create_sidebar_menu_setting_requires_entity_id_as_second_parameter() -> None:
    from appgenesis.menu_settings import create_sidebar_menu_setting

    parameter_names = list(inspect.signature(create_sidebar_menu_setting).parameters)
    assert parameter_names[:2] == ["session", "entity_id"]


def test_settings_handlers_imports_and_calls_the_unsuffixed_create_name() -> None:
    """
    settings_handlers.py importa e chama create_sidebar_menu_setting diretamente
    -- ja nao ha alias de modulo nem versao morta para a qual possa
    acidentalmente voltar a apontar.
    """
    handlers_path = (
        PROJECT_ROOT
        / "appgenesis"
        / "routes"
        / "profile"
        / "process_settings"
        / "general_handlers.py"
    )
    handlers_text = handlers_path.read_text(encoding="utf-8")

    assert "    create_sidebar_menu_setting,\n" in handlers_text
    assert "create_sidebar_menu_setting_v2" not in handlers_text
    assert handlers_text.count("create_sidebar_menu_setting(") == 1


####################################################################################
# (2) GERACAO UNICA CONFIRMADA: ao contrario de create_sidebar_menu_setting, as
# restantes funcoes de persistencia/consulta usadas pela aba Geral tem exatamente
# uma definicao cada no ficheiro fonte -- nao ha ambiguidade de qual versao esta
# em vigor.
####################################################################################

def test_menu_settings_single_generation_functions_used_by_geral() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    lines = menu_settings_path.read_text(encoding="utf-8").splitlines()

    single_generation_names = [
        "update_sidebar_menu_label",
        "move_sidebar_menu_setting",
        "delete_sidebar_menu_setting",
        "set_sidebar_menu_visibility",
        "_menu_exists",
        "_resolve_legacy_menu_alias",
        "resolve_menu_key_alias",
    ]

    for function_name in single_generation_names:
        definition_line_numbers = [
            line_number
            for line_number, line_text in enumerate(lines, start=1)
            if line_text.startswith(f"def {function_name}(")
        ]
        assert len(definition_line_numbers) == 1, (
            f"esperada exatamente 1 definicao de {function_name}, "
            f"encontradas em {definition_line_numbers}"
        )


####################################################################################
# (3) AUSENCIA DE INTERCEPCAO/DUPLICACAO NO FRONTEND: nenhum ficheiro JS intercepta
# submissao dos formularios de edit/move/delete (sem fetch/XMLHttpRequest/
# preventDefault junto a essas rotas); apenas menu_section_form.js referencia uma
# rota de Geral (/settings/menu/create), e fa-lo apenas para injetar um campo, nunca
# para interceptar o submit.
####################################################################################

def test_no_js_file_references_the_edit_move_or_delete_menu_routes() -> None:
    modules_dir = PROJECT_ROOT / "static" / "js"
    offending_files = []

    blocked_routes = (
        "/settings/menu/edit",
        "/settings/menu/move",
        "/settings/menu/delete",
    )

    for script_path in modules_dir.rglob("*.js"):
        script_text = script_path.read_text(encoding="utf-8")
        if any(route in script_text for route in blocked_routes):
            offending_files.append(script_path.name)

    assert offending_files == []


####################################################################################
# (4) REMOCAO DO FRONTEND ORFAO: menu_section_form.js foi removido nesta fase --
# nao existia nenhum formulario real em new_user.html apontando para
# /settings/menu/create, tornando o script inerte na pratica. A rota backend
# permanece funcional (exercida diretamente pelos testes de handler); apenas o
# JS morto e a sua referencia no template foram eliminados. Migrar para uma UI de
# criacao funcional continua fora do escopo desta fase.
####################################################################################

def test_menu_section_form_js_file_no_longer_exists() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "menu_section_form.js"
    assert not script_path.exists()


def test_no_js_file_references_the_create_menu_route() -> None:
    modules_dir = PROJECT_ROOT / "static" / "js"
    matching_files = []

    for script_path in modules_dir.rglob("*.js"):
        script_text = script_path.read_text(encoding="utf-8")
        if "/settings/menu/create" in script_text:
            matching_files.append(script_path.name)

    assert matching_files == []


def test_new_user_html_has_no_script_reference_to_menu_section_form() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    assert "menu_section_form.js" not in template_text


####################################################################################
# (5) COMPORTAMENTO ESTRANHO: a rota /settings/menu/create (e a logica de
# persistencia que ela invoca) nao tem NENHUM formulario correspondente em nenhum
# template renderizado.
####################################################################################

def test_new_user_html_has_no_form_targeting_the_create_route() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    assert 'action="/settings/menu/create"' not in template_text


####################################################################################
# (6) CONTAGEM DE MARCADORES NO TEMPLATE: cada rota de Geral com formulario visivel
# tem exatamente as ocorrencias esperadas -- edit=1, move=2 (subir/descer),
# delete=1, create=0 (documentado como ausente, nao "deveria ser 1").
####################################################################################

def test_new_user_html_form_action_occurrence_counts_for_geral_routes() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    assert template_text.count('action="/settings/menu/edit"') == 1
    assert template_text.count('action="/settings/menu/move"') == 2
    assert template_text.count('action="/settings/menu/delete"') == 1
    assert template_text.count('action="/settings/menu/create"') == 0


####################################################################################
# (7) COMPORTAMENTO ESTRANHO: o handler de criacao nunca declarou "menu_section"
# como parametro Form(...) -- mesmo com o antigo menu_section_form.js injetando
# esse campo, o FastAPI ignorava o valor silenciosamente (nao gera erro 422, o
# campo e' simplesmente descartado).
####################################################################################

def test_create_handler_signature_has_no_menu_section_form_parameter() -> None:
    import appgenesis.routes.profile.process_settings.general_handlers as general_handlers_module

    signature = inspect.signature(
        general_handlers_module.create_sidebar_menu_setting_handler_v1
    )
    assert "menu_section" not in signature.parameters
