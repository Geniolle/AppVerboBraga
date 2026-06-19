(function () {
  "use strict";

  if (window.__appverboAdminUserUrlStateGuardV1Loaded) {
    return;
  }

  window.__appverboAdminUserUrlStateGuardV1Loaded = true;

  const CANONICAL_USER_LIST_URL = "/users/new?menu=administrativo&admin_tab=utilizador";

  function normalize_v1(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function parseUrl_v1(href) {
    try {
      return new URL(href, window.location.origin);
    }
    catch (error) {
      return null;
    }
  }

  function textOf_v1(element) {
    if (!element) {
      return "";
    }

    return normalize_v1(
      element.textContent ||
      element.value ||
      element.getAttribute("aria-label") ||
      element.getAttribute("title") ||
      ""
    );
  }

  function hasActionParams_v1(url) {
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

  function isUtilizadorMenuElement_v1(element) {
    if (!element) {
      return false;
    }

    const text = textOf_v1(element);
    const adminTab = normalize_v1(element.getAttribute("data-admin-tab"));
    const tab = normalize_v1(element.getAttribute("data-tab"));
    const subprocess = normalize_v1(element.getAttribute("data-subprocess"));
    const subprocessKey = normalize_v1(element.getAttribute("data-subprocess-key"));
    const target = normalize_v1(element.getAttribute("data-target"));
    const href = element.getAttribute("href");
    const url = href ? parseUrl_v1(href) : null;

    const isByData =
      adminTab === "utilizador" ||
      tab === "utilizador" ||
      subprocess === "utilizador" ||
      subprocessKey === "utilizador" ||
      target === "utilizador";

    const isByText =
      text === "utilizador" ||
      text === "utilizadores" ||
      (
        text.length <= 40 &&
        text.indexOf("utilizador") >= 0
      );

    const isByUrl =
      Boolean(url) &&
      url.pathname === "/users/new" &&
      url.searchParams.get("admin_tab") === "utilizador";

    if (isByUrl && hasActionParams_v1(url) && !isByText && !isByData) {
      return false;
    }

    return isByData || isByText || (isByUrl && !hasActionParams_v1(url));
  }

  function sanitizeUtilizadorLinks_v1() {
    const anchors = Array.from(document.querySelectorAll("a[href]"));

    anchors.forEach(function (anchor) {
      if (!isUtilizadorMenuElement_v1(anchor)) {
        return;
      }

      const href = anchor.getAttribute("href");
      const url = href ? parseUrl_v1(href) : null;

      if (!url) {
        return;
      }

      if (
        url.pathname === "/users/new" &&
        url.searchParams.get("admin_tab") === "utilizador"
      ) {
        anchor.setAttribute("href", CANONICAL_USER_LIST_URL);
        anchor.dataset.appverboUtilizadorCanonicalUrlV1 = "1";
      }
    });
  }

  function isCloseFromUserCard_v1(element) {
    if (!element) {
      return false;
    }

    const card = element.closest("#edit-user-card");

    if (!card) {
      return false;
    }

    const text = textOf_v1(element);

    return (
      text === "fechar" ||
      text === "voltar" ||
      text.indexOf("fechar") >= 0 ||
      text.indexOf("voltar") >= 0
    );
  }

  function goToCanonicalUserList_v1(event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    window.location.assign(CANONICAL_USER_LIST_URL);
  }

  function handleClick_v1(event) {
    const closeControl = event.target.closest("a,button,input[type='button'],input[type='submit']");

    if (closeControl && isCloseFromUserCard_v1(closeControl)) {
      goToCanonicalUserList_v1(event);
      return;
    }

    const navigationControl = event.target.closest(
      "a[href],button,[role='tab'],[data-admin-tab],[data-tab],[data-subprocess],[data-subprocess-key],[data-target]"
    );

    if (!navigationControl) {
      return;
    }

    if (!isUtilizadorMenuElement_v1(navigationControl)) {
      return;
    }

    goToCanonicalUserList_v1(event);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", sanitizeUtilizadorLinks_v1);
  }
  else {
    sanitizeUtilizadorLinks_v1();
  }

  document.addEventListener("click", handleClick_v1, true);
})();
