import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) AUSENCIA DE LISTENERS DUPLICADOS: cada bind function usa um guard idempotente
# (dataset.xxxBoundV1 === "1") antes de anexar os seus event listeners.
####################################################################################

def test_process_subsequent_fields_manager_v1_bind_functions_are_idempotency_guarded() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_subsequent_fields_manager_v1.js"
    script_text = script_path.read_text(encoding="utf-8")

    guarded_flags = [
        "processSubsequentOptionsBoundV1",
        "processSubsequentCancelBoundV1",
        "processSubsequentSubmitBoundV1",
        "processSubsequentSubmitNativeBoundV1",
        "processSubsequentFieldsManagerBoundV1",
    ]

    for flag in guarded_flags:
        guard_pattern = rf'form\.dataset\.{flag} === "1"'
        set_pattern = rf'form\.dataset\.{flag} = "1"'
        assert re.search(guard_pattern, script_text), f"guard ausente para {flag}"
        assert re.search(set_pattern, script_text), f"set do guard ausente para {flag}"


####################################################################################
# (2) AUSENCIA DE DUPLICACAO NO FRONTEND: o template global deve conter exatamente
# um formulario/manager de Campos Subsequentes.
####################################################################################

def test_template_has_single_process_subsequent_fields_form() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    occurrences = template_text.count('data-process-subsequent-fields-manager-v1="1"')
    assert occurrences == 1


####################################################################################
# (3) NORMALIZE_MENU_PROCESS_SUBSEQUENT_FIELDS: apos a consolidacao desta fase,
# existe exatamente 1 definicao no ficheiro fonte (as 2 geracoes mortas e o seu
# helper exclusivo _normalize_subsequent_field_operator_v2 foram removidos). A
# definicao restante preserva deduplicacao, geracao deterministica de key e
# operadores ativos em ingles.
####################################################################################

def test_menu_settings_has_exactly_one_subsequent_fields_normalizer_definition() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    menu_settings_text = menu_settings_path.read_text(encoding="utf-8")
    lines = menu_settings_text.splitlines()

    definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def normalize_menu_process_subsequent_fields(")
    ]

    assert len(definition_line_numbers) == 1

    from appgenesis.menu_settings import normalize_menu_process_subsequent_fields
    import inspect

    live_source = inspect.getsource(normalize_menu_process_subsequent_fields)
    _, live_start_line = inspect.getsourcelines(normalize_menu_process_subsequent_fields)

    assert live_start_line == definition_line_numbers[0]
    assert "seen_fields" in live_source
    assert "_build_subsequent_field_key_v3" in live_source
    assert '"is_empty"' in live_source
    assert '"is_not_empty"' in live_source
    assert '"equals"' in live_source
    assert '"not_equals"' in live_source

    assert "_normalize_subsequent_field_operator_v2" not in menu_settings_text
