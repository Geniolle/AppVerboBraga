//###################################################################################
// (1) NORMALIZAR ABAS DA EDICAO DE PROCESSO
//###################################################################################

(function () {
  "use strict";

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
      "campos-subsequentes": "campos-subsequentes"
    };

    return aliases[cleanValue] || "";
  }

  function getCurrentlyActiveTab() {
    const card = document.querySelector("#settings-menu-edit-card");

    if (!card) {
      return "";
    }

    const activePane = card.querySelector("[data-process-edit-pane].active");
    return activePane ? normalizeSettingsTab(activePane.getAttribute("data-process-edit-pane")) : "";
  }

  function getRequestedSettingsTab() {
    // Uma aba ja ativada (por clique do utilizador ou pelo boot de setupProcessEditTabs)
    // e a fonte da verdade: os reruns por timer nao podem reverter para o snapshot
    // congelado do bootstrap/URL de carregamento inicial, senao anulam a troca de aba.
    const activeTab = getCurrentlyActiveTab();

    if (activeTab) {
      return activeTab;
    }

    const bootstrapTab = normalizeSettingsTab(
      window.__APPGENESIS_BOOTSTRAP__ && window.__APPGENESIS_BOOTSTRAP__.settingsTab
    );

    if (bootstrapTab) {
      return bootstrapTab;
    }

    try {
      return normalizeSettingsTab(new URLSearchParams(window.location.search).get("settings_tab"));
    } catch (error) {
      return "";
    }
  }

  function activateProcessEditTab(requestedTab) {
    const activeTab = normalizeSettingsTab(requestedTab);

    if (!activeTab) {
      return;
    }

    const card = document.querySelector("#settings-menu-edit-card");

    if (!card) {
      return;
    }

    const tabLinks = Array.from(card.querySelectorAll("[data-process-edit-tab]"));
    const tabPanes = Array.from(card.querySelectorAll("[data-process-edit-pane]"));

    const targetLink = tabLinks.find(function (element) {
      return normalizeSettingsTab(element.getAttribute("data-process-edit-tab")) === activeTab;
    });
    const targetPane = tabPanes.find(function (element) {
      return normalizeSettingsTab(element.getAttribute("data-process-edit-pane")) === activeTab;
    });

    if (!targetLink || !targetPane) {
      return;
    }

    tabLinks.forEach(function (element) {
      const isActive = normalizeSettingsTab(element.getAttribute("data-process-edit-tab")) === activeTab;
      element.classList.toggle("active", isActive);
      element.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    tabPanes.forEach(function (element) {
      const isActive = normalizeSettingsTab(element.getAttribute("data-process-edit-pane")) === activeTab;
      element.classList.toggle("active", isActive);
    });
  }

  //###################################################################################
  // (3) CORRIGIR TEXTOS VISIVEIS
  //###################################################################################


  //###################################################################################
  // (4) NORMALIZAR LINKS DAS ABAS
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
  // (5) GARANTIR OS NOMES DAS 3 ABAS
  //###################################################################################

  // Atualiza so o texto da aba; preserva a bolinha (span filho) quando existe.
  function setTabLabelKeepingDots_v1(element, label) {
    const textNode = Array.from(element.childNodes).find(function (node) {
      return node.nodeType === Node.TEXT_NODE;
    });
    if (element.querySelector(".profile-tab-missing-dot-v1") && textNode) {
      textNode.nodeValue = label;
      return;
    }
    element.textContent = label;
  }

  function normalizeVisibleTabLabels() {
    const candidates = Array.from(document.querySelectorAll("a, button, [role='tab']"));

    candidates.forEach(function (element) {
      const text = normalizeText(element.textContent);

      if (text === "geral") {
        setTabLabelKeepingDots_v1(element, "Geral");
        return;
      }

      if (
        text === "configuracao dos campos" ||
        text === "configuracao de campos" ||
        text === "configuracao campos"
      ) {
        setTabLabelKeepingDots_v1(element, "Configuração dos campos");
        return;
      }

      if (
        text === "campos adicionais" ||
        text === "campo adicionais"
      ) {
        setTabLabelKeepingDots_v1(element, "Campos adicionais");
        return;
      }

      if (text === "campos quantidade" || text === "campos de quantidade") {
        setTabLabelKeepingDots_v1(element, "Campos Quantidade");
        return;
      }

      if (text === "lista") {
        setTabLabelKeepingDots_v1(element, "Lista");
      }
    });
  }

  //###################################################################################
  // (6) INICIALIZACAO
  //###################################################################################

  function run() {
    normalizeTabLinks();
    normalizeVisibleTabLabels();
    activateProcessEditTab(getRequestedSettingsTab());
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