//###################################################################################
// APPVERBOBRAGA - ABA LISTA + TIPO DE CAMPO LISTA
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) FUNÇÕES AUXILIARES
  //###################################################################################

  function normalizeKey(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function getBootstrap() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function getUrlParam(name) {
    try {
      return new URL(window.location.href).searchParams.get(name) || "";
    } catch (error) {
      return "";
    }
  }

  function getSettingsEditKey() {
    return normalizeKey(getUrlParam("settings_edit_key") || getBootstrap().settingsEditKey);
  }

  function getCurrentSettingsTab() {
    return normalizeKey(getUrlParam("settings_tab") || getBootstrap().settingsTab).replace(/_/g, "-");
  }

  function getCurrentSetting() {
    const key = getSettingsEditKey();
    const settings = Array.isArray(getBootstrap().sidebarMenuSettings)
      ? getBootstrap().sidebarMenuSettings
      : [];

    return settings.find(function (setting) {
      return normalizeKey(setting.key) === key;
    }) || null;
  }

  function getProcessLists() {
    const setting = getCurrentSetting();

    return setting && Array.isArray(setting.process_lists)
      ? setting.process_lists
      : [];
  }

  function getListByKey(listKey) {
    const cleanListKey = normalizeKey(listKey);

    return getProcessLists().find(function (item) {
      return normalizeKey(item.key) === cleanListKey;
    }) || null;
  }

  function getProcessFieldOptions() {
    const setting = getCurrentSetting();

    return setting && Array.isArray(setting.process_field_options)
      ? setting.process_field_options
      : [];
  }

  //###################################################################################
  // (2) GARANTIR ABA LISTA
  //###################################################################################

  function buildListaHref() {
    const url = new URL(window.location.href);
    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("settings_action", "edit");
    url.searchParams.set("settings_tab", "lista");

    const key = getSettingsEditKey();

    if (key) {
      url.searchParams.set("settings_edit_key", key);
    }

    url.hash = "settings-menu-edit-card";

    return `${url.pathname}${url.search}${url.hash}`;
  }

  function ensureListaTab() {
    const key = getSettingsEditKey();

    if (!key) {
      return;
    }

    if (document.querySelector("[data-settings-tab='lista'], a[href*='settings_tab=lista']")) {
      return;
    }

    const candidates = Array.from(
      document.querySelectorAll("a[href*='settings_tab='], button[data-settings-tab]")
    );

    if (!candidates.length) {
      return;
    }

    const reference = candidates.find(function (element) {
      return String(element.getAttribute("href") || "").includes("settings_tab=campos-adicionais")
        || String(element.getAttribute("data-settings-tab") || "") === "campos-adicionais";
    }) || candidates[candidates.length - 1];

    const listaTab = reference.cloneNode(true);
    listaTab.textContent = "Lista";
    listaTab.setAttribute("data-settings-tab", "lista");

    if (listaTab.tagName && listaTab.tagName.toLowerCase() === "a") {
      listaTab.setAttribute("href", buildListaHref());
    }

    reference.insertAdjacentElement("afterend", listaTab);
  }

  //###################################################################################
  // (3) RENDERIZAR ABA LISTA
  //###################################################################################

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function buildListRow(item) {
    const row = document.createElement("div");
    row.className = "process-list-row-v1";

    const itemsCsv = item.items_csv || (Array.isArray(item.items) ? item.items.join(", ") : "");

    row.innerHTML = [
      `<input type="hidden" name="process_list_key" value="${escapeHtml(item.key || "")}">`,
      `<div class="field">`,
      `  <label>Nome da lista</label>`,
      `  <input name="process_list_label" value="${escapeHtml(item.label || "")}" placeholder="Ex.: Estado">`,
      `</div>`,
      `<div class="field full">`,
      `  <label>Itens da lista separados por vírgula</label>`,
      `  <input name="process_list_items_csv" value="${escapeHtml(itemsCsv)}" placeholder="Ativo, Inativo, Pendente, Em acompanhamento">`,
      `</div>`,
      `<div class="field process-list-actions-v1">`,
      `  <button type="button" class="action-btn-cancel" data-remove-process-list>Remover</button>`,
      `</div>`
    ].join("");

    row.querySelector("[data-remove-process-list]").addEventListener("click", function () {
      row.remove();
    });

    return row;
  }

  function renderListaTab() {
    if (getCurrentSettingsTab() !== "lista") {
      return;
    }

    const key = getSettingsEditKey();
    const card = document.getElementById("settings-menu-edit-card");

    if (!key || !card) {
      return;
    }

    if (card.querySelector("[data-process-list-pane-v1]")) {
      return;
    }

    Array.from(card.querySelectorAll("form")).forEach(function (form) {
      if (!String(form.getAttribute("action") || "").includes("/settings/menu/process-lists")) {
        form.style.display = "none";
      }
    });

    const pane = document.createElement("section");
    pane.className = "admin-subsection";
    pane.setAttribute("data-process-list-pane-v1", "1");

    const lists = getProcessLists();
    const rows = lists.length ? lists : [{ key: "", label: "", items_csv: "" }];

    pane.innerHTML = [
      `<h3>Lista</h3>`,
      `<p class="muted">Crie listas reutilizáveis. Separe os itens por vírgula. Ex.: Ativo, Inativo, Pendente, Em acompanhamento.</p>`,
      `<form method="post" action="/settings/menu/process-lists" id="process-lists-form-v1">`,
      `  <input type="hidden" name="menu_key" value="${escapeHtml(key)}">`,
      `  <input type="hidden" name="redirect_menu" value="administrativo">`,
      `  <input type="hidden" name="redirect_target" value="#settings-menu-edit-card">`,
      `  <div id="process-lists-rows-v1" class="process-lists-rows-v1"></div>`,
      `  <div class="form-action-row">`,
      `    <button type="button" class="action-btn-secondary" id="add-process-list-v1">Adicionar lista</button>`,
      `    <button type="submit" class="action-btn">Guardar listas</button>`,
      `  </div>`,
      `</form>`
    ].join("");

    const rowsContainer = pane.querySelector("#process-lists-rows-v1");

    rows.forEach(function (item) {
      rowsContainer.appendChild(buildListRow(item));
    });

    pane.querySelector("#add-process-list-v1").addEventListener("click", function () {
      rowsContainer.appendChild(buildListRow({ key: "", label: "", items_csv: "" }));
    });

    const header = card.querySelector("h2, .profile-card-header, .admin-subsection");

    if (header && header.parentNode === card) {
      header.insertAdjacentElement("afterend", pane);
    } else {
      card.prepend(pane);
    }
  }

  //###################################################################################
  // (4) ACRESCENTAR TIPO LISTA NA CONFIGURAÇÃO DOS CAMPOS
  //###################################################################################

  function buildListSelect(selectedValue) {
    const select = document.createElement("select");
    select.name = "additional_field_list_key";

    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = getProcessLists().length ? "Selecione a lista" : "Crie uma lista na aba Lista";
    select.appendChild(emptyOption);

    getProcessLists().forEach(function (item) {
      const option = document.createElement("option");
      option.value = normalizeKey(item.key);
      option.textContent = item.label || item.key;

      if (normalizeKey(selectedValue) === normalizeKey(item.key)) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function enhanceAdditionalFieldsForm() {
    const forms = Array.from(
      document.querySelectorAll("form[action*='/settings/menu/process-additional-fields']")
    );

    if (!forms.length) {
      return;
    }

    const processFields = getProcessFieldOptions();

    forms.forEach(function (form) {
      const typeSelects = Array.from(form.querySelectorAll("select[name='additional_field_type']"));

      typeSelects.forEach(function (typeSelect, index) {
        if (!typeSelect.querySelector("option[value='list']")) {
          const option = document.createElement("option");
          option.value = "list";
          option.textContent = "Lista";
          typeSelect.appendChild(option);
        }

        const row = typeSelect.closest(".additional-field-row-equalized")
          || (typeSelect.closest(".field") ? typeSelect.closest(".field").parentElement : null)
          || typeSelect.parentElement;

        if (!row || row.querySelector("[data-list-picker-v1]")) {
          return;
        }

        const currentMeta = processFields[index] || {};
        const picker = document.createElement("div");
        picker.className = "field additional-field-list-col-v1";
        picker.setAttribute("data-list-picker-v1", "1");

        const label = document.createElement("label");
        label.textContent = "Lista";
        picker.appendChild(label);
        picker.appendChild(buildListSelect(currentMeta.list_key || currentMeta.listKey || ""));

        row.appendChild(picker);

        function refreshPicker() {
          picker.style.display = typeSelect.value === "list" ? "" : "none";
        }

        typeSelect.addEventListener("change", refreshPicker);
        refreshPicker();
      });
    });
  }

  //###################################################################################
  // (5) TRANSFORMAR CAMPO LISTA EM SELECT NO PROCESSO
  //###################################################################################

  function enhanceDynamicProcessListFields() {
    const setting = getCurrentSetting();

    if (!setting) {
      return;
    }

    const menuKey = normalizeKey(setting.key || getUrlParam("menu"));

    if (!menuKey) {
      return;
    }

    const listFields = getProcessFieldOptions().filter(function (field) {
      return normalizeKey(field.field_type || field.fieldType) === "list";
    });

    listFields.forEach(function (field) {
      const fieldKey = normalizeKey(field.key);
      const listKey = normalizeKey(field.list_key || field.listKey);
      const processList = getListByKey(listKey);

      if (!fieldKey || !processList) {
        return;
      }

      const inputName = `process__${menuKey}__${fieldKey}`;
      const currentInput = document.querySelector(`[name="${inputName}"]`);

      if (!currentInput || currentInput.tagName.toLowerCase() === "select") {
        return;
      }

      const select = document.createElement("select");
      select.name = currentInput.name;
      select.id = currentInput.id;
      select.className = currentInput.className;

      if (currentInput.required) {
        select.required = true;
      }

      const emptyOption = document.createElement("option");
      emptyOption.value = "";
      emptyOption.textContent = "Selecione";
      select.appendChild(emptyOption);

      const currentValue = String(currentInput.value || "");
      const items = Array.isArray(processList.items) ? processList.items : [];

      items.forEach(function (item) {
        const option = document.createElement("option");
        option.value = String(item || "");
        option.textContent = String(item || "");

        if (String(item || "") === currentValue) {
          option.selected = true;
        }

        select.appendChild(option);
      });

      currentInput.replaceWith(select);
    });
  }

  //###################################################################################
  // (6) INICIALIZAÇÃO
  //###################################################################################

  function run() {
    ensureListaTab();
    renderListaTab();
    enhanceAdditionalFieldsForm();
    enhanceDynamicProcessListFields();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }

  window.setTimeout(run, 100);
  window.setTimeout(run, 400);
  window.setTimeout(run, 1000);
  window.setTimeout(run, 1800);
})();
