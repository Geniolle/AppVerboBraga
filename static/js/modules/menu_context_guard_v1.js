// APPVERBO_MENU_CONTEXT_GUARD_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  const MEU_PERFIL_MENU_KEY_V1 = "meu_perfil";
  const ADMINISTRATIVO_MENU_KEY_V1 = "administrativo";

  function normalizarTextoMenuContextGuard_v1(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterUrlAtualMenuContextGuard_v1() {
    try {
      return new URL(window.location.href);
    }
    catch (error) {
      return null;
    }
  }

  function obterParametroMenuContextGuard_v1(nome) {
    const url = obterUrlAtualMenuContextGuard_v1();

    if (!url) {
      return "";
    }

    return String(url.searchParams.get(nome) || "").trim().toLowerCase();
  }

  //###################################################################################
  // (2) DETETAR CONTEXTO REAL DO MEU PERFIL
  //###################################################################################

  function existeAreaRealMeuPerfil_v1() {
    const textoPagina = normalizarTextoMenuContextGuard_v1(
      document.body ? document.body.textContent : ""
    );

    return textoPagina.includes("dados pessoais do utilizador") &&
      textoPagina.includes("dados pessoais") &&
      textoPagina.includes("dados de agregados");
  }

  function urlEstaPresoNoAdministrativoMenuMeuPerfil_v1() {
    const menu = obterParametroMenuContextGuard_v1("menu");
    const adminTab = obterParametroMenuContextGuard_v1("admin_tab");
    const settingsEditKey = obterParametroMenuContextGuard_v1("settings_edit_key");

    return menu === ADMINISTRATIVO_MENU_KEY_V1 &&
      adminTab === "menu" &&
      settingsEditKey === MEU_PERFIL_MENU_KEY_V1;
  }

  function deveCorrigirContextoMeuPerfil_v1() {
    return urlEstaPresoNoAdministrativoMenuMeuPerfil_v1() &&
      existeAreaRealMeuPerfil_v1();
  }

  //###################################################################################
  // (3) LIMPAR CONTEXTO ANTIGO DE POS-GRAVACAO
  //###################################################################################

  function limparSessionStorageContextoAdministrativo_v1() {
    try {
      const keys = [];

      for (let index = 0; index < window.sessionStorage.length; index += 1) {
        const key = String(window.sessionStorage.key(index) || "");

        if (
          key.includes("appverbo:post-save-context") ||
          key.includes("appverbo:menu-context") ||
          key.includes("settings-menu-edit")
        ) {
          keys.push(key);
        }
      }

      keys.forEach(function (key) {
        window.sessionStorage.removeItem(key);
      });
    }
    catch (error) {
      // Sem acao: alguns browsers podem bloquear sessionStorage.
    }
  }

  //###################################################################################
  // (4) OCULTAR RAPIDAMENTE BLOCOS ADMINISTRATIVOS ANTES DO REDIRECT
  //###################################################################################

  function instalarEstiloAntiFlickerMeuPerfil_v1() {
    if (document.getElementById("appverbo-menu-context-guard-style-v1")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "appverbo-menu-context-guard-style-v1";
    style.textContent = [
      ".appverbo-context-stale-admin-v1 { display: none !important; }"
    ].join("\n");

    document.head.appendChild(style);
  }

  function contemTextoAlvoMenuContextGuard_v1(elemento, textosAlvo) {
    const texto = normalizarTextoMenuContextGuard_v1(elemento ? elemento.textContent : "");

    return textosAlvo.some(function (textoAlvo) {
      return texto.includes(textoAlvo);
    });
  }

  function localizarContainerSeguroMenuContextGuard_v1(elemento, textosAlvo) {
    let atual = elemento;

    while (atual && atual !== document.body) {
      const texto = normalizarTextoMenuContextGuard_v1(atual.textContent);
      const id = normalizarTextoMenuContextGuard_v1(atual.id);
      const classes = normalizarTextoMenuContextGuard_v1(atual.className);

      if (!contemTextoAlvoMenuContextGuard_v1(atual, textosAlvo)) {
        atual = atual.parentElement;
        continue;
      }

      if (
        classes.includes("card") ||
        id.includes("card") ||
        atual.tagName.toLowerCase() === "section" ||
        atual.tagName.toLowerCase() === "article"
      ) {
        return atual;
      }

      if (texto.length > 80 && texto.length < 5000) {
        return atual;
      }

      atual = atual.parentElement;
    }

    return null;
  }

  function ocultarBlocosAdministrativosPresos_v1() {
    instalarEstiloAntiFlickerMeuPerfil_v1();

    const textosAlvo = [
      "criar menu",
      "menus ativos",
      "menus inativos"
    ];

    const candidatos = Array.from(
      document.querySelectorAll("button, h1, h2, h3, h4, strong, p, div, section")
    );

    candidatos.forEach(function (elemento) {
      if (!contemTextoAlvoMenuContextGuard_v1(elemento, textosAlvo)) {
        return;
      }

      const container = localizarContainerSeguroMenuContextGuard_v1(elemento, textosAlvo);

      if (!container) {
        return;
      }

      const textoContainer = normalizarTextoMenuContextGuard_v1(container.textContent);

      if (textoContainer.includes("dados pessoais do utilizador")) {
        return;
      }

      container.classList.add("appverbo-context-stale-admin-v1");
    });
  }

  //###################################################################################
  // (5) REDIRECIONAR PARA URL CANONICA DO MEU PERFIL
  //###################################################################################

  function redirecionarParaMeuPerfilLimpo_v1() {
    limparSessionStorageContextoAdministrativo_v1();
    ocultarBlocosAdministrativosPresos_v1();

    const destino = "/users/new?menu=meu_perfil";
    const atual = window.location.pathname + window.location.search + window.location.hash;

    if (atual !== destino) {
      window.location.replace(destino);
    }
  }

  //###################################################################################
  // (6) INTERCETAR CLIQUE NO MENU LATERAL MEU PERFIL
  //###################################################################################

  function elementoEstaNoMenuLateral_v1(elemento) {
    if (!elemento || !elemento.closest) {
      return false;
    }

    return Boolean(
      elemento.closest("aside, nav, .sidebar, .app-sidebar, #sidebar, [data-sidebar]")
    );
  }

  function deveIntercetarCliqueMeuPerfil_v1(elemento) {
    if (!elementoEstaNoMenuLateral_v1(elemento)) {
      return false;
    }

    const texto = normalizarTextoMenuContextGuard_v1(elemento.textContent);
    const menuKey = normalizarTextoMenuContextGuard_v1(
      elemento.getAttribute("data-menu") ||
      elemento.getAttribute("data-menu-key") ||
      elemento.getAttribute("data-key") ||
      ""
    );

    return menuKey === MEU_PERFIL_MENU_KEY_V1 ||
      texto === "meu perfil" ||
      texto.includes("meu perfil");
  }

  function instalarInterceptadorCliqueMeuPerfil_v1() {
    document.addEventListener(
      "click",
      function (event) {
        const alvo = event.target && event.target.closest
          ? event.target.closest("a, button, [data-menu], [data-menu-key], [data-key], [role='button']")
          : null;

        if (!alvo) {
          return;
        }

        if (!deveIntercetarCliqueMeuPerfil_v1(alvo)) {
          return;
        }

        if (!urlEstaPresoNoAdministrativoMenuMeuPerfil_v1()) {
          return;
        }

        event.preventDefault();
        event.stopPropagation();

        redirecionarParaMeuPerfilLimpo_v1();
      },
      true
    );
  }

  //###################################################################################
  // (7) INICIAR
  //###################################################################################

  function iniciarMenuContextGuard_v1() {
    instalarInterceptadorCliqueMeuPerfil_v1();

    if (deveCorrigirContextoMeuPerfil_v1()) {
      redirecionarParaMeuPerfilLimpo_v1();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarMenuContextGuard_v1);
  }
  else {
    iniciarMenuContextGuard_v1();
  }

  window.addEventListener("pageshow", function () {
    if (deveCorrigirContextoMeuPerfil_v1()) {
      redirecionarParaMeuPerfilLimpo_v1();
    }
  });
})();
// APPVERBO_MENU_CONTEXT_GUARD_V1_END
