(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizeText(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function buildKeyFromLabel(value) {
    return normalizeText(value)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  //###################################################################################
  // (2) LOCALIZAR CARD DE SESSOES DO SIDEBAR
  //###################################################################################

  function findSidebarSectionsCard() {
    const cards = Array.from(document.querySelectorAll(".card, section"));

    return cards.find((card) => {
      const headings = Array.from(card.querySelectorAll("h1, h2, h3"));
      return headings.some((heading) => {
        const text = normalizeText(heading.textContent);
        return text.includes("sessoes do sidebar") || text.includes("sessoes criadas");
      });
    });
  }

  function findCreatedSectionsArea(card) {
    if (!card) {
      return null;
    }

    const headings = Array.from(card.querySelectorAll("h3, h4, strong, legend"));
    const heading = headings.find((item) => normalizeText(item.textContent).includes("sessoes criadas"));

    if (!heading) {
      return card;
    }

    return (
      heading.closest(".admin-subsection") ||
      heading.closest(".entity-panel-card") ||
      heading.parentElement ||
      card
    );
  }

  //###################################################################################
  // (3) COLETAR LINHAS DAS SESSOES CRIADAS
  //###################################################################################

  function getRowForElement(element) {
    return (
      element.closest("tr") ||
      element.closest(".sidebar-section-row") ||
      element.closest(".settings-row") ||
      element.closest(".menu-row") ||
      element.parentElement?.parentElement ||
      element.parentElement
    );
  }

  function getLabelInput(row) {
    if (!row) {
      return null;
    }

    return (
      row.querySelector('input[name*="section_label"]') ||
      row.querySelector('input[name*="label"]') ||
      row.querySelector('input[type="text"]') ||
      row.querySelector("input:not([type])")
    );
  }

  function getKeyInput(row) {
    if (!row) {
      return null;
    }

    return (
      row.querySelector('input[name*="section_key"]') ||
      row.querySelector('input[name*="key"][type="hidden"]') ||
      row.querySelector('input[type="hidden"][name*="key"]')
    );
  }

  function collectSectionRows(area) {
    const selects = Array.from(area.querySelectorAll("select"));
    const rows = [];

    selects.forEach((selectElement) => {
      const row = getRowForElement(selectElement);
      const labelInput = getLabelInput(row);

      if (!row || !labelInput) {
        return;
      }

      const label = String(labelInput.value || "").trim();

      if (!label) {
        return;
      }

      const keyInput = getKeyInput(row);
      const key = String(keyInput?.value || row.dataset.sectionKey || buildKeyFromLabel(label)).trim();

      rows.push({
        key: key,
        label: label,
        visibility: String(selectElement.value || "all").trim() || "all",
      });
    });

    return rows;
  }

  //###################################################################################
  // (4) MENSAGEM LOCAL SEM MUDAR DE TELA
  //###################################################################################

  function getStatusElement(area) {
    let statusElement = area.querySelector("[data-sidebar-sections-autosave-status='1']");

    if (statusElement) {
      return statusElement;
    }

    statusElement = document.createElement("div");
    statusElement.dataset.sidebarSectionsAutosaveStatus = "1";
    statusElement.style.marginTop = "8px";
    statusElement.style.fontSize = "12px";
    statusElement.style.fontWeight = "600";
    statusElement.style.color = "#1f6f43";
    statusElement.style.display = "none";

    area.appendChild(statusElement);

    return statusElement;
  }

  function showStatus(area, message, isError) {
    const statusElement = getStatusElement(area);

    statusElement.textContent = message;
    statusElement.style.color = isError ? "#b42318" : "#1f6f43";
    statusElement.style.display = "block";

    window.clearTimeout(statusElement._hideTimer);
    statusElement._hideTimer = window.setTimeout(() => {
      statusElement.style.display = "none";
    }, 3500);
  }

  //###################################################################################
  // (5) SUBMETER ALTERACOES SEM REFRESH
  //###################################################################################

  let submitTimer = null;
  let isSubmitting = false;
  let pendingSubmit = false;

  function buildFormData(rows) {
    const formData = new FormData();

    rows.forEach((row) => {
      formData.append("section_key", row.key);
      formData.append("section_label", row.label);
      formData.append("section_visibility_scope_mode", row.visibility);
    });

    formData.append("redirect_menu", "administrativo");
    formData.append("redirect_target", "#settings-menu-edit-card");

    return formData;
  }

  function submitSidebarSections(area) {
    if (isSubmitting) {
      pendingSubmit = true;
      return;
    }

    const rows = collectSectionRows(area);

    if (!rows.length) {
      return;
    }

    isSubmitting = true;
    pendingSubmit = false;

    showStatus(area, "A gravar alteração...", false);

    fetch("/settings/menu/sidebar-sections", {
      method: "POST",
      body: buildFormData(rows),
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "fetch"
      }
    })
      .then((response) => {
        if (!response.ok && !response.redirected) {
          throw new Error("Falha HTTP " + response.status);
        }

        showStatus(area, "Alteração gravada. A tela foi mantida.", false);
      })
      .catch((error) => {
        console.error("Erro ao gravar sessões do sidebar:", error);
        showStatus(area, "Erro ao gravar. Atualize a página e tente novamente.", true);
      })
      .finally(() => {
        isSubmitting = false;

        if (pendingSubmit) {
          pendingSubmit = false;
          window.setTimeout(() => submitSidebarSections(area), 250);
        }
      });
  }

  function scheduleSubmit(area) {
    window.clearTimeout(submitTimer);
    submitTimer = window.setTimeout(() => submitSidebarSections(area), 350);
  }

  //###################################################################################
  // (6) INICIALIZAR EVENTOS
  //###################################################################################

  function initSidebarSectionsAutosave() {
    const card = findSidebarSectionsCard();
    const area = findCreatedSectionsArea(card);

    if (!area) {
      return;
    }

    area.addEventListener("change", (event) => {
      const target = event.target;

      if (!(target instanceof HTMLSelectElement) && !(target instanceof HTMLInputElement)) {
        return;
      }

      const row = getRowForElement(target);
      const labelInput = getLabelInput(row);

      if (!labelInput || !String(labelInput.value || "").trim()) {
        return;
      }

      scheduleSubmit(area);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidebarSectionsAutosave);
  } else {
    initSidebarSectionsAutosave();
  }
})();
