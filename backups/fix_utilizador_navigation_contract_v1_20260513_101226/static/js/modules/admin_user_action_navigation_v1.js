/* APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1
 * Responsabilidade única:
 * - capturar cliques nos ícones Exibir/Editar do subprocesso Utilizador;
 * - normalizar para a URL canónica;
 * - navegar antes de outros handlers bloquearem o clique.
 */
(function () {
  "use strict";

  const MODULE_NAME_V1 = "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1";
  const BOUND_FLAG_V1 = "__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1_BOUND__";
  const ACTION_SELECTOR_V1 = [
    'a[data-admin-user-action-link="1"]',
    'a[href*="admin_tab=utilizador"][href*="user_edit_id="]',
    'button[data-admin-user-action-link="1"]'
  ].join(",");

  function isModifiedClick_v1(event) {
    return Boolean(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey);
  }

  function hasUsableTarget_v1(event) {
    if (!event) {
      return false;
    }

    if (event.type === "click" && typeof event.button === "number" && event.button !== 0) {
      return false;
    }

    return true;
  }

  function normalizarUrlAcaoUtilizador_v1(rawHref) {
    const cleanHref = String(rawHref || "").trim();

    if (!cleanHref || cleanHref === "#" || cleanHref.toLowerCase().startsWith("javascript:")) {
      return null;
    }

    try {
      return new URL(cleanHref, window.location.origin);
    }
    catch (_error) {
      return null;
    }
  }

  function isUrlAcaoUtilizador_v1(url) {
    if (!url) {
      return false;
    }

    if (url.origin !== window.location.origin) {
      return false;
    }

    if (url.pathname !== "/users/new") {
      return false;
    }

    if (url.searchParams.get("admin_tab") !== "utilizador") {
      return false;
    }

    const userEditId = String(url.searchParams.get("user_edit_id") || "").trim();

    return /^\d+$/.test(userEditId);
  }

  function resolverModoAcaoUtilizador_v1(actionElement, url) {
    const dataAction = String(actionElement.getAttribute("data-admin-user-action") || "").trim().toLowerCase();

    if (dataAction === "view" || dataAction === "exibir") {
      return "1";
    }

    if (dataAction === "edit" || dataAction === "editar" || dataAction === "modificar") {
      return "0";
    }

    const currentMode = String(url.searchParams.get("user_view") || "").trim();

    if (currentMode === "1") {
      return "1";
    }

    return "0";
  }

  function normalizarDestinoUtilizador_v1(rawHref, actionElement) {
    const url = normalizarUrlAcaoUtilizador_v1(rawHref);

    if (!isUrlAcaoUtilizador_v1(url)) {
      return "";
    }

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "utilizador");
    url.searchParams.set("user_view", resolverModoAcaoUtilizador_v1(actionElement, url));
    url.searchParams.set("target", "edit-user-card");
    url.hash = "#edit-user-card";

    return url.pathname + url.search + url.hash;
  }

  function localizarLinkAcaoUtilizador_v1(eventTarget) {
    if (!eventTarget || typeof eventTarget.closest !== "function") {
      return null;
    }

    return eventTarget.closest(ACTION_SELECTOR_V1);
  }

  function extrairHrefAcaoUtilizador_v1(actionElement) {
    if (!actionElement) {
      return "";
    }

    return (
      actionElement.getAttribute("href") ||
      actionElement.getAttribute("data-href") ||
      actionElement.getAttribute("data-url") ||
      ""
    );
  }

  function bloquearHandlersConcorrentes_v1(event) {
    event.preventDefault();
    event.stopPropagation();

    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }
  }

  function navegarParaAcaoUtilizador_v1(event) {
    if (!hasUsableTarget_v1(event)) {
      return;
    }

    if (isModifiedClick_v1(event)) {
      return;
    }

    const actionElement = localizarLinkAcaoUtilizador_v1(event.target);

    if (!actionElement) {
      return;
    }

    const destino = normalizarDestinoUtilizador_v1(
      extrairHrefAcaoUtilizador_v1(actionElement),
      actionElement
    );

    if (!destino) {
      return;
    }

    bloquearHandlersConcorrentes_v1(event);
    window.location.assign(destino);
  }

  function navegarPorTecladoUtilizador_v1(event) {
    const key = String(event.key || "");

    if (key !== "Enter" && key !== " ") {
      return;
    }

    const actionElement = localizarLinkAcaoUtilizador_v1(event.target);

    if (!actionElement) {
      return;
    }

    const destino = normalizarDestinoUtilizador_v1(
      extrairHrefAcaoUtilizador_v1(actionElement),
      actionElement
    );

    if (!destino) {
      return;
    }

    bloquearHandlersConcorrentes_v1(event);
    window.location.assign(destino);
  }

  function inicializarNavegacaoAcoesUtilizador_v1() {
    if (window[BOUND_FLAG_V1]) {
      return;
    }

    window[BOUND_FLAG_V1] = true;

    document.addEventListener("click", navegarParaAcaoUtilizador_v1, true);
    document.addEventListener("keydown", navegarPorTecladoUtilizador_v1, true);
  }

  inicializarNavegacaoAcoesUtilizador_v1();

  window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1 = {
    moduleName: MODULE_NAME_V1,
    normalizarUrlAcaoUtilizador_v1,
    isUrlAcaoUtilizador_v1,
    normalizarDestinoUtilizador_v1,
    localizarLinkAcaoUtilizador_v1,
    extrairHrefAcaoUtilizador_v1,
    navegarParaAcaoUtilizador_v1,
    inicializarNavegacaoAcoesUtilizador_v1
  };
})();
