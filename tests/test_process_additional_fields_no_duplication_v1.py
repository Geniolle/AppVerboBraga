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
# (3) NORMALIZE_MENU_PROCESS_ADDITIONAL_FIELDS: consolidado na Fase 3 estrutural e
# realocado na Fase 9 estrutural para
# appgenesis/services/process_settings/additional_field_service.py (menu_settings.py
# passou a reexportar ambas as implementacoes para manter compatibilidade externa).
# As geracoes mortas (v0 bare, v2, v3 x2, v4, e o wrapper bare que apenas delegava
# para _v1) foram removidas, junto dos guards _original_..._for_list_vN exclusivos
# a essa cadeia. Restam exatamente DUAS implementacoes ativas, com responsabilidades
# distintas (nao devem ser fundidas nesta fase):
#   - normalize_menu_process_additional_fields (bare): normalizacao final completa,
#     com suporte a lista automatica/manual e reordenamento de headers; usada na
#     gravacao (update_sidebar_menu_additional_fields_v4) e por Campos Quantidade.
#   - normalize_menu_process_additional_fields_v1: normalizacao auxiliar usada por
#     _rebuild_menu_process_hierarchy_from_additional_fields_v1 (calculo do estado
#     anterior), por move_sidebar_menu_additional_field e por
#     scripts/backfill_menu_hierarchy_v1.py.
####################################################################################

def test_menu_settings_has_exactly_two_active_additional_fields_normalizers() -> None:
    additional_field_service_path = (
        PROJECT_ROOT
        / "appgenesis"
        / "services"
        / "process_settings"
        / "additional_field_service.py"
    )
    text = additional_field_service_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    bare_definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def normalize_menu_process_additional_fields(")
    ]
    v1_definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def normalize_menu_process_additional_fields_v1(")
    ]

    # Exatamente uma definicao bare e uma definicao _v1 -- as duas implementacoes
    # ativas e explicitas desta fase. Nenhuma geracao morta (v2/v3/v4) remanesce.
    assert len(bare_definition_line_numbers) == 1
    assert len(v1_definition_line_numbers) == 1
    assert "normalize_menu_process_additional_fields_v2(" not in text
    assert "normalize_menu_process_additional_fields_v3(" not in text
    assert "normalize_menu_process_additional_fields_v4(" not in text
    assert "_original_normalize_menu_process_additional_fields_for_list_v1" not in text
    assert "_original_normalize_menu_process_additional_fields_for_list_v2" not in text
    assert "_original_normalize_menu_process_additional_fields_for_list_v3" not in text

    from appgenesis.menu_settings import (
        normalize_menu_process_additional_fields,
        normalize_menu_process_additional_fields_v1,
    )

    bare_source = inspect.getsource(normalize_menu_process_additional_fields)
    _, bare_start_line = inspect.getsourcelines(normalize_menu_process_additional_fields)
    v1_source = inspect.getsource(normalize_menu_process_additional_fields_v1)

    assert bare_start_line == bare_definition_line_numbers[0]
    # Assinatura distintiva da versao bare: reordena headers para o inicio da lista.
    assert "header" in bare_source
    # As duas implementacoes permanecem distintas (nao foram fundidas nesta fase).
    assert bare_source != v1_source


####################################################################################
# (4) UPDATE_SIDEBAR_MENU_ADDITIONAL_FIELDS: consolidado na Fase 3 estrutural e
# realocado na Fase 9 estrutural para
# appgenesis/services/process_settings/additional_field_service.py (menu_settings.py
# passou a reexportar a cadeia v1->v4 para manter compatibilidade externa). As duas
# definicoes de nome nao sufixado (a original e a que continha o bug latente
# raw_fields=raw_fields) foram removidas, junto dos imports orfaos em
# profile_handlers.py e page_handler.py. Resta apenas a cadeia de persistencia ativa
# e explicita: update_sidebar_menu_additional_fields_v1 (chamada pelo handler) delega
# para update_sidebar_menu_additional_fields_v4 (implementacao real, grava no banco).
####################################################################################

def test_menu_settings_has_only_the_v1_to_v4_persistence_chain() -> None:
    additional_field_service_path = (
        PROJECT_ROOT
        / "appgenesis"
        / "services"
        / "process_settings"
        / "additional_field_service.py"
    )
    text = additional_field_service_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    bare_definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def update_sidebar_menu_additional_fields(")
    ]
    v1_definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def update_sidebar_menu_additional_fields_v1(")
    ]
    v4_definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def update_sidebar_menu_additional_fields_v4(")
    ]

    # Nenhum wrapper bare morto remanesce; a cadeia _v1 -> _v4 e' unica e explicita.
    assert len(bare_definition_line_numbers) == 0
    assert len(v1_definition_line_numbers) == 1
    assert len(v4_definition_line_numbers) == 1

    # O bug latente raw_fields=raw_fields foi removido do codigo executavel.
    assert "raw_fields=raw_fields" not in text

    from appgenesis.menu_settings import (
        update_sidebar_menu_additional_fields_v1,
        update_sidebar_menu_additional_fields_v4,
    )

    v1_source = inspect.getsource(update_sidebar_menu_additional_fields_v1)
    assert "update_sidebar_menu_additional_fields_v4" in v1_source
    assert update_sidebar_menu_additional_fields_v4 is not None


def test_settings_handlers_only_imports_and_calls_the_v1_suffixed_persistence_function() -> None:
    handlers_path = (
        PROJECT_ROOT
        / "appgenesis"
        / "routes"
        / "profile"
        / "process_settings"
        / "additional_field_handlers.py"
    )
    handlers_text = handlers_path.read_text(encoding="utf-8")

    assert "update_sidebar_menu_additional_fields_v1" in handlers_text
    # O nome nao sufixado (a versao com bug latente) nao deve aparecer no handler --
    # confirma que o caminho realmente executado nunca passa pela definicao quebrada.
    assert re.search(r'\bupdate_sidebar_menu_additional_fields\(', handlers_text) is None
