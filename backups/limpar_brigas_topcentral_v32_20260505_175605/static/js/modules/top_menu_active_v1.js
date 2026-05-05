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
      sessoes: "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card"
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

    if (adminTab === "sessoes" ||
      String(parametros.get("sidebar_sections_tab") || "").trim().toLowerCase() === "sessoes" ||
      parametros.has("sidebar_section_edit_key")) {
      return "sessoes";
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

// APPVERBO_SESSOES_ABAS_ACIMA_V29_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoAbasSessoes_v7(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterUrlAtualAbasSessoes_v7() {
    try {
      return new URL(window.location.href);
    } catch (erro) {
      return null;
    }
  }

  function estaNoAdministrativoAbasSessoes_v7() {
    const url = obterUrlAtualAbasSessoes_v7();

    if (!url) {
      return false;
    }

    return normalizarTextoAbasSessoes_v7(url.searchParams.get("menu")) === "administrativo";
  }

  function contextoSessoesNaUrlAbasSessoes_v7() {
    const url = obterUrlAtualAbasSessoes_v7();

    if (!url) {
      return false;
    }

    const adminTab = normalizarTextoAbasSessoes_v7(url.searchParams.get("admin_tab"));
    const sidebarTab = normalizarTextoAbasSessoes_v7(url.searchParams.get("sidebar_sections_tab"));
    const hash = normalizarTextoAbasSessoes_v7(window.location.hash);

    return adminTab === "sessoes" ||
      sidebarTab === "sessoes" ||
      url.searchParams.has("sidebar_section_edit_key") ||
      hash === "#admin-sidebar-sections-card" ||
      hash === "#admin-sidebar-sections-form-card";
  }

  function obterUrlSessoesCorreta_v7() {
    return "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card";
  }

  //###################################################################################
  // (2) LOCALIZAR ABAS
  //###################################################################################

  function obterContainerAbasSessoes_v7() {
    return document.getElementById("submenu-items");
  }

  function obterCardAbasSessoes_v7() {
    return document.getElementById("menu-tabs-card");
  }

  function obterAbasSuperioresSessoes_v7() {
    const container = obterContainerAbasSessoes_v7();

    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll("a, button, .submenu-item, [role='tab']"));
  }

  function obterTextoAbaSessoes_v7(aba) {
    return normalizarTextoAbasSessoes_v7(aba ? aba.textContent : "");
  }

  function localizarAbaSessoes_v7() {
    return obterAbasSuperioresSessoes_v7().find(function (aba) {
      return obterTextoAbaSessoes_v7(aba) === "sessoes";
    }) || null;
  }

  //###################################################################################
  // (3) LOCALIZAR PRIMEIRO BLOCO DE SESSOES
  //###################################################################################

  function contemTextoSessoes_v7(elemento) {
    const texto = normalizarTextoAbasSessoes_v7(elemento ? elemento.textContent : "");

    return texto.indexOf("sessoes ativas") >= 0 ||
      texto.indexOf("sessoes do sidebar") >= 0 ||
      texto.indexOf("sessoes inativas") >= 0 ||
      texto.indexOf("criar sessao") >= 0 ||
      texto.indexOf("editar sessao") >= 0;
  }

  function obterPrimeiroCardSessoes_v7() {
    const porIdOuAtributo = document.querySelector('[data-admin-tab-pane="sessoes"]') ||
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card");

    if (porIdOuAtributo) {
      return porIdOuAtributo;
    }

    return Array.from(document.querySelectorAll("section.card, section, .card")).find(function (elemento) {
      return contemTextoSessoes_v7(elemento);
    }) || null;
  }

  //###################################################################################
  // (4) GARANTIR ABAS ACIMA DO BLOCO SESSOES
  //###################################################################################

  function garantirAbasAcimaDoBlocoSessoes_v7() {
    if (!estaNoAdministrativoAbasSessoes_v7()) {
      return;
    }

    const cardAbas = obterCardAbasSessoes_v7();
    const primeiroCardSessoes = obterPrimeiroCardSessoes_v7();

    if (!cardAbas || !primeiroCardSessoes || !primeiroCardSessoes.parentElement) {
      return;
    }

    if (cardAbas.nextElementSibling !== primeiroCardSessoes) {
      primeiroCardSessoes.parentElement.insertBefore(cardAbas, primeiroCardSessoes);
    }
  }

  //###################################################################################
  // (5) ACTIVE DA ABA SESSOES
  //###################################################################################

  function aplicarActiveSessoes_v7() {
    if (!estaNoAdministrativoAbasSessoes_v7() || !contextoSessoesNaUrlAbasSessoes_v7()) {
      return;
    }

    const abaSessoes = localizarAbaSessoes_v7();

    if (!abaSessoes) {
      return;
    }

    obterAbasSuperioresSessoes_v7().forEach(function (aba) {
      aba.classList.remove("active");
      aba.classList.remove("is-active");
      aba.classList.remove("selected");
      aba.setAttribute("aria-selected", "false");
    });

    abaSessoes.classList.add("active");
    abaSessoes.setAttribute("aria-selected", "true");
  }

  //###################################################################################
  // (6) CLIQUE NA ABA SESSOES
  //###################################################################################

  function tratarCliqueAbaSessoes_v7(event) {
    if (!estaNoAdministrativoAbasSessoes_v7()) {
      return;
    }

    const container = obterContainerAbasSessoes_v7();

    if (!container) {
      return;
    }

    const aba = event.target.closest("a, button, .submenu-item, [role='tab']");

    if (!aba || !container.contains(aba)) {
      return;
    }

    if (obterTextoAbaSessoes_v7(aba) !== "sessoes") {
      return;
    }

    const destino = obterUrlSessoesCorreta_v7();
    const atual = String(window.location.pathname || "") +
      String(window.location.search || "") +
      String(window.location.hash || "");

    event.preventDefault();
    event.stopPropagation();

    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }

    if (atual !== destino) {
      window.location.assign(destino);
      return;
    }

    aplicarCorrecaoSessoesAbas_v7();
  }

  //###################################################################################
  // (7) INICIALIZACAO
  //###################################################################################

  function aplicarCorrecaoSessoesAbas_v7() {
    garantirAbasAcimaDoBlocoSessoes_v7();
    aplicarActiveSessoes_v7();
  }

  function inicializarSessoesAbasAcima_v7() {
    if (window.__appverboSessoesAbasAcimaV29 === "1") {
      aplicarCorrecaoSessoesAbas_v7();
      return;
    }

    window.__appverboSessoesAbasAcimaV29 = "1";

    document.addEventListener("click", tratarCliqueAbaSessoes_v7, true);

    aplicarCorrecaoSessoesAbas_v7();

    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 80);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 180);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 420);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 820);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 1320);
    window.setTimeout(aplicarCorrecaoSessoesAbas_v7, 1820);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarSessoesAbasAcima_v7);
  } else {
    inicializarSessoesAbasAcima_v7();
  }

  window.addEventListener("popstate", aplicarCorrecaoSessoesAbas_v7);
  window.addEventListener("hashchange", aplicarCorrecaoSessoesAbas_v7);
})();
// APPVERBO_SESSOES_ABAS_ACIMA_V29_END

// APPVERBO_TOPCENTRAL_ANTES_CRIAR_V31_START
(function () {
  "use strict";

  //###################################################################################
  // (1) ESTADO
  //###################################################################################

  let aplicandoOrdemTopCentral_v31 = false;
  let observadorTopCentral_v31 = null;
  let timerTopCentral_v31 = null;

  //###################################################################################
  // (2) LOCALIZAR ESTRUTURA CENTRAL
  //###################################################################################

  function obterMainContentTopCentral_v31() {
    return document.querySelector("main.content");
  }

  function obterContainerCentralTopCentral_v31() {
    const main = obterMainContentTopCentral_v31();

    if (!main) {
      return null;
    }

    return main.querySelector(":scope > .container") ||
      main.querySelector(".container") ||
      null;
  }

  function obterCardTopCentral_v31() {
    return document.getElementById("menu-tabs-card");
  }

  function obterContainerAbasTopCentral_v31() {
    return document.getElementById("submenu-items");
  }

  //###################################################################################
  // (3) GARANTIR TOPCENTRAL ANTES DO BOTAO CRIAR
  //###################################################################################

  function garantirTopCentralPrimeiroCard_v31() {
    if (aplicandoOrdemTopCentral_v31) {
      return;
    }

    const container = obterContainerCentralTopCentral_v31();
    const cardTopCentral = obterCardTopCentral_v31();

    if (!container || !cardTopCentral) {
      return;
    }

    aplicandoOrdemTopCentral_v31 = true;

    try {
      if (cardTopCentral.parentElement !== container) {
        container.insertBefore(cardTopCentral, container.firstElementChild || null);
      }

      if (container.firstElementChild !== cardTopCentral) {
        container.insertBefore(cardTopCentral, container.firstElementChild || null);
      }
    } finally {
      window.setTimeout(function () {
        aplicandoOrdemTopCentral_v31 = false;
      }, 0);
    }
  }

  function reagendarGarantiaTopCentral_v31() {
    if (timerTopCentral_v31) {
      window.clearTimeout(timerTopCentral_v31);
    }

    timerTopCentral_v31 = window.setTimeout(function () {
      timerTopCentral_v31 = null;
      garantirTopCentralPrimeiroCard_v31();
    }, 20);
  }

  //###################################################################################
  // (4) GARANTIR URL CORRETA DA ABA SESSOES
  //###################################################################################

  function normalizarTextoTopCentral_v31(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterAbasSuperioresTopCentral_v31() {
    const containerAbas = obterContainerAbasTopCentral_v31();

    if (!containerAbas) {
      return [];
    }

    return Array.from(containerAbas.querySelectorAll("a, button, .submenu-item, [role='tab']"));
  }

  function obterTextoAbaTopCentral_v31(aba) {
    return normalizarTextoTopCentral_v31(aba ? aba.textContent : "");
  }

  function obterUrlSessoesTopCentral_v31() {
    return "/users/new?menu=administrativo&admin_tab=sessoes&sidebar_sections_tab=sessoes&target=admin-sidebar-sections-card#admin-sidebar-sections-card";
  }

  function tratarCliqueTopCentral_v31(event) {
    const containerAbas = obterContainerAbasTopCentral_v31();

    if (!containerAbas) {
      return;
    }

    const aba = event.target.closest("a, button, .submenu-item, [role='tab']");

    if (!aba || !containerAbas.contains(aba)) {
      return;
    }

    garantirTopCentralPrimeiroCard_v31();

    if (obterTextoAbaTopCentral_v31(aba) !== "sessoes") {
      return;
    }

    const destino = obterUrlSessoesTopCentral_v31();
    const atual = String(window.location.pathname || "") +
      String(window.location.search || "") +
      String(window.location.hash || "");

    event.preventDefault();
    event.stopPropagation();

    if (typeof event.stopImmediatePropagation === "function") {
      event.stopImmediatePropagation();
    }

    if (atual !== destino) {
      window.location.assign(destino);
    }
  }

  //###################################################################################
  // (5) OBSERVAR ALTERACOES DINAMICAS
  //###################################################################################

  function observarContainerTopCentral_v31() {
    const container = obterContainerCentralTopCentral_v31();

    if (!container || observadorTopCentral_v31) {
      return;
    }

    observadorTopCentral_v31 = new MutationObserver(function () {
      reagendarGarantiaTopCentral_v31();
    });

    observadorTopCentral_v31.observe(container, {
      childList: true,
      subtree: false
    });
  }

  //###################################################################################
  // (6) INICIALIZACAO
  //###################################################################################

  function inicializarTopCentralAntesCriar_v31() {
    document.addEventListener("click", tratarCliqueTopCentral_v31, true);

    garantirTopCentralPrimeiroCard_v31();
    observarContainerTopCentral_v31();

    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 50);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 120);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 250);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 500);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 900);
    window.setTimeout(garantirTopCentralPrimeiroCard_v31, 1500);
    window.setTimeout(observarContainerTopCentral_v31, 1600);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarTopCentralAntesCriar_v31);
  } else {
    inicializarTopCentralAntesCriar_v31();
  }

  window.addEventListener("popstate", garantirTopCentralPrimeiroCard_v31);
  window.addEventListener("hashchange", garantirTopCentralPrimeiroCard_v31);
  window.addEventListener("pageshow", garantirTopCentralPrimeiroCard_v31);
})();
// APPVERBO_TOPCENTRAL_ANTES_CRIAR_V31_END
