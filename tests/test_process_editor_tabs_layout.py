from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EDITOR_LAYOUT_CSS_PATHS = [
    PROJECT_ROOT / "static" / "css" / "modules" / "configurable_items_manager_v1.css",
    PROJECT_ROOT / "static" / "entities" / "css" / "modules" / "configurable_items_manager_v1.css",
]


####################################################################################
# (1) ESTRUTURA GLOBAL DAS ABAS DO EDITOR DE PROCESSO
####################################################################################


def _read_new_user_html() -> str:
    return (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")


def _pane_segment(html_text: str, pane_key: str) -> str:
    pane_marker = f'data-process-edit-pane="{pane_key}"'
    pane_start = html_text.index(pane_marker)
    next_pane_start = html_text.find('data-process-edit-pane="', pane_start + 1)
    return html_text[pane_start: next_pane_start if next_pane_start != -1 else len(html_text)]


def _read_editor_layout_css() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in EDITOR_LAYOUT_CSS_PATHS)


def test_all_process_editor_panes_remain_present_and_structural_only() -> None:
    html_text = _read_new_user_html()

    pane_keys = [
        "geral",
        "campos-config",
        "campos-adicionais",
        "campos-quantidade",
        "lista",
        "campos-subsequentes",
    ]

    assert html_text.count("data-process-edit-pane=") == len(pane_keys)

    for pane_key in pane_keys:
        pane_text = _pane_segment(html_text, pane_key)
        opening_tag = pane_text.split(">", 1)[0]

        assert f'data-process-edit-pane="{pane_key}"' in opening_tag
        assert "process-edit-pane" in opening_tag
        assert "admin-subsection" not in opening_tag
        assert "card" not in opening_tag


def test_geral_tab_keeps_the_reference_card_layout() -> None:
    html_text = _read_new_user_html()
    geral_pane = _pane_segment(html_text, "geral")

    assert 'id="settings-process-fields-list-card"' in geral_pane
    assert 'class="card admin-subprocess-table-card-v1"' in geral_pane
    assert "<h2>Campos disponíveis</h2>" in geral_pane


def test_non_general_tabs_do_not_reintroduce_outer_admin_subsection_cards() -> None:
    html_text = _read_new_user_html()

    for pane_key in [
        "campos-config",
        "campos-adicionais",
        "campos-quantidade",
        "lista",
        "campos-subsequentes",
    ]:
        pane_text = _pane_segment(html_text, pane_key)

        assert "admin-subsection" not in pane_text
        assert "render_configurable_form_card" in pane_text
        assert "render_configurable_list_card" in pane_text


def test_process_editor_list_wrapper_is_explicitly_transparent() -> None:
    css_text = _read_editor_layout_css()

    assert "#settings-menu-edit-card .process-edit-pane .configurable-items-list-v1" in css_text
    assert "border: 0 !important;" in css_text
    assert "border-radius: 0 !important;" in css_text
    assert "background: transparent !important;" in css_text
    assert "box-shadow: none !important;" in css_text
    assert "padding: 0 !important;" in css_text
