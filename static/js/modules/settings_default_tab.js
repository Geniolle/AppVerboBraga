//###################################################################################
// (1) REGRA DEFAULT - EDITAR PROCESSO ABRE NA PRIMEIRA ABA
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function obterUrlSegura(href) {
    try {
      return new URL(href, window.location.origin);
    } catch (error) {
      return null;
    }
  }

  function normalizarTexto(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function isUrlEdicaoProcesso(url) {
    if (!url) {
      return false;
    }

    const settingsEditKey = String(url.searchParams.get("settings_edit_key") || "").trim();
    const settingsAction = normalizarTexto(url.searchParams.get("settings_action"));

    if (!settingsEditKey) {
      return false;
    }

    if (!settingsAction) {
      return true;
    }

    return settingsAction === "edit";
  }

  function isUrlEdicaoMenuAdministrativo(url) {
    if (!isUrlEdicaoProcesso(url)) {
      return false;
    }

    return normalizarTexto(url.searchParams.get("admin_tab")) === "menu";
  }

  function aplicarAbaGeralNaUrl(url) {
    if (!isUrlEdicaoProcesso(url)) {
      return url;
    }

    url.searchParams.set("settings_tab", "geral");
    return url;
  }

  function montarHref(url) {
    return `${url.pathname}${url.search}${url.hash}`;
  }

  function isModifiedClick(event) {
    if (!event) {
      return false;
    }

    return Boolean(
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    );
  }

  function obterMenuAtualSeguranca() {
    try {
      const urlAtual = new URL(window.location.href);
      return normalizarTexto(urlAtual.searchParams.get("menu"));
    } catch (error) {
      return "";
    }
  }

  function normalizarContextoMenuNaUrl(url) {
    if (!isUrlEdicaoMenuAdministrativo(url)) {
      return url;
    }

    const menuDaUrl = normalizarTexto(url.searchParams.get("menu"));
    if (menuDaUrl) {
      return url;
    }

    const menuAtual = obterMenuAtualSeguranca();
    if (menuAtual === "administrativo" || menuAtual === "sessoes") {
      url.searchParams.set("menu", menuAtual);
      return url;
    }

    url.searchParams.set("menu", "sessoes");
    return url;
  }

  //###################################################################################
  // (3) AJUSTAR APENAS LINKS DE ENTRADA NA EDICAO
  //###################################################################################

  function ajustarLinksDeEntradaNaEdicao() {
    const links = document.querySelectorAll("a[href*='settings_edit_key=']");

    links.forEach(function (link) {
      const url = obterUrlSegura(link.getAttribute("href"));

      if (!isUrlEdicaoProcesso(url)) {
        return;
      }

      const novaUrl = normalizarContextoMenuNaUrl(aplicarAbaGeralNaUrl(url));
      link.setAttribute("href", montarHref(novaUrl));
    });
  }

  //###################################################################################
  // (4) AO CLICAR EM EDITAR, ABRIR SEMPRE NA ABA GERAL
  //###################################################################################

  document.addEventListener(
    "click",
    function (event) {
      const link = event.target.closest("a[href*='settings_edit_key=']");

      if (!link) {
        return;
      }

      const url = obterUrlSegura(link.getAttribute("href"));

      if (!isUrlEdicaoProcesso(url)) {
        return;
      }

      const novaUrl = normalizarContextoMenuNaUrl(aplicarAbaGeralNaUrl(url));
      link.setAttribute("href", montarHref(novaUrl));

      if (!isUrlEdicaoMenuAdministrativo(novaUrl) || isModifiedClick(event)) {
        return;
      }

      const destino = montarHref(novaUrl);
      const atual = `${window.location.pathname}${window.location.search}${window.location.hash}`;

      event.preventDefault();
      event.stopPropagation();

      if (typeof event.stopImmediatePropagation === "function") {
        event.stopImmediatePropagation();
      }

      if (destino === atual) {
        window.location.reload();
        return;
      }

      window.location.assign(destino);
    },
    true
  );

  //###################################################################################
  // (5) SOMENTE NO PRIMEIRO ACESSO A EDICAO SEM settings_tab, ASSUMIR GERAL
  //###################################################################################

  function garantirAbaGeralApenasNaEntrada() {
    const url = new URL(window.location.href);

    if (!isUrlEdicaoProcesso(url)) {
      return;
    }

    const settingsTabAtual = normalizarTexto(url.searchParams.get("settings_tab"));

    if (settingsTabAtual) {
      return;
    }

    url.searchParams.set("settings_tab", "geral");
    window.history.replaceState({}, "", montarHref(url));
  }

  //###################################################################################
  // (6) CLICAR NA ABA GERAL SOMENTE QUANDO A URL PEDE GERAL
  //###################################################################################

  function abrirAbaGeralSeForDefault() {
    const params = new URLSearchParams(window.location.search);
    const settingsEditKey = String(params.get("settings_edit_key") || "").trim();
    const settingsTab = normalizarTexto(params.get("settings_tab"));

    if (!settingsEditKey || settingsTab !== "geral") {
      return;
    }

    const card = document.querySelector("#settings-menu-edit-card") || document;

    const candidatos = Array.from(
      card.querySelectorAll("button, a, [role='tab'], [data-settings-tab], [data-tab], [data-tab-target]")
    );

    const abaGeral = candidatos.find(function (elemento) {
      if (!elemento || elemento.disabled) {
        return false;
      }

      const texto = normalizarTexto(elemento.textContent);
      const settingsTabAttr = normalizarTexto(elemento.getAttribute("data-settings-tab"));
      const dataTab = normalizarTexto(elemento.getAttribute("data-tab"));
      const dataTarget = normalizarTexto(elemento.getAttribute("data-tab-target"));

      return (
        texto === "geral" ||
        settingsTabAttr === "geral" ||
        dataTab === "geral" ||
        dataTarget.includes("geral")
      );
    });

    if (abaGeral && typeof abaGeral.click === "function") {
      abaGeral.click();
    }
  }

  //###################################################################################
  // (7) INICIALIZACAO
  //###################################################################################

  function inicializar() {
    ajustarLinksDeEntradaNaEdicao();
    garantirAbaGeralApenasNaEntrada();

    window.setTimeout(abrirAbaGeralSeForDefault, 50);
    window.setTimeout(abrirAbaGeralSeForDefault, 250);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar);
  } else {
    inicializar();
  }
})();
