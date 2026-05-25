// APPVERBO_PROFILE_ALLOCATION_MULTIVALUE_V1_MODULE_START
(function registerProfileAllocationMultivalueV1Module() {
  "use strict";

  //###################################################################################
  // (1) FACTORY
  //###################################################################################
  window.APPVERBO_CREATE_PROFILE_ALLOCATION_MULTIVALUE_API_V1 = function createProfileAllocationMultivalueApiV1(
    options
  ) {
    const deps = options && typeof options === "object" ? options : {};
    const normalizeLookupText =
      typeof deps.normalizeLookupText === "function"
        ? deps.normalizeLookupText
        : function defaultNormalizeLookupText(value) {
            return String(value || "")
              .normalize("NFD")
              .replace(/[\u0300-\u036f]/g, "")
              .replace(/[^a-zA-Z0-9]/g, "_")
              .replace(/_+/g, "_")
              .replace(/^_+|_+$/g, "")
              .toLowerCase();
          };

    //###################################################################################
    // (2) HELPERS
    //###################################################################################
    function normalizeProfileMultiValueList(rawValue) {
      return String(rawValue || "")
        .split(/\r?\n|,/)
        .map((item) => String(item || "").trim())
        .filter(Boolean);
    }

    function isAllocationProfileSection(sectionKey) {
      const cleanSection = normalizeLookupText(sectionKey);
      if (!cleanSection) {
        return false;
      }
      return cleanSection.includes("alocacao");
    }

    function setProfileControlValue(controlEl, value) {
      if (!controlEl) {
        return;
      }
      const cleanValue = String(value || "").trim();
      if (controlEl.tagName === "SELECT") {
        const options = Array.from(controlEl.options || []);
        const hasExactValue = options.some((option) => String(option.value || "") === cleanValue);
        if (hasExactValue) {
          controlEl.value = cleanValue;
          return;
        }
        const matchingOption = options.find(
          (option) => String(option.textContent || "").trim().toLowerCase() === cleanValue.toLowerCase()
        );
        controlEl.value = matchingOption ? String(matchingOption.value || "") : "";
        return;
      }
      controlEl.value = cleanValue;
    }

    //###################################################################################
    // (3) RUNTIME
    //###################################################################################
    function setupAllocationFieldMultiValue(fieldEl) {
      if (!fieldEl || fieldEl.getAttribute("data-allocation-multi-ready") === "1") {
        return;
      }
      const baseControlEl = fieldEl.querySelector(
        "input[name^='custom_field__']:not([type='checkbox']):not([type='hidden']), select[name^='custom_field__'], textarea[name^='custom_field__']"
      );
      if (!baseControlEl) {
        return;
      }
      const baseFieldName = String(baseControlEl.getAttribute("name") || "").trim();
      if (!baseFieldName) {
        return;
      }

      const baseLabelEl = fieldEl.querySelector("label");
      if (baseLabelEl && !baseLabelEl.classList.contains("profile-multi-value-label")) {
        baseLabelEl.classList.add("profile-multi-value-label");
      }

      const valuesListEl = document.createElement("div");
      valuesListEl.className = "profile-multi-value-list";

      const addButtonEl = document.createElement("button");
      addButtonEl.type = "button";
      addButtonEl.className = "table-icon-btn profile-multi-value-add-btn";
      addButtonEl.title = "Adicionar linha";
      addButtonEl.setAttribute("aria-label", "Adicionar linha");
      addButtonEl.innerHTML = "&#43;";
      if (baseLabelEl) {
        baseLabelEl.appendChild(addButtonEl);
      } else {
        fieldEl.appendChild(addButtonEl);
      }

      function createControlRow(controlEl, isRemovable) {
        const rowEl = document.createElement("div");
        rowEl.className = "profile-multi-value-row";
        rowEl.appendChild(controlEl);
        if (isRemovable) {
          const removeButtonEl = document.createElement("button");
          removeButtonEl.type = "button";
          removeButtonEl.className = "table-icon-btn table-icon-btn-danger profile-multi-value-remove-btn";
          removeButtonEl.title = "Remover linha";
          removeButtonEl.setAttribute("aria-label", "Remover linha");
          removeButtonEl.innerHTML = "&#10005;";
          removeButtonEl.addEventListener("click", () => {
            rowEl.remove();
          });
          rowEl.appendChild(removeButtonEl);
        }
        valuesListEl.appendChild(rowEl);
        return rowEl;
      }

      function createExtraControl(initialValue = "") {
        const clonedControlEl = baseControlEl.cloneNode(true);
        clonedControlEl.removeAttribute("id");
        clonedControlEl.name = baseFieldName;
        clonedControlEl.required = false;
        setProfileControlValue(clonedControlEl, initialValue);
        if (clonedControlEl.tagName !== "SELECT") {
          clonedControlEl.defaultValue = clonedControlEl.value;
        }
        return clonedControlEl;
      }

      const initialValues = normalizeProfileMultiValueList(baseControlEl.value);
      if (initialValues.length) {
        setProfileControlValue(baseControlEl, initialValues[0]);
      }
      baseControlEl.name = baseFieldName;

      fieldEl.insertBefore(valuesListEl, baseControlEl);
      createControlRow(baseControlEl, false);

      const extraValues = initialValues.slice(1);
      extraValues.forEach((value) => {
        createControlRow(createExtraControl(value), true);
      });

      addButtonEl.addEventListener("click", () => {
        const rowEl = createControlRow(createExtraControl(""), true);
        const inputEl = rowEl.querySelector("input, select, textarea");
        if (inputEl) {
          inputEl.focus();
        }
      });

      fieldEl.setAttribute("data-allocation-multi-ready", "1");
    }

    function setupAllocationSectionMultiValue(personalCardEl, sectionKey) {
      if (!personalCardEl || !isAllocationProfileSection(sectionKey)) {
        return;
      }
      const formEl = personalCardEl.querySelector(".profile-edit-form");
      if (!formEl) {
        return;
      }
      const cleanSection = String(sectionKey || "").trim().toLowerCase();
      const sectionFields = Array.from(formEl.querySelectorAll(".field[data-profile-section-pane]")).filter(
        (fieldEl) =>
          String(fieldEl.getAttribute("data-profile-section-pane") || "geral").trim().toLowerCase() === cleanSection
      );
      sectionFields.forEach((fieldEl) => {
        setupAllocationFieldMultiValue(fieldEl);
      });
    }

    return {
      normalizeProfileMultiValueList,
      isAllocationProfileSection,
      setProfileControlValue,
      setupAllocationFieldMultiValue,
      setupAllocationSectionMultiValue
    };
  };
})();
// APPVERBO_PROFILE_ALLOCATION_MULTIVALUE_V1_MODULE_END
