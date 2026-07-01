//###################################################################################
// (1) TOOLTIP DE INFORMACAO PARA CAMPOS (GENERICO E REUTILIZAVEL)
//###################################################################################
// Alterna um popover de ajuda ao clicar no icone data-field-info-trigger.
// A exibicao em hover/click e feita por CSS (:hover / :focus-within / classe);
// o JS apenas reposiciona o painel para nao ultrapassar a viewport.

(function () {
  "use strict";

  function positionFieldInfoPanel(wrapperEl) {
    var panelEl = wrapperEl.querySelector(".field-info-panel-v1");
    if (!panelEl) {
      return;
    }
    var margin = 8;
    panelEl.style.left = "0px";
    var rect = panelEl.getBoundingClientRect();
    var overflowRight = rect.right - (window.innerWidth - margin);
    if (overflowRight > 0) {
      panelEl.style.left = (0 - overflowRight) + "px";
    }
    rect = panelEl.getBoundingClientRect();
    if (rect.left < margin) {
      panelEl.style.left = (parseFloat(panelEl.style.left) + (margin - rect.left)) + "px";
    }
  }

  function closeAllFieldInfoTooltips(exceptWrapperEl) {
    document.querySelectorAll(".field-info-tooltip-open-v1").forEach(function (wrapperEl) {
      if (wrapperEl === exceptWrapperEl) {
        return;
      }
      wrapperEl.classList.remove("field-info-tooltip-open-v1");
      var triggerEl = wrapperEl.querySelector("[data-field-info-trigger]");
      if (triggerEl) {
        triggerEl.setAttribute("aria-expanded", "false");
      }
    });
  }

  document.addEventListener("click", function (event) {
    var triggerEl = event.target.closest("[data-field-info-trigger]");
    if (triggerEl) {
      var wrapperEl = triggerEl.closest("[data-field-info-tooltip]");
      if (!wrapperEl) {
        return;
      }
      var wasOpen = wrapperEl.classList.contains("field-info-tooltip-open-v1");
      closeAllFieldInfoTooltips(wrapperEl);
      wrapperEl.classList.toggle("field-info-tooltip-open-v1", !wasOpen);
      triggerEl.setAttribute("aria-expanded", String(!wasOpen));
      if (!wasOpen) {
        positionFieldInfoPanel(wrapperEl);
      }
      event.preventDefault();
      return;
    }
    if (!event.target.closest("[data-field-info-tooltip]")) {
      closeAllFieldInfoTooltips(null);
    }
  });

  document.addEventListener(
    "mouseover",
    function (event) {
      var wrapperEl = event.target.closest("[data-field-info-tooltip]");
      if (wrapperEl) {
        positionFieldInfoPanel(wrapperEl);
      }
    },
    true
  );

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeAllFieldInfoTooltips(null);
    }
  });
})();
