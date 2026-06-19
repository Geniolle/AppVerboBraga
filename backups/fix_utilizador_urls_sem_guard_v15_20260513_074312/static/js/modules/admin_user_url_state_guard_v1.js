(function () {
  "use strict";

  if (window.__appverboAdminUserUrlStateGuardV14Loaded) {
    return;
  }

  window.__appverboAdminUserUrlStateGuardV14Loaded = true;

  const CANONICAL_USER_LIST_URL = "/users/new?menu=administrativo&admin_tab=utilizador";

  function normalize_v14(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function parseUrl_v14(href) {
    try {
      return new URL(href, window.location.origin);
    }
    catch (error) {
      return null;
    }
  }

  function textOf_v14(element) {
    if (!element) {
      return "";
    }

    return normalize_v14(
      element.textContent ||
      element.value ||
      element.getAttribute("aria-label") ||
      element.getAttribute("title") ||
      ""
    );
  }

  function isUserActionUrl_v14(url) {
    if (!url) {
      return false;
    }

    return (
      url.pathname === "/users/new" &&
      url.searchParams.get("admin_tab") === "utilizador" &&
      (
        url.searchParams.has("user_edit_id") ||
        url.searchParams.has("user_view") ||
        url.searchParams.get("target") === "edit-user-card" ||
        url.hash === "#edit-user-card"
      )
    );
  }

  function isCleanUtilizadorUrl_v14(url) {
    if (!url) {
      return false;
    }

    return (
      url.pathname === "/users/new" &&
      url.searchParams.get("menu") === "administrativo" &&
      url.searchParams.get("admin_tab") === "utilizador" &&
      !isUserActionUrl_v14(url)
    );
  }

  function isUtilizadorNavigationControl_v14(element) {
    if (!element) {
      return false;
    }

    const href = element.getAttribute("href");
    const url = href ? parseUrl_v14(href) : null;

    if (isUserActionUrl_v14(url)) {
      return false;
    }

    if (element.closest("#edit-user-card")) {
      return false;
    }

    if (element.closest("td") || element.closest("form")) {
      return false;
    }

    const text = textOf_v14(element);
    const role = normalize_v14(element.getAttribute("role"));
    const adminTab = normalize_v14(element.getAttribute("data-admin-tab"));
    const tab = normalize_v14(element.getAttribute("data-tab"));
    const subprocess = normalize_v14(element.getAttribute("data-subprocess"));
    const subprocessKey = normalize_v14(element.getAttribute("data-subprocess-key"));
    const target = normalize_v14(element.getAttribute("data-target"));

    const isExactText = text === "utilizador" || text === "utilizadores";

    const isDataNavigation =
      adminTab === "utilizador" ||
      tab === "utilizador" ||
      subprocess === "utilizador" ||
      subprocessKey === "utilizador" ||
      target === "utilizador";

    const isTabNavigation = role === "tab" && isExactText;

    return (
      isExactText ||
      isDataNavigation ||
      isTabNavigation ||
      isCleanUtilizadorUrl_v14(url)
    );
  }

  function handleClick_v14(event) {
    const actionLink = event.target.closest("a[href]");

    if (actionLink) {
      const actionUrl = parseUrl_v14(actionLink.getAttribute("href"));

      if (isUserActionUrl_v14(actionUrl)) {
        return;
      }
    }

    const control = event.target.closest(
      "a[href],button,[role='tab'],[data-admin-tab],[data-tab],[data-subprocess],[data-subprocess-key],[data-target]"
    );

    if (!control) {
      return;
    }

    if (!isUtilizadorNavigationControl_v14(control)) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    window.location.assign(CANONICAL_USER_LIST_URL);
  }

  document.addEventListener("click", handleClick_v14, true);
})();
