//###################################################################################
// (1) NORMALIZAR ABAS DA EDICAO DE PROCESSO
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1.1) LOGGER DE ROTAS PARA CLIQUES NAS ABAS DE EDICAO
  //###################################################################################

  const PROCESS_EDIT_TRACE_ENDPOINT_V2 = "/debug/admin-subprocess-click-trace";
  const PROCESS_EDIT_TRACE_SOURCE_V2 = "settings_process_tabs_v2";
  let processEditTraceSequenceV2 = 0;

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function normalizeText(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function repairText(value) {
    return String(value || "")
      .replaceAll("Atualize as configuraÃ§Ãµes deste processo.", "Atualize as configurações deste processo.")
      .replaceAll("ConfiguraÃ§Ã£o dos campos", "Configuração dos campos")
      .replaceAll("ConfiguraÃ§Ãµes", "Configurações")
      .replaceAll("ConfiguraÃ§Ã£o", "Configuração")
      .replaceAll("configuraÃ§Ãµes", "configurações")
      .replaceAll("configuraÃ§Ã£o", "configuração")
      .replaceAll("CabeÃ§alho", "Cabeçalho")
      .replaceAll("cabeÃ§alho", "cabeçalho")
      .replaceAll("Sem cabeÃ§alho", "Sem cabeçalho")
      .replaceAll("DefiniÃ§Ãµes", "Definições")
      .replaceAll("sÃ³", "só")
      .replaceAll("AÃ‡Ã•ES", "AÇÕES")
      .replaceAll("pÃ¡gina", "página");
  }

  function normalizeSettingsTab(value) {
    const cleanValue = String(value || "")
      .trim()
      .toLowerCase()
      .replaceAll("_", "-")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "");

    const aliases = {
      "geral": "geral",
      "configuracao-campos": "campos-config",
      "configuracao-dos-campos": "campos-config",
      "campos-configuracao": "campos-config",
      "campos-config": "campos-config",
      "campos-adicionais": "campos-adicionais",
      "campos-quantidade": "campos-quantidade",
      "additional-fields": "campos-adicionais",
      "adicionais": "campos-adicionais",
      "quantity-fields": "campos-quantidade",
      "lista": "lista",
      "listas": "lista",
      "campos-subsequentes": "campos-subsequentes"
    };

    return aliases[cleanValue] || "";
  }

  function buildRouteSnapshotV2(hrefValue) {
    try {
      const url = new URL(hrefValue || window.location.href, window.location.origin);
      return {
        href: String(url.href || ""),
        pathname: String(url.pathname || ""),
        search: String(url.search || ""),
        hash: String(url.hash || ""),
        settings_tab: normalizeSettingsTab(url.searchParams.get("settings_tab")),
      };
    } catch (error) {
      return {
        href: String(window.location.href || ""),
        pathname: String(window.location.pathname || ""),
        search: String(window.location.search || ""),
        hash: String(window.location.hash || ""),
        settings_tab: "",
      };
    }
  }

  function getProcessEditTabLabelV2(tabElement) {
    if (!tabElement) {
      return "";
    }
    return String(tabElement.textContent || "").trim();
  }

  function collectProcessEditStateV2(card, tabLinks, panes) {
    const activeTab = (tabLinks || []).find(function (link) {
      return (
        link.classList.contains("active") ||
        String(link.getAttribute("aria-selected") || "").trim().toLowerCase() === "true" ||
        String(link.getAttribute("data-active") || "").trim().toLowerCase() === "true"
      );
    });

    const activePane = (panes || []).find(function (pane) {
      return pane.classList && pane.classList.contains("active");
    });

    return {
      card_id: card && card.id ? String(card.id) : "",
      active_tab_key: normalizeSettingsTab(activeTab && activeTab.getAttribute("data-process-edit-tab")),
      active_tab_label: getProcessEditTabLabelV2(activeTab),
      active_pane_key: normalizeSettingsTab(activePane && activePane.getAttribute("data-process-edit-pane")),
    };
  }

  function sendProcessEditTraceV2(stage, payload) {
    try {
      processEditTraceSequenceV2 += 1;

      const tracePayload = {
        logger: "APPVERBO_SETTINGS_PROCESS_TABS_TRACE_V2",
        source: PROCESS_EDIT_TRACE_SOURCE_V2,
        sequence: processEditTraceSequenceV2,
        stage: String(stage || "").trim() || "unknown",
        timestamp_client_iso: new Date().toISOString(),
        route: buildRouteSnapshotV2(window.location.href),
        payload: payload && typeof payload === "object" ? payload : {},
      };

      const body = JSON.stringify(tracePayload);

      if (navigator && typeof navigator.sendBeacon === "function") {
        const blob = new Blob([body], { type: "application/json" });
        navigator.sendBeacon(PROCESS_EDIT_TRACE_ENDPOINT_V2, blob);
        return;
      }

      fetch(PROCESS_EDIT_TRACE_ENDPOINT_V2, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true,
      }).catch(function () {
      });
    } catch (error) {
    }
  }

  //###################################################################################
  // (3) ABAS INTERNAS DO EDITAR PROCESSO - ESTADO ATIVO
  //###################################################################################

  function getProcessEditCard() {
    return document.getElementById("settings-menu-edit-card");
  }

  function getProcessEditTabLinks(card) {
    if (!card) {
      return [];
    }
    return Array.from(card.querySelectorAll(".process-edit-tab-link[data-process-edit-tab]"));
  }

  function getProcessEditPanes(card) {
    if (!card) {
      return [];
    }
    return Array.from(card.querySelectorAll("[data-process-edit-pane]"));
  }

  function normalizeProcessEditTabKey(value) {
    return normalizeSettingsTab(value);
  }

  function resolveProcessEditTabFromUrl() {
    const url = new URL(window.location.href);
    return normalizeSettingsTab(url.searchParams.get("settings_tab"));
  }

  function setProcessEditTabInUrl(tabKey) {
    const cleanTabKey = normalizeProcessEditTabKey(tabKey);
    if (!cleanTabKey) {
      return;
    }

    const routeBefore = buildRouteSnapshotV2(window.location.href);
    const url = new URL(window.location.href);
    const settingsEditKey = String(url.searchParams.get("settings_edit_key") || "").trim();
    if (!settingsEditKey) {
      return;
    }

    url.searchParams.set("settings_tab", cleanTabKey);
    const nextUrl = `${url.pathname}${url.search}${url.hash}`;
    window.history.replaceState({}, "", nextUrl);
    const routeAfter = buildRouteSnapshotV2(nextUrl);

    sendProcessEditTraceV2("process_edit_tab_url_sync_v2", {
      tab_key: cleanTabKey,
      route_before: routeBefore,
      route_after: routeAfter,
    });
  }

  function resolveFallbackProcessEditTab(tabLinks) {
    const activeLink = tabLinks.find(function (link) {
      return (
        link.classList.contains("active") ||
        String(link.getAttribute("aria-selected") || "").trim().toLowerCase() === "true"
      );
    });
    const activeKey = normalizeProcessEditTabKey(activeLink && activeLink.getAttribute("data-process-edit-tab"));
    if (activeKey) {
      return activeKey;
    }
    return "geral";
  }

  function getCurrentActiveProcessEditTabKey(tabLinks) {
    const activeLink = (tabLinks || []).find(function (link) {
      return (
        link.classList.contains("active") ||
        String(link.getAttribute("aria-selected") || "").trim().toLowerCase() === "true" ||
        String(link.getAttribute("data-active") || "").trim().toLowerCase() === "true"
      );
    });

    return normalizeProcessEditTabKey(activeLink && activeLink.getAttribute("data-process-edit-tab"));
  }

  function getCurrentActiveProcessEditPaneKey(panes) {
    const activePane = (panes || []).find(function (pane) {
      return pane.classList && pane.classList.contains("active");
    });
    return normalizeProcessEditTabKey(activePane && activePane.getAttribute("data-process-edit-pane"));
  }

  function activateProcessEditTab(tabKey, options) {
    const config = options || {};
    const card = getProcessEditCard();
    const tabLinks = getProcessEditTabLinks(card);
    const panes = getProcessEditPanes(card);

    if (!tabLinks.length || !panes.length) {
      return;
    }

    const normalizedTabKey = normalizeProcessEditTabKey(tabKey);
    const hasRequestedTab = tabLinks.some(function (link) {
      const linkTab = normalizeProcessEditTabKey(link.getAttribute("data-process-edit-tab"));
      return linkTab && linkTab === normalizedTabKey;
    });
    const resolvedTabKey = hasRequestedTab
      ? normalizedTabKey
      : resolveFallbackProcessEditTab(tabLinks);
    const stateBeforeActivation = collectProcessEditStateV2(card, tabLinks, panes);

    tabLinks.forEach(function (link) {
      const linkTab = normalizeProcessEditTabKey(link.getAttribute("data-process-edit-tab"));
      const isActive = Boolean(linkTab && linkTab === resolvedTabKey);
      link.style.removeProperty("background");
      link.style.removeProperty("background-color");
      link.style.removeProperty("border-color");
      link.style.removeProperty("color");
      link.classList.toggle("active", isActive);
      link.classList.toggle("is-active", isActive);
      link.setAttribute("aria-selected", isActive ? "true" : "false");
      if (isActive) {
        link.setAttribute("data-active", "true");
        link.setAttribute("data-selected", "true");
        link.removeAttribute("data-appverbo-force-active");
        link.removeAttribute("data-appverbo-force-inactive");
        link.removeAttribute("data-appverbo-menu-active");
      } else {
        link.removeAttribute("data-active");
        link.removeAttribute("data-selected");
        link.removeAttribute("data-appverbo-force-active");
        link.removeAttribute("data-appverbo-force-inactive");
        link.removeAttribute("data-appverbo-menu-active");
      }
    });

    panes.forEach(function (pane) {
      const paneTab = normalizeProcessEditTabKey(pane.getAttribute("data-process-edit-pane"));
      const isActive = Boolean(paneTab && paneTab === resolvedTabKey);
      pane.classList.toggle("active", isActive);
    });

    if (config.syncUrl === true) {
      setProcessEditTabInUrl(resolvedTabKey);
    }

    const stateAfterActivation = collectProcessEditStateV2(card, tabLinks, panes);
    sendProcessEditTraceV2("process_edit_tab_activate_v2", {
      requested_tab_key: normalizedTabKey,
      resolved_tab_key: resolvedTabKey,
      sync_url: config.syncUrl === true,
      state_before: stateBeforeActivation,
      state_after: stateAfterActivation,
    });

    window.dispatchEvent(new CustomEvent("appverbo:normalize-tabs-width-v1"));
  }

  function bindProcessEditTabs() {
    const card = getProcessEditCard();
    if (!card) {
      return;
    }

    if (card.dataset.processEditTabsBoundV2 !== "1") {
      card.dataset.processEditTabsBoundV2 = "1";

      card.addEventListener("click", function (event) {
        const tabLink = event.target.closest(".process-edit-tab-link[data-process-edit-tab]");
        if (!tabLink || !card.contains(tabLink)) {
          return;
        }

        const clickBeforeRoute = buildRouteSnapshotV2(window.location.href);
        const clickBeforeState = collectProcessEditStateV2(
          card,
          getProcessEditTabLinks(card),
          getProcessEditPanes(card)
        );
        event.preventDefault();
        const tabKey = normalizeProcessEditTabKey(tabLink.getAttribute("data-process-edit-tab")) || "geral";
        activateProcessEditTab(tabKey, { syncUrl: true });
        const clickAfterRoute = buildRouteSnapshotV2(window.location.href);
        const clickAfterState = collectProcessEditStateV2(
          card,
          getProcessEditTabLinks(card),
          getProcessEditPanes(card)
        );

        sendProcessEditTraceV2("process_edit_tab_click_v2", {
          clicked_tab_key: tabKey,
          clicked_tab_label: getProcessEditTabLabelV2(tabLink),
          clicked_tab_href: String(tabLink.getAttribute("href") || ""),
          route_before: clickBeforeRoute,
          route_after: clickAfterRoute,
          state_before: clickBeforeState,
          state_after: clickAfterState,
        });
      });
    }

    const initialTabFromUrl = resolveProcessEditTabFromUrl();
    activateProcessEditTab(initialTabFromUrl || "geral", { syncUrl: false });

    if (card.dataset.processEditTabsPaneObserverV2 !== "1") {
      card.dataset.processEditTabsPaneObserverV2 = "1";

      const observer = new MutationObserver(function () {
        const tabLinks = getProcessEditTabLinks(card);
        const panes = getProcessEditPanes(card);

        if (!tabLinks.length || !panes.length) {
          return;
        }

        const activePaneKey = getCurrentActiveProcessEditPaneKey(panes);
        const activeTabKey = getCurrentActiveProcessEditTabKey(tabLinks);

        if (activePaneKey && activePaneKey !== activeTabKey) {
          sendProcessEditTraceV2("process_edit_tab_observer_sync_v2", {
            active_pane_key: activePaneKey,
            active_tab_key: activeTabKey,
          });
          activateProcessEditTab(activePaneKey, { syncUrl: false });
        }
      });

      observer.observe(card, {
        subtree: true,
        attributes: true,
        attributeFilter: ["class"]
      });
    }
  }

  //###################################################################################
  // (4) CORRIGIR TEXTOS VISIVEIS
  //###################################################################################

  function repairTextNodes(root) {
    const walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];

    while (walker.nextNode()) {
      nodes.push(walker.currentNode);
    }

    nodes.forEach(function (node) {
      const originalValue = node.nodeValue || "";
      const repairedValue = repairText(originalValue);

      if (originalValue !== repairedValue) {
        node.nodeValue = repairedValue;
      }
    });
  }

  //###################################################################################
  // (5) NORMALIZAR LINKS DAS ABAS
  //###################################################################################

  function normalizeTabLinks() {
    const links = document.querySelectorAll("a[href*='settings_tab='], button[data-settings-tab], [data-settings-tab]");

    links.forEach(function (element) {
      const currentTab = normalizeSettingsTab(element.getAttribute("data-settings-tab"));

      if (currentTab) {
        element.setAttribute("data-settings-tab", currentTab);
      }

      if (element.tagName && element.tagName.toLowerCase() === "a") {
        try {
          const url = new URL(element.getAttribute("href"), window.location.origin);
          const tab = normalizeSettingsTab(url.searchParams.get("settings_tab"));

          if (tab) {
            url.searchParams.set("settings_tab", tab);
            element.setAttribute("href", `${url.pathname}${url.search}${url.hash}`);
          }
        } catch (error) {
          return;
        }
      }
    });
  }

  //###################################################################################
  // (6) GARANTIR OS NOMES DAS 3 ABAS
  //###################################################################################

  function normalizeVisibleTabLabels() {
    const candidates = Array.from(document.querySelectorAll("a, button, [role='tab']"));

    candidates.forEach(function (element) {
      const text = normalizeText(element.textContent);

      if (text === "geral") {
        element.textContent = "Geral";
        return;
      }

      if (
        text === "configuracao dos campos" ||
        text === "configuracao de campos" ||
        text === "configuracao campos"
      ) {
        element.textContent = "Configuração dos campos";
        return;
      }

      if (
        text === "campos adicionais" ||
        text === "campo adicionais"
      ) {
        element.textContent = "Campos adicionais";
        return;
      }

      if (text === "campos quantidade" || text === "campos de quantidade") {
        element.textContent = "Campos Quantidade";
        return;
      }

      if (text === "lista") {
        element.textContent = "Lista";
      }
    });
  }

  //###################################################################################
  // (7) INICIALIZACAO
  //###################################################################################

  function run() {
    repairTextNodes(document.body);
    normalizeTabLinks();
    normalizeVisibleTabLabels();
    bindProcessEditTabs();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }

  window.setTimeout(run, 100);
  window.setTimeout(run, 400);
  window.setTimeout(run, 1000);
})();
