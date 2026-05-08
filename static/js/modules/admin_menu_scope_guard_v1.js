// APPVERBO_ADMIN_MENU_SCOPE_GUARD_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoAdminMenuScope_v1(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ");
  }

  function obterUrlAtualAdminMenuScope_v1() {
    try {
      return new URL(window.location.href);
    }
    catch (error) {
      return null;
    }
  }

  function obterMenuAtualAdminMenuScope_v1() {
    const url = obterUrlAtualAdminMenuScope_v1();

    if (!url) {
      return "";
    }

    return normalizarTextoAdminMenuScope_v1(url.searchParams.get("menu") || "");
  }

  function paginaMeuPerfilAdminMenuScope_v1() {
    const menuAtual = obterMenuAtualAdminMenuScope_v1();

    if (menuAtual === "meu_perfil") {
      return true;
    }

    const textoPagina = normalizarTextoAdminMenuScope_v1(document.body ? document.body.textContent : "");

    return textoPagina.includes("dados pessoais do utilizador") &&
      textoPagina.includes("meu perfil");
  }

  //###################################################################################
  // (2) DETETAR BLOCOS DO SUBPROCESSO ADMINISTRATIVO MENU
  //###################################################################################

  function elementoTemTextoMenuAdministrativo_v1(elemento) {
    const texto = normalizarTextoAdminMenuScope_v1(elemento ? elemento.textContent : "");

    return texto.includes("criar menu") ||
      texto.includes("menus ativos") ||
      texto.includes("menus inativos");
  }

  function elementoTemTextoMeuPerfilReal_v1(elemento) {
    const texto = normalizarTextoAdminMenuScope_v1(elemento ? elemento.textContent : "");

    return texto.includes("dados pessoais do utilizador") ||
      texto.includes("dados de agregados");
  }

  function localizarCardSeguroAdminMenuScope_v1(elemento) {
    let atual = elemento;

    while (atual && atual !== document.body) {
      const tag = String(atual.tagName || "").toLowerCase();
      const id = normalizarTextoAdminMenuScope_v1(atual.id || "");
      const classes = normalizarTextoAdminMenuScope_v1(atual.className || "");
      const texto = normalizarTextoAdminMenuScope_v1(atual.textContent || "");

      if (elementoTemTextoMeuPerfilReal_v1(atual)) {
        return null;
      }

      if (
        tag === "section" ||
        tag === "article" ||
        classes.includes("card") ||
        id.includes("card")
      ) {
        if (elementoTemTextoMenuAdministrativo_v1(atual)) {
          return atual;
        }
      }

      if (
        texto.length > 20 &&
        texto.length < 9000 &&
        elementoTemTextoMenuAdministrativo_v1(atual)
      ) {
        return atual;
      }

      atual = atual.parentElement;
    }

    return null;
  }

  function obterCardsMenuAdministrativo_v1() {
    const seletores = [
      "section",
      ".card",
      "article",
      "div",
      "h1",
      "h2",
      "h3",
      "button"
    ];

    const candidatos = Array.from(document.querySelectorAll(seletores.join(",")));
    const cards = [];
    const vistos = new Set();

    candidatos.forEach(function (elemento) {
      if (!elementoTemTextoMenuAdministrativo_v1(elemento)) {
        return;
      }

      const card = localizarCardSeguroAdminMenuScope_v1(elemento);

      if (!card || vistos.has(card)) {
        return;
      }

      vistos.add(card);
      cards.push(card);
    });

    return cards;
  }

  //###################################################################################
  // (3) OCULTAR BLOCOS NO MEU PERFIL
  //###################################################################################

  function instalarCssAdminMenuScope_v1() {
    if (document.getElementById("appverbo-admin-menu-scope-guard-style-v1")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "appverbo-admin-menu-scope-guard-style-v1";
    style.textContent = [
      ".appverbo-admin-menu-fora-do-escopo-v1 { display: none !important; visibility: hidden !important; height: 0 !important; min-height: 0 !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; border: 0 !important; }"
    ].join("\n");

    document.head.appendChild(style);
  }

  function ocultarMenuAdministrativoNoMeuPerfil_v1() {
    if (!paginaMeuPerfilAdminMenuScope_v1()) {
      return;
    }

    instalarCssAdminMenuScope_v1();

    obterCardsMenuAdministrativo_v1().forEach(function (card) {
      card.classList.add("appverbo-admin-menu-fora-do-escopo-v1");
      card.setAttribute("data-appverbo-hidden-reason-v1", "admin-menu-fora-do-meu-perfil");
    });
  }

  //###################################################################################
  // (4) CORRIGIR URL CASO VENHA COM CONTEXTO MISTO
  //###################################################################################

  function corrigirUrlMistaAdminMenuScope_v1() {
    const url = obterUrlAtualAdminMenuScope_v1();

    if (!url) {
      return;
    }

    const menuAtual = normalizarTextoAdminMenuScope_v1(url.searchParams.get("menu") || "");
    const adminTab = normalizarTextoAdminMenuScope_v1(url.searchParams.get("admin_tab") || "");
    const settingsEditKey = normalizarTextoAdminMenuScope_v1(url.searchParams.get("settings_edit_key") || "");

    if (
      menuAtual === "administrativo" &&
      adminTab === "menu" &&
      settingsEditKey === "meu_perfil"
    ) {
      window.location.replace("/users/new?menu=meu_perfil");
    }
  }

  //###################################################################################
  // (5) INICIAR SEM MUTATIONOBSERVER PARA EVITAR LOOP
  //###################################################################################

  function iniciarAdminMenuScopeGuard_v1() {
    corrigirUrlMistaAdminMenuScope_v1();
    ocultarMenuAdministrativoNoMeuPerfil_v1();

    window.setTimeout(ocultarMenuAdministrativoNoMeuPerfil_v1, 100);
    window.setTimeout(ocultarMenuAdministrativoNoMeuPerfil_v1, 400);
    window.setTimeout(ocultarMenuAdministrativoNoMeuPerfil_v1, 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarAdminMenuScopeGuard_v1);
  }
  else {
    iniciarAdminMenuScopeGuard_v1();
  }

  window.addEventListener("pageshow", iniciarAdminMenuScopeGuard_v1);
})();
// APPVERBO_ADMIN_MENU_SCOPE_GUARD_V1_END
