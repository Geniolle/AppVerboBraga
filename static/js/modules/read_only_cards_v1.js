//###################################################################################
// (1) READ ONLY CARDS V1
//###################################################################################
(function registerReadOnlyCardsV1() {
  "use strict";

  function setupReadOnlyCardsV1() {
    const readonlyCards = document.querySelectorAll('.entity-panel-card[data-readonly-mode="1"]');
    readonlyCards.forEach((card) => {
      const controls = card.querySelectorAll("input, select, textarea, button");
      controls.forEach((control) => {
        if (control.tagName === "INPUT" && control.type === "hidden") {
          return;
        }
        control.disabled = true;
        control.required = false;
        control.classList.add("readonly-field");
      });

      const formEl = card.querySelector("form");
      if (formEl) {
        formEl.addEventListener("submit", (event) => {
          event.preventDefault();
        });
      }
    });
  }

  window.APPVERBO_SETUP_READ_ONLY_CARDS_V1 = setupReadOnlyCardsV1;
})();
