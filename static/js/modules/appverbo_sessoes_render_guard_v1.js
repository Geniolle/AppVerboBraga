// APPVERBO_SESSOES_RENDER_GUARD_V1_START
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

  function isSessoesPageV1() {
    const url = getCurrentUrlV1();

    if (!isAdminPageV1(url)) {
      return false;
    }

    const adminTab = cleanValueV1(url.searchParams.get("admin_tab"));
    const target = cleanValueV1(url.searchParams.get("target"));
    const hash = cleanValueV1((url.hash || "").replace(/^#/, ""));
    const settingsTab = cleanValueV1(url.searchParams.get("settings_tab")).replace(/_/g, "-");
    const sidebarSectionsTab = cleanValueV1(url.searchParams.get("sidebar_sections_tab")).replace(/_/g, "-");
    const sidebarSectionEditKey = cleanValueV1(url.searchParams.get("sidebar_section_edit_key"));

    return (
      adminTab === "sessoes" ||
      settingsTab === "sessoes" ||
      settingsTab === "sessoes-sidebar" ||
      sidebarSectionsTab === "sessoes" ||
      sidebarSectionsTab === "sessoes-sidebar" ||
      sidebarSectionEditKey !== "" ||
      target.includes("admin-sidebar-sections") ||
      target.includes("sidebar-sections") ||
      target.includes("sessoes") ||
      hash.includes("admin-sidebar-sections") ||
      hash.includes("sidebar-sections") ||
      hash.includes("sessoes")
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
  // (2) IDENTIFICAR CARDS
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

  function isSessoesCardV1(card) {
    if (!card || isMenuTabsCardV1(card) || isHomeCardV1(card)) {
      return false;
    }

    const id = cleanValueV1(card.id);
    const className = cleanValueV1(card.className);
    const subprocess = cleanValueV1(card.getAttribute("data-admin-subprocess"));
    const text = normalizeTextV1(card.textContent || "");

    return (
      subprocess === "sessoes" ||
      id.includes("admin-sidebar-sections") ||
      id.includes("sidebar-sections") ||
      className.includes("sidebar-sections") ||
      text.includes("criar sessao") ||
      text.includes("sessoes ativas") ||
      text.includes("sessoes inativas")
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
          current.id === "admin-sidebar-sections-card"
        )
      ) {
        return current;
      }

      current = current.parentElement;
    }

    return null;
  }

  function findSessoesCardsByTextV1() {
    const candidates = Array.from(
      document.querySelectorAll("h1, h2, h3, h4, button, summary, table, div")
    );

    const cards = [];

    candidates.forEach(function (element) {
      const text = normalizeTextV1(element.textContent || "");

      if (
        !text.includes("criar sessao") &&
        !text.includes("sessoes ativas") &&
        !text.includes("sessoes inativas")
      ) {
        return;
      }

      const card = findCardAncestorV1(element);

      if (card && !cards.includes(card)) {
        cards.push(card);
      }
    });

    return cards;
  }

  //###################################################################################
  // (3) MARCAR ABA SESSOES COMO ATIVA
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

    if (rawAdminTab) {
      if (rawAdminTab === "sessoes") {
        return "sessoes";
      }

      if (rawAdminTab === "entidade") {
        return "entidade";
      }

      if (rawAdminTab === "utilizador") {
        return "utilizador";
      }

      if (rawAdminTab === "contas" || rawAdminTab === "menu") {
        return "contas";
      }
    }

    const lookup = normalizeTextV1([
      element.textContent || "",
      element.id || "",
      element.className || "",
      element.getAttribute("title") || "",
      element.getAttribute("aria-label") || ""
    ].join(" "));

    if (lookup.includes("sessao") || lookup.includes("sessoes")) {
      return "sessoes";
    }

    if (lookup.includes("entidade")) {
      return "entidade";
    }

    if (lookup.includes("utilizador") || lookup.includes("usuario")) {
      return "utilizador";
    }

    if (lookup.includes("menu") || lookup.includes("conta")) {
      return "contas";
    }

    return "";
  }

  function markSessoesTabActiveV1() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu) {
      return;
    }

    const items = Array.from(
      submenu.querySelectorAll(".submenu-item, button, a, [data-admin-tab], [data-tab], [aria-controls]")
    );

    items.forEach(function (item) {
      const tab = getTabFromElementV1(item);
      const isActive = tab === "sessoes";

      item.classList.toggle("active", isActive);
      item.classList.toggle("selected", isActive);
      item.classList.toggle("is-active", isActive);
      item.setAttribute("aria-selected", isActive ? "true" : "false");

      if (isActive) {
        item.setAttribute("data-appverbo-force-active", "true");
        item.removeAttribute("data-appverbo-force-inactive");
      } else if (tab) {
        item.setAttribute("data-appverbo-force-inactive", "true");
        item.removeAttribute("data-appverbo-force-active");
        item.removeAttribute("data-active");
        item.removeAttribute("data-selected");
      }
    });
  }

  //###################################################################################
  // (4) RENDERIZAR SESSOES
  //###################################################################################

  function normalizeSessoesUrlV1() {
    const url = getCurrentUrlV1();

    if (!isAdminPageV1(url)) {
      return;
    }

    let changed = false;

    if (cleanValueV1(url.searchParams.get("admin_tab")) !== "sessoes") {
      url.searchParams.set("admin_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV1(url.searchParams.get("sidebar_sections_tab"))) {
      url.searchParams.set("sidebar_sections_tab", "sessoes");
      changed = true;
    }

    if (!cleanValueV1(url.searchParams.get("target"))) {
      url.searchParams.set("target", "admin-sidebar-sections-card");
      changed = true;
    }

    if (!url.hash) {
      url.hash = "admin-sidebar-sections-card";
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

  function renderSessoesV1() {
    if (!isSessoesPageV1()) {
      if (document.body) {
        document.body.classList.remove("appverbo-sessoes-render-ok");
      }
      return;
    }

    normalizeSessoesUrlV1();

    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    document.body.classList.remove("appverbo-admin-tab-entidade");
    document.body.classList.remove("appverbo-admin-tab-utilizador");
    document.body.classList.remove("appverbo-admin-tab-menu");
    document.body.classList.remove("appverbo-admin-tab-contas");

    document.body.classList.add("appverbo-admin-subprocess-context");
    document.body.classList.add("appverbo-admin-submenu-stable");
    document.body.classList.add("appverbo-admin-tab-sessoes");
    document.body.classList.add("appverbo-admin-sessoes");
    document.body.classList.add("appverbo-sessoes-render-ok");
    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");

    const cards = getAdminCardsV1();
    let shownCount = 0;

    cards.forEach(function (card) {
      card.removeAttribute("data-appverbo-sessoes-card");
      card.removeAttribute("data-appverbo-not-sessoes-card");

      if (isMenuTabsCardV1(card)) {
        showElementV1(card);
        return;
      }

      if (isSessoesCardV1(card)) {
        card.setAttribute("data-appverbo-sessoes-card", "true");
        showElementV1(card);
        shownCount += 1;
        return;
      }

      card.setAttribute("data-appverbo-not-sessoes-card", "true");
      hideElementV1(card);
    });

    if (shownCount === 0) {
      findSessoesCardsByTextV1().forEach(function (card) {
        card.setAttribute("data-appverbo-sessoes-card", "true");
        showElementV1(card);
        shownCount += 1;
      });
    }

    const directCard = document.getElementById("admin-sidebar-sections-card");

    if (directCard) {
      directCard.setAttribute("data-appverbo-sessoes-card", "true");
      showElementV1(directCard);
      shownCount += 1;
    }

    markSessoesTabActiveV1();

    if (shownCount === 0) {
      console.warn("[AppVerbo] Nenhum card de Sessoes encontrado no DOM.");
    }
  }

  function renderSessoesRepeatedV1() {
    renderSessoesV1();

    [0, 30, 90, 180, 360, 700].forEach(function (delay) {
      window.setTimeout(renderSessoesV1, delay);
    });

    if (renderTimerV1) {
      window.clearInterval(renderTimerV1);
    }

    let count = 0;

    renderTimerV1 = window.setInterval(function () {
      count += 1;

      if (!isSessoesPageV1() || count > 20) {
        window.clearInterval(renderTimerV1);
        renderTimerV1 = null;
        return;
      }

      renderSessoesV1();
    }, 120);
  }

  //###################################################################################
  // (5) INICIALIZAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderSessoesRepeatedV1, { once: true });
  } else {
    renderSessoesRepeatedV1();
  }

  window.addEventListener("load", renderSessoesRepeatedV1, { once: true });
  window.addEventListener("pageshow", renderSessoesRepeatedV1);

  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(renderSessoesRepeatedV1);
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

    if (tab !== "sessoes") {
      return;
    }

    window.setTimeout(renderSessoesRepeatedV1, 0);
  }, true);
})();
// APPVERBO_SESSOES_RENDER_GUARD_V1_END
