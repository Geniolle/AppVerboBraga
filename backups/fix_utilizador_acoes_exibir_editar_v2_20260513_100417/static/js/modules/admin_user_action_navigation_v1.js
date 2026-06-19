/* APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1
 * Responsabilidade única:
 * - navegar para Exibir/Editar/Fechar do subprocesso Utilizador;
 * - não renderiza tabela;
 * - não filtra tabela;
 * - não pagina tabela;
 * - não altera layout visual.
 */
(function () {
  "use strict";

  //###################################################################################
  // (1) CONSTANTES DO SUBPROCESSO UTILIZADOR
  //###################################################################################

  const MODULE_NAME_V1 = "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1";
  const USER_PATH_V1 = "/users/new";
  const USER_TAB_V1 = "utilizador";
  const USER_TARGET_V1 = "edit-user-card";

  //###################################################################################
  // (2) HELPERS DE URL
  //###################################################################################

  function normalizarUrlAcaoUtilizador_v1(rawHref) {
    if (!rawHref) {
      return null;
    }

    try {
      return new URL(String(rawHref), window.location.origin);
    } catch (error) {
      return null;
    }
  }

  function isUrlAcaoUtilizador_v1(url) {
    if (!url) {
      return false;
    }

    if (url.pathname !== USER_PATH_V1) {
      return false;
    }

    if (url.searchParams.get("menu") !== "administrativo") {
      return false;
    }

    if (url.searchParams.get("admin_tab") !== USER_TAB_V1) {
      return false;
    }

    const hasViewOrEdit = Boolean(url.searchParams.get("user_edit_id"));
    const isClose = !url.searchParams.has("user_edit_id") && !url.searchParams.has("user_view");

    return hasViewOrEdit || isClose;
  }

  function normalizarDestinoUtilizador_v1(url) {
    if (!url) {
      return "";
    }

    if (url.searchParams.get("user_edit_id")) {
      url.searchParams.set("target", USER_TARGET_V1);

      if (!url.hash) {
        url.hash = USER_TARGET_V1;
      }
    }

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (3) DETEÇÃO DO ELEMENTO CLICADO
  //###################################################################################

  function localizarLinkAcaoUtilizador_v1(eventTarget) {
    if (!eventTarget || !document.documentElement.contains(eventTarget)) {
      return null;
    }

    const element = eventTarget.nodeType === 1 ? eventTarget : eventTarget.parentElement;

    if (!element) {
      return null;
    }

    return element.closest(
      "a[href], button[data-href], [data-user-action-url], [data-admin-user-action-url]"
    );
  }

  function extrairHrefAcaoUtilizador_v1(actionElement) {
    if (!actionElement) {
      return "";
    }

    const dataUserActionUrl = actionElement.getAttribute("data-user-action-url") || "";
    if (dataUserActionUrl.trim()) {
      return dataUserActionUrl.trim();
    }

    const dataAdminUserActionUrl = actionElement.getAttribute("data-admin-user-action-url") || "";
    if (dataAdminUserActionUrl.trim()) {
      return dataAdminUserActionUrl.trim();
    }

    const dataHref = actionElement.getAttribute("data-href") || "";
    if (dataHref.trim()) {
      return dataHref.trim();
    }

    const href = actionElement.getAttribute("href") || "";
    return href.trim();
  }

  //###################################################################################
  // (4) NAVEGAÇÃO CONTROLADA
  //###################################################################################

  function navegarParaAcaoUtilizador_v1(event) {
    if (!event || event.defaultPrevented) {
      return;
    }

    if (event.button !== undefined && event.button !== 0) {
      return;
    }

    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }

    const actionElement = localizarLinkAcaoUtilizador_v1(event.target);

    if (!actionElement) {
      return;
    }

    const href = extrairHrefAcaoUtilizador_v1(actionElement);
    const url = normalizarUrlAcaoUtilizador_v1(href);

    if (!isUrlAcaoUtilizador_v1(url)) {
      return;
    }

    const destino = normalizarDestinoUtilizador_v1(url);

    if (!destino) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    window.location.assign(destino);
  }

  //###################################################################################
  // (5) INICIALIZAÇÃO
  //###################################################################################

  function inicializarNavegacaoAcoesUtilizador_v1() {
    if (window.__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1_BOUND__) {
      return;
    }

    window.__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1_BOUND__ = true;
    document.addEventListener("click", navegarParaAcaoUtilizador_v1, true);
  }

  inicializarNavegacaoAcoesUtilizador_v1();

  window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1 = {
    moduleName: MODULE_NAME_V1,
    isUrlAcaoUtilizador_v1,
    normalizarDestinoUtilizador_v1,
  };
})();
