// Editor inline dos subprocessos administrativos com row_click_edit (ex.: Funcoes administrativas).
// Em modo Editar, o formulario abre logo abaixo da linha clicada (padrao de Campos adicionais e
// Perfil de autorizacao), e nao no topo da lista. Segundo clique na mesma linha sem alteracoes fecha o editor.
(function initAppGenesisAdminSubprocessInlineEditorV1(global) {
  const HOLDER_CLASS = "admin-subprocess-inline-editor-row";
  const TABLE_SELECTOR = "table[data-admin-inline-edit-param]";
  const FORM_SELECTOR = "[data-admin-inline-edit-form='1']";
  const INTERACTIVE_SELECTOR = "a, button, input, select, textarea, label, summary, details, .table-actions";

  const state = {
    formOrigin: null,
    snapshot: "",
    rowEl: null,
    holderEl: null,
    editParam: ""
  };

  function getEditKeyFromUrlV1(editParam) {
    try {
      return String(new URLSearchParams(global.location.search).get(editParam) || "").trim();
    } catch (error) {
      return "";
    }
  }

  function findRowForEditKeyV1(tableEl, editParam, editKey) {
    return Array.from(tableEl.querySelectorAll("tbody > tr")).find((rowEl) => {
      return Array.from(rowEl.querySelectorAll("a[href]")).some((linkEl) => {
        try {
          const href = new URL(linkEl.getAttribute("href"), global.location.origin);
          return String(href.searchParams.get(editParam) || "") === editKey;
        } catch (error) {
          return false;
        }
      });
    }) || null;
  }

  function serializeFormV1(formEl) {
    return Array.from(formEl.querySelectorAll("input, select, textarea"))
      .map((el) => (el.name || el.id) + "=" + (el.type === "checkbox" || el.type === "radio" ? String(el.checked) : String(el.value)))
      .join("&");
  }

  function hasChangesV1() {
    const formEl = global.document.querySelector(FORM_SELECTOR);
    return Boolean(state.holderEl && formEl) && serializeFormV1(formEl) !== state.snapshot;
  }

  function cleanEditUrlV1() {
    try {
      const url = new URL(global.location.href);
      const tableEl = global.document.querySelector(TABLE_SELECTOR);
      url.searchParams.delete(state.editParam);
      url.searchParams.delete("target");
      if (tableEl && tableEl.getAttribute("data-admin-inline-tab")) {
        url.searchParams.set("admin_tab", tableEl.getAttribute("data-admin-inline-tab"));
      }
      const cardId = tableEl ? tableEl.getAttribute("data-admin-inline-card-id") : "";
      url.hash = cardId ? "#" + cardId : "";
      global.history.replaceState(global.history.state, global.document.title, url.pathname + url.search + url.hash);
    } catch (error) {
      // URL limpa e so cosmetica; ignorar falhas.
    }
  }

  function closeEditorV1() {
    const formEl = global.document.querySelector(FORM_SELECTOR);
    const origin = state.formOrigin;

    if (formEl && origin && origin.parent) {
      const anchor = origin.next && origin.next.parentNode === origin.parent ? origin.next : null;
      origin.parent.insertBefore(formEl, anchor);
      formEl.style.display = "none";
    }

    if (state.holderEl && state.holderEl.parentNode) {
      state.holderEl.parentNode.removeChild(state.holderEl);
    }

    state.holderEl = null;
    state.rowEl = null;
    state.snapshot = "";
    cleanEditUrlV1();
  }

  function placeInlineEditorV1() {
    const tableEl = global.document.querySelector(TABLE_SELECTOR);
    const formEl = global.document.querySelector(FORM_SELECTOR);

    if (!tableEl || !formEl) {
      return;
    }

    const editParam = tableEl.getAttribute("data-admin-inline-edit-param") || "";
    const editKey = getEditKeyFromUrlV1(editParam);

    if (!editParam || !editKey) {
      return;
    }

    const rowEl = findRowForEditKeyV1(tableEl, editParam, editKey);

    if (!rowEl) {
      return;
    }

    state.editParam = editParam;

    if (!state.formOrigin) {
      state.formOrigin = { parent: formEl.parentNode, next: formEl.nextSibling };
    }

    const holderEl = global.document.createElement("tr");
    holderEl.className = HOLDER_CLASS;
    const cellEl = global.document.createElement("td");
    cellEl.colSpan = Math.max(rowEl.cells.length, 1);
    holderEl.appendChild(cellEl);
    cellEl.appendChild(formEl);

    rowEl.insertAdjacentElement("afterend", holderEl);
    formEl.style.display = "";

    state.rowEl = rowEl;
    state.holderEl = holderEl;
    state.snapshot = serializeFormV1(formEl);

    if (typeof formEl.scrollIntoView === "function") {
      formEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  // Captura antes do handler de clique de linha: o segundo clique na linha aberta fecha o editor
  // (sem alteracoes) ou fica quieto (com alteracoes), sem navegar.
  global.document.addEventListener("click", (event) => {
    const clickedRow = event.target.closest && event.target.closest("tbody tr");

    if (!clickedRow || clickedRow.classList.contains(HOLDER_CLASS)) {
      return;
    }

    if (!state.rowEl || clickedRow !== state.rowEl) {
      return;
    }

    if (event.target.closest(INTERACTIVE_SELECTOR)) {
      return;
    }

    event.stopImmediatePropagation();
    event.preventDefault();

    if (!hasChangesV1()) {
      closeEditorV1();
    }
  }, true);

  if (global.document.readyState === "loading") {
    global.document.addEventListener("DOMContentLoaded", placeInlineEditorV1);
  } else {
    placeInlineEditorV1();
  }

  global.AppGenesisAdminSubprocessInlineEditorV1 = Object.freeze({
    placeInlineEditorV1,
    closeEditorV1
  });
})(window);
