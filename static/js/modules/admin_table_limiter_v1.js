//###################################################################################
// (1) ADMIN TABLE LIMITER V1
//###################################################################################
(function registerAdminTableLimiterV1() {
  "use strict";

  function setupTableLimiterV1(config) {
    const safeConfig = config || {};
    const prefix = String(safeConfig.prefix || "").trim();
    if (!prefix) {
      return;
    }

    const tableEl = document.getElementById(prefix + "-table");
    const limiterEl = document.getElementById(prefix + "-limiter");
    const pageSizeEl = document.getElementById(prefix + "-page-size");
    const prevEl = document.getElementById(prefix + "-prev");
    const nextEl = document.getElementById(prefix + "-next");
    const pageEl = document.getElementById(prefix + "-page");
    if (!tableEl || !limiterEl || !pageSizeEl || !prevEl || !nextEl || !pageEl) {
      return;
    }

    const rows = Array.from(tableEl.querySelectorAll("tbody tr"));
    if (!rows.length) {
      limiterEl.style.display = "none";
      return;
    }

    let pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
    let currentPage = 1;

    function getFilteredRows() {
      return rows.filter((row) => row.dataset.adminSearchMatchV1 !== "0");
    }

    function getTotalPages() {
      const filteredRows = getFilteredRows();
      return Math.max(1, Math.ceil(filteredRows.length / pageSize));
    }

    function render() {
      const filteredRows = getFilteredRows();
      const totalPages = getTotalPages();
      if (currentPage > totalPages) {
        currentPage = totalPages;
      }
      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize;

      const filteredRowSet = new Set(filteredRows);
      rows.forEach((row) => {
        if (!filteredRowSet.has(row)) {
          row.style.display = "none";
        }
      });

      filteredRows.forEach((row, index) => {
        row.style.display = index >= start && index < end ? "" : "none";
      });
      pageEl.textContent = String(currentPage);
      prevEl.disabled = currentPage <= 1;
      nextEl.disabled = currentPage >= totalPages;
    }

    pageSizeEl.addEventListener("change", () => {
      pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
      currentPage = 1;
      render();
    });

    prevEl.addEventListener("click", () => {
      if (currentPage <= 1) {
        return;
      }
      currentPage -= 1;
      render();
    });

    nextEl.addEventListener("click", () => {
      const totalPages = getTotalPages();
      if (currentPage >= totalPages) {
        return;
      }
      currentPage += 1;
      render();
    });

    tableEl.addEventListener("admin-table-filter-changed", () => {
      currentPage = 1;
      render();
    });

    render();
  }

  window.APPVERBO_SETUP_TABLE_LIMITER_V1 = setupTableLimiterV1;
})();
