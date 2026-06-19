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

// APPVERBO_UTILIZADOR_EXIBIR_TOGGLE_V5_START
(function () {
  "use strict";

  if (window.__appverboUtilizadorExibirToggleV5Loaded) {
    return;
  }

  window.__appverboUtilizadorExibirToggleV5Loaded = true;

  const VIEW_PARAM = "user_view";
  const EDIT_ID_PARAM = "user_edit_id";
  const PANEL_MARKER = "data-appverbo-user-view-panel-v5";

  function normalize_v5(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function getParams_v5() {
    return new URLSearchParams(window.location.search || "");
  }

  function isUtilizadorPage_v5() {
    const params = getParams_v5();
    const path = normalize_v5(window.location.pathname);

    return (
      path.indexOf("/users/new") >= 0 ||
      params.get("admin_tab") === "utilizador" ||
      params.has(VIEW_PARAM) ||
      params.has(EDIT_ID_PARAM)
    );
  }

  function isViewMode_v5() {
    const params = getParams_v5();

    return (
      params.get(VIEW_PARAM) === "1" &&
      Boolean(params.get(EDIT_ID_PARAM))
    );
  }

  function textOf_v5(element) {
    if (!element) {
      return "";
    }

    return normalize_v5(
      element.textContent ||
      element.value ||
      element.getAttribute("aria-label") ||
      element.getAttribute("title") ||
      ""
    );
  }

  function hasTitle_v5(element) {
    const text = textOf_v5(element);

    return (
      text.indexOf("exibir utilizador") >= 0 ||
      text.indexOf("exibir usuário") >= 0 ||
      text.indexOf("exibir usuario") >= 0
    );
  }

  function hasReadonlyFields_v5(element) {
    const text = textOf_v5(element);

    return (
      text.indexOf("nome completo") >= 0 &&
      text.indexOf("telefone") >= 0 &&
      text.indexOf("email") >= 0 &&
      text.indexOf("estado da conta") >= 0
    );
  }

  function findTitleElement_v5() {
    const candidates = Array.from(
      document.querySelectorAll("h1,h2,h3,h4,h5,h6,legend,strong,b,span,div,p")
    );

    return candidates.find(function (element) {
      const text = textOf_v5(element);

      return (
        text === "exibir utilizador" ||
        text === "exibir usuário" ||
        text === "exibir usuario"
      );
    });
  }

  function findPanelFromTitle_v5(titleElement) {
    if (!titleElement) {
      return null;
    }

    let current = titleElement.parentElement;

    for (let level = 0; level < 14 && current && current !== document.body; level += 1) {
      if (hasTitle_v5(current) && hasReadonlyFields_v5(current)) {
        return current;
      }

      current = current.parentElement;
    }

    return null;
  }

  function buildClosedUrl_v5() {
    const url = new URL(window.location.href);

    url.searchParams.delete(VIEW_PARAM);
    url.searchParams.delete(EDIT_ID_PARAM);
    url.searchParams.delete("user_view_id");
    url.searchParams.delete("view_user_id");

    if (!url.searchParams.has("menu")) {
      url.searchParams.set("menu", "administrativo");
    }

    url.searchParams.set("admin_tab", "utilizador");

    return url.pathname + "?" + url.searchParams.toString() + url.hash;
  }

  function closePanel_v5(event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    window.location.href = buildClosedUrl_v5();
  }

  function bindCloseButtons_v5(panel) {
    if (!panel || panel.dataset.appverboUserViewCloseBoundV5 === "1") {
      return;
    }

    const controls = Array.from(
      panel.querySelectorAll("button, a, input[type='button'], input[type='submit']")
    );

    controls.forEach(function (control) {
      const text = textOf_v5(control);

      if (text === "fechar" || text.indexOf("fechar") >= 0) {
        control.addEventListener("click", closePanel_v5);
      }
    });

    panel.dataset.appverboUserViewCloseBoundV5 = "1";
  }

  function applyUserViewVisibility_v5() {
    if (!isUtilizadorPage_v5()) {
      return;
    }

    const titleElement = findTitleElement_v5();

    if (!titleElement) {
      return;
    }

    const panel = findPanelFromTitle_v5(titleElement);

    if (!panel) {
      return;
    }

    panel.setAttribute(PANEL_MARKER, "1");

    if (isViewMode_v5()) {
      panel.hidden = false;
      panel.style.removeProperty("display");
      panel.dataset.appverboUserViewOpenV5 = "1";
      bindCloseButtons_v5(panel);
      return;
    }

    panel.hidden = true;
    panel.style.display = "none";
    panel.dataset.appverboUserViewOpenV5 = "0";
  }

  function scheduleApply_v5() {
    window.clearTimeout(window.__appverboUtilizadorExibirToggleTimerV5);
    window.__appverboUtilizadorExibirToggleTimerV5 = window.setTimeout(applyUserViewVisibility_v5, 80);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyUserViewVisibility_v5);
  }
  else {
    applyUserViewVisibility_v5();
  }

  window.addEventListener("load", applyUserViewVisibility_v5);
  window.addEventListener("popstate", applyUserViewVisibility_v5);

  if (document.body && window.MutationObserver) {
    const observer = new MutationObserver(scheduleApply_v5);

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
})();
// APPVERBO_UTILIZADOR_EXIBIR_TOGGLE_V5_END
