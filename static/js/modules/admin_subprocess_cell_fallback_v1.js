//###################################################################################
// (1) ADMIN SUBPROCESS CELL FALLBACK V1
//###################################################################################
(function registerAdminSubprocessCellFallbackV1() {
  "use strict";

  const DEBUG_LOGGER_V1 = "APPVERBO_SESSOES_DEPARTMENT_FALLBACK_V1";
  let observerStartedV1 = false;
  let scheduledRunV1 = 0;
  let debugLoggedV1 = false;

  function safeTextV1(value) {
    return String(value === null || value === undefined ? "" : value).trim();
  }

  function collectSessionDepartmentSnapshotV1() {
    return Array.from(
      document.querySelectorAll(
        "[data-admin-subprocess='sessoes'] .admin-subprocess-table-v1 tbody tr"
      )
    ).map(function (rowEl) {
      const departmentCellEl = rowEl.querySelector(
        "td[data-admin-column-key='department']"
      );
      return {
        key: safeTextV1(rowEl.getAttribute("data-admin-row-key")),
        fallbackLabel: safeTextV1(
          rowEl.getAttribute("data-admin-row-department-label")
        ),
        fallbackValue: safeTextV1(rowEl.getAttribute("data-admin-row-department")),
        renderedText: safeTextV1(
          departmentCellEl ? departmentCellEl.textContent : ""
        ),
      };
    });
  }

  function repairSessionDepartmentCellsV1() {
    const rows = Array.from(
      document.querySelectorAll(
        "[data-admin-subprocess='sessoes'] .admin-subprocess-table-v1 tbody tr"
      )
    );
    let restoredCount = 0;

    rows.forEach(function (rowEl) {
      const departmentCellEl = rowEl.querySelector(
        "td[data-admin-column-key='department']"
      );

      if (!departmentCellEl) {
        return;
      }

      const renderedText = safeTextV1(departmentCellEl.textContent);
      const fallbackText =
        safeTextV1(rowEl.getAttribute("data-admin-row-department-label")) ||
        safeTextV1(rowEl.getAttribute("data-admin-row-department")) ||
        safeTextV1(departmentCellEl.getAttribute("data-admin-cell-fallback"));

      if (renderedText || !fallbackText) {
        return;
      }

      departmentCellEl.textContent = fallbackText;
      departmentCellEl.setAttribute("title", fallbackText);
      restoredCount += 1;
    });

    if (!debugLoggedV1) {
      console.info("[" + DEBUG_LOGGER_V1 + "] snapshot", collectSessionDepartmentSnapshotV1());
      debugLoggedV1 = true;
      return;
    }

    if (restoredCount > 0) {
      console.info("[" + DEBUG_LOGGER_V1 + "] restored", {
        restoredCount: restoredCount,
        rows: collectSessionDepartmentSnapshotV1(),
      });
    }
  }

  function scheduleRepairV1() {
    if (scheduledRunV1) {
      window.clearTimeout(scheduledRunV1);
    }

    scheduledRunV1 = window.setTimeout(function () {
      scheduledRunV1 = 0;
      repairSessionDepartmentCellsV1();
    }, 60);
  }

  function startObserverV1() {
    if (observerStartedV1 || !document.body) {
      return;
    }

    const observer = new MutationObserver(function () {
      scheduleRepairV1();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    observerStartedV1 = true;
  }

  function initializeV1() {
    repairSessionDepartmentCellsV1();
    window.setTimeout(repairSessionDepartmentCellsV1, 200);
    window.setTimeout(repairSessionDepartmentCellsV1, 800);
    startObserverV1();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeV1, { once: true });
  } else {
    initializeV1();
  }
})();
