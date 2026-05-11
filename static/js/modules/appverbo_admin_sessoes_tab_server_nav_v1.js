/* APPVERBO_ADMIN_SESSOES_TAB_SERVER_NAV_V1_START */
//###################################################################################
// (1) FUNCOES BASE
//###################################################################################

(function () {
  "use strict";

  function normalizarTextoSessoesServerNav_v1(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/\s+/g, " ")
      .trim();
  }

  function obterUrlAtualSessoesServerNav_v1() {
    try {
      return new URL(String(window.location));
    }
    catch (erro) {
      return null;
    }
  }

  function montarUrlSessoesServerNav_v1() {
    var url = obterUrlAtualSessoesServerNav_v1();

    if (!url) {
      return "/users/new?menu=administrativo&admin_tab=sessoes";
    }

    url.pathname = "/users/new";
    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.delete("target");
    url.searchParams.delete("section");
    url.searchParams.delete("profile_section");
    url.searchParams.delete("dynamic_process_section");
    url.hash = "";

    return url.toString();
  }

  function estaNaAbaSessoesServerNav_v1() {
    var url = obterUrlAtualSessoesServerNav_v1();

    if (!url) {
      return false;
    }

    return url.searchParams.get("admin_tab") === "sessoes";
  }

  //###################################################################################
  // (2) LOCALIZAR ELEMENTOS DA ABA
  //###################################################################################

  function obterAreaAbasSessoesServerNav_v1() {
    return document.querySelector("#submenu-items") ||
      document.querySelector("#menu-tabs-card .menu-tabs") ||
      document.querySelector("#menu-tabs-card");
  }

  function obterElementoClicavelSessoesServerNav_v1(origem) {
    if (!origem || !origem.closest) {
      return null;
    }

    return origem.closest(
      "a, button, [role='tab'], [data-admin-tab], [data-tab], [data-menu-key], [data-menu-target], [data-menu-value], .menu-tab, .tab"
    );
  }

  function elementoEstaNaAreaAbasSessoesServerNav_v1(elemento) {
    var areaAbas = obterAreaAbasSessoesServerNav_v1();

    if (!elemento || !areaAbas) {
      return false;
    }

    return areaAbas === elemento || areaAbas.contains(elemento);
  }

  function obterTextoElementoSessoesServerNav_v1(elemento) {
    var partes = [];

    if (!elemento) {
      return "";
    }

    partes.push(elemento.textContent || "");
    partes.push(elemento.getAttribute("href") || "");
    partes.push(elemento.getAttribute("aria-label") || "");
    partes.push(elemento.getAttribute("title") || "");
    partes.push(elemento.getAttribute("data-admin-tab") || "");
    partes.push(elemento.getAttribute("data-tab") || "");
    partes.push(elemento.getAttribute("data-menu-key") || "");
    partes.push(elemento.getAttribute("data-menu-target") || "");
    partes.push(elemento.getAttribute("data-menu-value") || "");
    partes.push(elemento.id || "");
    partes.push(elemento.className || "");

    return normalizarTextoSessoesServerNav_v1(partes.join(" "));
  }

  function elementoRepresentaAbaSessoesServerNav_v1(elemento) {
    var texto;

    if (!elementoEstaNaAreaAbasSessoesServerNav_v1(elemento)) {
      return false;
    }

    texto = obterTextoElementoSessoesServerNav_v1(elemento);

    if (!texto) {
      return false;
    }

    return texto === "sessoes" ||
      texto.indexOf("sessoes") >= 0 ||
      texto.indexOf("admin_tab=sessoes") >= 0 ||
      texto.indexOf("admin-tab-sessoes") >= 0;
  }

  //###################################################################################
  // (3) APLICAR URL REAL NA ABA SESSOES
  //###################################################################################

  function aplicarUrlRealAbaSessoesServerNav_v1() {
    var areaAbas = obterAreaAbasSessoesServerNav_v1();
    var elementos;
    var destino;
    var indice;
    var elemento;

    if (!areaAbas) {
      return;
    }

    destino = montarUrlSessoesServerNav_v1();

    elementos = areaAbas.querySelectorAll(
      "a, button, [role='tab'], [data-admin-tab], [data-tab], [data-menu-key], [data-menu-target], [data-menu-value], .menu-tab, .tab"
    );

    for (indice = 0; indice < elementos.length; indice += 1) {
      elemento = elementos[indice];

      if (!elementoRepresentaAbaSessoesServerNav_v1(elemento)) {
        continue;
      }

      elemento.setAttribute("data-appverbo-sessoes-server-nav-v1", "1");
      elemento.setAttribute("data-appverbo-sessoes-url-v1", destino);

      if (elemento.tagName && elemento.tagName.toLowerCase() === "a") {
        elemento.setAttribute("href", destino);
      }
    }
  }

  //###################################################################################
  // (4) TRATAR CLIQUE DO UTILIZADOR SEM LOOP
  //###################################################################################

  function deveIgnorarCliqueSessoesServerNav_v1(evento) {
    if (!evento) {
      return true;
    }

    if (evento.defaultPrevented) {
      return false;
    }

    if (evento.button && evento.button !== 0) {
      return true;
    }

    if (evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) {
      return true;
    }

    return false;
  }

  function tratarCliqueAbaSessoesServerNav_v1(evento) {
    var clicavel;
    var destino;

    if (deveIgnorarCliqueSessoesServerNav_v1(evento)) {
      return;
    }

    clicavel = obterElementoClicavelSessoesServerNav_v1(evento.target);

    if (!elementoRepresentaAbaSessoesServerNav_v1(clicavel)) {
      return;
    }

    if (estaNaAbaSessoesServerNav_v1()) {
      return;
    }

    destino = montarUrlSessoesServerNav_v1();

    evento.preventDefault();
    evento.stopPropagation();

    if (typeof evento.stopImmediatePropagation === "function") {
      evento.stopImmediatePropagation();
    }

    window.location.assign(destino);
  }

  //###################################################################################
  // (5) OBSERVAR ABAS DINAMICAS SEM RELOAD AUTOMATICO
  //###################################################################################

  function iniciarObservadorSessoesServerNav_v1() {
    var alvo;

    aplicarUrlRealAbaSessoesServerNav_v1();

    alvo = document.querySelector("#submenu-items") || document.body;

    if (!alvo || !window.MutationObserver) {
      return;
    }

    new MutationObserver(function () {
      aplicarUrlRealAbaSessoesServerNav_v1();
    }).observe(alvo, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["href", "data-admin-tab", "data-tab", "data-menu-key", "data-menu-target"]
    });
  }

  document.addEventListener("click", tratarCliqueAbaSessoesServerNav_v1, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarObservadorSessoesServerNav_v1, { once: true });
  }
  else {
    iniciarObservadorSessoesServerNav_v1();
  }

  window.addEventListener("load", aplicarUrlRealAbaSessoesServerNav_v1, { once: true });
})();

/* APPVERBO_ADMIN_SESSOES_TAB_SERVER_NAV_V1_END */
