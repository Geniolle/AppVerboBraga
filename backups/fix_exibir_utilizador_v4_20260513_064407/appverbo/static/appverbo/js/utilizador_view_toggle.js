(function () {
  "use strict";

  if (window.__utilizadorViewToggleV3Loaded) {
    return;
  }

  window.__utilizadorViewToggleV3Loaded = true;

  const VIEW_PARAM = "user_view";
  const EDIT_ID_PARAM = "user_edit_id";
  const PANEL_MARKER = "data-user-view-panel-v3";

  function normalize_v3(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function getParams_v3() {
    return new URLSearchParams(window.location.search || "");
  }

  function isUtilizadorPage_v3() {
    const params = getParams_v3();
    const path = normalize_v3(window.location.pathname);

    return (
      path.indexOf("/users/new") >= 0 ||
      params.get("admin_tab") === "utilizador" ||
      params.has(VIEW_PARAM) ||
      params.has(EDIT_ID_PARAM)
    );
  }

  function isViewMode_v3() {
    const params = getParams_v3();

    return (
      params.get(VIEW_PARAM) === "1" &&
      Boolean(params.get(EDIT_ID_PARAM))
    );
  }

  function textOf_v3(element) {
    if (!element) {
      return "";
    }

    return normalize_v3(
      element.textContent ||
      element.value ||
      element.getAttribute("aria-label") ||
      element.getAttribute("title") ||
      ""
    );
  }

  function findTitleElement_v3() {
    const candidates = Array.from(
      document.querySelectorAll("h1,h2,h3,h4,h5,h6,legend,strong,b,span,div,p")
    );

    return candidates.find(function (element) {
      const text = textOf_v3(element);

      return (
        text === "exibir utilizador" ||
        text === "exibir usuário" ||
        text === "exibir usuario"
      );
    });
  }

  function hasUserViewContent_v3(element) {
    const text = textOf_v3(element);

    const hasTitle =
      text.indexOf("exibir utilizador") >= 0 ||
      text.indexOf("exibir usuário") >= 0 ||
      text.indexOf("exibir usuario") >= 0;

    const hasFields =
      text.indexOf("nome completo") >= 0 &&
      text.indexOf("telefone") >= 0 &&
      text.indexOf("email") >= 0;

    return hasTitle && hasFields;
  }

  function findPanelFromTitle_v3(titleElement) {
    if (!titleElement) {
      return null;
    }

    const selectors = [
      "[" + PANEL_MARKER + "]",
      ".card",
      ".card-body",
      ".panel",
      ".box",
      ".section",
      ".content-box",
      ".form-section",
      ".native-card",
      ".admin-card",
      "section",
      "fieldset",
      "form",
      "article"
    ];

    for (let index = 0; index < selectors.length; index += 1) {
      const found = titleElement.closest(selectors[index]);

      if (
        found &&
        found !== document.body &&
        found !== document.documentElement &&
        hasUserViewContent_v3(found)
      ) {
        return found;
      }
    }

    let current = titleElement.parentElement;

    for (let level = 0; level < 10 && current && current !== document.body; level += 1) {
      if (hasUserViewContent_v3(current)) {
        return current;
      }

      current = current.parentElement;
    }

    return titleElement.parentElement;
  }

  function buildClosedUrl_v3() {
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

  function closePanel_v3(event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    window.location.href = buildClosedUrl_v3();
  }

  function bindCloseButtons_v3(panel) {
    if (!panel || panel.dataset.userViewCloseBoundV3 === "1") {
      return;
    }

    const controls = Array.from(
      panel.querySelectorAll("button, a, input[type='button'], input[type='submit']")
    );

    controls.forEach(function (control) {
      const text = textOf_v3(control);

      if (text === "fechar" || text.indexOf("fechar") >= 0) {
        control.addEventListener("click", closePanel_v3);
      }
    });

    panel.dataset.userViewCloseBoundV3 = "1";
  }

  function applyUserViewVisibility_v3() {
    if (!isUtilizadorPage_v3()) {
      return;
    }

    const titleElement = findTitleElement_v3();

    if (!titleElement) {
      return;
    }

    const panel = findPanelFromTitle_v3(titleElement);

    if (!panel) {
      return;
    }

    panel.setAttribute(PANEL_MARKER, "1");

    if (isViewMode_v3()) {
      panel.hidden = false;
      panel.style.removeProperty("display");
      bindCloseButtons_v3(panel);
      return;
    }

    panel.hidden = true;
    panel.style.display = "none";
  }

  function scheduleApply_v3() {
    window.clearTimeout(window.__utilizadorViewToggleTimerV3);
    window.__utilizadorViewToggleTimerV3 = window.setTimeout(applyUserViewVisibility_v3, 80);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyUserViewVisibility_v3);
  }
  else {
    applyUserViewVisibility_v3();
  }

  window.addEventListener("load", applyUserViewVisibility_v3);
  window.addEventListener("popstate", applyUserViewVisibility_v3);

  if (document.body && window.MutationObserver) {
    const observer = new MutationObserver(scheduleApply_v3);

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
})();
