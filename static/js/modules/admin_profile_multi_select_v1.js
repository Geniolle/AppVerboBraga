// Campo "Perfil de autorizacao" com varias linhas (subprocesso Funcoes administrativas).
// "+" adiciona uma linha; "-" remove (mantem sempre uma linha); cada select so mostra os perfis
// que nao estao escolhidos nas outras linhas do mesmo campo, para nao haver duplicados.
// A primeira opcao "Todos os perfis" (valor __all__) e exclusiva: escolhida, bloqueia as outras opcoes.
(function initAppGenesisAdminProfileMultiSelectV1(global) {
  const FIELD_SELECTOR = "[data-admin-profile-multi='1']";
  const ROWS_SELECTOR = "[data-admin-profile-multi-rows]";
  const ROW_SELECTOR = "[data-admin-profile-multi-row]";
  const SELECT_SELECTOR = "[data-admin-profile-multi-select]";
  const ALL_VALUE = "__all__";

  function selectsOf(fieldEl) {
    return Array.from(fieldEl.querySelectorAll(SELECT_SELECTOR));
  }

  function syncFieldV1(fieldEl) {
    const selects = selectsOf(fieldEl);
    const allChosen = selects.some((s) => s.value === ALL_VALUE);

    selects.forEach((selectEl) => {
      const otherValues = selects
        .filter((other) => other !== selectEl && other.value)
        .map((other) => other.value);

      Array.from(selectEl.options).forEach((optionEl) => {
        if (!optionEl.value) {
          return;
        }
        let blocked;
        if (allChosen) {
          blocked = optionEl.value !== ALL_VALUE || selectEl.value !== ALL_VALUE;
        } else if (optionEl.value === ALL_VALUE) {
          blocked = otherValues.length > 0;
        } else {
          blocked = otherValues.includes(optionEl.value);
        }
        optionEl.hidden = blocked;
        optionEl.disabled = blocked;
      });
    });

    const addBtn = fieldEl.querySelector("[data-admin-profile-multi-add]");
    if (addBtn && selects.length) {
      const specificTotal = Math.max(0, selects[0].options.length - 2);
      const chosenSpecific = selects.filter((s) => s.value && s.value !== ALL_VALUE).length;
      addBtn.disabled = allChosen || chosenSpecific >= specificTotal;
    }
  }

  function addRowV1(fieldEl) {
    const rowsEl = fieldEl.querySelector(ROWS_SELECTOR);
    const templateEl = fieldEl.querySelector("template[data-admin-profile-multi-template]");
    if (!rowsEl || !templateEl) {
      return;
    }
    rowsEl.appendChild(templateEl.content.firstElementChild.cloneNode(true));
    syncFieldV1(fieldEl);
  }

  function removeRowV1(rowEl) {
    const fieldEl = rowEl.closest(FIELD_SELECTOR);
    const rowsEl = rowEl.parentElement;
    rowEl.remove();
    if (fieldEl && rowsEl && !rowsEl.querySelector(ROW_SELECTOR)) {
      addRowV1(fieldEl);
    }
    if (fieldEl) {
      syncFieldV1(fieldEl);
    }
  }

  global.document.addEventListener("click", (event) => {
    const addBtn = event.target.closest && event.target.closest("[data-admin-profile-multi-add]");
    if (addBtn) {
      const fieldEl = addBtn.closest(FIELD_SELECTOR);
      if (fieldEl) {
        event.preventDefault();
        addRowV1(fieldEl);
      }
      return;
    }
    const removeBtn = event.target.closest && event.target.closest("[data-admin-profile-multi-remove]");
    if (removeBtn) {
      const rowEl = removeBtn.closest(ROW_SELECTOR);
      if (rowEl) {
        event.preventDefault();
        removeRowV1(rowEl);
      }
    }
  });

  global.document.addEventListener("change", (event) => {
    const selectEl = event.target.closest && event.target.closest(SELECT_SELECTOR);
    if (!selectEl) {
      return;
    }
    const fieldEl = selectEl.closest(FIELD_SELECTOR);
    if (fieldEl) {
      syncFieldV1(fieldEl);
    }
  });

  function initV1() {
    global.document.querySelectorAll(FIELD_SELECTOR).forEach(syncFieldV1);
  }

  if (global.document.readyState === "loading") {
    global.document.addEventListener("DOMContentLoaded", initV1);
  } else {
    initV1();
  }

  global.AppGenesisAdminProfileMultiSelectV1 = Object.freeze({ syncFieldV1, addRowV1, removeRowV1 });
})(window);
