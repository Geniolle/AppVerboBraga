// APPVERBO_ADMIN_MENU_SCOPE_GUARD_V2_START
(function () {
  "use strict";

  //###################################################################################
  // (1) LEITURA DE CONTEXTO DA URL
  //###################################################################################

  function normalizarTextoScopeGuardV2(valor) {
    return String(valor || "").trim().toLowerCase();
  }

  function lerParametroScopeGuardV2(nome) {
    try {
      const urlAtual = new URL(window.location.href);
      return normalizarTextoScopeGuardV2(urlAtual.searchParams.get(nome) || "");
    } catch (erro) {
      return "";
    }
  }

  function contextoMenuAdministrativoAtivoV2() {
    return (
      lerParametroScopeGuardV2("menu") === "administrativo" &&
      lerParametroScopeGuardV2("admin_tab") === "menu"
    );
  }

  function shouldBypassScopeGuardV2() {
    return Boolean(
      document.querySelector("script[src*='appverbo_navigation_smooth_v7.js']")
    );
  }

  //###################################################################################
  // (2) APLICAR VISIBILIDADE APENAS NOS CARDS DO SUBPROCESSO MENU
  //###################################################################################

  function obterCardsMenuAdministrativoV2() {
    return [
      document.getElementById("admin-menu-card-create"),
      document.getElementById("admin-menu-card"),
      document.getElementById("admin-menu-card-inactive"),
      document.getElementById("settings-menu-edit-card")
    ].filter(Boolean);
  }

  function aplicarEscopoMenuAdministrativoV2() {
    if (shouldBypassScopeGuardV2()) {
      return;
    }

    const menuAtivo = contextoMenuAdministrativoAtivoV2();
    const cards = obterCardsMenuAdministrativoV2();

    cards.forEach(function (card) {
      if (menuAtivo) {
        card.removeAttribute("hidden");
        card.style.removeProperty("display");
        card.style.removeProperty("visibility");
        card.style.removeProperty("opacity");
      } else {
        card.setAttribute("hidden", "hidden");
        card.style.setProperty("display", "none", "important");
      }
    });
  }

  //###################################################################################
  // (3) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", aplicarEscopoMenuAdministrativoV2, {
      once: true
    });
  } else {
    aplicarEscopoMenuAdministrativoV2();
  }

  window.addEventListener("pageshow", aplicarEscopoMenuAdministrativoV2);
})();
// APPVERBO_ADMIN_MENU_SCOPE_GUARD_V2_END
