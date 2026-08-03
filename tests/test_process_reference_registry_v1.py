from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_new_user_template_loads_process_reference_registry_before_new_user() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    module_snippet = '/static/js/modules/process_reference_registry_v1.js'
    new_user_snippet = '/static/js/new_user.js'

    assert module_snippet in template_text
    assert new_user_snippet in template_text
    assert template_text.index(module_snippet) < template_text.index(new_user_snippet)


def test_new_user_js_consumes_process_reference_registry_constants() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "const appGenesisProcessReferenceRegistryV1 =" in script_text
    assert "const HOME_MENU_KEY_V1 = appGenesisProcessReferenceRegistryV1" in script_text
    assert "const ADMINISTRATIVO_MENU_KEY_V1 = appGenesisProcessReferenceRegistryV1" in script_text
    assert "const PERFIL_AUTORIZACAO_MENU_KEY_V1 = appGenesisProcessReferenceRegistryV1" in script_text
    assert "const ENTIDADE_SUBPROCESS_KEY_V1 = appGenesisProcessReferenceRegistryV1" in script_text
    assert "const UTILIZADOR_SUBPROCESS_KEY_V1 = appGenesisProcessReferenceRegistryV1" in script_text
    assert "const MENU_SUBPROCESS_KEY_V1 = appGenesisProcessReferenceRegistryV1" in script_text
    assert "const OBJETO_AUTORIZACAO_SUBPROCESS_KEY_V1 = appGenesisProcessReferenceRegistryV1" in script_text


def test_process_reference_registry_module_exposes_expected_symbols() -> None:
    module_text = (
        PROJECT_ROOT / "static" / "js" / "modules" / "process_reference_registry_v1.js"
    ).read_text(encoding="utf-8")

    assert "AppGenesisProcessReferenceRegistryV1" in module_text
    assert "HOME_MENU_KEY_V1" in module_text
    assert "ADMINISTRATIVO_MENU_KEY_V1" in module_text
    assert "PERFIL_AUTORIZACAO_MENU_KEY_V1" in module_text
    assert "ENTIDADE_SUBPROCESS_KEY_V1" in module_text
    assert "UTILIZADOR_SUBPROCESS_KEY_V1" in module_text
    assert "MENU_SUBPROCESS_KEY_V1" in module_text
    assert "OBJETO_AUTORIZACAO_SUBPROCESS_KEY_V1" in module_text
