"use strict";

/*
 * APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1
 *
 * Responsabilidade única:
 * - capturar cliques nos ícones/links de ação do subprocesso Utilizador;
 * - validar se o destino pertence ao subprocesso Utilizador;
 * - normalizar a URL para Exibir/Editar;
 * - navegar sem depender de handlers genéricos da página.
 */
(function () {
  const MODULE_NAME_V1 = "APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1";
  const BOUND_FLAG_V1 = "__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1_BOUND__";
  const BOUND_TAP_FLAG_V1 = "__APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1_TAP_BOUND__";
  const DEBUG_ENDPOINT_V1 = "/debug/utilizador-action-flow";
  const DEBUG_FLAG_PARAM_V1 = "utilizador_action_debug";
  const DEBUG_GLOBAL_FLAG_V1 = "__APPVERBO_UTILIZADOR_ACTION_DEBUG__";

  function isDebugAtivo_v1() {
    try {
      const params = new URLSearchParams(String(window.location.search || ""));
      const debugParam = String(params.get(DEBUG_FLAG_PARAM_V1) || "").trim().toLowerCase();
      if (debugParam === "1" || debugParam === "true" || debugParam === "on") {
        return true;
      }
    } catch (error) {}

    return Boolean(window[DEBUG_GLOBAL_FLAG_V1]);
  }

  function descreverNo_v1(node) {
    if (!node || !node.tagName) {
      return "";
    }

    const tag = String(node.tagName || "").toLowerCase();
    const id = String(node.id || "").trim();
    const cls = String(node.className || "").trim();
    return [tag, id ? "#" + id : "", cls ? "." + cls.replace(/\s+/g, ".") : ""].join("");
  }

  function isPaginaUtilizador_v1() {
    try {
      const current = new URL(String(window.location.href || ""), window.location.origin);
      return (
        current.pathname === "/users/new" &&
        current.searchParams.get("menu") === "administrativo" &&
        current.searchParams.get("admin_tab") === "utilizador"
      );
    } catch (error) {
      return false;
    }
  }

  function isCliqueNoEscopoTabelaUtilizador_v1(target) {
    if (!target || typeof target.closest !== "function") {
      return false;
    }

    return Boolean(
      target.closest("#admin-user-shadow-readonly-card") ||
      target.closest("#admin-user-shadow-inactive-card") ||
      target.closest("#admin-users-created-card") ||
      target.closest("#inactive-users-card") ||
      target.closest("[data-admin-subprocess-shadow='utilizador']") ||
      target.closest("[data-admin-subprocess-shadow='utilizador-inactive']") ||
      target.closest("[data-admin-user-actions]")
    );
  }

  function enviarLogFluxoUtilizador_v1(stage, payload) {
    if (!isDebugAtivo_v1()) {
      return;
    }

    const body = {
      logger: MODULE_NAME_V1,
      stage: String(stage || "").trim(),
      payload: payload || {},
      page: {
        href: String(window.location.href || ""),
        pathname: String(window.location.pathname || ""),
        search: String(window.location.search || ""),
        hash: String(window.location.hash || "")
      },
      ts: new Date().toISOString()
    };

    try {
      const raw = JSON.stringify(body);

      if (navigator && typeof navigator.sendBeacon === "function") {
        const blob = new Blob([raw], { type: "application/json" });
        navigator.sendBeacon(DEBUG_ENDPOINT_V1, blob);
        return;
      }

      fetch(DEBUG_ENDPOINT_V1, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: raw,
        keepalive: true
      }).catch(function () {});
    } catch (error) {
      // Nao bloquear navegação por erro de debug.
    }
  }

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

    if (url.pathname !== "/users/new") {
      return false;
    }

    if (url.searchParams.get("menu") !== "administrativo") {
      return false;
    }

    if (url.searchParams.get("admin_tab") !== "utilizador") {
      return false;
    }

    if (!url.searchParams.get("user_edit_id")) {
      return false;
    }

    const userView = url.searchParams.get("user_view");
    return !userView || userView === "1" || userView === "0";
  }

  function resolverUserViewAcaoUtilizador_v1(url, actionElement) {
    const urlUserView = String(url.searchParams.get("user_view") || "").trim();

    if (urlUserView === "1" || urlUserView === "0") {
      return urlUserView;
    }

    const dataUserView = String(
      actionElement ? actionElement.getAttribute("data-appverbo-user-view") || "" : ""
    ).trim();

    if (dataUserView === "1" || dataUserView === "0") {
      return dataUserView;
    }

    const action = String(
      actionElement ? actionElement.getAttribute("data-appverbo-user-action") || "" : ""
    ).trim().toLowerCase();

    return action === "view" ? "1" : "0";
  }

  function normalizarDestinoUtilizador_v1(url, actionElement) {
    const destino = new URL("/users/new", window.location.origin);

    destino.searchParams.set("menu", "administrativo");
    destino.searchParams.set("admin_tab", "utilizador");
    destino.searchParams.set("user_edit_id", url.searchParams.get("user_edit_id"));
    destino.searchParams.set("user_view", resolverUserViewAcaoUtilizador_v1(url, actionElement));
    destino.searchParams.set("target", "edit-user-card");
    destino.hash = "edit-user-card";

    return destino.pathname + destino.search + destino.hash;
  }

  function localizarLinkAcaoUtilizador_v1(eventTarget) {
    if (!eventTarget) {
      return null;
    }

    let node = eventTarget;

    if (node.nodeType === Node.TEXT_NODE) {
      node = node.parentElement;
    }

    if (!node || typeof node.closest !== "function") {
      return null;
    }

    const explicitLink = node.closest("a[href][data-admin-user-action-link='1']");

    if (explicitLink) {
      return explicitLink;
    }

    if (!isCliqueNoEscopoTabelaUtilizador_v1(node)) {
      return null;
    }

    return node.closest("a[href*='user_edit_id=']");
  }

  function extrairHrefAcaoUtilizador_v1(actionElement) {
    if (!actionElement) {
      return "";
    }

    const href = actionElement.getAttribute("href") || "";
    return String(href).trim();
  }

  function deveIgnorarCliqueEspecial_v1(event) {
    if (!event) {
      return true;
    }

    if (event.defaultPrevented) {
      return true;
    }

    if (event.button && event.button !== 0) {
      return true;
    }

    return Boolean(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey);
  }

  function navegarParaAcaoUtilizador_v1(event) {
    if (isPaginaUtilizador_v1()) {
      enviarLogFluxoUtilizador_v1("navigate_handler_invocado", {
        defaultPrevented: Boolean(event && event.defaultPrevented)
      });
    }

    if (deveIgnorarCliqueEspecial_v1(event)) {
      return;
    }

    const cancelLink = event.target && event.target.closest
      ? event.target.closest("a[data-admin-user-edit-cancel='1'][href]")
      : null;

    if (cancelLink) {
      const cancelHref = String(cancelLink.getAttribute("href") || "").trim();

      if (cancelHref) {
        event.preventDefault();
        event.stopPropagation();

        if (typeof event.stopImmediatePropagation === "function") {
          event.stopImmediatePropagation();
        }

        enviarLogFluxoUtilizador_v1("cancel_navegacao_disparada", {
          href: cancelHref
        });
        window.location.assign(cancelHref);
      }
      return;
    }

    const rawTarget = event && event.target ? event.target : null;
    const normalizedTarget =
      rawTarget && rawTarget.nodeType === Node.TEXT_NODE ? rawTarget.parentElement : rawTarget;

    const actionElement = localizarLinkAcaoUtilizador_v1(event.target);
    if (!actionElement) {
      if (isPaginaUtilizador_v1() && isCliqueNoEscopoTabelaUtilizador_v1(normalizedTarget)) {
        enviarLogFluxoUtilizador_v1("clique_ignorado_sem_action_element", {
          target: descreverNo_v1(normalizedTarget),
          closestAnchor: descreverNo_v1(
            normalizedTarget && typeof normalizedTarget.closest === "function"
              ? normalizedTarget.closest("a[href]")
              : null
          )
        });
      }
      return;
    }

    const href = extrairHrefAcaoUtilizador_v1(actionElement);
    const url = normalizarUrlAcaoUtilizador_v1(href);

    enviarLogFluxoUtilizador_v1("click_detectado", {
      href: href,
      actionTitle: String(actionElement.getAttribute("title") || ""),
      actionLabel: String(actionElement.getAttribute("aria-label") || ""),
      dataUserId: String(actionElement.getAttribute("data-user-id") || "")
    });

    if (!isUrlAcaoUtilizador_v1(url)) {
      enviarLogFluxoUtilizador_v1("url_invalida_ignorada", {
        href: href
      });
      return;
    }

    const destino = normalizarDestinoUtilizador_v1(url, actionElement);
    if (!destino) {
      enviarLogFluxoUtilizador_v1("destino_vazio", {
        href: href
      });
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }

    enviarLogFluxoUtilizador_v1("navegacao_disparada", {
      hrefOriginal: href,
      destino: destino
    });
    window.location.assign(destino);
  }

  function registrarTapCliqueGlobal_v1(event) {
    if (!isPaginaUtilizador_v1()) {
      return;
    }

    const rawTarget = event && event.target ? event.target : null;
    const normalizedTarget =
      rawTarget && rawTarget.nodeType === Node.TEXT_NODE ? rawTarget.parentElement : rawTarget;

    if (!isCliqueNoEscopoTabelaUtilizador_v1(normalizedTarget)) {
      return;
    }

    enviarLogFluxoUtilizador_v1("click_tap_window", {
      target: descreverNo_v1(normalizedTarget),
      defaultPrevented: Boolean(event && event.defaultPrevented)
    });
  }

  function inicializarTapCliqueGlobal_v1() {
    if (window[BOUND_TAP_FLAG_V1]) {
      return;
    }

    window[BOUND_TAP_FLAG_V1] = true;
    window.addEventListener("click", registrarTapCliqueGlobal_v1, true);
    enviarLogFluxoUtilizador_v1("tap_bind_ativo", {});
  }

  function inicializarNavegacaoAcoesUtilizador_v1() {
    if (window[BOUND_FLAG_V1]) {
      enviarLogFluxoUtilizador_v1("bind_ignorado_ja_existente", {});
      return;
    }

    window[BOUND_FLAG_V1] = true;
    window.addEventListener("click", navegarParaAcaoUtilizador_v1, true);
    enviarLogFluxoUtilizador_v1("bind_ativo", {});
  }

  inicializarTapCliqueGlobal_v1();
  inicializarNavegacaoAcoesUtilizador_v1();

  window.APPVERBO_ADMIN_USER_ACTION_NAVIGATION_V1 = {
    moduleName: MODULE_NAME_V1,
    normalizarUrlAcaoUtilizador_v1,
    isUrlAcaoUtilizador_v1,
    resolverUserViewAcaoUtilizador_v1,
    normalizarDestinoUtilizador_v1,
    localizarLinkAcaoUtilizador_v1,
    extrairHrefAcaoUtilizador_v1,
    navegarParaAcaoUtilizador_v1,
    inicializarNavegacaoAcoesUtilizador_v1
  };
})();
