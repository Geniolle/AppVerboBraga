//###################################################################################
// (1) SETAS DE HIERARQUIA AO LADO DO CAMPO TAMANHO
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function normalizarTexto_v1(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function isHeaderTypeSelect_v1(select) {
    if (!select) {
      return false;
    }

    const selectedOption = select.options[select.selectedIndex];
    const selectedText = normalizarTexto_v1(selectedOption ? selectedOption.textContent : "");
    const selectedValue = normalizarTexto_v1(select.value);

    return (
      selectedText.includes("cabecalho") ||
      selectedValue.includes("cabecalho") ||
      selectedValue.includes("header")
    );
  }

  function getAdditionalFieldsForm_v1() {
    const forms = Array.from(document.querySelectorAll("form"));

    return forms.find(function (form) {
      const text = normalizarTexto_v1(form.textContent);

      return (
        text.includes("campos adicionais") &&
        text.includes("nome do campo adicional") &&
        text.includes("tipo do campo")
      );
    }) || null;
  }

  function getFieldLabelText_v1(field) {
    const label = field ? field.querySelector("label") : null;
    return normalizarTexto_v1(label ? label.textContent : "");
  }

  function getRows_v1(form) {
    return Array.from(form.querySelectorAll(".additional-field-row-equalized"));
  }

  function getTypeSelectFromRow_v1(row) {
    const selects = Array.from(row.querySelectorAll("select"));

    return selects.find(function (select) {
      const field = select.closest(".field");
      const labelText = getFieldLabelText_v1(field);

      return labelText.includes("tipo do campo");
    }) || null;
  }

  function getSizeColumnFromRow_v1(row) {
    return (
      row.querySelector(".additional-field-size-col") ||
      Array.from(row.children).find(function (child) {
        return getFieldLabelText_v1(child).includes("tamanho");
      }) ||
      null
    );
  }

  function getActionColumnFromRow_v1(row) {
    return (
      row.querySelector(".additional-field-action-col") ||
      Array.from(row.children).find(function (child) {
        return Boolean(child.querySelector("button"));
      }) ||
      null
    );
  }

  function getHierarchyColumnFromRow_v1(row) {
    return row.querySelector(".additional-field-hierarchy-col");
  }

  function garantirColunaHierarquia_v1(row) {
    let hierarchyColumn = getHierarchyColumnFromRow_v1(row);

    if (hierarchyColumn) {
      return hierarchyColumn;
    }

    hierarchyColumn = document.createElement("div");
    hierarchyColumn.className = "additional-field-hierarchy-col";

    const actionColumn = getActionColumnFromRow_v1(row);
    const sizeColumn = getSizeColumnFromRow_v1(row);

    if (actionColumn) {
      row.insertBefore(hierarchyColumn, actionColumn);
      return hierarchyColumn;
    }

    if (sizeColumn && sizeColumn.nextSibling) {
      row.insertBefore(hierarchyColumn, sizeColumn.nextSibling);
      return hierarchyColumn;
    }

    row.appendChild(hierarchyColumn);
    return hierarchyColumn;
  }

  function limparHierarquiaAntiga_v1(row) {
    const controls = Array.from(row.querySelectorAll(".header-hierarchy-controls"));

    controls.forEach(function (control) {
      const parentColumn = control.closest(".additional-field-hierarchy-col");

      if (!parentColumn) {
        control.remove();
      }
    });
  }

  //###################################################################################
  // (3) MOVER LINHAS
  //###################################################################################

  function moveRowUp_v1(row) {
    const previousRow = row.previousElementSibling;

    if (!previousRow || !previousRow.classList.contains("additional-field-row-equalized")) {
      return;
    }

    row.parentNode.insertBefore(row, previousRow);
    atualizarSetasHierarquia_v1();
  }

  function moveRowDown_v1(row) {
    const nextRow = row.nextElementSibling;

    if (!nextRow || !nextRow.classList.contains("additional-field-row-equalized")) {
      return;
    }

    if (nextRow.nextSibling) {
      row.parentNode.insertBefore(row, nextRow.nextSibling);
    } else {
      row.parentNode.appendChild(row);
    }

    atualizarSetasHierarquia_v1();
  }

  //###################################################################################
  // (4) CRIAR CONTROLES AO LADO DO TAMANHO
  //###################################################################################

  function criarControlesHierarquia_v1(row, typeSelect) {
    limparHierarquiaAntiga_v1(row);

    const hierarchyColumn = garantirColunaHierarquia_v1(row);
    hierarchyColumn.innerHTML = "";

    if (!isHeaderTypeSelect_v1(typeSelect)) {
      hierarchyColumn.classList.add("is-empty");
      return;
    }

    hierarchyColumn.classList.remove("is-empty");

    const controls = document.createElement("div");
    controls.className = "header-hierarchy-controls";
    controls.innerHTML = [
      '<span class="header-hierarchy-label">Hierarquia</span>',
      '<div class="header-hierarchy-buttons">',
      '  <button type="button" class="header-hierarchy-btn" data-header-move="up" title="Mover cabeçalho para cima">↑</button>',
      '  <button type="button" class="header-hierarchy-btn" data-header-move="down" title="Mover cabeçalho para baixo">↓</button>',
      '</div>'
    ].join("");

    controls.addEventListener("click", function (event) {
      const button = event.target.closest("[data-header-move]");

      if (!button) {
        return;
      }

      const direction = button.getAttribute("data-header-move");

      if (direction === "up") {
        moveRowUp_v1(row);
      }

      if (direction === "down") {
        moveRowDown_v1(row);
      }
    });

    hierarchyColumn.appendChild(controls);
  }

  //###################################################################################
  // (5) ATUALIZAR TODAS AS LINHAS
  //###################################################################################

  function atualizarSetasHierarquia_v1() {
    const form = getAdditionalFieldsForm_v1();

    if (!form) {
      return;
    }

    const rows = getRows_v1(form);

    rows.forEach(function (row) {
      const typeSelect = getTypeSelectFromRow_v1(row);

      if (!typeSelect) {
        return;
      }

      criarControlesHierarquia_v1(row, typeSelect);

      if (typeSelect.dataset.headerHierarchySideBound !== "1") {
        typeSelect.dataset.headerHierarchySideBound = "1";
        typeSelect.addEventListener("change", atualizarSetasHierarquia_v1);
      }
    });
  }

  //###################################################################################
  // (6) INICIALIZACAO
  //###################################################################################

  function inicializarHierarquia_v1() {
    atualizarSetasHierarquia_v1();

    window.setTimeout(atualizarSetasHierarquia_v1, 200);
    window.setTimeout(atualizarSetasHierarquia_v1, 800);
    window.setTimeout(atualizarSetasHierarquia_v1, 1500);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializarHierarquia_v1);
  } else {
    inicializarHierarquia_v1();
  }
})();
