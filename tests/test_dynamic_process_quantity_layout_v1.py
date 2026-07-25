from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) LAYOUT DINAMICO: QUANTIDADE DEVE INSERIR O BLOCO JUNTO DA SUA ANCORA
####################################################################################


def test_dynamic_process_quantity_groups_use_anchor_insertion_and_correct_actions_label() -> None:
    script_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert "function insertAfterAnchorOrAppendV1(containerEl, blockEl, anchorEl)" in script_text
    assert "dynamicProcessReadOnlyGridEl.querySelector" in script_text
    assert "dynamicProcessEditGridEl.querySelector" in script_text
    assert 'actionsHeadEl.textContent = "Ações";' in script_text
