import inspect
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) AUSENCIA DE LISTENERS DUPLICADOS: cada bind function ativa usa um guard
# idempotente antes de anexar os seus event listeners. Todos os 5 guards
# identificados usam o operador "===", ao contrario de Campos Adicionais e
# Configuração dos campos, onde pelo menos um guard usa o operador invertido "!==".
####################################################################################

def test_process_quantity_fields_manager_v1_bind_functions_are_idempotency_guarded() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_quantity_fields_manager_v1.js"
    script_text = script_path.read_text(encoding="utf-8")

    guarded_flags = [
        "processQuantityOptionsBoundV1",
        "processQuantityCancelBoundV1",
        "processQuantitySubmitBoundV1",
        "processQuantitySubmitNativeBoundV1",
        "processQuantityFieldsManagerBoundV1",
    ]

    for flag in guarded_flags:
        guard_pattern = rf'form\.dataset\.{flag} === "1"'
        set_pattern = rf'form\.dataset\.{flag} = "1"'
        assert re.search(guard_pattern, script_text), f"guard ausente para {flag}"
        assert re.search(set_pattern, script_text), f"set do guard ausente para {flag}"


def test_process_quantity_fields_manager_v1_resets_manager_guard_on_setup_failure() -> None:
    """
    Comportamento documentado (nao corrigido): ao contrario dos outros guards desta
    aba (que nunca sao limpos apos serem marcados), o guard
    processQuantityFieldsManagerBoundV1 e' explicitamente reposto a "" quando
    configurable-items-manager falha ao inicializar (manager === null), permitindo
    uma nova tentativa de setup numa chamada futura. Nenhum outro guard desta aba
    tem esse comportamento de rollback.
    """
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_quantity_fields_manager_v1.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert re.search(
        r'if \(!manager\) \{\s*form\.dataset\.processQuantityFieldsManagerBoundV1 = "";',
        script_text,
    )


def test_process_quantity_fields_manager_v1_is_the_sole_active_generation() -> None:
    """
    Ao contrario de Campos Adicionais (que tem uma geracao morta
    bindEditorExtras_v3 convivendo com a ativa bindEditorExtras_v4), a pasta de
    modulos JS nao contem scripts legados/paralelos para Campos Quantidade.
    O runtime novo passa a coexistir com o manager V1 porque e' a implementacao
    canonica da fase atual, enquanto o manager continua a ser o unico gerador
    administrativo.
    """
    modules_dir = PROJECT_ROOT / "static" / "js" / "modules"
    matches = sorted(
        path.name for path in modules_dir.glob("*quantity*")
    )
    assert matches == [
        "process_quantity_fields_manager_v1.js",
        "process_quantity_runtime_v1.js",
    ]


####################################################################################
# (2) AUSENCIA DE DUPLICACAO NO FRONTEND: o template global deve conter exatamente
# um manager e um painel de editor de Campos Quantidade.
####################################################################################

def test_template_has_single_process_quantity_fields_manager_marker() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    occurrences = template_text.count('data-process-quantity-fields-manager-v1="1"')
    assert occurrences == 1


def test_template_has_single_process_quantity_fields_panel() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    occurrences = template_text.count('id="settings-process-quantity-fields-card"')
    assert occurrences == 1


def test_template_has_single_process_quantity_fields_editor_form_action() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    occurrences = template_text.count('action="/settings/menu/process-quantity-fields"')
    assert occurrences == 1


####################################################################################
# (3) MULTIPLAS GERACOES NO BACKEND: ao contrario de Campos Adicionais (3 geracoes
# de normalizador, 4 de persistencia), Campos Quantidade tem exatamente UMA geracao
# de cada uma das suas duas funcoes proprias. Realocadas na Fase 9 estrutural para
# appgenesis/services/process_settings/quantity_field_service.py (menu_settings.py
# passou a reexporta-las para manter compatibilidade dos call sites existentes).
####################################################################################

def test_menu_settings_has_exactly_one_quantity_fields_normalizer_generation() -> None:
    quantity_field_service_path = (
        PROJECT_ROOT / "appgenesis" / "services" / "process_settings" / "quantity_field_service.py"
    )
    lines = quantity_field_service_path.read_text(encoding="utf-8").splitlines()

    definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def normalize_menu_process_quantity_fields(")
    ]

    assert len(definition_line_numbers) == 1


def test_menu_settings_has_exactly_one_quantity_fields_persistence_generation() -> None:
    quantity_field_service_path = (
        PROJECT_ROOT / "appgenesis" / "services" / "process_settings" / "quantity_field_service.py"
    )
    lines = quantity_field_service_path.read_text(encoding="utf-8").splitlines()

    definition_line_numbers = [
        line_number
        for line_number, line_text in enumerate(lines, start=1)
        if line_text.startswith("def update_sidebar_menu_process_quantity_fields_v1(")
    ]

    assert len(definition_line_numbers) == 1


def test_settings_handlers_only_calls_the_v1_suffixed_quantity_persistence_function() -> None:
    handlers_path = (
        PROJECT_ROOT
        / "appgenesis"
        / "routes"
        / "profile"
        / "process_settings"
        / "quantity_field_handlers.py"
    )
    handlers_text = handlers_path.read_text(encoding="utf-8")

    assert "update_sidebar_menu_process_quantity_fields_v1(" in handlers_text


####################################################################################
# (4) DEPENDENCIA DE UMA GERACAO PARTILHADA (Campos Adicionais): a validacao desta
# aba consulta normalize_menu_process_additional_fields, que tem 3 geracoes no
# ficheiro fonte -- a ultima (linha 4880) e' a que esta em vigor. Esta dependencia
# ja esta protegida por test_process_additional_fields_no_duplication_v1.py; este
# teste apenas confirma, do ponto de vista de Campos Quantidade, que a chamada
# dentro de update_sidebar_menu_process_quantity_fields_v1 usa o nome sem sufixo
# (que resolve para a geracao ativa via last-definition-wins), sem invocar
# diretamente nenhuma variante numerada.
####################################################################################

def test_quantity_fields_persistence_depends_on_unsuffixed_additional_fields_normalizer() -> None:
    from appgenesis.menu_settings import update_sidebar_menu_process_quantity_fields_v1

    source = inspect.getsource(update_sidebar_menu_process_quantity_fields_v1)
    assert "normalize_menu_process_additional_fields(" in source
    assert "normalize_menu_process_additional_fields_v" not in source


####################################################################################
# (5) COMPORTAMENTO ESTRANHO: referencia obsoleta nao e' revalidada na leitura
# (normalize_menu_process_quantity_fields nao recebe nem consulta additional_fields).
# A validacao cruzada so' acontece na GRAVACAO.
####################################################################################

def test_normalize_quantity_fields_signature_has_no_additional_fields_parameter() -> None:
    """
    Confirma, por assinatura, que normalize_menu_process_quantity_fields (usada em
    leitura via get_sidebar_menu_settings_v4) nao tem forma de cross-validar contra
    Campos Adicionais -- so' recebe raw_fields.
    """
    from appgenesis.menu_settings import normalize_menu_process_quantity_fields

    signature = inspect.signature(normalize_menu_process_quantity_fields)
    assert list(signature.parameters.keys()) == ["raw_fields"]


def test_get_sidebar_menu_settings_v4_reads_quantity_fields_via_bare_normalizer() -> None:
    menu_settings_path = PROJECT_ROOT / "appgenesis" / "menu_settings.py"
    menu_settings_text = menu_settings_path.read_text(encoding="utf-8")

    assert (
        'process_quantity_fields = normalize_menu_process_quantity_fields(\n'
        '            menu_config.get("process_quantity_fields")'
    ) in menu_settings_text
    assert 'item["process_quantity_fields"] = process_quantity_fields' in menu_settings_text


####################################################################################
# (6) RELACAO COM CONFIGURAÇÃO DOS CAMPOS: confirma, por leitura de codigo, que
# update_sidebar_menu_process_quantity_fields_v1 nunca consulta
# process_visible_fields -- nao ha filtragem cruzada com a aba Configuração dos
# campos.
####################################################################################

def test_quantity_fields_persistence_never_references_process_visible_fields() -> None:
    from appgenesis.menu_settings import update_sidebar_menu_process_quantity_fields_v1

    source = inspect.getsource(update_sidebar_menu_process_quantity_fields_v1)
    assert "process_visible_fields" not in source
