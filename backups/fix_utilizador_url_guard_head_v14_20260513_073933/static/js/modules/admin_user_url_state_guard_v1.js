(function () {
  "use strict";

  if (window.__appverboAdminUserUrlStateGuardV13Loaded) {
    return;
  }

  window.__appverboAdminUserUrlStateGuardV13Loaded = true;

  const CANONICAL_USER_LIST_URL = "/users/new?menu=administrativo&admin_tab=utilizador";

  function normalize_v13(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function parseUrl_v13(href) {
    try {
      return new URL(href, window.location.origin);
    }
    catch (error) {
      return null;
    }
  }

  function textOf_v13(element) {
    if (!element) {
      return "";
    }

    return normalize_v13(
      element.textContent ||
      element.value ||
      element.getAttribute("aria-label") ||
      element.getAttribute("title") ||
      ""
    );
  }

  function isUserActionUrl_v13(url) {
    if (!url) {
      return false;
    }

    return (
      url.searchParams.has("user_edit_id") ||
      url.searchParams.has("user_view") ||
      url.searchParams.has("user_view_id") ||
      url.searchParams.has("view_user_id") ||
      url.searchParams.get("target") === "edit-user-card" ||
      url.hash === "#edit-user-card"
    );
  }

  function isInsideUserActionArea_v13(element) {
    if (!element) {
      return false;
    }

    return Boolean(
      element.closest("#edit-user-card") ||
      element.closest("[data-admin-user-shadow-table]") ||
      element.closest(".table-actions") ||
      element.closest(".actions") ||
      element.closest("td") ||
      element.closest("form")
    );
  }

  function isUtilizadorNavigationControl_v13(element) {
    if (!element) {
      return false;
    }

    if (isInsideUserActionArea_v13(element)) {
      return false;
    }

    const href = element.getAttribute("href");
    const url = href ? parseUrl_v13(href) : null;

    if (isUserActionUrl_v13(url)) {
      return false;
    }

    const text = textOf_v13(element);
    const role = normalize_v13(element.getAttribute("role"));
    const adminTab = normalize_v13(element.getAttribute("data-admin-tab"));
    const tab = normalize_v13(element.getAttribute("data-tab"));
    const subprocess = normalize_v13(element.getAttribute("data-subprocess"));
    const subprocessKey = normalize_v13(element.getAttribute("data-subprocess-key"));
    const target = normalize_v13(element.getAttribute("data-target"));

    const isExactText =
      text === "utilizador" ||
      text === "utilizadores";

    const isDataNavigation =
      adminTab === "utilizador" ||
      tab === "utilizador" ||
      subprocess === "utilizador" ||
      subprocessKey === "utilizador" ||
      target === "utilizador";

    const isTabNavigation =
      role === "tab" &&
      isExactText;

    const isCleanUtilizadorUrl =
      Boolean(url) &&
      url.pathname === "/users/new" &&
      url.searchParams.get("admin_tab") === "utilizador" &&
      !isUserActionUrl_v13(url);

    return isExactText || isDataNavigation || isTabNavigation || isCleanUtilizadorUrl;
  }

  function handleClick_v13(event) {
    const control = event.target.closest(
      "a[href],button,[role='tab'],[data-admin-tab],[data-tab],[data-subprocess],[data-subprocess-key],[data-target]"
    );

    if (!control) {
      return;
    }

    if (!isUtilizadorNavigationControl_v13(control)) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    window.location.assign(CANONICAL_USER_LIST_URL);
  }

  document.addEventListener("click", handleClick_v13, true);
})();
