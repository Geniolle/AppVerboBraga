// APPVERBO_PROFILE_FIELD_ORDER_V4_START
//###################################################################################
// (1) ORDENAR MODO EDICAO CONFORME MODO LEITURA DO MEU PERFIL
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) CONSTANTES
  //###################################################################################

  const bootstrap = window.__APPVERBO_BOOTSTRAP__ || {};

  const fallbackVisibleFields = Array.isArray(bootstrap.profilePersonalVisibleFields)
    ? bootstrap.profilePersonalVisibleFields
      .map((fieldKey) => String(fieldKey || "").trim().toLowerCase())
      .filter(Boolean)
    : [];

  const profilePersonalFieldLabels = (
    bootstrap.profilePersonalFieldLabels &&
    typeof bootstrap.profilePersonalFieldLabels === "object" &&
    !Array.isArray(bootstrap.profilePersonalFieldLabels)
  )
    ? bootstrap.profilePersonalFieldLabels
    : {};

  const builtinLabelByKey = {
    nome: "Nome",
    email: "Email",
    telefone: "Telefone",
    pais: "País",
    data_nascimento: "Data de nascimento",
    whatsapp: "WhatsApp",
    autorizacao_whatsapp: "Autorização para avisos por WhatsApp",
    conta: "Conta",
    estado_membro: "Estado de membro",
    colaborador: "Colaborador",
    entidades: "Entidades",
    ultima_verificacao_whatsapp: "Última verificação WhatsApp",
    detalhe_verificacao: "Detalhe da verificação"
  };

  const builtinKeyByInputName = {
    full_name: "nome",
    primary_phone: "telefone",
    login_email: "email",
    email: "email",
    country: "pais",
    birth_date: "data_nascimento",
    whatsapp_notice_opt_in: "autorizacao_whatsapp"
  };

  let reorderInProgress = false;

  //###################################################################################
  // (3) NORMALIZACAO
  //###################################################################################

  function normalizeKey_v4(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeLookup_v4(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\*/g, "")
      .replace(/\s+/g, " ");
  }

  //###################################################################################
  // (4) MAPEAR LABEL PARA KEY
  //###################################################################################

  function buildLabelToKeyMap_v4() {
    const labelToKey = new Map();

    Object.keys(builtinLabelByKey).forEach(function (fieldKey) {
      labelToKey.set(normalizeLookup_v4(builtinLabelByKey[fieldKey]), fieldKey);
    });

    Object.keys(profilePersonalFieldLabels).forEach(function (fieldKey) {
      const cleanFieldKey = normalizeKey_v4(fieldKey);
      const label = String(profilePersonalFieldLabels[fieldKey] || "").trim();

      if (cleanFieldKey && label) {
        labelToKey.set(normalizeLookup_v4(label), cleanFieldKey);
      }
    });

    return labelToKey;
  }

  function resolveKeyByLabel_v4(labelText) {
    const labelToKey = buildLabelToKeyMap_v4();
    return labelToKey.get(normalizeLookup_v4(labelText)) || "";
  }

  //###################################################################################
  // (5) LOCALIZAR ELEMENTOS
  //###################################################################################

  function getProfileCard_v4() {
    return document.querySelector("#perfil-pessoal-card");
  }

  function getReadonlyGrid_v4() {
    const card = getProfileCard_v4();

    if (!card) {
      return null;
    }

    return card.querySelector(".profile-readonly .personal-grid");
  }

  function getEditForm_v4() {
    return (
      document.querySelector('form[action="/users/profile/personal"]') ||
      document.querySelector("#perfil-pessoal-card form.profile-edit-form")
    );
  }

  function getEditGrid_v4(form) {
    if (!form) {
      return null;
    }

    return form.querySelector(".personal-grid") || form;
  }

  //###################################################################################
  // (6) OBTER ORDEM REAL DO MODO LEITURA
  //###################################################################################

  function resolveReadonlyItemKey_v4(item) {
    if (!item) {
      return "";
    }

    const explicitKey = normalizeKey_v4(
      item.getAttribute("data-profile-field-key") ||
      item.dataset.profileFieldKey ||
      ""
    );

    if (explicitKey) {
      return explicitKey;
    }

    const labelElement = item.querySelector(".personal-label");
    const labelText = labelElement ? labelElement.textContent : "";

    return resolveKeyByLabel_v4(labelText);
  }

  function getReadonlyOrder_v4() {
    const readonlyGrid = getReadonlyGrid_v4();
    const order = [];
    const seen = new Set();

    if (!readonlyGrid) {
      return order;
    }

    Array.from(readonlyGrid.querySelectorAll(".personal-item")).forEach(function (item) {
      const fieldKey = resolveReadonlyItemKey_v4(item);

      if (!fieldKey || seen.has(fieldKey)) {
        return;
      }

      seen.add(fieldKey);
      order.push(fieldKey);
    });

    return order;
  }

  function mergeOrder_v4(primaryOrder, fallbackOrder) {
    const result = [];
    const seen = new Set();

    primaryOrder.concat(fallbackOrder).forEach(function (rawFieldKey) {
      const fieldKey = normalizeKey_v4(rawFieldKey);

      if (!fieldKey || seen.has(fieldKey)) {
        return;
      }

      seen.add(fieldKey);
      result.push(fieldKey);
    });

    return result;
  }

  function getEffectiveOrder_v4() {
    const readonlyOrder = getReadonlyOrder_v4();

    if (fallbackVisibleFields.length) {
      return mergeOrder_v4(fallbackVisibleFields, readonlyOrder);
    }

    return readonlyOrder.slice();
  }

  //###################################################################################
  // (7) IDENTIFICAR CAMPOS DO FORMULARIO
  //###################################################################################

  function resolveEditFieldKey_v4(field) {
    if (!field) {
      return "";
    }

    const explicitKey = normalizeKey_v4(
      field.getAttribute("data-profile-field-key") ||
      field.dataset.profileFieldKey ||
      ""
    );

    if (explicitKey) {
      return explicitKey;
    }

    const customInput = field.querySelector('[name^="custom_field__"]');

    if (customInput) {
      return normalizeKey_v4(
        String(customInput.getAttribute("name") || "").replace(/^custom_field__/, "")
      );
    }

    const input = field.querySelector("input, select, textarea");

    if (input) {
      const inputName = normalizeKey_v4(input.getAttribute("name") || "");

      if (builtinKeyByInputName[inputName]) {
        return builtinKeyByInputName[inputName];
      }
    }

    const label = field.querySelector("label");

    if (label) {
      return resolveKeyByLabel_v4(label.textContent);
    }

    return "";
  }

  function findEditFieldByKey_v4(form, fieldKey) {
    const cleanFieldKey = normalizeKey_v4(fieldKey);

    if (!form || !cleanFieldKey) {
      return null;
    }

    const allFields = Array.from(form.querySelectorAll(".field"));

    return allFields.find(function (field) {
      return resolveEditFieldKey_v4(field) === cleanFieldKey;
    }) || null;
  }

  //###################################################################################
  // (8) APLICAR ORDEM AO FORMULARIO
  //###################################################################################

  function applyOrderToEditForm_v4() {
    if (reorderInProgress) {
      return;
    }

    reorderInProgress = true;

    try {
      const form = getEditForm_v4();
      const editGrid = getEditGrid_v4(form);
      const effectiveOrder = getEffectiveOrder_v4();

      if (!form || !editGrid || !effectiveOrder.length) {
        return;
      }

      const orderedKeys = new Set();

      Array.from(editGrid.querySelectorAll(".field")).forEach(function (field) {
        field.style.order = "";
      });

      effectiveOrder.forEach(function (fieldKey, index) {
        const field = findEditFieldByKey_v4(form, fieldKey);

        if (!field || field.parentElement !== editGrid) {
          return;
        }

        field.style.order = String((index + 1) * 10);
        field.setAttribute("data-appverbo-profile-order-v4", String(index + 1));
        orderedKeys.add(fieldKey);
      });

      let nextOrder = (effectiveOrder.length + 1) * 10;

      Array.from(editGrid.querySelectorAll(".field")).forEach(function (field) {
        const fieldKey = resolveEditFieldKey_v4(field);

        if (fieldKey && orderedKeys.has(fieldKey)) {
          return;
        }

        field.style.order = String(nextOrder);
        field.setAttribute("data-appverbo-profile-order-v4", String(nextOrder));
        nextOrder += 10;
      });

      const actions = form.querySelector(".profile-edit-actions");

      if (actions) {
        actions.style.order = String(nextOrder + 10);
      }
    }
    finally {
      reorderInProgress = false;
    }
  }

  //###################################################################################
  // (8.1) APLICAR ORDEM AO MODO LEITURA
  //###################################################################################

  function applyOrderToReadonlyGrid_v4() {
    const readonlyGrid = getReadonlyGrid_v4();
    const effectiveOrder = getEffectiveOrder_v4();

    if (!readonlyGrid || !effectiveOrder.length) {
      return;
    }

    const readonlyItems = Array.from(readonlyGrid.querySelectorAll(".personal-item"));
    const orderedKeys = new Set();

    readonlyItems.forEach(function (item) {
      item.style.order = "";
    });

    effectiveOrder.forEach(function (fieldKey, index) {
      const cleanFieldKey = normalizeKey_v4(fieldKey);

      if (!cleanFieldKey) {
        return;
      }

      const targetItem = readonlyItems.find(function (item) {
        return resolveReadonlyItemKey_v4(item) === cleanFieldKey;
      });

      if (!targetItem) {
        return;
      }

      targetItem.style.order = String((index + 1) * 10);
      targetItem.setAttribute("data-appverbo-profile-order-v4", String(index + 1));
      orderedKeys.add(cleanFieldKey);
    });

    let nextOrder = (effectiveOrder.length + 1) * 10;

    readonlyItems.forEach(function (item) {
      const fieldKey = resolveReadonlyItemKey_v4(item);

      if (fieldKey && orderedKeys.has(fieldKey)) {
        return;
      }

      item.style.order = String(nextOrder);
      item.setAttribute("data-appverbo-profile-order-v4", String(nextOrder));
      nextOrder += 10;
    });
  }

  //###################################################################################
  // (9) EXECUTAR APENAS EM EVENTOS CONTROLADOS
  //###################################################################################

  function scheduleApplyOrder_v4() {
    window.setTimeout(applyOrderToReadonlyGrid_v4, 0);
    window.setTimeout(applyOrderToReadonlyGrid_v4, 120);
    window.setTimeout(applyOrderToReadonlyGrid_v4, 400);
    window.setTimeout(applyOrderToEditForm_v4, 0);
    window.setTimeout(applyOrderToEditForm_v4, 120);
    window.setTimeout(applyOrderToEditForm_v4, 400);
  }

  function installEditClickHook_v4() {
    document.addEventListener(
      "click",
      function (event) {
        const button = event.target && event.target.closest
          ? event.target.closest('[data-edit-target="perfil-pessoal-card"], .profile-edit-toggle')
          : null;

        if (!button) {
          return;
        }

        scheduleApplyOrder_v4();
      },
      true
    );
  }

  //###################################################################################
  // (10) INICIAR
  //###################################################################################

  function init_v4() {
    installEditClickHook_v4();
    scheduleApplyOrder_v4();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init_v4);
  }
  else {
    init_v4();
  }

  window.addEventListener("pageshow", scheduleApplyOrder_v4);
  window.reorderMeuPerfilProfileFields = applyOrderToEditForm_v4;
})();
// APPVERBO_PROFILE_FIELD_ORDER_V4_END
