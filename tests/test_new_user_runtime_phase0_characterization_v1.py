from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) POST-SAVE: O MOTOR LEGADO FOI REMOVIDO DO NEW_USER.JS
####################################################################################

def test_new_user_post_save_runtime_preserves_menu_target_and_section_order() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "function buildReturnUrlPostSaveV6(form)" not in script_text
    assert "function syncReturnUrlPostSaveV6(form)" not in script_text


####################################################################################
# (2) POST-SAVE: OS BLOCOS HISTORICOS FORAM REMOVIDOS DO NEW_USER.JS
####################################################################################

def test_new_user_post_save_runtime_removed_legacy_blocks_from_bootstrap() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "APPGENESIS_POST_SAVE_CONTEXT_CAPTURE_V3_START" not in script_text
    assert "APPGENESIS_RETURN_URL_POST_SAVE_CAPTURE_V4_START" not in script_text
    assert "APPGENESIS_FRONTEND_RETURN_URL_POST_SAVE_V6_START" not in script_text
    assert "APPGENESIS_INITIAL_PROFILE_SECTION_FROM_URL_V1_START" not in script_text
    assert "APPGENESIS_KEEP_CURRENT_PROCESS_AFTER_PROFILE_SAVE_V1_START" not in script_text


####################################################################################
# (3) CAMPO ADICIONAL: O LEGADO V2 FOI DESLIGADO E O BOOTSTRAP NAO PODE MAIS
# INVOCAR O GUARD DE COEXISTENCIA.
####################################################################################

def test_new_user_legacy_additional_fields_v2_is_removed_from_bootstrap() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "setupProcessAdditionalFieldsManagerV2" not in script_text
    assert "setupProcessAdditionalFieldsManagerV2_guard_v1" not in script_text
    assert "setupProcessAdditionalFieldsManagerV2();" not in script_text
    assert "window.__appgenesisAddAdditionalFieldV2" not in script_text
    assert "window.__appgenesisClearAdditionalFieldV2" not in script_text


####################################################################################
# (4) LOAD ORDER: O RELOAD GUARD TEM DE FICAR NO HEAD E O NEW_USER DEPOIS DOS MODULOS
####################################################################################

def test_new_user_template_keeps_reload_guard_in_head_and_new_user_after_canonical_modules() -> None:
    template_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")

    head_guard_index = template_text.index('src="/static/js/modules/navigation_reload_guard_v1.js')
    body_new_user_index = template_text.index('src="/static/js/new_user.js')
    quantity_manager_index = template_text.index('src="/static/js/modules/process_quantity_fields_manager_v1.js')
    subsequent_manager_index = template_text.index('src="/static/js/modules/process_subsequent_fields_manager_v1.js')

    assert head_guard_index < quantity_manager_index < subsequent_manager_index < body_new_user_index
