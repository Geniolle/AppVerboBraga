// Menu de origem depende da Sessao da origem: so mostra os menus da sessao escolhida.
(function initAppGenesisAuthProfileMenuOriginFilterV1(global) {
  const originalOptionsBySelect = new WeakMap();

  function getOriginalOptionsV1(selectEl) {
    if (!originalOptionsBySelect.has(selectEl)) {
      originalOptionsBySelect.set(
        selectEl,
        Array.from(selectEl.options).map((optionEl) => ({
          value: optionEl.value,
          label: optionEl.textContent,
          group: optionEl.getAttribute("data-group") || "",
        }))
      );
    }
    return originalOptionsBySelect.get(selectEl);
  }

  function applyDependentSelectV1(selectEl) {
    const formEl = selectEl.closest("form");
    const parentName = selectEl.getAttribute("data-depends-on") || "";
    const parentEl = formEl && parentName ? formEl.querySelector('[name="' + parentName + '"]') : null;

    if (!parentEl) {
      return;
    }

    const parentValue = String(parentEl.value || "");
    const previousValue = String(selectEl.value || "");
    const originals = getOriginalOptionsV1(selectEl);
    const visible = originals.filter((option) => option.group === parentValue);

    selectEl.innerHTML = "";
    visible.forEach((option) => {
      const optionEl = global.document.createElement("option");
      optionEl.value = option.value;
      optionEl.textContent = option.label;
      optionEl.setAttribute("data-group", option.group);
      selectEl.appendChild(optionEl);
    });

    const keepPrevious = visible.some((option) => option.value === previousValue);
    selectEl.value = keepPrevious ? previousValue : (visible[0] ? visible[0].value : "");
  }

  function applyAllV1(root) {
    (root || global.document).querySelectorAll("select[data-depends-on]").forEach(applyDependentSelectV1);
  }

  global.document.addEventListener("change", (event) => {
    const target = event.target;
    if (!target || !target.name) {
      return;
    }
    const formEl = target.closest && target.closest("form");
    if (!formEl) {
      return;
    }
    formEl.querySelectorAll('select[data-depends-on="' + target.name + '"]').forEach(applyDependentSelectV1);
  });

  if (global.document.readyState === "loading") {
    global.document.addEventListener("DOMContentLoaded", () => applyAllV1());
  } else {
    applyAllV1();
  }

  global.AppGenesisAuthProfileMenuOriginFilterV1 = Object.freeze({
    applyAllV1,
  });
})(window);
