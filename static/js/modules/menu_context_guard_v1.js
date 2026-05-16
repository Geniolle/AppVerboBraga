// APPVERBO_MENU_CONTEXT_GUARD_V2_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO DE PARAMETROS
  //###################################################################################

  function normalizarTextoMenuContextV2(valor) {
    return String(valor || "").trim().toLowerCase();
  }

  function lerUrlMenuContextV2() {
    try {
      return new URL(window.location.href);
    } catch (erro) {
      return null;
    }
  }

  function lerParametroMenuContextV2(url, nome) {
    if (!url) {
      return "";
    }

    return normalizarTextoMenuContextV2(url.searchParams.get(nome) || "");
  }

  //###################################################################################
  // (2) CORRIGIR CONTEXTO LEGADO PRESO EM MENU > MEU PERFIL
  //###################################################################################

  function urlPresaNoMenuMeuPerfilV2(url) {
    if (!url) {
      return false;
    }

    const menu = lerParametroMenuContextV2(url, "menu");
    const adminTab = lerParametroMenuContextV2(url, "admin_tab");
    const settingsEditKey = lerParametroMenuContextV2(url, "settings_edit_key");
    const settingsAction = lerParametroMenuContextV2(url, "settings_action");

    return (
      menu === "administrativo" &&
      adminTab === "menu" &&
      settingsEditKey === "meu_perfil" &&
      !settingsAction
    );
  }

  function redirecionarParaMeuPerfilCanonicoV2() {
    const destino = "/users/new?menu=meu_perfil";
    const atual = window.location.pathname + window.location.search + window.location.hash;

    if (atual !== destino) {
      window.location.replace(destino);
    }
  }

  function aplicarMenuContextGuardV2() {
    const url = lerUrlMenuContextV2();

    if (urlPresaNoMenuMeuPerfilV2(url)) {
      redirecionarParaMeuPerfilCanonicoV2();
    }
  }

  //###################################################################################
  // (3) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", aplicarMenuContextGuardV2, {
      once: true
    });
  } else {
    aplicarMenuContextGuardV2();
  }

  window.addEventListener("pageshow", aplicarMenuContextGuardV2);
})();
// APPVERBO_MENU_CONTEXT_GUARD_V2_END
