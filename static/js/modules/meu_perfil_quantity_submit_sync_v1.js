// APPVERBO_MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1_MODULE_START
(function registerMeuPerfilQuantitySubmitSyncV1Module() {
  "use strict";

  window.APPVERBO_SETUP_MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1 = function setupMeuPerfilQuantitySubmitSyncV1(options) {
    const deps = options && typeof options === "object" ? options : {};

    const collectCurrentMeuPerfilQuantityValues = typeof deps.collectCurrentMeuPerfilQuantityValues === "function"
      ? deps.collectCurrentMeuPerfilQuantityValues
      : window.collectCurrentMeuPerfilQuantityValues;
    const syncMeuPerfilQuantityHiddenInputs = typeof deps.syncMeuPerfilQuantityHiddenInputs === "function"
      ? deps.syncMeuPerfilQuantityHiddenInputs
      : window.syncMeuPerfilQuantityHiddenInputs;
// APPVERBO_MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1_START
//###################################################################################
// (MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1) SINCRONIZAR DADOS DE AGREGADOS ANTES DE GRAVAR
//###################################################################################

function syncMeuPerfilQuantityPayloadFromLiveControls_v1() {
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const formEl = personalCardEl
    ? personalCardEl.querySelector('form[action="/users/profile/personal"]')
    : null;

  if (!formEl) {
    return;
  }

  if (
    typeof collectCurrentMeuPerfilQuantityValues !== "function" ||
    typeof syncMeuPerfilQuantityHiddenInputs !== "function"
  ) {
    return;
  }

  const quantityValuesByRule = collectCurrentMeuPerfilQuantityValues();
  syncMeuPerfilQuantityHiddenInputs(quantityValuesByRule);
}

function syncMeuPerfilQuantityPayloadBeforeSubmit_v1(event) {
  syncMeuPerfilQuantityPayloadFromLiveControls_v1();
}

function attachMeuPerfilQuantitySubmitSync_v1() {
  const personalCardEl = document.getElementById("perfil-pessoal-card");
  const formEl = personalCardEl
    ? personalCardEl.querySelector('form[action="/users/profile/personal"]')
    : null;

  if (!formEl) {
    return;
  }

  if (formEl.dataset.meuPerfilQuantitySubmitSyncV1 === "1") {
    return;
  }

  formEl.dataset.meuPerfilQuantitySubmitSyncV1 = "1";

  formEl.addEventListener("submit", syncMeuPerfilQuantityPayloadBeforeSubmit_v1, true);

  formEl.addEventListener("input", function (event) {
    const targetEl = event && event.target ? event.target : null;

    if (!targetEl || typeof targetEl.matches !== "function") {
      return;
    }

    if (targetEl.matches("[data-meu-perfil-quantity-field-key]")) {
      syncMeuPerfilQuantityPayloadFromLiveControls_v1();
    }
  }, true);

  formEl.addEventListener("change", function (event) {
    const targetEl = event && event.target ? event.target : null;

    if (!targetEl || typeof targetEl.matches !== "function") {
      return;
    }

    if (
      targetEl.matches("[data-meu-perfil-quantity-field-key]") ||
      targetEl.matches("[name^='custom_field__']")
    ) {
      syncMeuPerfilQuantityPayloadFromLiveControls_v1();
    }
  }, true);

  syncMeuPerfilQuantityPayloadFromLiveControls_v1();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", attachMeuPerfilQuantitySubmitSync_v1);
} else {
  attachMeuPerfilQuantitySubmitSync_v1();
}

window.setTimeout(attachMeuPerfilQuantitySubmitSync_v1, 250);
window.setTimeout(attachMeuPerfilQuantitySubmitSync_v1, 1000);
// APPVERBO_MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1_END
  };
})();
// APPVERBO_MEU_PERFIL_QUANTITY_SUBMIT_SYNC_V1_MODULE_END
