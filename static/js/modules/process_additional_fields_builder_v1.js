//###################################################################################
// (1) PROCESS ADDITIONAL FIELDS BUILDER V1
//###################################################################################
(function registerProcessAdditionalFieldsBuilderV1() {
  "use strict";

  function setupProcessAdditionalFieldsBuilder() {
    const builderEl = document.getElementById("process-additional-fields-builder");
    if (!builderEl) {
      return;
    }

    const fieldTypesRaw = builderEl.getAttribute("data-field-types") || "[]";
    let fieldTypes = [];
    try {
      fieldTypes = JSON.parse(fieldTypesRaw);
    } catch (_error) {
      fieldTypes = [];
    }
    if (!Array.isArray(fieldTypes) || !fieldTypes.length) {
      fieldTypes = [
        { key: "text", label: "Texto" },
        { key: "textarea", label: "Texto longo" },
        { key: "number", label: "Número" },
        { key: "email", label: "Email" },
        { key: "phone", label: "Telefone" },
        { key: "date", label: "Data" },
        { key: "flag", label: "Flag" }
      ];
    }

    const containerEl = document.getElementById("process-additional-fields-container");
    const addButtonEl = document.getElementById("process-additional-field-add-btn");
    const formEl = builderEl.closest("form");
    const moveFormEl = document.getElementById("process-additional-field-move-form");
    const limiterEl = document.getElementById("process-additional-fields-limiter");
    const pageSizeEl = document.getElementById("process-additional-fields-page-size");
    const prevEl = document.getElementById("process-additional-fields-prev");
    const nextEl = document.getElementById("process-additional-fields-next");
    const pageEl = document.getElementById("process-additional-fields-page");
    if (!containerEl || !addButtonEl || !formEl) {
      return;
    }

    const sizedTypes = new Set(["text", "textarea", "number", "email", "phone"]);
    let additionalFieldsPageSize = Number.parseInt(pageSizeEl ? pageSizeEl.value : "5", 10) || 5;
    let additionalFieldsCurrentPage = 1;

    function renderTypeOptions(selectedType) {
      return fieldTypes
        .map((item) => {
          const optionKey = String(item.key || "");
          const optionLabel = String(item.label || optionKey);
          const isSelected = optionKey === String(selectedType || "text");
          return `<option value="${optionKey}"${isSelected ? " selected" : ""}>${optionLabel}</option>`;
        })
        .join("");
    }

    function syncRowState(rowEl) {
      const typeSelectEl = rowEl.querySelector("select[name='additional_field_type']");
      const requiredSelectEl = rowEl.querySelector("select[name='additional_field_required']");
      const sizeInputEl = rowEl.querySelector("input[name='additional_field_size']");
      if (!typeSelectEl || !sizeInputEl) {
        return;
      }
      const cleanType = String(typeSelectEl.value || "text").trim().toLowerCase();
      if (cleanType === "header" && requiredSelectEl) {
        requiredSelectEl.value = "0";
      }
      rowEl.classList.toggle("process-additional-field-row-header", cleanType === "header");
      const isSizeEnabled = sizedTypes.has(cleanType);
      if (isSizeEnabled) {
        sizeInputEl.readOnly = false;
        sizeInputEl.classList.remove("process-additional-size-readonly");
        if (!String(sizeInputEl.value || "").trim()) {
          sizeInputEl.value = "30";
        }
      } else {
        sizeInputEl.value = "";
        sizeInputEl.readOnly = true;
        sizeInputEl.classList.add("process-additional-size-readonly");
      }
    }

    function renderAdditionalFieldsPagination() {
      if (!limiterEl || !pageSizeEl || !prevEl || !nextEl || !pageEl) {
        return;
      }

      const rowEls = Array.from(containerEl.querySelectorAll(".process-additional-field-row"));
      if (!rowEls.length) {
        limiterEl.style.display = "none";
        return;
      }

      const totalPages = Math.max(1, Math.ceil(rowEls.length / additionalFieldsPageSize));
      if (additionalFieldsCurrentPage > totalPages) {
        additionalFieldsCurrentPage = totalPages;
      }

      const start = (additionalFieldsCurrentPage - 1) * additionalFieldsPageSize;
      const end = start + additionalFieldsPageSize;

      rowEls.forEach((rowEl, index) => {
        rowEl.style.display = index >= start && index < end ? "" : "none";
      });

      pageEl.textContent = String(additionalFieldsCurrentPage);
      prevEl.disabled = additionalFieldsCurrentPage <= 1;
      nextEl.disabled = additionalFieldsCurrentPage >= totalPages;
      limiterEl.style.display = rowEls.length > additionalFieldsPageSize ? "flex" : "none";
    }

    function bindRemoveButton(buttonEl) {
      buttonEl.addEventListener("click", () => {
        const rowEl = buttonEl.closest(".process-additional-field-row");
        if (rowEl) {
          rowEl.remove();
          renderAdditionalFieldsPagination();
        }
      });
    }

    function submitMoveRequest(buttonEl) {
      if (!moveFormEl || !buttonEl) {
        return;
      }

      const menuKey = String(buttonEl.getAttribute("data-menu-key") || "").trim();
      const fieldKey = String(buttonEl.getAttribute("data-field-key") || "").trim();
      const direction = String(buttonEl.getAttribute("data-move-direction") || "").trim().toLowerCase();
      const redirectMenu = String(buttonEl.getAttribute("data-redirect-menu") || "").trim();
      const redirectTarget = String(buttonEl.getAttribute("data-redirect-target") || "#settings-menu-edit-card").trim();

      if (!menuKey || !fieldKey || (direction !== "up" && direction !== "down")) {
        return;
      }

      const menuKeyEl = moveFormEl.querySelector('input[name="menu_key"]');
      const fieldKeyEl = moveFormEl.querySelector('input[name="field_key"]');
      const directionEl = moveFormEl.querySelector('input[name="direction"]');
      const redirectMenuEl = moveFormEl.querySelector('input[name="redirect_menu"]');
      const redirectTargetEl = moveFormEl.querySelector('input[name="redirect_target"]');

      if (!menuKeyEl || !fieldKeyEl || !directionEl || !redirectMenuEl || !redirectTargetEl) {
        return;
      }

      menuKeyEl.value = menuKey;
      fieldKeyEl.value = fieldKey;
      directionEl.value = direction;
      redirectMenuEl.value = redirectMenu;
      redirectTargetEl.value = redirectTarget;

      moveFormEl.submit();
    }

    function bindRow(rowEl) {
      const removeButtonEl = rowEl.querySelector(".process-additional-field-remove-btn");
      if (removeButtonEl) {
        bindRemoveButton(removeButtonEl);
      }
      rowEl.querySelectorAll(".process-additional-field-move-btn").forEach((buttonEl) => {
        if (buttonEl.dataset.moveBound === "1") {
          return;
        }
        buttonEl.dataset.moveBound = "1";
        buttonEl.addEventListener("click", () => {
          submitMoveRequest(buttonEl);
        });
      });
      const typeSelectEl = rowEl.querySelector("select[name='additional_field_type']");
      if (typeSelectEl) {
        typeSelectEl.addEventListener("change", () => {
          syncRowState(rowEl);
        });
      }
      syncRowState(rowEl);
    }

    function createAdditionalFieldRow(initialValue, initialType, initialRequired, initialSize) {
      const rowEl = document.createElement("div");
      rowEl.className = "process-field-row process-additional-field-row";
      rowEl.innerHTML = `
      <input type="hidden" name="additional_field_key" value="">
      <div class="field">
        <label>Nome do campo adicional</label>
        <input
          type="text"
          name="additional_field_label"
          maxlength="80"
          placeholder="Ex.: Data de batismo"
          value="${String(initialValue || "").replace(/"/g, "&quot;")}"
        >
      </div>
      <div class="field">
        <label>Tipo do campo</label>
        <select name="additional_field_type" class="process-additional-field-type-select">
          ${renderTypeOptions(initialType || "text")}
        </select>
      </div>
      <div class="field">
        <label>Obrigatório</label>
        <select name="additional_field_required" class="process-additional-field-required-select">
          <option value="0"${String(initialRequired || "0") === "0" ? " selected" : ""}>Não</option>
          <option value="1"${String(initialRequired || "0") === "1" ? " selected" : ""}>Sim</option>
        </select>
      </div>
      <div class="field">
        <label>Tamanho</label>
        <input
          type="number"
          name="additional_field_size"
          class="process-additional-field-size-input"
          min="1"
          max="4000"
          placeholder=""
          value="${String(initialSize || "")}"
        >
      </div>
      <button
        type="button"
        class="table-icon-btn table-icon-btn-danger process-additional-field-remove-btn"
        title="Remover campo adicional"
        aria-label="Remover campo adicional"
      >
        &#10005;
      </button>
    `;
      bindRow(rowEl);
      return rowEl;
    }

    containerEl.querySelectorAll(".process-additional-field-row").forEach((rowEl) => {
      bindRow(rowEl);
    });

    addButtonEl.addEventListener("click", () => {
      const rowEl = createAdditionalFieldRow("", "text", "0", "30");
      containerEl.appendChild(rowEl);
      const totalRows = containerEl.querySelectorAll(".process-additional-field-row").length;
      additionalFieldsCurrentPage = Math.max(1, Math.ceil(totalRows / additionalFieldsPageSize));
      renderAdditionalFieldsPagination();
      const inputEl = rowEl.querySelector("input[name='additional_field_label']");
      if (inputEl) {
        inputEl.focus();
      }
    });

    if (pageSizeEl && prevEl && nextEl && pageEl) {
      pageSizeEl.addEventListener("change", () => {
        additionalFieldsPageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
        additionalFieldsCurrentPage = 1;
        renderAdditionalFieldsPagination();
      });

      prevEl.addEventListener("click", () => {
        if (additionalFieldsCurrentPage <= 1) {
          return;
        }
        additionalFieldsCurrentPage -= 1;
        renderAdditionalFieldsPagination();
      });

      nextEl.addEventListener("click", () => {
        const rowCount = containerEl.querySelectorAll(".process-additional-field-row").length;
        const totalPages = Math.max(1, Math.ceil(rowCount / additionalFieldsPageSize));
        if (additionalFieldsCurrentPage >= totalPages) {
          return;
        }
        additionalFieldsCurrentPage += 1;
        renderAdditionalFieldsPagination();
      });
    }

    formEl.addEventListener("submit", () => {
      const rowEls = containerEl.querySelectorAll(".process-additional-field-row");
      rowEls.forEach((rowEl) => {
        const keyEl = rowEl.querySelector("input[name='additional_field_key']");
        const labelEl = rowEl.querySelector("input[name='additional_field_label']");
        const typeEl = rowEl.querySelector("select[name='additional_field_type']");
        const requiredEl = rowEl.querySelector("select[name='additional_field_required']");
        const sizeEl = rowEl.querySelector("input[name='additional_field_size']");
        if (!labelEl || !typeEl || !requiredEl || !sizeEl) {
          return;
        }
        const cleanLabel = String(labelEl.value || "").trim();
        labelEl.value = cleanLabel;
        const cleanType = String(typeEl.value || "text").trim().toLowerCase();
        if (cleanType === "header") {
          requiredEl.value = "0";
        }
        const isSizeEnabled = sizedTypes.has(cleanType);
        if (!isSizeEnabled) {
          sizeEl.value = "";
        }

        if (!cleanLabel) {
          if (keyEl) {
            keyEl.removeAttribute("name");
          }
          labelEl.removeAttribute("name");
          typeEl.removeAttribute("name");
          requiredEl.removeAttribute("name");
          sizeEl.removeAttribute("name");
        }
      });
    });

    renderAdditionalFieldsPagination();
  }

  window.APPVERBO_SETUP_PROCESS_ADDITIONAL_FIELDS_BUILDER_V1 = setupProcessAdditionalFieldsBuilder;
})();
