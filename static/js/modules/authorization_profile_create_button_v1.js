(function initAuthorizationProfileCreateButtonV1() {
  "use strict";

  const TARGET_PATH = "/users/new";
  const CREATE_LABEL = "Criar perfil";
  const HISTORY_TITLE = "Lista de perfis criados";
  const HISTORY_EMPTY = "Sem perfis criados.";

  if (!window.location || window.location.pathname !== TARGET_PATH) {
    return;
  }

  function normalizeLookupTextV1(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[_-]+/g, " ")
      .replace(/\s+/g, " ");
  }

  function normalizeRuntimeMenuKeyV1(value) {
    if (typeof window.normalizeMenuKey === "function") {
      return window.normalizeMenuKey(value);
    }

    return String(value || "").trim().toLowerCase();
  }

  function isAuthorizationProfileProcessV1(menuKey, menuLabel, sectionLabel) {
    const joined = [menuKey, menuLabel, sectionLabel]
      .map(normalizeLookupTextV1)
      .filter(Boolean)
      .join(" ");

    if (!joined) {
      return false;
    }

    return (
      (joined.includes("perfil") && joined.includes("autorizacao")) ||
      (joined.includes("profile") && joined.includes("authorization"))
    );
  }

  function patchHistoryDetectionV1() {
    if (
      typeof window.isHistoryProcessMenu === "function" &&
      !window.isHistoryProcessMenu.__authProfilePatchedV1
    ) {
      const originalIsHistoryProcessMenu = window.isHistoryProcessMenu;
      const patchedIsHistoryProcessMenu = function patchedIsHistoryProcessMenu(menuKey, menuLabel, sectionLabel) {
        if (isAuthorizationProfileProcessV1(menuKey, menuLabel, sectionLabel)) {
          return true;
        }

        return originalIsHistoryProcessMenu.apply(this, arguments);
      };

      patchedIsHistoryProcessMenu.__authProfilePatchedV1 = true;
      window.isHistoryProcessMenu = patchedIsHistoryProcessMenu;
    }

    if (
      typeof window.getHistoryRecordLabels === "function" &&
      !window.getHistoryRecordLabels.__authProfilePatchedV1
    ) {
      const originalGetHistoryRecordLabels = window.getHistoryRecordLabels;
      const patchedGetHistoryRecordLabels = function patchedGetHistoryRecordLabels(menuKey, menuLabel, sectionLabel) {
        if (isAuthorizationProfileProcessV1(menuKey, menuLabel, sectionLabel)) {
          return { singular: "perfil", plural: "perfis" };
        }

        return originalGetHistoryRecordLabels.apply(this, arguments);
      };

      patchedGetHistoryRecordLabels.__authProfilePatchedV1 = true;
      window.getHistoryRecordLabels = patchedGetHistoryRecordLabels;
    }
  }

  function getCurrentAuthorizationProfileTextsV1() {
    const processShellTitleEl = document.getElementById("process-shell-title");
    const dynamicTitleEl = document.getElementById("dynamic-process-title");
    const activeSidebarEl = document.querySelector(".menu-item.active");
    const activeSubmenuEl = document.querySelector("#submenu-items .submenu-item.active");
    const menuKeyInputEl = document.getElementById("dynamic-process-menu-key");
    const urlParams = new URLSearchParams(window.location.search || "");

    return [
      menuKeyInputEl ? menuKeyInputEl.value : "",
      urlParams.get("menu") || "",
      activeSidebarEl ? activeSidebarEl.textContent : "",
      processShellTitleEl ? processShellTitleEl.textContent : "",
      dynamicTitleEl ? dynamicTitleEl.textContent : "",
      activeSubmenuEl ? activeSubmenuEl.textContent : ""
    ];
  }

  function isCurrentAuthorizationProfilePageV1() {
    const texts = getCurrentAuthorizationProfileTextsV1();
    return isAuthorizationProfileProcessV1(texts[0], texts.slice(1).join(" "), "");
  }

  function getCurrentDynamicProcessKeysV1() {
    const menuKeyInputEl = document.getElementById("dynamic-process-menu-key");
    const sectionKeyInputEl = document.getElementById("dynamic-process-section-key");
    const urlParams = new URLSearchParams(window.location.search || "");
    const activeSubmenuEl = document.querySelector(
      "#submenu-items .submenu-item.active[data-dynamic-process-section]"
    );

    const rawMenuKey = String(
      (menuKeyInputEl && menuKeyInputEl.value) ||
      urlParams.get("menu") ||
      ""
    ).trim();

    return {
      menuKey: normalizeRuntimeMenuKeyV1(rawMenuKey),
      sectionKey: String(
        (sectionKeyInputEl && sectionKeyInputEl.value) ||
        (activeSubmenuEl && activeSubmenuEl.dataset
          ? activeSubmenuEl.dataset.dynamicProcessSection
          : "") ||
        ""
      ).trim()
    };
  }

  function rerenderCurrentDynamicProcessV1() {
    if (typeof window.renderDynamicProcessCard !== "function") {
      return;
    }

    const processKeys = getCurrentDynamicProcessKeysV1();
    if (!processKeys.menuKey) {
      return;
    }

    try {
      window.renderDynamicProcessCard(processKeys.menuKey, processKeys.sectionKey);
    } catch (error) {
      console.warn("Falha ao atualizar o botão do Perfil de autorização:", error);
    }
  }

  function patchCreateButtonDomV1() {
    const cardEl = document.getElementById("dynamic-process-card");

    if (!cardEl || cardEl.style.display === "none") {
      return;
    }

    if (!isCurrentAuthorizationProfilePageV1()) {
      return;
    }

    const editToggleEl = document.getElementById("dynamic-process-edit-toggle");
    const actionInputEl = document.getElementById("dynamic-process-history-action");
    const recordInputEl = document.getElementById("dynamic-process-history-record-id");
    const submitEl = document.getElementById("dynamic-process-submit-btn");
    const historyTitleEl = document.getElementById("dynamic-process-history-title");
    const historyEmptyEl = document.getElementById("dynamic-process-history-empty");

    if (editToggleEl) {
      editToggleEl.textContent = CREATE_LABEL;
      editToggleEl.title = CREATE_LABEL;
      editToggleEl.setAttribute("aria-label", CREATE_LABEL);

      if (editToggleEl.dataset.authProfileCreateReady !== "1") {
        editToggleEl.dataset.authProfileCreateReady = "1";
        editToggleEl.addEventListener(
          "click",
          function resetCreateProfileActionV1() {
            if (!isCurrentAuthorizationProfilePageV1()) {
              return;
            }

            if (actionInputEl) {
              actionInputEl.value = "create";
            }

            if (recordInputEl) {
              recordInputEl.value = "";
            }

            if (submitEl) {
              submitEl.textContent = "Guardar";
            }
          },
          true
        );
      }
    }

    if (historyTitleEl) {
      historyTitleEl.textContent = HISTORY_TITLE;
    }

    if (historyEmptyEl) {
      historyEmptyEl.textContent = HISTORY_EMPTY;
    }
  }

  let didRequestRerender = false;

  function applyAuthorizationProfilePatchV1() {
    patchHistoryDetectionV1();

    if (!didRequestRerender && isCurrentAuthorizationProfilePageV1()) {
      didRequestRerender = true;
      rerenderCurrentDynamicProcessV1();
    }

    patchCreateButtonDomV1();
  }

  function scheduleAuthorizationProfilePatchV1() {
    window.requestAnimationFrame(applyAuthorizationProfilePatchV1);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleAuthorizationProfilePatchV1);
  } else {
    scheduleAuthorizationProfilePatchV1();
  }

  window.setTimeout(applyAuthorizationProfilePatchV1, 250);
  window.setTimeout(applyAuthorizationProfilePatchV1, 800);

  const observerTarget = document.getElementById("dynamic-process-card") || document.body;
  if (observerTarget && window.MutationObserver) {
    const observer = new MutationObserver(scheduleAuthorizationProfilePatchV1);
    observer.observe(observerTarget, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["style", "class"]
    });
  }
})();
