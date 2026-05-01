from __future__ import annotations

import re
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path(__file__).resolve().parents[1]

HTML_PATH = PROJECT_ROOT / "templates" / "new_user.html"
V6_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v6.js"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def read_text_v2(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v2(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


####################################################################################
# (3) PATCH JS V6 - GARANTIR BOTOES GUARDAR E CANCELAR
####################################################################################

def patch_v6_buttons_v2() -> None:
    content = read_text_v2(V6_PATH)

    marker = "APPVERBO_PROCESS_FIELDS_V6_ACTION_BUTTONS_V2_START"

    if marker not in content:
        helper_block = '''  // APPVERBO_PROCESS_FIELDS_V6_ACTION_BUTTONS_V2_START

  function criarBotaoFormulario_v6(kind, label) {
    const button = document.createElement("button");

    button.type = "button";
    button.textContent = label;

    if (kind === "submit") {
      button.dataset.processFieldsConfigSubmit = "1";
      button.className = "action-btn process-fields-config-submit-v6";
    }

    if (kind === "cancel") {
      button.dataset.processFieldsConfigCancel = "1";
      button.className = "action-btn-cancel process-fields-config-cancel-v6";
    }

    button.hidden = false;
    button.removeAttribute("hidden");
    button.style.display = "inline-flex";
    button.style.visibility = "visible";
    button.style.opacity = "1";
    button.style.alignItems = "center";
    button.style.justifyContent = "center";
    button.style.minWidth = "110px";
    button.style.height = "38px";
    button.style.borderRadius = "8px";
    button.style.fontWeight = "700";
    button.style.cursor = "pointer";

    return button;
  }

  function mostrarElementoFormulario_v6(element) {
    if (!element) {
      return;
    }

    element.hidden = false;
    element.removeAttribute("hidden");
    element.style.display = "";
    element.style.visibility = "visible";
    element.style.opacity = "1";
  }

  function localizarLinhaEditorFormulario_v6(form, elements) {
    const editorWrapper =
      elements.editorKey.closest(".field") ||
      elements.editorKey.closest(".form-field") ||
      elements.editorKey.parentElement;

    const headerWrapper =
      elements.headerKey.closest(".field") ||
      elements.headerKey.closest(".form-field") ||
      elements.headerKey.parentElement;

    if (editorWrapper && headerWrapper && editorWrapper.parentElement === headerWrapper.parentElement) {
      return editorWrapper.parentElement;
    }

    return (
      form.querySelector(".process-fields-config-editor-row-v6") ||
      form.querySelector(".process-fields-config-editor-row-v4") ||
      headerWrapper ||
      editorWrapper ||
      form
    );
  }

  function garantirBotoesFormulario_v6(form, elements) {
    if (!form || !elements || !elements.editorKey || !elements.headerKey) {
      return;
    }

    let actionRow = form.querySelector("[data-process-fields-config-action-row-v6='1']");

    if (!actionRow) {
      actionRow = document.createElement("div");
      actionRow.dataset.processFieldsConfigActionRowV6 = "1";
      actionRow.className = "form-action-row process-fields-config-action-row-v6";
    }

    actionRow.hidden = false;
    actionRow.removeAttribute("hidden");
    actionRow.style.display = "flex";
    actionRow.style.gap = "10px";
    actionRow.style.alignItems = "center";
    actionRow.style.justifyContent = "flex-start";
    actionRow.style.marginTop = "12px";
    actionRow.style.width = "100%";
    actionRow.style.visibility = "visible";
    actionRow.style.opacity = "1";

    if (!elements.submitButton) {
      elements.submitButton = criarBotaoFormulario_v6("submit", "Guardar");
    }

    if (!elements.cancelButton) {
      elements.cancelButton = criarBotaoFormulario_v6("cancel", "Cancelar");
    }

    mostrarElementoFormulario_v6(elements.submitButton);
    mostrarElementoFormulario_v6(elements.cancelButton);

    if (!actionRow.contains(elements.submitButton)) {
      actionRow.appendChild(elements.submitButton);
    }

    if (!actionRow.contains(elements.cancelButton)) {
      actionRow.appendChild(elements.cancelButton);
    }

    const editorRow = localizarLinhaEditorFormulario_v6(form, elements);

    if (editorRow && editorRow.parentElement && editorRow !== actionRow) {
      editorRow.insertAdjacentElement("afterend", actionRow);
      return;
    }

    form.insertBefore(actionRow, form.firstChild);
  }

  // APPVERBO_PROCESS_FIELDS_V6_ACTION_BUTTONS_V2_END


'''

        insert_before = "  function elementosValidos_v6(elements) {"

        if insert_before not in content:
            raise RuntimeError("Ponto elementosValidos_v6 não encontrado em process_fields_config_manager_v6.js.")

        content = content.replace(insert_before, helper_block + insert_before, 1)

    old_block = '''    const elements = obterElementos_v6(form);

    if (!elementosValidos_v6(elements)) {
      return;
    }
'''

    new_block = '''    const elements = obterElementos_v6(form);

    garantirBotoesFormulario_v6(form, elements);

    if (!elementosValidos_v6(elements)) {
      return;
    }
'''

    if "garantirBotoesFormulario_v6(form, elements);" not in content:
        if old_block not in content:
            raise RuntimeError("Ponto de chamada garantirBotoesFormulario_v6 não encontrado.")

        content = content.replace(old_block, new_block, 1)

    write_text_v2(V6_PATH, content)


####################################################################################
# (4) PATCH TEMPLATE - USAR SOMENTE V6 COM CACHE NOVO
####################################################################################

def patch_template_v2() -> None:
    content = read_text_v2(HTML_PATH)

    obsolete_patterns = [
        r'(?m)^[ \t]*<script src="/static/js/modules/process_fields_config_manager_v4\.js\?v=[^"]*"></script>[ \t]*\r?\n?',
        r'(?m)^[ \t]*<script src="/static/js/modules/process_fields_action_buttons_fallback_v1\.js\?v=[^"]*"></script>[ \t]*\r?\n?',
        r'(?m)^[ \t]*<script src="/static/js/modules/process_fields_config_manager_v6\.js\?v=[^"]*"></script>[ \t]*\r?\n?',
    ]

    for pattern in obsolete_patterns:
        content = re.sub(pattern, "", content)

    script_tag = '  <script src="/static/js/modules/process_fields_config_manager_v6.js?v=20260501-process-fields-config-v6-buttons-v2"></script>'

    block_pattern = re.compile(
        r"(?s)({%\s*block\s+scripts\s*%})(.*?)(\r?\n[ \t]*{%\s*endblock\s*%})"
    )

    if not block_pattern.search(content):
        raise RuntimeError("Bloco scripts não encontrado em new_user.html.")

    content = block_pattern.sub(
        lambda item: item.group(1) + item.group(2).rstrip() + "\\n" + script_tag + item.group(3),
        content,
        count=1,
    )

    write_text_v2(HTML_PATH, content)


####################################################################################
# (5) EXECUCAO
####################################################################################

def main() -> None:
    patch_v6_buttons_v2()
    patch_template_v2()
    print("OK: process_fields_config_manager_v6.js agora garante Guardar e Cancelar.")
    print("OK: template limpo para carregar somente o v6 com cache novo.")


if __name__ == "__main__":
    main()