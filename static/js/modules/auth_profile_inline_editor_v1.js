// Editor do Perfil de autorizacao em modo Editar: abre logo abaixo da linha do perfil clicado
// (mesmo comportamento do editor inline de Campos adicionais), e nao no topo da lista.
(function initAppGenesisAuthProfileInlineEditorV1(global) {
  const FORM_ID = "auth-profile-form-card";
  const TABLE_ID = "auth-profile-active-table";
  const HOLDER_CLASS = "auth-profile-inline-editor-row";

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

    if (typeof formEl.scrollIntoView === "function") {
      formEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  if (global.document.readyState === "loading") {
    global.document.addEventListener("DOMContentLoaded", placeInlineEditorV1);
  } else {
    placeInlineEditorV1();
  }

  global.AppGenesisAuthProfileInlineEditorV1 = Object.freeze({
    placeInlineEditorV1
  });
})(window);
