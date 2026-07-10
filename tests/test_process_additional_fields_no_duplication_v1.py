import inspect
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) AUSENCIA DE LISTENERS DUPLICADOS: cada bind function ativa (geracao V3/V4) usa
# um guard idempotente (dataset.xxx === "1") antes de anexar os seus event listeners.
# Nota: ao contrario de Campos Subsequentes, os guards desta aba nao seguem um unico
# padrao uniforme -- cada um foi confirmado individualmente por leitura do codigo.
####################################################################################

def test_process_additional_fields_manager_v3_bind_functions_are_idempotency_guarded() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_additional_fields_manager_v3.js"
    script_text = script_path.read_text(encoding="utf-8")

    # bindEditorExtras_v4: guard estatico direto em root.dataset.
    assert re.search(r'root\.dataset\.additionalFieldsExtrasBoundV4 === "1"', script_text)
    assert re.search(r'root\.dataset\.additionalFieldsExtrasBoundV4 = "1"', script_text)

    # bindGlobalCancelReaction_v3: guard dinamico via root.dataset[boundKey], chamado
    # com a chave "additionalFieldsCancelBoundV4" a partir de bindEditorExtras_v4.
    assert re.search(r'root\.dataset\[boundKey\] === "1"', script_text)
    assert re.search(r'root\.dataset\[boundKey\] = "1"', script_text)
    assert re.search(
        r'bindGlobalCancelReaction_v3\(root, cancelButton, manager, "additionalFieldsCancelBoundV4"\)',
        script_text,
    )

    # submit do formulario-pai: guard com operador !== (inverso), nao ===.
    assert re.search(
        r'parentForm\.dataset\.additionalFieldsTopSubmitBoundV4 !== "1"',
        script_text,
    )
    assert re.search(r'parentForm\.dataset\.additionalFieldsTopSubmitBoundV4 = "1"', script_text)

    # inicializacao do manager (evita recriar o manager sobre o mesmo root).
    assert re.search(r'root\.dataset\.additionalFieldsManagerReadyV3 === "1"', script_text)
    assert re.search(r'root\.dataset\.additionalFieldsManagerReadyV3 = "1"', script_text)


def test_process_additional_fields_manager_v3_legacy_v3_extras_guard_remains_but_is_dead() -> None:
    """
    Documenta comportamento estranho pre-existente (nao corrigido nesta fase):
    bindEditorExtras_v3 (geracao anterior, com o seu proprio guard
    additionalFieldsExtrasBoundV3) continua definida no ficheiro fonte, mas nao e'
    invocada a partir do caminho de inicializacao ativo (que usa bindEditorExtras_v4).
    """
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_additional_fields_manager_v3.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert re.search(r'root\.dataset\.additionalFieldsExtrasBoundV3 === "1"', script_text)
    assert "function bindEditorExtras_v3(root, manager)" in script_text
    assert "function bindEditorExtras_v4(root, manager)" in script_text


####################################################################################
# (2) AUSENCIA DE DUPLICACAO NO FRONTEND: o template global deve conter exatamente
# um manager e um bloco de editor de Campos Adicionais.
####################################################################################

def test_template_has_single_process_additional_fields_manager_marker() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    occurrences = template_text.count('data-process-additional-fields-manager-v3="1"')
    assert occurrences == 1


def test_template_has_single_additional_field_editor_block() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    occurrences = template_text.count("data-additional-field-editor-block")
    assert occurrences == 1


####################################################################################
# (3) NORMALIZE_MENU_PROCESS_ADDITIONAL_FIELDS: existem 3 geracoes desta funcao no
# ficheiro fonte (linhas 795, 4044 e 4880), todas com o mesmo nome. Dado que Python
# usa "last-definition-wins", apenas a definicao de maior numero de linha (4880) esta
# efetivamente em vigor -- e' essa que faz o reordenamento de headers para o inicio da
# lista. Este teste trava o comportamento atual; nao consolidar nesta fase.
####################################################################################

def test_menu_settings_still_has_three_additional_fields_normalizer_generations() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    lines = menu_settings_path.read_text(encoding="utf-8").splitlines()

    definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def normalize_menu_process_additional_fields(")
    ]

    assert len(definition_line_numbers) == 3

    from appgenesis.menu_settings import normalize_menu_process_additional_fields

    live_source = inspect.getsource(normalize_menu_process_additional_fields)
    _, live_start_line = inspect.getsourcelines(normalize_menu_process_additional_fields)

    assert live_start_line == definition_line_numbers[-1]
    # Assinatura distintiva da geracao ativa: reordena headers para o inicio da lista.
    assert "header" in live_source


####################################################################################
# (4) UPDATE_SIDEBAR_MENU_ADDITIONAL_FIELDS: existem 4 definicoes de persistencia no
# ficheiro fonte. Apenas update_sidebar_menu_additional_fields_v1 (que delega para
# _v4) e' importada e chamada a partir de settings_handlers.py. As duas definicoes de
# nome nao sufixado (linhas 2467 e 4240) nunca sao invocadas pelo handler desta aba;
# a de linha 4240 (a que efetivamente "ganha" por last-definition-wins) tem, alem
# disso, um bug latente: chama update_sidebar_menu_additional_fields_v1(...,
# raw_fields=raw_fields) mas essa funcao espera o parametro "fields", nao
# "raw_fields" -- pelo que, se alguma vez fosse invocada, falharia com TypeError.
# Comportamento estranho documentado, nao corrigido nesta fase (regra 10).
####################################################################################

def test_menu_settings_still_has_four_additional_fields_persistence_generations() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    text = menu_settings_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def update_sidebar_menu_additional_fields(")
        or line_text.startswith("def update_sidebar_menu_additional_fields_v1(")
        or line_text.startswith("def update_sidebar_menu_additional_fields_v4(")
    ]

    assert len(definition_line_numbers) == 4

    # A definicao de nome nao sufixado que efetivamente esta em vigor (a ultima,
    # last-definition-wins) chama _v1 com o parametro errado ("raw_fields").
    unsuffixed_defs = [
        i for i, line_text in enumerate(lines, start=1)
        if line_text.startswith("def update_sidebar_menu_additional_fields(")
    ]
    assert len(unsuffixed_defs) == 2

    from appgenesis.menu_settings import update_sidebar_menu_additional_fields

    live_source = inspect.getsource(update_sidebar_menu_additional_fields)
    _, live_start_line = inspect.getsourcelines(update_sidebar_menu_additional_fields)

    assert live_start_line == unsuffixed_defs[-1]
    assert "raw_fields=raw_fields" in live_source


def test_settings_handlers_only_imports_and_calls_the_v1_suffixed_persistence_function() -> None:
    handlers_path = PROJECT_ROOT / "appgenesis" / "routes" / "profile" / "settings_handlers.py"
    handlers_text = handlers_path.read_text(encoding="utf-8")

    assert "update_sidebar_menu_additional_fields_v1" in handlers_text
    # O nome nao sufixado (a versao com bug latente) nao deve aparecer no handler --
    # confirma que o caminho realmente executado nunca passa pela definicao quebrada.
    assert re.search(r'\bupdate_sidebar_menu_additional_fields\(', handlers_text) is None
