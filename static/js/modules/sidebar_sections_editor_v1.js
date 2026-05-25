//###################################################################################
// (1) SIDEBAR SECTIONS EDITOR V1
//###################################################################################
(function registerSidebarSectionsEditorV1() {
  "use strict";

  function setupSidebarSectionsEditor() {
    const sectionsBodyEl = document.getElementById("sidebar-sections-created-body");
    if (!sectionsBodyEl) {
      return;
    }

    const refreshActionStates = () => {
      const rows = Array.from(sectionsBodyEl.querySelectorAll("[data-sidebar-section-row]"));
      rows.forEach((rowEl, index) => {
        const upBtn = rowEl.querySelector("[data-sidebar-section-action='up']");
        const downBtn = rowEl.querySelector("[data-sidebar-section-action='down']");
        const removeBtn = rowEl.querySelector("[data-sidebar-section-action='remove']");
        const sectionKey = String(rowEl.getAttribute("data-sidebar-section-key") || "").trim().toLowerCase();
        const isProtected = sectionKey === "geral" || sectionKey === "igreja";

        if (upBtn) {
          upBtn.disabled = index === 0;
          upBtn.classList.toggle("table-icon-btn-disabled", upBtn.disabled);
        }
        if (downBtn) {
          downBtn.disabled = index === rows.length - 1;
          downBtn.classList.toggle("table-icon-btn-disabled", downBtn.disabled);
        }
        if (removeBtn) {
          removeBtn.disabled = rows.length <= 1 || isProtected;
          removeBtn.classList.toggle("table-icon-btn-disabled", removeBtn.disabled);
        }
      });
    };

    sectionsBodyEl.addEventListener("click", (event) => {
      const actionBtn = event.target.closest("[data-sidebar-section-action]");
      if (!actionBtn) {
        return;
      }
      const actionType = String(actionBtn.getAttribute("data-sidebar-section-action") || "").trim().toLowerCase();
      const rowEl = actionBtn.closest("[data-sidebar-section-row]");
      if (!rowEl || actionBtn.disabled) {
        return;
      }

      if (actionType === "up") {
        const previousRow = rowEl.previousElementSibling;
        if (previousRow) {
          sectionsBodyEl.insertBefore(rowEl, previousRow);
        }
        refreshActionStates();
        return;
      }

      if (actionType === "down") {
        const nextRow = rowEl.nextElementSibling;
        if (nextRow) {
          sectionsBodyEl.insertBefore(nextRow, rowEl);
        }
        refreshActionStates();
        return;
      }

      if (actionType === "remove") {
        rowEl.remove();
        refreshActionStates();
      }
    });

    refreshActionStates();
  }

  window.APPVERBO_SETUP_SIDEBAR_SECTIONS_EDITOR_V1 = setupSidebarSectionsEditor;
})();
