(function () {
  "use strict";

  //###################################################################################
  // (1) CONFIGURACAO DO LOGGER
  //###################################################################################

  const LOGGER_VERSION = "APPVERBO_ADMIN_SUBPROCESS_CLICK_TRACE_JS_V1";
  const TRACE_ENDPOINT = "/debug/admin-subprocess-click-trace";
  const IMPORTANT_TEXT_RE = /(menu|sess|sessão|sessoes|sessões|entidade|utilizador|contas|subprocesso|criar|editar|guardar|cancelar|eliminar|mover|ativo|inativo)/i;
  const IMPORTANT_URL_RE = /(admin_tab=|settings_tab=|settings_edit_key=|sidebar_section|\/settings\/menu|\/users\/new|\/entities|\/users\/)/i;

  //###################################################################################
  // (2) FUNCOES UTILITARIAS
  //###################################################################################

  function limitarTexto_v1(value, maxLength) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    if (text.length > maxLength) {
      return text.slice(0, maxLength) + "...[TRUNCATED]";
    }
    return text;
  }

  function obterParametroUrl_v1(name) {
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

  function estadoElementoPorId_v1(id) {
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
      className: limitarTexto_v1(element.className || "", 220),
      display: style.display,
      visibility: style.visibility,
      opacity: style.opacity,
      text: limitarTexto_v1(element.innerText || element.textContent || "", 260),
    };
  }

  function obterElementoAcionavel_v1(startElement) {
    if (!startElement || !startElement.closest) {
      return null;
    }

    return startElement.closest(
      [
        "[data-admin-tab]",
        "[data-admin-subprocess]",
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

  function obterInfoElemento_v1(element) {
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
      className: limitarTexto_v1(element.className || "", 260),
      text: limitarTexto_v1(element.innerText || element.textContent || element.value || "", 260),
      href: element.getAttribute("href") || "",
      action: element.getAttribute("action") || "",
      formAction: form ? form.getAttribute("action") || "" : "",
      formMethod: form ? form.getAttribute("method") || "" : "",
      dataAdminTab: element.getAttribute("data-admin-tab") || "",
      dataAdminSubprocess: element.getAttribute("data-admin-subprocess") || "",
      dataAdminSubprocessAction: element.getAttribute("data-admin-subprocess-action") || "",
      dataProcessEditTab: element.getAttribute("data-process-edit-tab") || "",
      dataMenuKey: element.getAttribute("data-menu-key") || "",
      dataMenuTarget: element.getAttribute("data-menu-target") || "",
      dataEditTarget: element.getAttribute("data-edit-target") || "",
    };
  }

  function deveRegistarElemento_v1(info) {
    const haystack = [
      info.text,
      info.href,
      info.action,
      info.formAction,
      info.dataAdminTab,
      info.dataAdminSubprocess,
      info.dataAdminSubprocessAction,
      info.dataProcessEditTab,
      info.dataMenuKey,
      info.dataMenuTarget,
      info.dataEditTarget,
      window.location.href,
    ].join(" ");

    return IMPORTANT_TEXT_RE.test(haystack) || IMPORTANT_URL_RE.test(haystack);
  }

  //###################################################################################
  // (3) SNAPSHOT DO ESTADO DA PAGINA
  //###################################################################################

  function coletarSnapshotPagina_v1(stage, extra) {
    const activeAdminTab =
      document.querySelector("[data-admin-tab].active") ||
      document.querySelector(".admin-tab.active") ||
      document.querySelector("[aria-selected='true'][role='tab']");

    const activeProcessTab =
      document.querySelector("[data-process-edit-tab].active") ||
      document.querySelector(".process-edit-tab-link.active");

    const menuCards = [
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
      "create-entity-card",
      "recent-entities-card",
      "inactive-entities-card",
    ].map(estadoElementoPorId_v1);

    const adminSubprocessElements = Array.from(
      document.querySelectorAll("[data-admin-subprocess], [data-admin-subprocess-key], [data-admin-subprocess-card]")
    )
      .slice(0, 30)
      .map(function (element) {
        return {
          tagName: element.tagName,
          id: element.id || "",
          className: limitarTexto_v1(element.className || "", 180),
          dataAdminSubprocess: element.getAttribute("data-admin-subprocess") || "",
          dataAdminSubprocessKey: element.getAttribute("data-admin-subprocess-key") || "",
          visible: elementoVisivel_v1(element),
          text: limitarTexto_v1(element.innerText || element.textContent || "", 180),
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
        menu: obterParametroUrl_v1("menu"),
        admin_tab: obterParametroUrl_v1("admin_tab"),
        settings_edit_key: obterParametroUrl_v1("settings_edit_key"),
        settings_tab: obterParametroUrl_v1("settings_tab"),
        target: obterParametroUrl_v1("target"),
        sidebar_sections_tab: obterParametroUrl_v1("sidebar_sections_tab"),
        sidebar_section_edit_key: obterParametroUrl_v1("sidebar_section_edit_key"),
      },
      activeAdminTab: activeAdminTab
        ? {
            id: activeAdminTab.id || "",
            text: limitarTexto_v1(activeAdminTab.innerText || activeAdminTab.textContent || "", 160),
            href: activeAdminTab.getAttribute("href") || "",
            dataAdminTab: activeAdminTab.getAttribute("data-admin-tab") || "",
          }
        : null,
      activeProcessTab: activeProcessTab
        ? {
            id: activeProcessTab.id || "",
            text: limitarTexto_v1(activeProcessTab.innerText || activeProcessTab.textContent || "", 160),
            href: activeProcessTab.getAttribute("href") || "",
            dataProcessEditTab: activeProcessTab.getAttribute("data-process-edit-tab") || "",
          }
        : null,
      cards: menuCards,
      adminSubprocessElements,
      extra: extra || {},
    };
  }

  //###################################################################################
  // (4) ENVIO DO LOG
  //###################################################################################

  function enviarTrace_v1(stage, extra) {
    const payload = coletarSnapshotPagina_v1(stage, extra);

    try {
      const body = JSON.stringify(payload);

      if (navigator.sendBeacon) {
        const blob = new Blob([body], { type: "application/json" });
        navigator.sendBeacon(TRACE_ENDPOINT, blob);
        return;
      }

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

  //###################################################################################
  // (5) EVENTOS DE CLIQUE, SUBMIT E NAVEGACAO
  //###################################################################################

  document.addEventListener(
    "click",
    function (event) {
      const actionElement = obterElementoAcionavel_v1(event.target);
      const info = obterInfoElemento_v1(actionElement);

      if (!deveRegistarElemento_v1(info)) {
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
        className: limitarTexto_v1(form.className || "", 220),
        action: form.getAttribute("action") || "",
        method: form.getAttribute("method") || "",
        text: limitarTexto_v1(form.innerText || form.textContent || "", 220),
        fields: Array.from(form.elements || [])
          .slice(0, 80)
          .map(function (field) {
            return {
              tagName: field.tagName || "",
              type: field.getAttribute ? field.getAttribute("type") || "" : "",
              name: field.getAttribute ? field.getAttribute("name") || "" : "",
              id: field.id || "",
            };
          }),
      };

      if (!deveRegistarElemento_v1({
        text: info.text,
        href: "",
        action: info.action,
        formAction: info.action,
        dataAdminTab: "",
        dataAdminSubprocess: "",
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
      enviarTrace_v1("dom_snapshot_800ms", {});
    }, 800);
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
