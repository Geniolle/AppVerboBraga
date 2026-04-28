//###################################################################################
// APPVERBOBRAGA - MANTER ABA SUPERIOR MENU ATIVA AO EDITAR PROCESSO
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) LER URL
  //###################################################################################

  function obterParametrosUrl_v1() {
    try {
      return new URL(window.location.href).searchParams;
    } catch (erro) {
      return new URLSearchParams();
    }
  }

  //###################################################################################
  // (2) IDENTIFICAR SE ESTAMOS NO FLUXO ADMINISTRATIVO -> MENU
  //###################################################################################

  function estaNoFluxoAdministrativoMenu_v1() {
    const parametros = obterParametrosUrl_v1();

    const menuAtual = String(parametros.get("menu") || "").trim().toLowerCase();

    if (menuAtual !== "administrativo") {
      return false;
    }

    return (
      parametros.has("settings_edit_key") ||
      parametros.has("settings_action") ||
      parametros.has("settings_tab") ||
      parametros.has("settings_success") ||
      parametros.has("settings_error")
    );
  }

  //###################################################################################
  // (3) LOCALIZAR ABA SUPERIOR MENU
  //###################################################################################

  function obterAbasSuperiores_v1() {
    const container = document.getElementById("submenu-items");

    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll("a, button, .submenu-item"));
  }

  function normalizarTexto_v1(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function localizarAbaMenu_v1() {
    const abas = obterAbasSuperiores_v1();

    return abas.find(function (aba) {
      return normalizarTexto_v1(aba.textContent) === "menu";
    }) || null;
  }

  //###################################################################################
  // (4) APLICAR ACTIVE NA ABA MENU
  //###################################################################################

  function aplicarAbaMenuAtiva_v1() {
    if (!estaNoFluxoAdministrativoMenu_v1()) {
      return;
    }

    const abas = obterAbasSuperiores_v1();
    const abaMenu = localizarAbaMenu_v1();

    if (!abaMenu) {
      return;
    }

    abas.forEach(function (aba) {
      aba.classList.remove("active");
      aba.setAttribute("aria-selected", "false");
    });

    abaMenu.classList.add("active");
    abaMenu.setAttribute("aria-selected", "true");
  }

  //###################################################################################
  // (5) INICIALIZACAO
  //###################################################################################

  function inicializar_v1() {
    aplicarAbaMenuAtiva_v1();

    window.setTimeout(aplicarAbaMenuAtiva_v1, 100);
    window.setTimeout(aplicarAbaMenuAtiva_v1, 300);
    window.setTimeout(aplicarAbaMenuAtiva_v1, 700);
    window.setTimeout(aplicarAbaMenuAtiva_v1, 1200);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v1);
  } else {
    inicializar_v1();
  }

  window.addEventListener("popstate", aplicarAbaMenuAtiva_v1);
})();
