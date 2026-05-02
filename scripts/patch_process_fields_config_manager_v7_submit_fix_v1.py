from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


####################################################################################
# (1) CONFIGURACAO
####################################################################################

PROJECT_ROOT = Path.cwd()

TEMPLATE_PATH = PROJECT_ROOT / "templates" / "new_user.html"
JS_V7_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v7.js"


####################################################################################
# (2) FUNCOES AUXILIARES
####################################################################################

def now_stamp_v1() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_v1(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text_v1(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def backup_file_v1(path: Path, suffix: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado para backup: {path}")

    backup_path = path.with_name(path.name + f".bak_{suffix}_{now_stamp_v1()}")
    shutil.copy2(path, backup_path)
    return backup_path


def require_file_v1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Ficheiro obrigatorio nao encontrado: {path}")


####################################################################################
# (3) PATCH DO JS V7
####################################################################################

def patch_js_v1() -> None:
    content = read_text_v1(JS_V7_PATH)

    helper_block = r'''
  //###################################################################################
  // (8A) EVITAR ENVIO DE INPUTS LEGADOS/DUPLICADOS
  //###################################################################################

  function desativarInputsLegadosV8(form, elements) {
    const hiddenContainer = elements && elements.hiddenContainer ? elements.hiddenContainer : null;
    const legacyContainer = elements && elements.legacyContainer ? elements.legacyContainer : null;

    function devePreservarControle_v8(control) {
      return Boolean(hiddenContainer && hiddenContainer.contains(control));
    }

    function desativarControle_v8(control) {
      if (!control || devePreservarControle_v8(control)) {
        return;
      }

      control.disabled = true;
      control.dataset.processFieldsConfigDisabledByV8 = "1";
    }

    Array.from(
      form.querySelectorAll(
        "input[name='visible_fields'], input[name='visible_headers'], input[name='visible_fields[]'], input[name='visible_headers[]']"
      )
    ).forEach(desativarControle_v8);

    if (legacyContainer) {
      Array.from(
        legacyContainer.querySelectorAll("input, select, textarea")
      ).forEach(desativarControle_v8);
    }
  }
'''

    if "desativarInputsLegadosV8" not in content:
        marker = "  function submitNativo_v7(form) {"
        if marker not in content:
            raise RuntimeError("Nao encontrei function submitNativo_v7 para inserir helper V8.")

        content = content.replace(marker, helper_block.rstrip() + "\n\n" + marker, 1)

    old_submit = """      manager.syncHiddenInputs();
      submitNativo_v7(form);"""

    new_submit = """      manager.syncHiddenInputs();
      desativarInputsLegadosV8(form, elements);
      submitNativo_v7(form);"""

    if new_submit not in content:
        if old_submit not in content:
            raise RuntimeError("Nao encontrei bloco de submit do V7 para aplicar desativacao dos inputs legados.")

        content = content.replace(old_submit, new_submit, 1)

    submit_listener_marker = "processFieldsConfigSubmitNativeBoundV8"

    if submit_listener_marker not in content:
        old_cancel_block = """    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      manager.clearEditing();
    });
  }"""

        new_cancel_block = """    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      manager.clearEditing();
    });

    if (form.dataset.processFieldsConfigSubmitNativeBoundV8 !== "1") {
      form.dataset.processFieldsConfigSubmitNativeBoundV8 = "1";

      form.addEventListener("submit", function () {
        manager.syncHiddenInputs();
        desativarInputsLegadosV8(form, elements);
      });
    }
  }"""

        if old_cancel_block not in content:
            raise RuntimeError("Nao encontrei bloco do botao Cancelar para inserir listener submit V8.")

        content = content.replace(old_cancel_block, new_cancel_block, 1)

    write_text_v1(JS_V7_PATH, content)


####################################################################################
# (4) PATCH DO CACHE BUST NO TEMPLATE
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "process_fields_config_manager_v7.js" not in content:
        raise RuntimeError("new_user.html nao esta a carregar process_fields_config_manager_v7.js.")

    content = re.sub(
        r"process_fields_config_manager_v7\.js\?v=[^\"]+",
        "process_fields_config_manager_v7.js?v=20260502-process-fields-v7-submit-fix-v1",
        content,
    )

    if "process_fields_config_manager_v6.js" in content:
        raise RuntimeError("new_user.html ainda contem process_fields_config_manager_v6.js.")

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (5) VALIDAR CONTEUDO
####################################################################################

def validate_v1() -> None:
    js_content = read_text_v1(JS_V7_PATH)
    template_content = read_text_v1(TEMPLATE_PATH)

    required_js_markers = [
        "desativarInputsLegadosV8",
        "processFieldsConfigDisabledByV8",
        "processFieldsConfigSubmitNativeBoundV8",
        "desativarInputsLegadosV8(form, elements);",
        "visible_fields",
        "visible_headers",
    ]

    missing_js_markers = [
        marker for marker in required_js_markers
        if marker not in js_content
    ]

    if missing_js_markers:
        raise RuntimeError(
            "Marcadores ausentes no JS V7: " + ", ".join(missing_js_markers)
        )

    if "process_fields_config_manager_v7.js?v=20260502-process-fields-v7-submit-fix-v1" not in template_content:
        raise RuntimeError("Cache bust do V7 nao foi atualizado no template.")

    if "process_fields_config_manager_v6.js" in template_content:
        raise RuntimeError("Template ainda carrega V6.")


####################################################################################
# (6) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(TEMPLATE_PATH)
    require_file_v1(JS_V7_PATH)

    template_backup = backup_file_v1(TEMPLATE_PATH, "process_fields_v7_submit_fix")
    js_backup = backup_file_v1(JS_V7_PATH, "process_fields_v7_submit_fix")

    print(f"OK: backup criado: {template_backup}")
    print(f"OK: backup criado: {js_backup}")

    patch_js_v1()
    patch_template_v1()
    validate_v1()

    print("OK: JS V7 ajustado para desativar inputs legados antes do submit.")
    print("OK: template atualizado com cache bust submit-fix-v1.")
    print("OK: validacao de conteudo concluida.")


if __name__ == "__main__":
    main()
