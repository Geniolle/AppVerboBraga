// APPVERBO_MENU_RENDER_GUARD_V1_START
//###################################################################################
// (1) FUNCOES BASE
//###################################################################################

(function () {
  "use strict";

  let renderTimerV1 = null;

  function cleanValueV1(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeTextV1(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  function getCurrentUrlV1() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function isAdminPageV1(url) {
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      cleanValueV1(url.searchParams.get("menu")) === "administrativo"
    );
  }

  function isMenuPageV1() {
    const url = getCurrentUrlV1();

    if (!isAdminPageV1(url)) {
      return false;
    }

    const adminTab = cleanValueV1(url.searchParams.get("admin_tab"));
    const target = cleanValueV1(url.searchParams.get("target"));
    const hash = cleanValueV1((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV1(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const settingsEditKey = cleanValueV1(url.searchParams.get("settings_edit_key"));

    return (
      adminTab === "menu" ||
      settingsTab === "menu" ||
      settingsEditKey !== "" ||
      target === "settings-card" ||
      hash === "settings-card"
    );
  }

  function showElementV1(element) {
    if (!element || !element.style) {
      return;
    }

    element.style.setProperty("display", "block", "important");
    element.style.setProperty("visibility", "visible", "important");
    element.style.setProperty("opacity", "1", "important");
  }

  function hideElementV1(element) {
    if (!element || !element.style) {
      return;
    }

    element.style.setProperty("display", "none", "important");
  }

  //###################################################################################
  // (2) IDENTIFICAR CARDS DO MENU
  //###################################################################################

  function getMainContainerV1() {
    return (
      document.querySelector(".content .container") ||
      document.querySelector(".content") ||
      document.body
    );
  }

  function getAdminCardsV1() {
    const container = getMainContainerV1();

    if (!container) {
      return [];
    }

    return Array.from(container.querySelectorAll(".card, .admin-subprocess-card-v1"));
  }

  function isMenuTabsCardV1(card) {
    return Boolean(card && card.id === "menu-tabs-card");
  }

  function isHomeCardV1(card) {
    return Boolean(card && card.id === "home-summary-card");
  }

  function isMenuCardV1(card) {
    if (!card || isMenuTabsCardV1(card) || isHomeCardV1(card)) {
      return false;
    }

    const id = cleanValueV1(card.id);
    const subprocess = cleanValueV1(card.getAttribute("data-admin-subprocess"));
    const text = normalizeTextV1(card.textContent || "");

    return (
      subprocess === "menu" ||
      id === "settings-card" ||
      id.includes("settings-card") ||
      text.includes("menu") ||
      text.includes("configuracao do menu") ||
      text.includes("configuração do menu") ||
      text.includes("definicoes do menu") ||
      text.includes("definições do menu") ||
      text.includes("itens do menu") ||
      text.includes("processos do menu")
    );
  }

  function findCardAncestorV1(element) {
    let current = element;

    while (current && current !== document.body) {
      if (
        current.classList &&
        (
          current.classList.contains("card") ||
          current.classList.contains("admin-subprocess-card-v1") ||
          current.id === "settings-card"
        )
      ) {
        return current;
      }

      current = current.parentElement;
    }

    return null;
  }

  function findMenuCardsByTextV1() {
    const candidates = Array.from(
      document.querySelectorAll("h1, h2, h3, h4, button, summary, table, div")
    );

    const cards = [];

    candidates.forEach(function (element) {
      const text = normalizeTextV1(element.textContent || "");

      if (
        !text.includes("menu") &&
        !text.includes("configuracao") &&
        !text.includes("configuração") &&
        !text.includes("definicoes") &&
        !text.includes("definições")
      ) {
        return;
      }

      const card = findCardAncestorV1(element);

      if (card && !cards.includes(card) && !isMenuTabsCardV1(card)) {
        cards.push(card);
      }
    });

    return cards;
  }

  //###################################################################################
  // (3) MARCAR ABA MENU COMO ATIVA
  //###################################################################################

  function getTabFromElementV1(element) {
    if (!element) {
      return "";
    }

    const rawAdminTab = cleanValueV1(
      element.getAttribute("data-admin-tab") ||
      element.getAttribute("data-tab") ||
      element.getAttribute("data-admin-target") ||
      element.getAttribute("data-appverbo-subprocess-tab") ||
      ""
    );

    if (rawAdminTab === "menu") {
      return "menu";
    }

    if (rawAdminTab === "contas") {
      return "contas";
    }

    if (rawAdminTab === "entidade") {
      return "entidade";
    }

    if (rawAdminTab === "utilizador") {
      return "utilizador";
    }

    if (rawAdminTab === "sessoes") {
      return "sessoes";
    }

    const lookup = normalizeTextV1([
      element.textContent || "",
      element.id || "",
      element.className || "",
      element.getAttribute("title") || "",
      element.getAttribute("aria-label") || ""
    ].join(" "));

    if (lookup.includes("menu")) {
      return "menu";
    }

    if (lookup.includes("conta")) {
      return "contas";
    }

    if (lookup.includes("entidade")) {
      return "entidade";
    }

    if (lookup.includes("utilizador") || lookup.includes("usuario")) {
      return "utilizador";
    }

    if (lookup.includes("sessao") || lookup.includes("sessoes")) {
      return "sessoes";
    }

    return "";
  }

  function markMenuTabActiveV1() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu) {
      return;
    }

    const items = Array.from(
      submenu.querySelectorAll(".submenu-item, button, a, [data-admin-tab], [data-tab], [aria-controls]")
    );

    items.forEach(function (item) {
      const tab = getTabFromElementV1(item);
      const isActive = tab === "menu";

      item.classList.toggle("active", isActive);
      item.classList.toggle("selected", isActive);
      item.classList.toggle("is-active", isActive);
      item.setAttribute("aria-selected", isActive ? "true" : "false");

      if (isActive) {
        item.setAttribute("data-appverbo-menu-active", "true");
        item.setAttribute("data-appverbo-force-active", "true");
        item.removeAttribute("data-appverbo-menu-inactive");
        item.removeAttribute("data-appverbo-force-inactive");
      } else if (tab) {
        item.setAttribute("data-appverbo-menu-inactive", "true");
        item.setAttribute("data-appverbo-force-inactive", "true");
        item.removeAttribute("data-appverbo-menu-active");
        item.removeAttribute("data-appverbo-force-active");
        item.removeAttribute("data-active");
        item.removeAttribute("data-selected");
      }
    });
  }

  //###################################################################################
  // (4) NORMALIZAR URL DO MENU
  //###################################################################################

  function normalizeMenuUrlV1() {
    const url = getCurrentUrlV1();

    if (!isAdminPageV1(url)) {
      return;
    }

    let changed = false;

    if (cleanValueV1(url.searchParams.get("admin_tab")) !== "menu") {
      url.searchParams.set("admin_tab", "menu");
      changed = true;
    }

    if (!cleanValueV1(url.searchParams.get("settings_tab"))) {
      url.searchParams.set("settings_tab", "menu");
      changed = true;
    }

    if (cleanValueV1(url.searchParams.get("target")) !== "settings-card") {
      url.searchParams.set("target", "settings-card");
      changed = true;
    }

    if (cleanValueV1((url.hash || "").replace(/^#/, "")) !== "settings-card") {
      url.hash = "settings-card";
      changed = true;
    }

    if (changed && window.history && typeof window.history.replaceState === "function") {
      window.history.replaceState(
        window.history.state,
        document.title,
        url.pathname + url.search + url.hash
      );
    }
  }

  //###################################################################################
  // (5) RENDERIZAR MENU
  //###################################################################################

  function renderMenuV1() {
    if (!isMenuPageV1()) {
      if (document.body) {
        document.body.classList.remove("appverbo-menu-render-ok");
      }
      return;
    }

    normalizeMenuUrlV1();

    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    document.body.classList.remove("appverbo-admin-tab-entidade");
    document.body.classList.remove("appverbo-admin-tab-utilizador");
    document.body.classList.remove("appverbo-admin-tab-sessoes");
    document.body.classList.remove("appverbo-admin-tab-contas");
    document.body.classList.remove("appverbo-admin-sessoes");

    document.body.classList.add("appverbo-admin-subprocess-context");
    document.body.classList.add("appverbo-admin-submenu-stable");
    document.body.classList.add("appverbo-admin-tab-menu");
    document.body.classList.add("appverbo-menu-render-ok");
    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");

    const cards = getAdminCardsV1();
    let shownCount = 0;

    cards.forEach(function (card) {
      card.removeAttribute("data-appverbo-menu-card");
      card.removeAttribute("data-appverbo-not-menu-card");

      if (isMenuTabsCardV1(card)) {
        showElementV1(card);
        return;
      }

      if (isMenuCardV1(card)) {
        card.setAttribute("data-appverbo-menu-card", "true");
        showElementV1(card);
        shownCount += 1;
        return;
      }

      card.setAttribute("data-appverbo-not-menu-card", "true");
      hideElementV1(card);
    });

    if (shownCount === 0) {
      findMenuCardsByTextV1().forEach(function (card) {
        card.setAttribute("data-appverbo-menu-card", "true");
        showElementV1(card);
        shownCount += 1;
      });
    }

    const directCard = document.getElementById("settings-card");

    if (directCard) {
      directCard.setAttribute("data-appverbo-menu-card", "true");
      showElementV1(directCard);
      shownCount += 1;
    }

    markMenuTabActiveV1();

    if (shownCount === 0) {
      console.warn("[AppVerbo] Nenhum card do subprocesso Menu encontrado no DOM.");
    }
  }

  function renderMenuRepeatedV1() {
    renderMenuV1();

    [0, 30, 90, 180, 360, 700].forEach(function (delay) {
      window.setTimeout(renderMenuV1, delay);
    });

    if (renderTimerV1) {
      window.clearInterval(renderTimerV1);
    }

    let count = 0;

    renderTimerV1 = window.setInterval(function () {
      count += 1;

      if (!isMenuPageV1() || count > 20) {
        window.clearInterval(renderTimerV1);
        renderTimerV1 = null;
        return;
      }

      renderMenuV1();
    }, 120);
  }

  //###################################################################################
  // (6) INICIALIZAR E ESCUTAR CLIQUE EM MENU
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderMenuRepeatedV1, { once: true });
  } else {
    renderMenuRepeatedV1();
  }

  window.addEventListener("load", renderMenuRepeatedV1, { once: true });
  window.addEventListener("pageshow", renderMenuRepeatedV1);

  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(renderMenuRepeatedV1);
  });

  document.addEventListener("click", function (event) {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const clickedSubprocess = target.closest(
      "#submenu-items .submenu-item, #submenu-items button, #submenu-items a, #submenu-items [data-admin-tab], #submenu-items [aria-controls]"
    );

    if (!clickedSubprocess) {
      return;
    }

    const tab = getTabFromElementV1(clickedSubprocess);

    if (tab !== "menu") {
      return;
    }

    if (window.history && typeof window.history.pushState === "function") {
      const destination = "/users/new?menu=administrativo&admin_tab=menu&settings_tab=menu&target=settings-card#settings-card";
      const currentPath = window.location.pathname + window.location.search + window.location.hash;

      if (currentPath !== destination) {
        window.history.pushState(window.history.state, document.title, destination);
      }
    }

    window.setTimeout(renderMenuRepeatedV1, 0);
  }, true);
})();
// APPVERBO_MENU_RENDER_GUARD_V1_END
