from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O HELPER LEGADO DE POST-SAVE FOI REMOVIDO DO NEW_USER.JS
####################################################################################

def test_post_save_context_prioritizes_current_url_menu_over_form_fields() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "new_user.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert "function currentMenuFromUrlOrBootstrapPostSaveV3" not in script_text
    assert "function buildReturnUrlPostSaveV6" not in script_text
    assert "function syncReturnUrlPostSaveV6" not in script_text
