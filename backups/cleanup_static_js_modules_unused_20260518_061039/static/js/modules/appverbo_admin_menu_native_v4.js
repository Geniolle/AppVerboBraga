// APPVERBO_ADMIN_MENU_NATIVE_V4_START
//###################################################################################
// (1) FUNCOES BASE
//###################################################################################

(function () {
  "use strict";

  const MENU_URL_V4 = "/users/new?menu=administrativo&admin_tab=menu&target=admin-menu-card#admin-menu-card";
  let renderTimerV4 = null;
  let observerV4 = null;

  function cleanValueV4(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeTextV4(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  function getCurrentUrlV4() {
    try {
      return new URL(window.location.href);
    } catch (error) {
      return null;
    }
  }

  function isAdminPageV4(url) {
    return Boolean(
      url &&
      url.pathname === "/users/new" &&
      cleanValueV4(url.searchParams.get("menu")) === "administrativo"
    );
  }

  function isMenuRouteV4() {
    const url = getCurrentUrlV4();

    if (!isAdminPageV4(url)) {
      return false;
    }

    const adminTab = cleanValueV4(url.searchParams.get("admin_tab"));
    const settingsTab = cleanValueV4(url.searchParams.get("settings_tab"));
    const target = cleanValueV4(url.searchParams.get("target"));
    const hash = cleanValueV4((url.hash || "").replace(/^#/, ""));

    return (
      adminTab === "menu" ||
      settingsTab === "menu" ||
      target === "admin-menu-card" ||
      hash === "admin-menu-card" ||
      target === "settings-menu-edit-card" ||
      hash === "settings-menu-edit-card"
    );
  }

  function showElementV4(element) {
    if (!element || !element.style) {
      return;
    }

    element.style.setProperty("display", "block", "important");
    element.style.setProperty("visibility", "visible", "important");
    element.style.setProperty("opacity", "1", "important");
  }

  function hideElementV4(element) {
    if (!element || !element.style) {
      return;
    }

    element.style.setProperty("display", "none", "important");
    element.style.setProperty("visibility", "hidden", "important");
    element.style.setProperty("opacity", "0", "important");
  }

  //###################################################################################
  // (2) IDENTIFICAR ABA MENU
  //###################################################################################

  function getTabFromElementV4(element) {
    if (!element) {
      return "";
    }

    const rawAdminTab = cleanValueV4(
      element.getAttribute("data-admin-tab") ||
      element.getAttribute("data-tab") ||
      element.getAttribute("data-admin-target") ||
      element.getAttribute("data-appverbo-subprocess-tab") ||
      ""
    );

    if (["menu", "entidade", "utilizador", "sessoes", "contas"].includes(rawAdminTab)) {
      return rawAdminTab;
    }

    const href = element.getAttribute("href") || "";
    if (href) {
      try {
        const hrefUrl = new URL(href, window.location.origin);
        const hrefAdminTab = cleanValueV4(hrefUrl.searchParams.get("admin_tab"));
        const hrefSettingsTab = cleanValueV4(hrefUrl.searchParams.get("settings_tab"));
        const hrefTarget = cleanValueV4(hrefUrl.searchParams.get("target"));

        if (
          hrefAdminTab === "menu" ||
          hrefSettingsTab === "menu" ||
          hrefTarget === "admin-menu-card" ||
          hrefTarget === "settings-menu-edit-card"
        ) {
          return "menu";
        }
      } catch (error) {
        // ignora href invalido
      }
    }

    const rawTarget = cleanValueV4(
      element.getAttribute("data-target") ||
      element.getAttribute("data-menu-target") ||
      element.getAttribute("aria-controls") ||
      ""
    ).replace(/^#/, "");

    if (rawTarget === "admin-menu-card" || rawTarget === "settings-menu-edit-card") {
      return "menu";
    }

    const lookup = normalizeTextV4([
      element.textContent || "",
      element.id || "",
      element.className || "",
      element.getAttribute("title") || "",
      element.getAttribute("aria-label") || ""
    ].join(" "));

    if (lookup === "menu" || lookup.includes("menu")) {
      return "menu";
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

    if (lookup.includes("conta")) {
      return "contas";
    }

    return "";
  }

  function getSubmenuItemsV4() {
    const submenu = document.getElementById("submenu-items");

    if (!submenu) {
      return [];
    }

    return Array.from(
      submenu.querySelectorAll(".submenu-item, button, a, [data-admin-tab], [data-tab], [aria-controls]")
    );
  }

  function normalizeMenuTabLinksV4() {
    getSubmenuItemsV4().forEach(function (item) {
      const tab = getTabFromElementV4(item);

      if (tab !== "menu") {
        return;
      }

      item.setAttribute("data-admin-tab", "menu");
      item.setAttribute("data-appverbo-subprocess-tab", "menu");

      if (item.tagName && item.tagName.toLowerCase() === "a") {
        item.setAttribute("href", MENU_URL_V4);
      }

      const link = item.closest && item.closest("a[href]");
      if (link) {
        link.setAttribute("href", MENU_URL_V4);
        link.setAttribute("data-admin-tab", "menu");
        link.setAttribute("data-appverbo-subprocess-tab", "menu");
      }
    });
  }

  function markMenuTabActiveV4() {
    getSubmenuItemsV4().forEach(function (item) {
      const tab = getTabFromElementV4(item);
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
  // (3) ISOLAR CARDS DO MENU
  //###################################################################################

  function getMainContainerV4() {
    return (
      document.querySelector(".content .container") ||
      document.querySelector(".content") ||
      document.querySelector("main") ||
      document.body
    );
  }

  function getCandidateCardsV4() {
    const container = getMainContainerV4();

    if (!container) {
      return [];
    }

    return Array.from(
      container.querySelectorAll(".card, .admin-subprocess-card-v1, section[id], div[id]")
    ).filter(function (element) {
      if (!element || !element.id) {
        return false;
      }

      if (
        element.id === "menu-tabs-card" ||
        element.id === "admin-menu-card" ||
        element.id === "admin-menu-card-inactive" ||
        element.id === "admin-menu-card-create" ||
        element.id === "settings-menu-edit-card"
      ) {
        return true;
      }

      return (
        element.classList.contains("card") ||
        element.classList.contains("admin-subprocess-card-v1") ||
        element.hasAttribute("data-admin-subprocess")
      );
    });
  }

  function isolateMenuCardsV4() {
    const createCard = document.getElementById("admin-menu-card-create");
    const activeCard = document.getElementById("admin-menu-card");
    const inactiveCard = document.getElementById("admin-menu-card-inactive");
    const editCard = document.getElementById("settings-menu-edit-card");
    const menuTabsCard = document.getElementById("menu-tabs-card");
    const showEditCard = /#settings-menu-edit-card$/i.test(window.location.hash || "") ||
      cleanValueV4(getCurrentUrlV4() && getCurrentUrlV4().searchParams.get("target")) === "settings-menu-edit-card";

    getCandidateCardsV4().forEach(function (card) {
      const isMenuCard = (
        card.id === "admin-menu-card" ||
        card.id === "admin-menu-card-inactive" ||
        card.id === "admin-menu-card-create" ||
        card.id === "settings-menu-edit-card"
      );

      if (card.id === "menu-tabs-card") {
        showElementV4(card);
        return;
      }

      if (!isMenuCard) {
        hideElementV4(card);
        return;
      }

      if (showEditCard) {
        if (card.id === "settings-menu-edit-card") {
          showElementV4(card);
        } else {
          hideElementV4(card);
        }
        return;
      }

      if (
        card.id === "admin-menu-card" ||
        card.id === "admin-menu-card-inactive" ||
        card.id === "admin-menu-card-create"
      ) {
        showElementV4(card);
        return;
      }

      hideElementV4(card);
    });

    showElementV4(menuTabsCard);
    if (showEditCard) {
      showElementV4(editCard);
      hideElementV4(createCard);
      hideElementV4(activeCard);
      hideElementV4(inactiveCard);
      return;
    }

    showElementV4(createCard);
    showElementV4(activeCard);
    showElementV4(inactiveCard);
    hideElementV4(editCard);
  }

  function normalizeMenuUrlV4(usePush) {
    const currentPath = window.location.pathname + window.location.search + window.location.hash;

    if (currentPath === MENU_URL_V4) {
      return;
    }

    if (!window.history) {
      return;
    }

    if (usePush && typeof window.history.pushState === "function") {
      window.history.pushState(window.history.state, document.title, MENU_URL_V4);
      return;
    }

    if (typeof window.history.replaceState === "function") {
      window.history.replaceState(window.history.state, document.title, MENU_URL_V4);
    }
  }

  function applyBodyClassesV4() {
    if (!document.body) {
      return;
    }

    document.body.classList.remove("appverbo-admin-process-only");
    document.body.classList.remove("appverbo-admin-sessoes");
    document.body.classList.remove("appverbo-admin-tab-entidade");
    document.body.classList.remove("appverbo-admin-tab-utilizador");
    document.body.classList.remove("appverbo-admin-tab-sessoes");
    document.body.classList.remove("appverbo-admin-tab-contas");
    document.body.classList.add("appverbo-admin-tab-menu");
    document.body.classList.add("appverbo-admin-subprocess-context");
    document.body.classList.add("appverbo-admin-submenu-stable");
    document.body.classList.add("appverbo-menu-native-ok");
    document.body.classList.remove("appverbo-booting");
    document.body.classList.add("appverbo-ready");
  }

  function renderMenuNativeV4(options) {
    const config = options || {};

    if (!isMenuRouteV4()) {
      if (document.body) {
        document.body.classList.remove("appverbo-menu-native-ok");
      }

      normalizeMenuTabLinksV4();
      return false;
    }

    normalizeMenuUrlV4(Boolean(config.pushUrl));
    normalizeMenuTabLinksV4();
    applyBodyClassesV4();
    isolateMenuCardsV4();
    markMenuTabActiveV4();

    return true;
  }

  function renderMenuNativeRepeatedV4(options) {
    renderMenuNativeV4(options);

    [0, 30, 90, 180, 360, 700, 1200].forEach(function (delay) {
      window.setTimeout(function () {
        renderMenuNativeV4(options);
      }, delay);
    });

    if (renderTimerV4) {
      window.clearInterval(renderTimerV4);
    }

    let count = 0;

    renderTimerV4 = window.setInterval(function () {
      count += 1;

      if (!isMenuRouteV4() || count > 25) {
        window.clearInterval(renderTimerV4);
        renderTimerV4 = null;
        return;
      }

      renderMenuNativeV4(options);
    }, 120);
  }

  //###################################################################################
  // (4) OBSERVAR DOM PARA NAO DEIXAR OUTROS CARDS VOLTAREM
  //###################################################################################

  function startObserverV4() {
    if (observerV4) {
      return;
    }

    const container = getMainContainerV4();

    if (!container) {
      return;
    }

    observerV4 = new MutationObserver(function () {
      if (!isMenuRouteV4()) {
        return;
      }

      window.requestAnimationFrame(function () {
        applyBodyClassesV4();
        isolateMenuCardsV4();
        markMenuTabActiveV4();
      });
    });

    observerV4.observe(container, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["style", "class", "data-admin-subprocess"]
    });
  }

  //###################################################################################
  // (5) INICIALIZAR E INTERCETAR CLIQUE NO MENU
  //###################################################################################

  function initV4() {
    normalizeMenuTabLinksV4();
    startObserverV4();

    if (isMenuRouteV4()) {
      renderMenuNativeRepeatedV4({ pushUrl: false });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initV4, { once: true });
  } else {
    initV4();
  }

  window.addEventListener("load", initV4, { once: true });
  window.addEventListener("pageshow", initV4);

  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(initV4);
  });

  ["pointerdown", "mousedown", "click"].forEach(function (eventName) {
    document.addEventListener(eventName, function (event) {
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

      const tab = getTabFromElementV4(clickedSubprocess);

      if (tab !== "menu") {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      if (typeof event.stopImmediatePropagation === "function") {
        event.stopImmediatePropagation();
      }

      normalizeMenuUrlV4(true);
      renderMenuNativeRepeatedV4({ pushUrl: false });
    }, true);
  });
})();
// APPVERBO_ADMIN_MENU_NATIVE_V4_END
