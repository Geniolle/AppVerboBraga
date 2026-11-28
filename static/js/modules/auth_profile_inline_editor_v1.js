// Editor do Perfil de autorizacao em modo Editar: abre logo abaixo da linha do perfil clicado
// (mesmo comportamento do editor inline de Campos adicionais), e nao no topo da lista.
// Segundo clique na mesma linha sem alteracoes fecha o editor.
(function initAppGenesisAuthProfileInlineEditorV1(global) {
  const FORM_ID = "auth-profile-form-card";
  const TABLE_ID = "auth-profile-active-table";
  const HOLDER_CLASS = "auth-profile-inline-editor-row";
  const INTERACTIVE_SELECTOR = "a, button, input, select, textarea, label, .table-actions";

  const state = {
    formOrigin: null,
    snapshot: "",
    rowEl: null,
    holderEl: null
  };

  function getEditKeyFromUrlV1() {
    try {
      return String(new URLSearchParams(global.location.search).get("auth_profile_edit_key") || "").trim();
    } catch (error) {
      return "";
    }
  }

  function findRowForEditKeyV1(tableEl, editKey) {
    return Array.from(tableEl.querySelectorAll("tbody > tr")).find((rowEl) => {
      return Array.from(rowEl.querySelectorAll("a[href]")).some((linkEl) => {
        try {
          const href = new URL(linkEl.getAttribute("href"), global.location.origin);
          return String(href.searchParams.get("auth_profile_edit_key") || "") === editKey;
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
    const formEl = global.document.getElementById(FORM_ID);
    return Boolean(state.holderEl && formEl) && serializeFormV1(formEl) !== state.snapshot;
  }

  function cleanEditUrlV1() {
    try {
      const url = new URL(global.location.href);
      url.searchParams.delete("auth_profile_edit_key");
      url.searchParams.delete("target");
      url.hash = "#auth-profile-card";
      global.history.replaceState(global.history.state, global.document.title, url.pathname + url.search + url.hash);
    } catch (error) {
      // URL limpa e so cosmetica; ignorar falhas.
    }
  }

  function closeEditorV1() {
    const formEl = global.document.getElementById(FORM_ID);
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
    const formEl = global.document.getElementById(FORM_ID);
    const tableEl = global.document.getElementById(TABLE_ID);
    const editKey = getEditKeyFromUrlV1();

    if (!formEl || !tableEl || !editKey) {
      return;
    }

    const rowEl = findRowForEditKeyV1(tableEl, editKey);

    if (!rowEl) {
      return;
    }

    if (!state.formOrigin) {
      state.formOrigin = { parent: formEl.parentNode, next: formEl.nextSibling };
    }

    let holderEl = tableEl.querySelector("tbody > tr." + HOLDER_CLASS);

    if (!holderEl) {
      holderEl = global.document.createElement("tr");
      holderEl.className = HOLDER_CLASS;
      const cellEl = global.document.createElement("td");
      cellEl.colSpan = Math.max(rowEl.cells.length, 1);
      holderEl.appendChild(cellEl);
    }

    holderEl.firstElementChild.appendChild(formEl);
    rowEl.insertAdjacentElement("afterend", holderEl);
    formEl.style.display = "";

    state.rowEl = rowEl;
    state.holderEl = holderEl;
    state.snapshot = serializeFormV1(formEl);

    if (typeof formEl.scrollIntoView === "function") {
      formEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  // Captura antes do handler de linha de new_user.js: o segundo clique na linha aberta
  // fecha o editor (sem alteracoes) ou fica quieto (com alteracoes), sem navegar.
  global.document.addEventListener("click", (event) => {
    const tableEl = global.document.getElementById(TABLE_ID);
    const clickedRow = event.target.closest && event.target.closest("tbody tr");

    if (!tableEl || !clickedRow || !tableEl.contains(clickedRow)) {
      return;
    }

    if (clickedRow.classList.contains(HOLDER_CLASS) || event.target.closest(INTERACTIVE_SELECTOR)) {
      return;
    }

    if (!state.rowEl || clickedRow !== state.rowEl) {
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

  global.AppGenesisAuthProfileInlineEditorV1 = Object.freeze({
    placeInlineEditorV1,
    closeEditorV1
  });
})(window);
