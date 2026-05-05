//###################################################################################
// APPVERBOBRAGA - ACTIVE UNICO E NAVEGACAO LIMPA NAS ABAS SUPERIORES - V4
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) ESTADO
  //###################################################################################

  let activeTabLabelV4 = "";
  let applyingActiveV4 = false;
  let observerTimerV4 = null;

  //###################################################################################
  // (2) URL
  //###################################################################################

  function obterUrlAtual_v4() {
    try {
      return new URL(window.location.href);
    } catch (erro) {
      return null;
    }
  }

  function obterParametrosUrl_v4() {
    const url = obterUrlAtual_v4();
    return url ? url.searchParams : new URLSearchParams();
  }

  function obterMenuAtual_v4() {
    return String(obterParametrosUrl_v4().get("menu") || "").trim().toLowerCase();
  }

  function estaNoAdministrativo_v4() {
    return obterMenuAtual_v4() === "administrativo";
  }

  function temContextoDeEdicaoMenu_v4() {
    const parametros = obterParametrosUrl_v4();

    return (
      parametros.has("settings_edit_key") ||
      parametros.has("settings_action") ||
      parametros.has("settings_tab") ||
      parametros.has("settings_success") ||
      parametros.has("settings_error")
    );
  }

  function normalizarPathQueryHash_v4(urlString) {
    const link = document.createElement("a");
    link.href = urlString;

    return String(link.pathname || "") +
      String(link.search || "") +
      String(link.hash || "");
  }

  //###################################################################################
  // (3) ABAS SUPERIORES
  //###################################################################################

  function obterContainerAbas_v4() {
    return document.getElementById("submenu-items");
  }

  function obterAbasSuperiores_v4() {
    const container = obterContainerAbas_v4();

    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll("a, button, .submenu-item"));
  }

  function normalizarTexto_v4(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function obterTextoAba_v4(aba) {
    return normalizarTexto_v4(aba ? aba.textContent : "");
  }

  function localizarAbaPorTexto_v4(texto) {
    const textoNormalizado = normalizarTexto_v4(texto);

    if (!textoNormalizado) {
      return null;
    }

    return obterAbasSuperiores_v4().find(function (aba) {
      return obterTextoAba_v4(aba) === textoNormalizado;
    }) || null;
  }

  function localizarAbaAtivaAtual_v4() {
    return obterAbasSuperiores_v4().find(function (aba) {
      return aba.classList.contains("active") ||
        aba.classList.contains("is-active") ||
        aba.classList.contains("selected") ||
        aba.getAttribute("aria-selected") === "true";
    }) || null;
  }

  //###################################################################################
  // (4) MAPA DE NAVEGACAO LIMPA
  //###################################################################################

  function obterUrlLimpaParaAba_v4(aba) {
    const texto = obterTextoAba_v4(aba);

    const mapa = {
      utilizador: "/users/new?menu=administrativo&admin_tab=utilizador",
      entidade: "/users/new?menu=administrativo&admin_tab=entidade",
      menu: "/users/new?menu=administrativo&admin_tab=contas",
      sessoes: "/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card"
    };

    return mapa[texto] || "";
  }

  function obterAbaEsperadaPelaUrl_v4() {
    const parametros = obterParametrosUrl_v4();
    const adminTab = String(parametros.get("admin_tab") || "").trim().toLowerCase();
    const hash = String(window.location.hash || "").trim().toLowerCase();

    if (temContextoDeEdicaoMenu_v4()) {
      return "menu";
    }

    if (adminTab === "entidade") {
      return "entidade";
    }

    if (adminTab === "utilizador") {
      return "utilizador";
    }

    if (adminTab === "contas" && hash === "#admin-sidebar-sections-card") {
      return "sessoes";
    }

    if (adminTab === "contas" || adminTab === "definicoes") {
      return "menu";
    }

    return "";
  }

  function deveNavegarComRefreshLimpo_v4(aba) {
    if (!estaNoAdministrativo_v4()) {
      return false;
    }

    const urlLimpa = obterUrlLimpaParaAba_v4(aba);

    if (!urlLimpa) {
      return false;
    }

    const atual = String(window.location.pathname || "") +
      String(window.location.search || "") +
      String(window.location.hash || "");

    const destino = normalizarPathQueryHash_v4(urlLimpa);

    if (temContextoDeEdicaoMenu_v4()) {
      return atual !== destino;
    }

    const abaAtual = obterAbaEsperadaPelaUrl_v4();
    const abaDestino = obterTextoAba_v4(aba);

    if (abaAtual && abaDestino && abaAtual !== abaDestino) {
      return atual !== destino;
    }

    return false;
  }

  function navegarComRefreshLimpo_v4(aba) {
    const urlLimpa = obterUrlLimpaParaAba_v4(aba);

    if (!urlLimpa) {
      return false;
    }

    const destino = normalizarPathQueryHash_v4(urlLimpa);
    const atual = String(window.location.pathname || "") +
      String(window.location.search || "") +
      String(window.location.hash || "");

    if (atual === destino) {
      return false;
    }

    window.location.assign(urlLimpa);
    return true;
  }

  //###################################################################################
  // (5) ACTIVE UNICO
  //###################################################################################

  function limparActiveDasAbas_v4() {
    obterAbasSuperiores_v4().forEach(function (aba) {
      aba.classList.remove("active");
      aba.classList.remove("is-active");
      aba.classList.remove("selected");
      aba.setAttribute("aria-selected", "false");
    });
  }

  function aplicarActiveUnico_v4(abaAtiva) {
    if (!abaAtiva) {
      return;
    }

    applyingActiveV4 = true;

    limparActiveDasAbas_v4();

    abaAtiva.classList.add("active");
    abaAtiva.setAttribute("aria-selected", "true");

    window.setTimeout(function () {
      applyingActiveV4 = false;
    }, 0);
  }

  function aplicarActivePorTexto_v4(texto) {
    const aba = localizarAbaPorTexto_v4(texto);

    if (!aba) {
      return;
    }

    activeTabLabelV4 = obterTextoAba_v4(aba);
    aplicarActiveUnico_v4(aba);
  }

  function guardarAbaAtiva_v4(aba) {
    const texto = obterTextoAba_v4(aba);

    if (!texto) {
      return;
    }

    activeTabLabelV4 = texto;
  }

  //###################################################################################
  // (6) ACTIVE INICIAL
  //###################################################################################

  function aplicarActiveInicial_v4() {
    if (!estaNoAdministrativo_v4()) {
      return;
    }

    const abaEsperada = obterAbaEsperadaPelaUrl_v4();

    if (abaEsperada) {
      aplicarActivePorTexto_v4(abaEsperada);
      return;
    }

    if (activeTabLabelV4) {
      aplicarActivePorTexto_v4(activeTabLabelV4);
      return;
    }

    const abaAtivaAtual = localizarAbaAtivaAtual_v4();

    if (abaAtivaAtual) {
      guardarAbaAtiva_v4(abaAtivaAtual);
      aplicarActiveUnico_v4(abaAtivaAtual);
      return;
    }

    aplicarActivePorTexto_v4("menu");
  }

  //###################################################################################
  // (7) CLIQUE NAS ABAS
  //###################################################################################

  function tratarCliqueAbaSuperior_v4(event) {
    const container = obterContainerAbas_v4();

    if (!container) {
      return;
    }

    const aba = event.target.closest("a, button, .submenu-item");

    if (!aba || !container.contains(aba)) {
      return;
    }

    if (deveNavegarComRefreshLimpo_v4(aba)) {
      event.preventDefault();
      event.stopPropagation();

      if (typeof event.stopImmediatePropagation === "function") {
        event.stopImmediatePropagation();
      }

      navegarComRefreshLimpo_v4(aba);
      return;
    }

    guardarAbaAtiva_v4(aba);

    window.setTimeout(function () {
      aplicarActiveUnico_v4(aba);
    }, 0);

    window.setTimeout(function () {
      aplicarActiveUnico_v4(aba);
    }, 50);

    window.setTimeout(function () {
      aplicarActiveUnico_v4(aba);
    }, 150);
  }

  function ligarCliqueAbas_v4() {
    const container = obterContainerAbas_v4();

    if (!container || container.dataset.topMenuActiveBoundV4 === "1") {
      return;
    }

    container.dataset.topMenuActiveBoundV4 = "1";

    container.addEventListener("click", tratarCliqueAbaSuperior_v4, true);
  }

  //###################################################################################
  // (8) OBSERVAR ALTERACOES DINAMICAS
  //###################################################################################

  function reagirMudancaAbas_v4() {
    if (applyingActiveV4) {
      return;
    }

    if (observerTimerV4) {
      window.clearTimeout(observerTimerV4);
    }

    observerTimerV4 = window.setTimeout(function () {
      observerTimerV4 = null;

      ligarCliqueAbas_v4();

      if (activeTabLabelV4) {
        aplicarActivePorTexto_v4(activeTabLabelV4);
        return;
      }

      aplicarActiveInicial_v4();
    }, 20);
  }

  function observarAbasDinamicas_v4() {
    const container = obterContainerAbas_v4();

    if (!container || container.dataset.topMenuActiveObserverV4 === "1") {
      return;
    }

    container.dataset.topMenuActiveObserverV4 = "1";

    const observer = new MutationObserver(reagirMudancaAbas_v4);

    observer.observe(container, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "aria-selected"]
    });
  }

  //###################################################################################
  // (9) LIMPEZA DE CACHE VISUAL DO ADMINISTRATIVO
  //###################################################################################

  function limparEstadoVisualAdministrativo_v4() {
    if (!estaNoAdministrativo_v4()) {
      return;
    }

    try {
      window.__appverboTopMenuManualOverrideV2 = false;
    } catch (erro) {
    }
  }

  //###################################################################################
  // (10) INICIALIZACAO
  //###################################################################################

  function inicializar_v4() {
    limparEstadoVisualAdministrativo_v4();
    ligarCliqueAbas_v4();
    observarAbasDinamicas_v4();

    aplicarActiveInicial_v4();

    window.setTimeout(aplicarActiveInicial_v4, 100);
    window.setTimeout(aplicarActiveInicial_v4, 300);
    window.setTimeout(aplicarActiveInicial_v4, 700);
    window.setTimeout(aplicarActiveInicial_v4, 1200);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v4);
  } else {
    inicializar_v4();
  }

  window.addEventListener("popstate", function () {
    activeTabLabelV4 = "";
    aplicarActiveInicial_v4();
  });
})();
