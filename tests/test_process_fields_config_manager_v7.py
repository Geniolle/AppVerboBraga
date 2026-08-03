from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) TESTAR LEITURA DO HEADER LEGADO NO MANAGER V7
####################################################################################

def test_process_fields_config_manager_v7_reads_legacy_header_key() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v7.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert 'valorLinhaLegacy_v7(row, "[data-process-config-header-key]")' in script_text
    assert "headerKey: explicitHeaderKey || currentHeaderKey" in script_text


####################################################################################
# (2) TESTAR TEMPLATE LEGADO COM HEADER KEY EXPLICITO
####################################################################################

def test_new_user_template_exposes_legacy_process_field_header_key() -> None:
    template_path = PROJECT_ROOT / "templates" / "new_user.html"
    template_text = template_path.read_text(encoding="utf-8")

    assert "data-process-config-header-key" in template_text
