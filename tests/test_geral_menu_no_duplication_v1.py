import inspect
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) MULTIPLAS GERACOES CONFIRMADAS: create_sidebar_menu_setting tem 2 geracoes no
# ficheiro fonte (v1 morta na linha ~2570, v2 ativa na linha ~2750), religadas por
# um alias a nivel de modulo ("create_sidebar_menu_setting = create_sidebar_menu_setting_v2")
# que faz com que TODOS os importadores do nome sem sufixo (menu_settings.py e
# settings_handlers.py) resolvam para o comportamento de v2, nao de v1.
####################################################################################

def test_menu_settings_has_exactly_two_create_sidebar_menu_setting_definitions() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    lines = menu_settings_path.read_text(encoding="utf-8").splitlines()

    definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def create_sidebar_menu_setting(")
        or line_text.startswith("def create_sidebar_menu_setting_v2(")
    ]

    assert len(definition_line_numbers) == 2


def test_create_sidebar_menu_setting_is_rebound_to_v2_via_module_level_alias() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    menu_settings_text = menu_settings_path.read_text(encoding="utf-8")

    assert "create_sidebar_menu_setting = create_sidebar_menu_setting_v2" in menu_settings_text


def test_create_sidebar_menu_setting_name_is_identical_object_to_v2_at_runtime() -> None:
    from appgenesis.menu_settings import (
        create_sidebar_menu_setting,
        create_sidebar_menu_setting_v2,
    )

    assert create_sidebar_menu_setting is create_sidebar_menu_setting_v2


def test_settings_handlers_imports_and_calls_the_unsuffixed_create_name() -> None:
    """
    settings_handlers.py nunca referencia create_sidebar_menu_setting_v2
    explicitamente -- importa e chama o nome sem sufixo, que resolve para v2
    apenas por causa do alias de modulo. Se o alias fosse removido/alterado,
    este ficheiro voltaria a chamar a v1 morta sem qualquer aviso.
    """
    handlers_path = PROJECT_ROOT / "appgenesis" / "routes" / "profile" / "settings_handlers.py"
    handlers_text = handlers_path.read_text(encoding="utf-8")

    assert "    create_sidebar_menu_setting,\n" in handlers_text
    assert "create_sidebar_menu_setting_v2" not in handlers_text
    assert handlers_text.count("create_sidebar_menu_setting(") == 2


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


def test_menu_section_form_js_is_the_sole_js_reference_to_the_create_route() -> None:
    modules_dir = PROJECT_ROOT / "static" / "js"
    matching_files = []

    for script_path in modules_dir.rglob("*.js"):
        script_text = script_path.read_text(encoding="utf-8")
        if "/settings/menu/create" in script_text:
            matching_files.append(script_path.name)

    assert matching_files == ["menu_section_form.js"]


def test_menu_section_form_js_never_intercepts_form_submission() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "menu_section_form.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert "preventDefault" not in script_text
    assert "fetch(" not in script_text
    assert "XMLHttpRequest" not in script_text


####################################################################################
# (4) COMPORTAMENTO ESTRANHO: a rota /settings/menu/create (e a logica de
# persistencia v2 que ela invoca, incluindo o bug de entity_id documentado em
# test_geral_menu_persistence_isolation_v1.py) nao tem NENHUM formulario
# correspondente em nenhum template renderizado. menu_section_form.js procura um
# seletor DOM que nunca existe em new_user.html, tornando-o inerte na pratica.
####################################################################################

def test_new_user_html_has_no_form_targeting_the_create_route() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    assert 'action="/settings/menu/create"' not in template_text


def test_menu_section_form_js_selector_targets_a_form_action_absent_from_the_template() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "menu_section_form.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert 'form[action="/settings/menu/create"]' in script_text

    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    assert 'action="/settings/menu/create"' not in template_text


####################################################################################
# (5) CONTAGEM DE MARCADORES NO TEMPLATE: cada rota de Geral com formulario visivel
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
# (6) COMPORTAMENTO ESTRANHO: menu_section_form.js injeta dinamicamente um campo
# <select name="menu_section"> no (inexistente) formulario de criacao, mas o
# handler de criacao nao declara esse nome como parametro Form(...) -- mesmo que o
# form existisse e o campo fosse submetido, o FastAPI ignoraria o valor
# silenciosamente (nao gera erro 422, o campo e' simplesmente descartado).
####################################################################################

def test_create_handler_signature_has_no_menu_section_form_parameter() -> None:
    import appgenesis.routes.profile.settings_handlers as settings_handlers_module

    signature = inspect.signature(
        settings_handlers_module.create_sidebar_menu_setting_handler_v1
    )
    assert "menu_section" not in signature.parameters


def test_menu_section_form_js_injects_a_field_named_menu_section() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "menu_section_form.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert 'name="menu_section"' in script_text
