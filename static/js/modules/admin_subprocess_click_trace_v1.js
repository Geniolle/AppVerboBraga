(function () {
  "use strict";

  const LOGGER_VERSION = "APPVERBO_ADMIN_SUBPROCESS_CLICK_TRACE_JS_V1";
  const TRACE_ENDPOINT = "/debug/admin-subprocess-click-trace";

  function textoLimpo_v1(value, maxLength) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    if (text.length > maxLength) {
      return text.slice(0, maxLength) + "...[TRUNCATED]";
    }
    return text;
  }

  function parametroUrl_v1(name) {
    try {
      return new URL(window.location.href).searchParams.get(name) || "";
    } catch (error) {
      return "";
    }
  }

  function elementoVisivel_v1(element) {
    if (!element) {
      return false;
    }

    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();

    return (
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      style.opacity !== "0" &&
      rect.width > 0 &&
      rect.height > 0
    );
  }

  function estadoElemento_v1(id) {
    const element = document.getElementById(id);

    if (!element) {
      return {
        id,
        exists: false,
      };
    }

    const style = window.getComputedStyle(element);

    return {
      id,
      exists: true,
      visible: elementoVisivel_v1(element),
      tagName: element.tagName,
      className: textoLimpo_v1(element.className || "", 260),
      display: style.display,
      visibility: style.visibility,
      opacity: style.opacity,
      text: textoLimpo_v1(element.innerText || element.textContent || "", 350),
    };
  }

  function elementoAcionavel_v1(element) {
    if (!element || !element.closest) {
      return null;
    }

    return element.closest(
      [
        "[data-admin-tab]",
        "[data-admin-subprocess]",
        "[data-admin-subprocess-key]",
        "[data-admin-subprocess-action]",
        "[data-process-edit-tab]",
        "[data-menu-key]",
        "[data-menu-target]",
        "[data-edit-target]",
        "[role='tab']",
        "a",
        "button",
        "summary",
        "input[type='submit']",
        "input[type='button']",
      ].join(",")
    );
  }

  function infoElemento_v1(element) {
    if (!element) {
      return {};
    }

    const form = element.closest ? element.closest("form") : null;

    return {
      tagName: element.tagName || "",
      id: element.id || "",
      name: element.getAttribute("name") || "",
      type: element.getAttribute("type") || "",
      role: element.getAttribute("role") || "",
      className: textoLimpo_v1(element.className || "", 260),
      text: textoLimpo_v1(element.innerText || element.textContent || element.value || "", 300),
      href: element.getAttribute("href") || "",
      action: element.getAttribute("action") || "",
      formAction: form ? form.getAttribute("action") || "" : "",
      formMethod: form ? form.getAttribute("method") || "" : "",
      dataAdminTab: element.getAttribute("data-admin-tab") || "",
      dataAdminSubprocess: element.getAttribute("data-admin-subprocess") || "",
      dataAdminSubprocessKey: element.getAttribute("data-admin-subprocess-key") || "",
      dataAdminSubprocessAction: element.getAttribute("data-admin-subprocess-action") || "",
      dataProcessEditTab: element.getAttribute("data-process-edit-tab") || "",
      dataMenuKey: element.getAttribute("data-menu-key") || "",
      dataMenuTarget: element.getAttribute("data-menu-target") || "",
      dataEditTarget: element.getAttribute("data-edit-target") || "",
    };
  }

  function deveRegistar_v1(info) {
    const haystack = [
      info.text,
      info.href,
      info.action,
      info.formAction,
      info.dataAdminTab,
      info.dataAdminSubprocess,
      info.dataAdminSubprocessKey,
      info.dataAdminSubprocessAction,
      info.dataProcessEditTab,
      info.dataMenuKey,
      info.dataMenuTarget,
      info.dataEditTarget,
      window.location.href,
    ].join(" ");

    return /(menu|sess|sessão|sessoes|sessões|entidade|utilizador|contas|criar|editar|guardar|cancelar|eliminar|mover|admin_tab=|settings_tab=|settings_edit_key=|sidebar_section|\/settings\/menu)/i.test(haystack);
  }

  function snapshot_v1(stage, extra) {
    const activeAdminTab =
      document.querySelector("[data-admin-tab].active") ||
      document.querySelector(".admin-tab.active") ||
      document.querySelector("[aria-selected='true'][role='tab']");

    const activeProcessTab =
      document.querySelector("[data-process-edit-tab].active") ||
      document.querySelector(".process-edit-tab-link.active");

    const cards = [
      "admin-menu-card-create",
      "admin-menu-card",
      "admin-menu-card-active",
      "admin-menu-card-inactive",
      "settings-card",
      "settings-menu-edit-card",
      "admin-sidebar-sections-card",
      "admin-sidebar-sections-form-card",
      "create-user-card",
      "admin-users-created-card",
      "inactive-users-card",
      "create-entity-card",
      "recent-entities-card",
      "inactive-entities-card",
    ].map(estadoElemento_v1);

    const adminSubprocessElements = Array.from(
      document.querySelectorAll("[data-admin-subprocess], [data-admin-subprocess-key], [data-admin-subprocess-card]")
    )
      .slice(0, 40)
      .map(function (element) {
        return {
          tagName: element.tagName,
          id: element.id || "",
          className: textoLimpo_v1(element.className || "", 220),
          dataAdminSubprocess: element.getAttribute("data-admin-subprocess") || "",
          dataAdminSubprocessKey: element.getAttribute("data-admin-subprocess-key") || "",
          visible: elementoVisivel_v1(element),
          text: textoLimpo_v1(element.innerText || element.textContent || "", 260),
        };
      });

    return {
      logger: LOGGER_VERSION,
      stage,
      href: window.location.href,
      pathname: window.location.pathname,
      search: window.location.search,
      hash: window.location.hash,
      params: {
        menu: parametroUrl_v1("menu"),
        admin_tab: parametroUrl_v1("admin_tab"),
        settings_edit_key: parametroUrl_v1("settings_edit_key"),
        settings_tab: parametroUrl_v1("settings_tab"),
        target: parametroUrl_v1("target"),
        sidebar_sections_tab: parametroUrl_v1("sidebar_sections_tab"),
        sidebar_section_edit_key: parametroUrl_v1("sidebar_section_edit_key"),
      },
      activeAdminTab: activeAdminTab
        ? {
            id: activeAdminTab.id || "",
            text: textoLimpo_v1(activeAdminTab.innerText || activeAdminTab.textContent || "", 180),
            href: activeAdminTab.getAttribute("href") || "",
            dataAdminTab: activeAdminTab.getAttribute("data-admin-tab") || "",
          }
        : null,
      activeProcessTab: activeProcessTab
        ? {
            id: activeProcessTab.id || "",
            text: textoLimpo_v1(activeProcessTab.innerText || activeProcessTab.textContent || "", 180),
            href: activeProcessTab.getAttribute("href") || "",
            dataProcessEditTab: activeProcessTab.getAttribute("data-process-edit-tab") || "",
          }
        : null,
      cards,
      adminSubprocessElements,
      bodyTextPreview: textoLimpo_v1(document.body ? document.body.innerText : "", 1000),
      extra: extra || {},
    };
  }

  function enviarTrace_v1(stage, extra) {
    const payload = snapshot_v1(stage, extra);

    try {
      const body = JSON.stringify(payload);

      fetch(TRACE_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true,
      }).catch(function () {});
    } catch (error) {
      try {
        console.warn("APPVERBO click trace failed", error);
      } catch (ignored) {}
    }
  }

  document.addEventListener(
    "click",
    function (event) {
      const actionElement = elementoAcionavel_v1(event.target);
      const info = infoElemento_v1(actionElement);

      if (!deveRegistar_v1(info)) {
        return;
      }

      enviarTrace_v1("click_capture", {
        element: info,
        mouse: {
          button: event.button,
          ctrlKey: event.ctrlKey,
          shiftKey: event.shiftKey,
          altKey: event.altKey,
          metaKey: event.metaKey,
        },
      });
    },
    true
  );

  document.addEventListener(
    "submit",
    function (event) {
      const form = event.target;

      if (!form || !form.matches || !form.matches("form")) {
        return;
      }

      const info = {
        id: form.id || "",
        className: textoLimpo_v1(form.className || "", 240),
        action: form.getAttribute("action") || "",
        method: form.getAttribute("method") || "",
        text: textoLimpo_v1(form.innerText || form.textContent || "", 300),
      };

      if (!deveRegistar_v1({
        text: info.text,
        href: "",
        action: info.action,
        formAction: info.action,
        dataAdminTab: "",
        dataAdminSubprocess: "",
        dataAdminSubprocessKey: "",
        dataAdminSubprocessAction: "",
        dataProcessEditTab: "",
        dataMenuKey: "",
        dataMenuTarget: "",
        dataEditTarget: "",
      })) {
        return;
      }

      enviarTrace_v1("submit_capture", {
        form: info,
      });
    },
    true
  );

  document.addEventListener("DOMContentLoaded", function () {
    enviarTrace_v1("dom_content_loaded", {});
    window.setTimeout(function () {
      enviarTrace_v1("dom_snapshot_1000ms", {});
    }, 1000);
  });

  window.addEventListener("hashchange", function () {
    enviarTrace_v1("hashchange", {});
  });

  window.addEventListener("popstate", function () {
    enviarTrace_v1("popstate", {});
  });

  window.APPVERBO_ADMIN_SUBPROCESS_CLICK_TRACE_V1 = {
    snapshot: function () {
      enviarTrace_v1("manual_snapshot", {});
    },
  };
})();
