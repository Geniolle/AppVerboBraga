from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


####################################################################################
# (1) O BOTAO "CRIAR/EDITAR" DO PROCESSO DINAMICO FICA NUM CARD DE ACAO SEPARADO,
# REUTILIZANDO O MESMO PADRAO VISUAL DO BLOCO "CRIAR PERFIL" (admin_subprocess).
####################################################################################

def test_dynamic_process_action_card_is_separate_from_content_card() -> None:
    html_path = PROJECT_ROOT / "templates" / "new_user.html"
    html_text = html_path.read_text(encoding="utf-8")

    action_card_index = html_text.index('id="dynamic-process-action-card"')
    content_card_index = html_text.index('id="dynamic-process-card"')
    toolbar_index = html_text.index('class="appgenesis-process-action-toolbar-v1"')
    toggle_button_index = html_text.index('id="dynamic-process-edit-toggle"')

    # O card de acao (com o botao) aparece ANTES do card de conteudo (Agenda geral / readonly).
    assert action_card_index < content_card_index

    # O botao esta dentro do toolbar de acao, e o toolbar esta dentro do card de acao —
    # nao dentro do card de conteudo (#dynamic-process-card).
    assert action_card_index < toolbar_index < toggle_button_index < content_card_index

    # O card de acao reutiliza as mesmas classes do bloco "Criar perfil" (admin_subprocess).
    action_card_snippet = html_text[action_card_index:toolbar_index]
    assert "appgenesis-process-action-card-v1" in action_card_snippet

    toggle_snippet = html_text[toolbar_index:toggle_button_index + 200]
    assert "appgenesis-process-action-toggle-v1" in toggle_snippet


def test_admin_subprocess_create_toggle_uses_same_css_classes() -> None:
    macro_path = PROJECT_ROOT / "templates" / "macros" / "admin_subprocess.html"
    macro_text = macro_path.read_text(encoding="utf-8")

    assert "appgenesis-process-action-toolbar-v1" in macro_text
    assert "appgenesis-process-action-toggle-v1" in macro_text
    assert "appgenesis-process-action-card-v1" in macro_text


####################################################################################
# (2) A VISIBILIDADE DO CARD DE ACAO SEPARADO E GERIDA EM JS (fora de #dynamic-process-card)
####################################################################################

def test_new_user_js_manages_action_card_visibility_and_toggle_display() -> None:
    script_path = PROJECT_ROOT / "static" / "js" / "new_user.js"
    script_text = script_path.read_text(encoding="utf-8")

    assert 'const dynamicProcessActionCardEl = document.getElementById("dynamic-process-action-card");' in script_text
    assert "function setDynamicProcessEditToggleVisible(isVisible)" in script_text
    # Sincroniza a visibilidade do card de acao junto com a do botao em applyContentForMenuTarget.
    assert 'dynamicProcessActionCardEl.style.display = targetSelector === "#dynamic-process-card" ? "" : "none";' in script_text
