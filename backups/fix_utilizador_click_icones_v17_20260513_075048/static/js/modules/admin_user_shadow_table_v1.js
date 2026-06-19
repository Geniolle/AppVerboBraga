(function () {
  "use strict";

  function normalizeText(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function resolvePageSize(tableRoot) {
    const pageSizeSelect = tableRoot.querySelector("[data-admin-user-shadow-page-size]");
    const parsedValue = Number.parseInt(pageSizeSelect ? pageSizeSelect.value : "5", 10);

    if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
      return 5;
    }

    return parsedValue;
  }

  function updateTable(tableRoot) {
    const searchInput = tableRoot.querySelector("[data-admin-user-shadow-search]");
    const rows = Array.from(tableRoot.querySelectorAll("[data-admin-user-shadow-row]"));
    const currentPageLabel = tableRoot.querySelector("[data-admin-user-shadow-current-page]");
    const prevButton = tableRoot.querySelector("[data-admin-user-shadow-prev]");
    const nextButton = tableRoot.querySelector("[data-admin-user-shadow-next]");

    const query = normalizeText(searchInput ? searchInput.value : "");
    const pageSize = resolvePageSize(tableRoot);
    let currentPage = Number.parseInt(tableRoot.dataset.adminUserShadowPage || "1", 10);

    if (!Number.isFinite(currentPage) || currentPage <= 0) {
      currentPage = 1;
    }

    const matchingRows = rows.filter(function (row) {
      const rowText = normalizeText(row.textContent);
      return !query || rowText.includes(query);
    });

    const totalRows = matchingRows.length;
    const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));

    if (currentPage > totalPages) {
      currentPage = totalPages;
    }

    tableRoot.dataset.adminUserShadowPage = String(currentPage);

    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;

    rows.forEach(function (row) {
      row.hidden = true;
    });

    matchingRows.slice(startIndex, endIndex).forEach(function (row) {
      row.hidden = false;
    });

    if (currentPageLabel) {
      currentPageLabel.textContent = String(currentPage);
      currentPageLabel.classList.add("active");
      currentPageLabel.disabled = true;
    }

    if (prevButton) {
      prevButton.classList.remove("active");
      prevButton.disabled = currentPage <= 1;
    }

    if (nextButton) {
      nextButton.classList.remove("active");
      nextButton.disabled = currentPage >= totalPages;
    }
  }

  function initTable(tableRoot) {
    if (!tableRoot || tableRoot.dataset.adminUserShadowReady === "1") {
      return;
    }

    tableRoot.dataset.adminUserShadowReady = "1";
    tableRoot.dataset.adminUserShadowPage = "1";

    const searchInput = tableRoot.querySelector("[data-admin-user-shadow-search]");
    const pageSizeSelect = tableRoot.querySelector("[data-admin-user-shadow-page-size]");
    const prevButton = tableRoot.querySelector("[data-admin-user-shadow-prev]");
    const nextButton = tableRoot.querySelector("[data-admin-user-shadow-next]");

    if (searchInput) {
      searchInput.addEventListener("input", function () {
        tableRoot.dataset.adminUserShadowPage = "1";
        updateTable(tableRoot);
      });
    }

    if (pageSizeSelect) {
      pageSizeSelect.addEventListener("change", function () {
        tableRoot.dataset.adminUserShadowPage = "1";
        updateTable(tableRoot);
      });
    }

    if (prevButton) {
      prevButton.addEventListener("click", function () {
        const currentPage = Number.parseInt(tableRoot.dataset.adminUserShadowPage || "1", 10);
        tableRoot.dataset.adminUserShadowPage = String(Math.max(1, currentPage - 1));
        updateTable(tableRoot);
      });
    }

    if (nextButton) {
      nextButton.addEventListener("click", function () {
        const currentPage = Number.parseInt(tableRoot.dataset.adminUserShadowPage || "1", 10);
        tableRoot.dataset.adminUserShadowPage = String(currentPage + 1);
        updateTable(tableRoot);
      });
    }

    updateTable(tableRoot);
  }

  function buildUserActionUrl(action, userId) {
    const cleanUserId = String(userId || "").trim();

    if (!cleanUserId) {
      return "";
    }

    const userViewValue = action === "view" ? "1" : "0";

    return "/users/new"
      + "?menu=administrativo"
      + "&admin_tab=utilizador"
      + "&user_edit_id=" + encodeURIComponent(cleanUserId)
      + "&user_view=" + userViewValue
      + "&target=edit-user-card"
      + "#edit-user-card";
  }

  function forceNativeActionNavigation(event) {
    const actionLink = event.target.closest(
      "#admin-user-shadow-readonly-card [data-admin-user-shadow-real-link]"
    );

    if (!actionLink) {
      return;
    }

    const action = actionLink.getAttribute("data-admin-user-shadow-real-link");
    const userId = actionLink.getAttribute("data-admin-user-shadow-user-id");
    const explicitUrl = buildUserActionUrl(action, userId);
    const fallbackUrl = actionLink.getAttribute("href") || actionLink.href;
    const targetUrl = explicitUrl || fallbackUrl;

    if (!targetUrl) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    window.location.href = targetUrl;
  }

  function findCreateActionsCard() {
    const cards = Array.from(document.querySelectorAll(".card"));

    return cards.find(function (card) {
      const text = normalizeText(card.textContent);
      return text.includes("criar utilizador") && text.includes("gerar link");
    }) || null;
  }

  function moveCreateActionsCardToTop() {
    const params = new URLSearchParams(window.location.search);

    if (params.get("menu") !== "administrativo" || params.get("admin_tab") !== "utilizador") {
      return;
    }

    const shadowCard = document.getElementById("admin-user-shadow-readonly-card");
    const actionsCard = findCreateActionsCard();

    if (!shadowCard || !actionsCard || actionsCard === shadowCard) {
      return;
    }

    actionsCard.classList.add("admin-user-actions-top-card-v1");

    if (actionsCard.nextElementSibling === shadowCard) {
      return;
    }

    shadowCard.parentNode.insertBefore(actionsCard, shadowCard);
  }

  function focusEditUserCardFromQuery() {
    const params = new URLSearchParams(window.location.search);

    if (params.get("menu") !== "administrativo") {
      return;
    }

    if (params.get("admin_tab") !== "utilizador") {
      return;
    }

    if (!params.get("user_edit_id")) {
      return;
    }

    const editCard = document.getElementById("edit-user-card");

    if (!editCard) {
      console.warn("APPVERBO_UTILIZADOR_FOCUS_DEBUG_V1 edit-user-card não encontrado.");
      return;
    }

    editCard.hidden = false;
    editCard.removeAttribute("hidden");
    editCard.style.display = "";

    window.setTimeout(function () {
      editCard.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 120);
  }

  function initAll() {
    document
      .querySelectorAll("[data-admin-user-shadow-table]")
      .forEach(initTable);

    moveCreateActionsCardToTop();
    focusEditUserCardFromQuery();

    window.setTimeout(moveCreateActionsCardToTop, 250);
    window.setTimeout(focusEditUserCardFromQuery, 350);
  }

  document.addEventListener("click", forceNativeActionNavigation, true);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();

// APPVERBO_UTILIZADOR_ACTION_ICON_CLICK_V16_START
(function () {
  "use strict";

  if (window.__appverboUtilizadorActionIconClickV16Loaded) {
    return;
  }

  window.__appverboUtilizadorActionIconClickV16Loaded = true;

  function parseUserActionUrl_v16(href) {
    try {
      return new URL(href, window.location.origin);
    }
    catch (error) {
      return null;
    }
  }

  function isUtilizadorActionUrl_v16(url) {
    if (!url) {
      return false;
    }

    return (
      url.pathname === "/users/new" &&
      url.searchParams.get("menu") === "administrativo" &&
      url.searchParams.get("admin_tab") === "utilizador" &&
      url.searchParams.has("user_edit_id") &&
      url.searchParams.has("user_view")
    );
  }

  function findActionAnchor_v16(target) {
    if (!target || !target.closest) {
      return null;
    }

    const anchor = target.closest("a[href]");

    if (!anchor) {
      return null;
    }

    const url = parseUserActionUrl_v16(anchor.getAttribute("href"));

    if (!isUtilizadorActionUrl_v16(url)) {
      return null;
    }

    return anchor;
  }

  function navigateToUserAction_v16(event) {
    const anchor = findActionAnchor_v16(event.target);

    if (!anchor) {
      return;
    }

    const href = anchor.getAttribute("href");

    if (!href) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    window.location.assign(href);
  }

  document.addEventListener("click", navigateToUserAction_v16, true);
})();
// APPVERBO_UTILIZADOR_ACTION_ICON_CLICK_V16_END
