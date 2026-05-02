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
CORE_JS_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "configurable_items_manager_core_v1.js"
OLD_V6_JS_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v6.js"
NEW_V7_JS_PATH = PROJECT_ROOT / "static" / "js" / "modules" / "process_fields_config_manager_v7.js"


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
# (3) CONTEUDO DO NOVO GESTOR V7
####################################################################################

V7_JS_CONTENT = r"""//###################################################################################
// APPVERBOBRAGA - PROCESS FIELDS CONFIG MANAGER V7
// Usa o core generico AppVerboConfigurableItems, igual ao processo Campos adicionais.
//###################################################################################

(function (window, document) {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES
  //###################################################################################

  const FORM_SELECTOR = "form[data-process-fields-config-manager-v1='1']";
  const CORE_NAMESPACE = "AppVerboConfigurableItems";

  //###################################################################################
  // (2) HELPERS GERAIS
  //###################################################################################

  function textoSeguro_v7(value) {
    return String(value === null || value === undefined ? "" : value);
  }

  function normalizarTexto_v7(value) {
    return textoSeguro_v7(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizarChave_v7(value) {
    return normalizarTexto_v7(value);
  }

  function limparLabelCabecalho_v7(value) {
    return textoSeguro_v7(value)
      .replace(/\s*-\s*Cabeçalho\s*$/i, "")
      .replace(/\s*-\s*Cabecalho\s*$/i, "")
      .trim();
  }

  function optionEhCabecalho_v7(option) {
    if (!option || !textoSeguro_v7(option.value).trim()) {
      return false;
    }

    const kind = normalizarTexto_v7(
      option.dataset.processConfigKind ||
      option.dataset.fieldType ||
      option.dataset.type ||
      option.getAttribute("data-process-config-kind") ||
      option.getAttribute("data-field-type") ||
      option.getAttribute("data-type") ||
      ""
    );

    const texto = normalizarTexto_v7(option.textContent);
    const value = normalizarTexto_v7(option.value);

    return kind === "header" || texto.includes("cabecalho") || value.includes("cabecalho");
  }

  function criarOption_v7(value, label, selectedValue, kind) {
    const option = document.createElement("option");

    option.value = value || "";
    option.textContent = label || "";

    if (kind) {
      option.dataset.processConfigKind = kind;
    }

    if (label) {
      option.dataset.processConfigLabel = label;
    }

    if (textoSeguro_v7(value) === textoSeguro_v7(selectedValue)) {
      option.selected = true;
    }

    return option;
  }

  //###################################################################################
  // (3) ELEMENTOS
  //###################################################################################

  function obterElementos_v7(form) {
    return {
      legacyContainer: form.querySelector("[data-process-fields-config-legacy-container]"),
      hiddenContainer: form.querySelector("[data-process-fields-config-hidden-container]"),
      editorBlock: (
        form.querySelector("[data-process-fields-config-editor-block]") ||
        form.querySelector(".process-fields-config-editor-v1") ||
        form
      ),
      editorKey: form.querySelector("[data-process-fields-config-editor-key]"),
      headerKey: form.querySelector("[data-process-fields-config-header-editor-key]"),
      submitButton: form.querySelector("[data-process-fields-config-submit]"),
      cancelButton: form.querySelector("[data-process-fields-config-cancel]"),
      table: form.querySelector("[data-process-fields-config-table]"),
      tableBody: form.querySelector("[data-process-fields-config-table-body]"),
      emptyState: form.querySelector("[data-process-fields-config-empty]"),
      totalLabel: form.querySelector("[data-process-fields-config-total-label]"),
      pageSize: form.querySelector("[data-process-fields-config-page-size]"),
      pagination: form.querySelector("[data-process-fields-config-pagination]")
    };
  }

  function elementosMinimosValidos_v7(elements) {
    return Boolean(
      elements.hiddenContainer &&
      elements.editorKey &&
      elements.headerKey &&
      elements.submitButton &&
      elements.cancelButton &&
      elements.table &&
      elements.tableBody &&
      elements.emptyState &&
      elements.totalLabel &&
      elements.pageSize &&
      elements.pagination
    );
  }

  //###################################################################################
  // (4) OPÇÕES DISPONIVEIS
  //###################################################################################

  function lerOpcoesOriginais_v7(elements) {
    const seen = new Set();

    return Array.from(elements.editorKey.options)
      .map(function (option) {
        const key = textoSeguro_v7(option.value).trim().toLowerCase();

        if (!key || seen.has(key)) {
          return null;
        }

        seen.add(key);

        return {
          key,
          label: limparLabelCabecalho_v7(
            textoSeguro_v7(option.dataset.processConfigLabel || option.textContent)
          ),
          kind: optionEhCabecalho_v7(option) ? "header" : "field"
        };
      })
      .filter(Boolean);
  }

  function lerHeaderOptions_v7(elements, originalOptions) {
    const fromHeaderSelect = Array.from(elements.headerKey.options)
      .map(function (option) {
        const key = textoSeguro_v7(option.value).trim().toLowerCase();

        if (!key) {
          return null;
        }

        return {
          key,
          label: limparLabelCabecalho_v7(
            textoSeguro_v7(option.dataset.processConfigLabel || option.textContent)
          ),
          kind: "header"
        };
      })
      .filter(Boolean);

    if (fromHeaderSelect.length) {
      return fromHeaderSelect;
    }

    return originalOptions.filter(function (item) {
      return item.kind === "header";
    });
  }

  function localizarPorChave_v7(options, key) {
    const cleanKey = normalizarChave_v7(key);

    return options.find(function (item) {
      return normalizarChave_v7(item.key) === cleanKey;
    }) || null;
  }

  function labelCampo_v7(state, key) {
    const item = localizarPorChave_v7(state.fieldOptions, key);
    return item ? item.label : key;
  }

  function labelCabecalho_v7(state, key) {
    const item = localizarPorChave_v7(state.headerOptions, key);
    return item ? item.label : "";
  }

  //###################################################################################
  // (5) RECONSTRUIR SELECTS
  //###################################################################################

  function obterEditingItem_v7(state) {
    if (!state || !state.editingId) {
      return null;
    }

    return state.items.find(function (item) {
      return textoSeguro_v7(item.__managerId || item.managerId || item.id) === textoSeguro_v7(state.editingId);
    }) || null;
  }

  function reconstruirSelectCampo_v7(elements, state, selectedKey) {
    const editingItem = obterEditingItem_v7(state);
    const currentValue = normalizarChave_v7(
      selectedKey ||
      elements.editorKey.dataset.processFieldsConfigEditingKeyV7 ||
      elements.editorKey.value ||
      (editingItem ? editingItem.key : "")
    );

    const configuredKeys = new Set(
      state.items.map(function (item) {
        return normalizarChave_v7(item.key);
      })
    );

    elements.editorKey.innerHTML = "";
    elements.editorKey.appendChild(criarOption_v7("", "Selecione", "", ""));

    state.fieldOptions.forEach(function (item) {
      const itemKey = normalizarChave_v7(item.key);

      if (configuredKeys.has(itemKey) && itemKey !== currentValue) {
        return;
      }

      elements.editorKey.appendChild(
        criarOption_v7(item.key, item.label, currentValue, "field")
      );
    });

    elements.editorKey.value = currentValue;
  }

  function reconstruirSelectCabecalho_v7(elements, state, selectedKey) {
    const currentValue = normalizarChave_v7(selectedKey || elements.headerKey.value);

    elements.headerKey.innerHTML = "";
    elements.headerKey.appendChild(criarOption_v7("", "Sem cabeçalho", currentValue, ""));

    state.headerOptions.forEach(function (item) {
      elements.headerKey.appendChild(
        criarOption_v7(item.key, item.label, currentValue, "header")
      );
    });

    elements.headerKey.value = currentValue;
  }

  //###################################################################################
  // (6) LER CONFIGURACOES EXISTENTES
  //###################################################################################

  function valorLinhaLegacy_v7(row, selector) {
    const input = row.querySelector(selector);
    return input ? textoSeguro_v7(input.value).trim().toLowerCase() : "";
  }

  function lerItensLegacy_v7(elements, state) {
    if (!elements.legacyContainer) {
      return [];
    }

    const rows = Array.from(
      elements.legacyContainer.querySelectorAll("[data-process-config-field-row]")
    );

    const items = [];
    let currentHeaderKey = "";

    rows.forEach(function (row, index) {
      const key = valorLinhaLegacy_v7(row, "[data-process-config-key]");
      const kind = valorLinhaLegacy_v7(row, "[data-process-config-kind]");

      if (!key) {
        return;
      }

      if (kind === "header") {
        currentHeaderKey = key;
        return;
      }

      items.push({
        id: "legacy_" + index + "_" + key,
        key,
        label: labelCampo_v7(state, key),
        headerKey: currentHeaderKey,
        headerLabel: labelCabecalho_v7(state, currentHeaderKey)
      });
    });

    return items;
  }

  function lerItensHidden_v7(elements, state) {
    const fieldInputs = Array.from(
      elements.hiddenContainer.querySelectorAll("input[name='visible_fields']")
    );

    const headerInputs = Array.from(
      elements.hiddenContainer.querySelectorAll("input[name='visible_headers']")
    );

    return fieldInputs
      .map(function (input, index) {
        const key = textoSeguro_v7(input.value).trim().toLowerCase();

        if (!key) {
          return null;
        }

        const headerKey = textoSeguro_v7(headerInputs[index] ? headerInputs[index].value : "")
          .trim()
          .toLowerCase();

        return {
          id: "hidden_" + index + "_" + key,
          key,
          label: labelCampo_v7(state, key),
          headerKey,
          headerLabel: labelCabecalho_v7(state, headerKey)
        };
      })
      .filter(Boolean);
  }

  function juntarItensSemDuplicados_v7(first, second) {
    const merged = [];
    const seen = new Set();

    first.concat(second).forEach(function (item) {
      const key = normalizarChave_v7(item.key);

      if (!key || seen.has(key)) {
        return;
      }

      seen.add(key);
      merged.push(item);
    });

    return merged;
  }

  //###################################################################################
  // (7) EDITOR
  //###################################################################################

  function limparEditor_v7(context) {
    const root = context.root;
    const elements = root.__processFieldsConfigElementsV7;

    if (!elements) {
      return;
    }

    delete elements.editorKey.dataset.processFieldsConfigEditingKeyV7;
    elements.editorKey.value = "";
    elements.headerKey.value = "";

    reconstruirSelectCampo_v7(elements, context.state || context.manager.state, "");
    reconstruirSelectCabecalho_v7(elements, context.state || context.manager.state, "");
  }

  function carregarEditor_v7(item, context) {
    const root = context.root;
    const elements = root.__processFieldsConfigElementsV7;
    const state = context.state || context.manager.state;

    if (!elements) {
      return;
    }

    elements.editorKey.dataset.processFieldsConfigEditingKeyV7 = item.key || "";
    reconstruirSelectCampo_v7(elements, state, item.key || "");
    reconstruirSelectCabecalho_v7(elements, state, item.headerKey || "");

    elements.editorKey.value = item.key || "";
    elements.headerKey.value = item.headerKey || "";

    if (typeof elements.editorKey.focus === "function") {
      elements.editorKey.focus();
    }
  }

  function lerEditorItem_v7(context) {
    const root = context.root;
    const elements = root.__processFieldsConfigElementsV7;
    const state = context.state || context.manager.state;

    if (!elements) {
      return null;
    }

    const selectedOption = elements.editorKey.options[elements.editorKey.selectedIndex];

    if (!selectedOption || !selectedOption.value) {
      return null;
    }

    const key = textoSeguro_v7(selectedOption.value).trim().toLowerCase();
    const headerKey = textoSeguro_v7(elements.headerKey.value).trim().toLowerCase();

    return {
      id: state.editingId || "field_" + Date.now() + "_" + key,
      key,
      label: textoSeguro_v7(selectedOption.dataset.processConfigLabel || selectedOption.textContent),
      headerKey,
      headerLabel: labelCabecalho_v7(state, headerKey)
    };
  }

  function validarEditorItem_v7(item, context) {
    if (!item || !item.key) {
      return { valid: false, message: "Selecione um campo." };
    }

    const editingId = textoSeguro_v7(context.state.editingId);

    const duplicated = context.items.some(function (existingItem) {
      const sameKey = normalizarChave_v7(existingItem.key) === normalizarChave_v7(item.key);
      const sameId = textoSeguro_v7(existingItem.__managerId) === editingId;

      return sameKey && !sameId;
    });

    if (duplicated) {
      return { valid: false, message: "Este campo já está configurado." };
    }

    return { valid: true };
  }

  function existeDraft_v7(elements, manager) {
    return Boolean(manager.state.editingId || elements.editorKey.value);
  }

  //###################################################################################
  // (8) SINCRONIZAR INPUTS PARA BACKEND
  //###################################################################################

  function sincronizarHiddenInputs_v7(context) {
    const root = context.root;
    const elements = root.__processFieldsConfigElementsV7;

    if (!elements || !elements.hiddenContainer) {
      return;
    }

    elements.hiddenContainer.innerHTML = "";

    context.items.forEach(function (item) {
      const fieldInput = document.createElement("input");
      fieldInput.type = "hidden";
      fieldInput.name = "visible_fields";
      fieldInput.value = item.key || "";
      elements.hiddenContainer.appendChild(fieldInput);

      const headerInput = document.createElement("input");
      headerInput.type = "hidden";
      headerInput.name = "visible_headers";
      headerInput.value = item.headerKey || "";
      elements.hiddenContainer.appendChild(headerInput);
    });
  }

  //###################################################################################
  // (9) SUBMIT DA CONFIGURACAO
  //###################################################################################

  function submitNativo_v7(form) {
    HTMLFormElement.prototype.submit.call(form);
  }

  function vincularBotoesFormulario_v7(form, elements, manager) {
    if (form.dataset.processFieldsConfigSubmitBoundV7 === "1") {
      return;
    }

    form.dataset.processFieldsConfigSubmitBoundV7 = "1";

    elements.submitButton.addEventListener("click", function (event) {
      event.preventDefault();

      if (existeDraft_v7(elements, manager)) {
        const item = lerEditorItem_v7({
          manager,
          root: form,
          elements: manager.elements,
          state: manager.state
        });

        const validationResult = validarEditorItem_v7(item, {
          manager,
          root: form,
          elements: manager.elements,
          state: manager.state,
          items: manager.getItems()
        });

        if (validationResult && validationResult.valid === false) {
          if (validationResult.message) {
            window.alert(validationResult.message);
          }

          return;
        }

        manager.addOrUpdate(item);
      }

      manager.syncHiddenInputs();
      submitNativo_v7(form);
    });

    elements.cancelButton.addEventListener("click", function (event) {
      event.preventDefault();
      manager.clearEditing();
    });
  }

  //###################################################################################
  // (10) INICIALIZAR UM FORMULARIO
  //###################################################################################

  function iniciarGestorV7(form) {
    if (!form || form.dataset.processFieldsConfigManagerBoundV7 === "1") {
      return null;
    }

    const core = window[CORE_NAMESPACE];

    if (!core || typeof core.createConfigurableItemsManager_v1 !== "function") {
      return null;
    }

    const elements = obterElementos_v7(form);

    if (!elementosMinimosValidos_v7(elements)) {
      return null;
    }

    form.dataset.processFieldsConfigManagerBoundV7 = "1";
    form.__processFieldsConfigElementsV7 = elements;

    const originalOptions = lerOpcoesOriginais_v7(elements);

    const provisionalState = {
      fieldOptions: originalOptions.filter(function (item) { return item.kind !== "header"; }),
      headerOptions: lerHeaderOptions_v7(elements, originalOptions),
      items: [],
      page: 1,
      pageSize: Number.parseInt(elements.pageSize.value, 10) || 5,
      editingId: ""
    };

    const initialItems = juntarItensSemDuplicados_v7(
      lerItensHidden_v7(elements, provisionalState),
      lerItensLegacy_v7(elements, provisionalState)
    );

    const manager = core.createConfigurableItemsManager_v1({
      root: form,
      itemName: "campo",
      itemNamePlural: "campos",
      pageSizeDefault: Number.parseInt(elements.pageSize.value, 10) || 5,
      pageSizeOptions: [5, 10, 25],
      initialItems,
      selectors: {
        editorForm: "[data-process-fields-config-editor-block]",
        table: "[data-process-fields-config-table]",
        tableBody: "[data-process-fields-config-table-body]",
        emptyState: "[data-process-fields-config-empty]",
        pagination: "[data-process-fields-config-pagination]",
        pageSize: "[data-process-fields-config-page-size]",
        hiddenContainer: "[data-process-fields-config-hidden-container]",
        totalLabel: "[data-process-fields-config-total-label]"
      },
      columns: [
        {
          key: "label",
          label: "Nome do campo"
        },
        {
          key: "headerLabel",
          label: "Cabeçalho do campo",
          render: function (item) {
            return item.headerLabel || "Sem cabeçalho";
          }
        }
      ],
      getItemId: function (item, index) {
        return item.id || item.key || "field_" + (index + 1);
      },
      readEditorItem: lerEditorItem_v7,
      loadEditorItem: carregarEditor_v7,
      clearEditor: limparEditor_v7,
      validateItem: validarEditorItem_v7,
      syncHiddenInputs: sincronizarHiddenInputs_v7,
      onRender: function (context) {
        const state = context.state;
        state.fieldOptions = provisionalState.fieldOptions;
        state.headerOptions = provisionalState.headerOptions;

        reconstruirSelectCampo_v7(elements, state);
        reconstruirSelectCabecalho_v7(elements, state);
      }
    });

    if (!manager) {
      return null;
    }

    manager.state.fieldOptions = provisionalState.fieldOptions;
    manager.state.headerOptions = provisionalState.headerOptions;

    reconstruirSelectCampo_v7(elements, manager.state);
    reconstruirSelectCabecalho_v7(elements, manager.state);
    vincularBotoesFormulario_v7(form, elements, manager);
    manager.syncHiddenInputs();

    return manager;
  }

  function iniciarTodosV7() {
    Array.from(document.querySelectorAll(FORM_SELECTOR)).forEach(iniciarGestorV7);
  }

  //###################################################################################
  // (11) INICIALIZACAO
  //###################################################################################

  window.setupProcessFieldsConfigManagerV7 = iniciarTodosV7;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarTodosV7);
  } else {
    iniciarTodosV7();
  }
})(window, document);
"""


####################################################################################
# (4) PATCH DO TEMPLATE
####################################################################################

def patch_template_v1() -> None:
    content = read_text_v1(TEMPLATE_PATH)

    if "data-process-fields-config-manager-v1" not in content:
        raise RuntimeError(
            "Nao encontrei data-process-fields-config-manager-v1 no template. "
            "A estrutura da aba Configuracao dos campos pode ter mudado."
        )

    if "data-process-fields-config-hidden-container" not in content:
        raise RuntimeError("Nao encontrei data-process-fields-config-hidden-container no template.")

    if "data-process-fields-config-editor-key" not in content:
        raise RuntimeError("Nao encontrei data-process-fields-config-editor-key no template.")

    if "data-process-fields-config-header-editor-key" not in content:
        raise RuntimeError("Nao encontrei data-process-fields-config-header-editor-key no template.")

    content = re.sub(
        r'(?m)^[ \t]*<script src="/static/js/modules/process_fields_config_manager_v[1-7]\.js\?v=[^"]*"></script>[ \t]*\r?\n?',
        "",
        content,
    )

    core_script = '  <script src="/static/js/modules/configurable_items_manager_core_v1.js?v=20260502-process-fields-v7-core"></script>'
    v7_script = '  <script src="/static/js/modules/process_fields_config_manager_v7.js?v=20260502-process-fields-v7-core"></script>'

    scripts_block_pattern = re.compile(
        r"(?s)({%\s*block\s+scripts\s*%})(.*?)(\r?\n[ \t]*{%\s*endblock\s*%})"
    )

    match = scripts_block_pattern.search(content)

    if not match:
        content = content.rstrip() + "\n\n{% block scripts %}\n" + core_script + "\n" + v7_script + "\n{% endblock %}\n"
    else:
        body = match.group(2).rstrip()

        lines_to_add: list[str] = []

        if "configurable_items_manager_core_v1.js" not in body:
            lines_to_add.append(core_script)

        lines_to_add.append(v7_script)

        new_body = body + "\n" + "\n".join(lines_to_add)

        content = (
            content[:match.start()]
            + match.group(1)
            + new_body
            + match.group(3)
            + content[match.end():]
        )

    write_text_v1(TEMPLATE_PATH, content)


####################################################################################
# (5) CRIAR JS V7
####################################################################################

def write_v7_js_v1() -> None:
    write_text_v1(NEW_V7_JS_PATH, V7_JS_CONTENT)


####################################################################################
# (6) VALIDACOES DE CONTEUDO
####################################################################################

def validate_files_v1() -> None:
    template = read_text_v1(TEMPLATE_PATH)
    js = read_text_v1(NEW_V7_JS_PATH)

    required_template_markers = [
        "process_fields_config_manager_v7.js",
        "configurable_items_manager_core_v1.js",
        "data-process-fields-config-manager-v1",
        "data-process-fields-config-hidden-container",
        "data-process-fields-config-editor-key",
        "data-process-fields-config-header-editor-key",
    ]

    missing_template = [
        marker for marker in required_template_markers
        if marker not in template
    ]

    if missing_template:
        raise RuntimeError(
            "Marcadores ausentes no template: " + ", ".join(missing_template)
        )

    if "process_fields_config_manager_v6.js" in template:
        raise RuntimeError(
            "O template ainda carrega process_fields_config_manager_v6.js."
        )

    required_js_markers = [
        "APPVERBOBRAGA - PROCESS FIELDS CONFIG MANAGER V7",
        "createConfigurableItemsManager_v1",
        "visible_fields",
        "visible_headers",
        "syncHiddenInputs",
        "setupProcessFieldsConfigManagerV7",
    ]

    missing_js = [
        marker for marker in required_js_markers
        if marker not in js
    ]

    if missing_js:
        raise RuntimeError(
            "Marcadores ausentes no JS V7: " + ", ".join(missing_js)
        )


####################################################################################
# (7) EXECUCAO
####################################################################################

def main() -> None:
    require_file_v1(TEMPLATE_PATH)
    require_file_v1(CORE_JS_PATH)

    template_backup = backup_file_v1(TEMPLATE_PATH, "process_fields_v7")
    print(f"OK: backup criado: {template_backup}")

    if OLD_V6_JS_PATH.exists():
        old_v6_backup = backup_file_v1(OLD_V6_JS_PATH, "process_fields_v7_refactor")
        print(f"OK: backup criado: {old_v6_backup}")

    if NEW_V7_JS_PATH.exists():
        old_v7_backup = backup_file_v1(NEW_V7_JS_PATH, "process_fields_v7_previous")
        print(f"OK: backup criado: {old_v7_backup}")

    patch_template_v1()
    write_v7_js_v1()
    validate_files_v1()

    print("OK: process_fields_config_manager_v7.js criado.")
    print("OK: new_user.html atualizado para carregar o gestor V7.")
    print("OK: backend mantido com visible_fields e visible_headers.")


if __name__ == "__main__":
    main()
