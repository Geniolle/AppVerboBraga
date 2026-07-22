from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) CAMPO DE ORIGEM NUNCA DEVE REAPROVEITAR HEADERS COMO OPCOES VALIDAS
####################################################################################

def test_process_additional_fields_manager_v3_filters_headers_from_source_field_options() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_additional_fields_manager_v3.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert '.filter((opt) => opt && opt.fieldType !== "header")' in script_text
    assert 'clean === "automatic" || clean === "field_list" || clean === "active_menus" || clean === "profile_menu_tabs"' in script_text
    assert 'return "Menus ativos";' in script_text
    assert 'return "Abas do processo selecionado";' in script_text


####################################################################################
# (2) TIPO "HORARIO" (time) DEVE ESTAR DISPONIVEL E COM O LABEL CORRETO
####################################################################################

def test_process_additional_fields_manager_v3_supports_time_field_type() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_additional_fields_manager_v3.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert '"text", "number", "email", "phone", "date", "time", "flag", "header", "list"' in script_text
    assert 'time: "Horário"' in script_text
    # "time" nao deve ser tratado como tipo textual (tamanho maximo continua opcional)
    assert 'const TEXTUAL_TYPES = new Set(["text", "number", "email", "phone"]);' in script_text


####################################################################################
# (3) CAMPO LISTA DEVE USAR O SELECT "NOME DA LISTA" DO PROPRIO PROCESSO
####################################################################################

def test_process_additional_fields_manager_v3_exposes_named_list_selector() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_additional_fields_manager_v3.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert "Nome da Lista" in template_text
    assert "Lista manual" not in template_text
    assert "Fonte dos dados" not in template_text
    assert "data-additional-field-editor-key" in template_text
    assert 'data-additional-field-editor-list-key' in template_text
    assert 'data-additional-field-list-wrap' not in template_text
    assert "settings_edit_data.process_lists|default([])" in template_text
    assert "function getProcessListOptions_v3(root)" in script_text
    assert 'function getProcessListsSourceElement_v3(root)' in script_text
    assert 'root.querySelector("[data-process-lists]")' in script_text
    assert 'refreshProcessListOptions_v3(root, selectedListKey);' in script_text
    assert 'Lista: ${getManualListLabelByKey_v3(root, manualListKey)}' in script_text
    assert 'Selecione o nome da lista.' in script_text
    assert 'Lista não encontrada' in script_text
    assert 'Nenhuma lista criada' in script_text
    assert 'Informe pelo menos uma opção da lista manual.' not in script_text
