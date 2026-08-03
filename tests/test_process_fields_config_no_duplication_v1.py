import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) AUSENCIA DE LISTENERS DUPLICADOS: cada bind function ativa usa um guard
# idempotente antes de anexar os seus event listeners. Ao contrario de Campos
# Subsequentes (onde TODOS os guards usam o mesmo padrao "=== '1'"), esta aba tem
# uma unica excecao confirmada por leitura direta do codigo: o guard nativo de
# submit usa o operador invertido "!== '1'" (linha 781), nao "=== '1'".
####################################################################################

def test_process_fields_config_manager_v7_bind_functions_are_idempotency_guarded() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v7.js"
    script_text = script_path.read_text(encoding="utf-8")

    positive_guarded_flags = [
        "processFieldsConfigCancelBoundV7",
        "processFieldsConfigSubmitBoundV7",
        "processFieldsConfigOptionsBoundV7",
        "processFieldsConfigManagerBoundV7",
    ]

    for flag in positive_guarded_flags:
        guard_pattern = rf'form\.dataset\.{flag} === "1"'
        set_pattern = rf'form\.dataset\.{flag} = "1"'
        assert re.search(guard_pattern, script_text), f"guard ausente para {flag}"
        assert re.search(set_pattern, script_text), f"set do guard ausente para {flag}"


def test_process_fields_config_manager_v7_native_submit_guard_uses_inverted_operator() -> None:
    """
    Comportamento estranho documentado (nao corrigido): o guard nativo de submit
    (linha 781-782) usa "!==" (operador invertido) em vez de "===", ao contrario de
    todos os outros guards desta mesma aba. Alem disso, este guard usa numeracao V8
    ("processFieldsConfigSubmitNativeBoundV8"), inconsistente com o resto do
    ficheiro, que usa V7. Este teste trava o comportamento atual.
    """
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v7.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert re.search(
        r'form\.dataset\.processFieldsConfigSubmitNativeBoundV8 !== "1"', script_text
    )
    assert re.search(
        r'form\.dataset\.processFieldsConfigSubmitNativeBoundV8 = "1"', script_text
    )
    # V7/V8 mixed numbering, confirmed present in the same file.
    assert "processFieldsConfigManagerBoundV7" in script_text
    assert "processFieldsConfigSubmitNativeBoundV8" in script_text


####################################################################################
# (2) AUSENCIA DE DUPLICACAO NO FRONTEND: o template global deve conter exatamente
# um manager e um bloco de editor de Configuracao dos campos.
####################################################################################

def test_template_has_single_process_fields_config_manager_marker() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    occurrences = template_text.count('data-process-fields-config-manager-v1="1"')
    assert occurrences == 1


def test_template_has_single_process_fields_config_editor_block() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    occurrences = template_text.count("data-process-fields-config-editor-block")
    assert occurrences == 1


####################################################################################
# (3) MULTIPLAS GERACOES: ao contrario de Campos Adicionais (3-4 geracoes,
# last-definition-wins), esta aba tem apenas 2 geracoes de persistencia e 2 de
# normalizacao -- e AMBAS estao vivas (a versao sem sufixo delega diretamente para
# a versao _v4, nao ha nenhuma definicao morta ou sobreposta). O Phase 0 assessment
# doc especulava que update_sidebar_menu_process_fields_v4 pudesse ser codigo morto
# ("candidata a codigo morto") -- este teste confirma, por leitura direta, que essa
# especulacao estava incorreta: e' a implementacao real, chamada pela funcao sem
# sufixo, que por sua vez e' a unica importada por settings_handlers.py. Realocadas
# na Fase 9 estrutural para appgenesis/services/process_settings/field_service.py
# (menu_settings.py passou a reexporta-las para manter compatibilidade dos call
# sites existentes).
####################################################################################

def test_menu_settings_has_exactly_two_process_fields_persistence_generations() -> None:
    field_service_path = (
        PROJECT_ROOT / "appgenesis" / "services" / "process_settings" / "field_service.py"
    )
    lines = field_service_path.read_text(encoding="utf-8").splitlines()

    definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def update_sidebar_menu_process_fields(")
        or line_text.startswith("def update_sidebar_menu_process_fields_v4(")
    ]

    assert len(definition_line_numbers) == 2

    import inspect

    from appgenesis.menu_settings import (
        update_sidebar_menu_process_fields,
        update_sidebar_menu_process_fields_v4,
    )

    wrapper_source = inspect.getsource(update_sidebar_menu_process_fields)
    assert "update_sidebar_menu_process_fields_v4(" in wrapper_source

    # A implementacao real (_v4) escreve na base de dados via SQL bruto -- prova de
    # que nao esta morta.
    v4_source = inspect.getsource(update_sidebar_menu_process_fields_v4)
    assert "UPDATE sidebar_menu_settings" in v4_source


def test_menu_settings_has_exactly_two_process_fields_normalizer_generations() -> None:
    field_service_path = (
        PROJECT_ROOT / "appgenesis" / "services" / "process_settings" / "field_service.py"
    )
    lines = field_service_path.read_text(encoding="utf-8").splitlines()

    definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def normalize_menu_process_visible_fields(")
        or line_text.startswith("def normalize_menu_process_visible_fields_v4(")
    ]

    assert len(definition_line_numbers) == 2

    import inspect

    from appgenesis.menu_settings import normalize_menu_process_visible_fields

    wrapper_source = inspect.getsource(normalize_menu_process_visible_fields)
    assert "normalize_menu_process_visible_fields_v4(" in wrapper_source


def test_settings_handlers_only_calls_the_unsuffixed_persistence_wrapper() -> None:
    handlers_path = (
        PROJECT_ROOT
        / "appgenesis"
        / "routes"
        / "profile"
        / "process_settings"
        / "field_handlers.py"
    )
    handlers_text = handlers_path.read_text(encoding="utf-8")

    assert re.search(r'\bupdate_sidebar_menu_process_fields\(', handlers_text) is not None
    # O handler nunca chama a versao _v4 diretamente -- sempre passa pelo wrapper.
    assert re.search(r'\bupdate_sidebar_menu_process_fields_v4\(', handlers_text) is None


def test_unsuffixed_helpers_are_imported_but_never_called_elsewhere() -> None:
    """
    Comportamento estranho de baixo risco, documentado e nao corrigido (regra 18):
    update_sidebar_menu_process_fields e' importado em page_handler.py e
    profile_handlers.py mas nunca invocado nesses ficheiros -- imports mortos, nao
    um risco funcional real (o handler ativo desta aba, em settings_handlers.py,
    continua a ser o unico chamador real).
    """
    page_handler_path = PROJECT_ROOT / "appgenesis" / "routes" / "profile" / "page_handler.py"
    profile_handlers_path = PROJECT_ROOT / "appgenesis" / "routes" / "profile" / "profile_handlers.py"

    for path in (page_handler_path, profile_handlers_path):
        text = path.read_text(encoding="utf-8")
        assert "update_sidebar_menu_process_fields" in text
        assert re.search(r'\bupdate_sidebar_menu_process_fields\(', text) is None
