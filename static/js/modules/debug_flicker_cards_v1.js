(function () {
  "use strict";

  //###################################################################################
  // (1) CHECK DEBUG FLAG
  //###################################################################################
  let url = null;
  try {
    url = new URL(window.location.href);
  } catch (e) {
    return;
  }

  if (url.searchParams.get("debug_flicker") !== "1") {
    return;
  }

  //###################################################################################
  // (2) HELPER FUNCTIONS
  //###################################################################################
  function isSessionsCard(element) {
    if (!element) return false;
    if (element.id === "admin-sidebar-sections-form-card" || 
        element.id === "admin-sidebar-sections-card" || 
        element.id === "admin-sidebar-sections-inactive-card") {
      return true;
    }
    const text = element.textContent || "";
    if (text.includes("Criar sessão") || text.includes("Sessões ativas") || text.includes("Sessões inativas") ||
        text.includes("Criar sessao") || text.includes("Sessoes ativas") || text.includes("Sessoes inativas")) {
      return true;
    }
    if (element.getAttribute && element.getAttribute("data-admin-subprocess") === "sessoes") {
      return true;
    }
    return false;
  }

  function collectCards() {
    const elements = new Set();
    
    [
      "#menu-tabs-card",
      "#dynamic-process-card",
      "#admin-sidebar-sections-form-card",
      "#admin-sidebar-sections-card",
      "#admin-sidebar-sections-inactive-card",
      "#auth-profile-form-card",
      "#auth-profile-active-card",
      "#auth-profile-inactive-card"
    ].forEach(selector => {
      const el = document.querySelector(selector);
      if (el) elements.add(el);
    });
    
    document.querySelectorAll(".admin-subprocess-card-v1").forEach(el => elements.add(el));
    document.querySelectorAll("[data-standard-list-process-v1]").forEach(el => elements.add(el));
    document.querySelectorAll("[data-menu-scope]").forEach(el => elements.add(el));
    
    return Array.from(elements);
  }

  function getCardSnapshotData(element) {
    const rect = element.getBoundingClientRect ? element.getBoundingClientRect() : { width: 0, height: 0, top: 0, left: 0 };
    const computedStyle = window.getComputedStyle ? window.getComputedStyle(element) : {};
    const inlineDisplay = element.style ? element.style.display || "" : "";
    const computedDisplay = computedStyle.display || "";
    const visibility = computedStyle.visibility || "";
    const opacity = computedStyle.opacity || "";
    const offsetParentExists = element.offsetParent !== null;
    const textContent = element.textContent || "";
    
    const containsCriarSessao = textContent.includes("Criar sessão") || textContent.includes("Criar sessao");
    const containsSessoes = textContent.includes("Sessões") || textContent.includes("Sessoes");
    const containsCriarPerfil = textContent.includes("Criar perfil");
    const containsPerfis = textContent.includes("Perfis");

    return {
      id: element.id || "N/A",
      className: element.className || "",
      "data-menu-scope": element.getAttribute ? (element.getAttribute("data-menu-scope") || "") : "",
      "data-admin-subprocess": element.getAttribute ? (element.getAttribute("data-admin-subprocess") || "") : "",
      "display inline": inlineDisplay,
      "computed display": computedDisplay,
      visibility: visibility,
      opacity: opacity,
      "offsetParent existe": offsetParentExists,
      width: rect.width,
      height: rect.height,
      top: rect.top,
      left: rect.left,
      "contem Criar sessao": containsCriarSessao,
      "contem Sessoes": containsSessoes,
      "contem Criar perfil": containsCriarPerfil,
      "contem Perfis": containsPerfis
    };
  }

  function captureSnapshot(momento) {
    const cards = collectCards();
    const rows = cards.map(getCardSnapshotData);
    
    console.groupCollapsed(`[APPVERBO FLICKER DEBUG] ${momento}`);
    if (rows.length > 0) {
      console.table(rows);
    } else {
      console.log("Nenhum card monitorado encontrado no DOM.");
    }
    console.groupEnd();
  }

  //###################################################################################
  // (3) MUTATION OBSERVER
  //###################################################################################
  function logSessionsCardChange(element, mutation) {
    const timestamp = new Date().toISOString();
    const id = element.id || "";
    const className = element.className || "";
    let displayBefore = "N/A";
    let displayAfter = "N/A";
    
    if (mutation.type === "attributes" && mutation.attributeName === "style") {
      const oldStyle = mutation.oldValue || "";
      const matchOld = oldStyle.match(/display\s*:\s*([^;]+)/i);
      displayBefore = matchOld ? matchOld[1].trim() : "inline/default";
      
      const newStyle = element.getAttribute("style") || "";
      const matchNew = newStyle.match(/display\s*:\s*([^;]+)/i);
      displayAfter = matchNew ? matchNew[1].trim() : "inline/default";
    } else if (mutation.type === "attributes" && mutation.attributeName === "hidden") {
      displayBefore = mutation.oldValue !== null ? "hidden" : "visible";
      displayAfter = element.hasAttribute("hidden") ? "hidden" : "visible";
    }
    
    console.log(`[APPVERBO FLICKER DEBUG] Sessões card changed`, {
      timestamp,
      id,
      displayBefore,
      displayAfter,
      className,
      mutationType: mutation.type,
      attributeName: mutation.attributeName || "N/A"
    });
    console.trace();
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach(mutation => {
      if (mutation.type === "attributes") {
        if (isSessionsCard(mutation.target)) {
          logSessionsCardChange(mutation.target, mutation);
        }
      } else if (mutation.type === "childList") {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            if (isSessionsCard(node) || (node.querySelector && node.querySelector("#admin-sidebar-sections-card, #admin-sidebar-sections-form-card, #admin-sidebar-sections-inactive-card"))) {
              logSessionsCardChange(node, mutation);
            }
          }
        });
        mutation.removedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            if (isSessionsCard(node)) {
              logSessionsCardChange(node, mutation);
            }
          }
        });
      }
    });
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["style", "class", "hidden"],
    attributeOldValue: true,
    childList: true,
    subtree: true
  });

  setTimeout(() => {
    observer.disconnect();
  }, 2000);

  //###################################################################################
  // (4) SNAPSHOT SCHEDULER
  //###################################################################################
  captureSnapshot("script loaded");

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      captureSnapshot("DOMContentLoaded");
    });
  } else {
    captureSnapshot("DOMContentLoaded");
  }

  window.addEventListener("load", () => {
    captureSnapshot("window load");
  });

  requestAnimationFrame(() => {
    captureSnapshot("requestAnimationFrame 1");
    requestAnimationFrame(() => {
      captureSnapshot("requestAnimationFrame 2");
    });
  });

  setTimeout(() => { captureSnapshot("setTimeout 0ms"); }, 0);
  setTimeout(() => { captureSnapshot("setTimeout 50ms"); }, 50);
  setTimeout(() => { captureSnapshot("setTimeout 100ms"); }, 100);
  setTimeout(() => { captureSnapshot("setTimeout 300ms"); }, 300);
  setTimeout(() => { captureSnapshot("setTimeout 1000ms"); }, 1000);
})();
