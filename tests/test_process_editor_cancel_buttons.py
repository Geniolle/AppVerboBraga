import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) TODOS OS BOTOES CANCELAR DO EDITOR DE PROCESSO SAEM DO EDITOR INTEIRO, USANDO O
# MESMO PADRAO GENERICO JA USADO NA ABA GERAL (settings_edit_origin_menu / cancel_target).
####################################################################################

CANCEL_BUTTON_MARKERS = [
    "data-process-fields-config-cancel",
    "data-process-quantity-editor-cancel",
    "data-process-list-editor-cancel",
    "data-process-subsequent-field-cancel",
    "data-additional-field-editor-cancel",
]


def _read_new_user_html() -> str:
    return (PROJECT_ROOT / "templates" / "new_user.html").read_text(encoding="utf-8")


def test_all_process_editor_tab_cancel_buttons_exit_the_whole_editor() -> None:
    html_text = _read_new_user_html()

    for marker in CANCEL_BUTTON_MARKERS:
        marker_index = html_text.index(marker)
        # Janela ampla o suficiente para cobrir o bloco <button ...> inteiro em qualquer formatacao.
        window = html_text[max(0, marker_index - 400):marker_index + 400]

        assert 'data-appgenesis-cancel-target="settings-menu-edit-card"' in window, (
            f"Botao Cancelar de {marker} nao sai do editor de processo inteiro."
        )
        assert "data-appgenesis-cancel-return-target=" in window
        assert "data-appgenesis-cancel-return-url=" in window


def test_process_editor_cancel_buttons_use_generic_origin_menu_not_hardcoded() -> None:
    html_text = _read_new_user_html()

    # O padrao generico usado em toda a app: settings_edit_origin_menu (variavel Jinja calculada uma
    # vez para o processo em edicao), nunca um menu_key literal como "calendario" ou "administrativo".
    return_url_pattern = re.compile(
        r'data-appgenesis-cancel-return-url="/users/new\?menu=\{\{\s*settings_edit_origin_menu\s*\}\}'
    )
    matches = return_url_pattern.findall(html_text)

    # Aba Geral (2 variantes: owner editavel + somente leitura) + as 5 abas do editor.
    assert len(matches) == 7

    for hardcoded_menu in ("menu=calendario", "menu=administrativo\"", "menu=sessoes\""):
        assert hardcoded_menu not in html_text


def test_process_editor_cancel_return_target_reuses_settings_edit_cancel_target_variable() -> None:
    html_text = _read_new_user_html()

    assert html_text.count(
        'data-appgenesis-cancel-return-target="{{ settings_edit_cancel_target }}"'
    ) == 7


####################################################################################
# (2) OUTROS BOTOES CANCELAR (fora do editor de processo) NAO FORAM ALTERADOS
####################################################################################

def test_unrelated_cancel_buttons_outside_process_editor_are_untouched() -> None:
    html_text = _read_new_user_html()

    # Botoes de cancelar de outros fluxos (perfil pessoal, dados de treino, entidade, utilizador,
    # processo dinamico) continuam a apontar para os proprios cards, nao para settings-menu-edit-card.
    assert 'data-appgenesis-cancel-target="dynamic-process-card"' in html_text
    assert 'data-appgenesis-cancel-target="perfil-pessoal-card"' in html_text
    assert 'data-appgenesis-cancel-target="dados-treinamento-card"' in html_text
    assert 'data-appgenesis-cancel-target="edit-entity-card"' in html_text
    assert 'data-appgenesis-cancel-target="edit-user-card"' in html_text
