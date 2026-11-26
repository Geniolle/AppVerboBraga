from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dynamic_process_has_no_separate_action_card() -> None:
    html_text = (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")
    js_text = (PROJECT_ROOT / "static" / "js" / "new_user.js").read_text(encoding="utf-8")

    assert 'id="dynamic-process-action-card"' not in html_text
    assert "dynamicProcessActionCardEl" not in js_text

    # O botao Editar vive dentro do cabecalho do card do processo.
    card_index = html_text.index('id="dynamic-process-card"')
    toggle_index = html_text.index('id="dynamic-process-edit-toggle"')
    readonly_index = html_text.index('id="dynamic-process-readonly"')
    assert card_index < toggle_index < readonly_index
