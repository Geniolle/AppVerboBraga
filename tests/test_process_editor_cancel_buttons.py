from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) TODOS OS BOTOES CANCELAR DO EDITOR DEVOLVEM O UTILIZADOR A LISTA DE ORIGEM
# (o "target" de contexto continua a ser o proprio card do editor -- necessario para o
# controlador global localizar/fechar o card -- mas o "return-target"/"return-url" ja
# nao apontam mais para o proprio editor, e sim para a lista de onde ele foi aberto).
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


def test_all_process_editor_tab_cancel_buttons_belong_to_process_editor() -> None:
    html_text = _read_new_user_html()

    for marker in CANCEL_BUTTON_MARKERS:
        marker_index = html_text.index(marker)
        # Janela ampla o suficiente para cobrir o bloco <button ...> inteiro em qualquer formatacao.
        window = html_text[max(0, marker_index - 400):marker_index + 400]

        assert 'data-appgenesis-cancel-target="settings-menu-edit-card"' in window, (
            f"Botao Cancelar de {marker} nao pertence ao editor de processo."
        )
        assert 'data-appgenesis-cancel-return-target="#{{ settings_edit_exit_target }}"' in window
        assert 'data-appgenesis-cancel-return-url="{{ settings_edit_exit_url }}"' in window


def test_process_editor_cancel_buttons_reuse_editor_exit_url() -> None:
    html_text = _read_new_user_html()

    # O padrao generico usado em toda a app: settings_edit_exit_url (variavel Jinja calculada uma
    # vez a partir do menu/aba de origem), nunca um menu_key literal como "calendario" ou "administrativo".
    matches = html_text.count(
        'data-appgenesis-cancel-return-url="{{ settings_edit_exit_url }}"'
    )

    # A aba Geral nao possui formulario/Guardar/Cancelar (mostra apenas "Campos disponiveis"),
    # por isso o botao Cancelar so existe nos 5 managers com criacao/edicao do editor
    # (campos-config, quantidade, listas, subsequentes, adicionais). O editor de colunas da
    # listagem foi consolidado dentro do manager de Listas e nao tem mais botao Cancelar proprio.
    assert matches == 5

    for hardcoded_menu in ("menu=calendario", "menu=administrativo\"", "menu=sessoes\""):
        assert hardcoded_menu not in html_text


def test_process_editor_cancel_return_target_is_the_origin_list() -> None:
    html_text = _read_new_user_html()

    assert html_text.count(
        'data-appgenesis-cancel-return-target="#{{ settings_edit_exit_target }}"'
    ) == 5


def test_geral_tab_has_no_form_only_available_fields_card() -> None:
    html_text = _read_new_user_html()

    geral_start = html_text.index('data-process-edit-pane="geral"')
    geral_end = html_text.index('data-process-edit-pane="campos-config"', geral_start)
    geral_pane = html_text[geral_start:geral_end]

    # Regra aprovada: a aba Geral nao tem formulario proprio, nem Guardar/Cancelar --
    # mostra apenas o card "Campos disponiveis" (somente leitura).
    assert "<form" not in geral_pane
    assert 'action="/settings/menu/edit"' not in geral_pane
    assert ">Guardar<" not in geral_pane
    assert ">Cancelar<" not in geral_pane
    assert "data-appgenesis-cancel-return-target" not in geral_pane
    assert "data-appgenesis-cancel-return-url" not in geral_pane
    assert "Campos disponíveis" in geral_pane


####################################################################################
# (1.1) TODAS AS ABAS DO EDITOR ENVIAM return_url NO GUARDAR, REUSANDO A MESMA VARIAVEL
# GLOBAL (settings_edit_return_url), PARA O BACKEND PRESERVAR CONTEXTO (ex.: admin_tab)
# SEM DEPENDER DE NAVEGACAO CORRETIVA NO CLIENTE.
####################################################################################

PROCESS_EDITOR_FORM_ACTIONS = [
    # A aba Geral nao tem formulario (somente leitura), por isso "/settings/menu/edit"
    # nao faz parte desta lista -- os 5 managers com criacao/edicao continuam cobertos.
    "/settings/menu/process-fields",
    "/settings/menu/process-quantity-fields",
    "/settings/menu/process-lists",
    "/settings/menu/process-subsequent-fields",
    "/settings/menu/process-additional-fields",
]


def test_all_process_editor_tab_forms_send_generic_return_url() -> None:
    html_text = _read_new_user_html()

    assert html_text.count(
        '<input type="hidden" name="return_url" value="{{ settings_edit_return_url }}">'
    ) == len(PROCESS_EDITOR_FORM_ACTIONS)

    for action in PROCESS_EDITOR_FORM_ACTIONS:
        action_index = html_text.index(f'action="{action}"')
        # A proxima ocorrencia de return_url apos a abertura do form tem de pertencer a ele.
        return_url_index = html_text.index('name="return_url"', action_index)
        next_action_index = html_text.find('action="/settings/menu/', action_index + 1)

        if next_action_index != -1:
            assert return_url_index < next_action_index, (
                f"Form {action} nao envia return_url dentro do proprio bloco."
            )


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
