//###################################################################################
// (1) SINCRONIZAR CAMPOS DE ENTIDADE NOS FORMULARIOS DE UTILIZADOR
//###################################################################################
(function () {
  function getTargetInput(id) {
    if (!id) {
      return null;
    }
    return document.getElementById(id);
  }

  function syncSelectTargets(select, nameInput, numberInput) {
    var option = select.options[select.selectedIndex] || null;
    var entityName = option ? option.getAttribute("data-entity-name") || "" : "";
    var entityNumber = option ? option.getAttribute("data-entity-number") || "" : "";

    if (nameInput) {
      nameInput.value = entityName || "-";
    }

    if (numberInput) {
      numberInput.value = entityNumber;
    }
  }

  function initEntitySelector(select) {
    if (!select || select.dataset.userEntitySelectorReady === "1") {
      return;
    }

    select.dataset.userEntitySelectorReady = "1";

    var nameInput = getTargetInput(select.getAttribute("data-user-entity-name-target"));
    var numberInput = getTargetInput(select.getAttribute("data-user-entity-number-target"));

    function handleChange() {
      syncSelectTargets(select, nameInput, numberInput);
    }

    handleChange();
    select.addEventListener("change", handleChange);
  }

  function initUserEntitySelectors() {
    var selectors = document.querySelectorAll('[data-user-entity-select="1"]');
    for (var index = 0; index < selectors.length; index += 1) {
      initEntitySelector(selectors[index]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initUserEntitySelectors, { once: true });
  } else {
    initUserEntitySelectors();
  }
})();
