//###################################################################################
// (1) MODO GLOBAL DE EDICAO DE PROCESSO
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function normalizeText(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function isEditingProcess() {
    const params = new URLSearchParams(window.location.search);

    const settingsEditKey = String(params.get("settings_edit_key") || "").trim();
    const settingsAction = normalizeText(params.get("settings_action"));

    if (!settingsEditKey) {
      return false;
    }

    if (!settingsAction) {
      return true;
    }

    return settingsAction === "edit";
  }

  function getCardTitle(card) {
    const titleElement = card.querySelector("h1, h2, h3");
    return normalizeText(titleElement ? titleElement.textContent : "");
  }

  function isEditProcessCard(card) {
    const title = getCardTitle(card);
    return title.startsWith("editar processo:");
  }

  function isMenuTabsCard(card) {
    return card.id === "menu-tabs-card" || Boolean(card.querySelector("#submenu-items"));
  }

  function isCardToHideDuringProcessEdit(card) {
    const title = getCardTitle(card);

    if (!title) {
      return false;
    }

    if (title === "criar pasta no menu lateral") {
      return true;
    }

    if (title === "definicoes" || title === "definições") {
      return true;
    }

    if (title.includes("entidades criadas")) {
      return true;
    }

    if (title.includes("entidades inativas")) {
      return true;
    }

    return false;
  }

  //###################################################################################
  // (3) APLICAR REGRA GLOBAL
  //###################################################################################

  function applyProcessEditFocusMode() {
    if (!isEditingProcess()) {
      return;
    }

    const cards = Array.from(document.querySelectorAll(".card"));

    cards.forEach(function (card) {
      if (isMenuTabsCard(card)) {
        card.style.display = "";
        return;
      }

      if (isEditProcessCard(card)) {
        card.style.display = "";
        return;
      }

      if (isCardToHideDuringProcessEdit(card)) {
        card.style.display = "none";
      }
    });

    const editCard = cards.find(isEditProcessCard);

    if (editCard) {
      editCard.scrollIntoView({
        behavior: "auto",
        block: "start"
      });
    }
  }

  //###################################################################################
  // (4) INICIALIZACAO
  //###################################################################################

  function init() {
    applyProcessEditFocusMode();

    window.setTimeout(applyProcessEditFocusMode, 100);
    window.setTimeout(applyProcessEditFocusMode, 300);
    window.setTimeout(applyProcessEditFocusMode, 800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
