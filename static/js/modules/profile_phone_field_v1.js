// Campo de telefone com seletor de pais: o select mostra "+351 Portugal" e o utilizador escreve so o numero nacional.
// Guardamos o pais por nome (country) e o telefone completo em formato internacional (primary_phone), ex. "+351 910000000".
(function initProfilePhoneFieldV1() {
  const DEFAULT_COUNTRY = "Portugal";
  const DEFAULT_DIAL = "+351";

  function readOptions(selectEl) {
    return Array.from(selectEl.options).map((optionEl) => {
      const [dial, country] = optionEl.value.split("|");
      return { dial, country: country || "", el: optionEl };
    });
  }

  function findByCountry(options, countryName) {
    const clean = String(countryName || "").trim().toLowerCase();
    return options.find((item) => item.country.toLowerCase() === clean) || null;
  }

  function splitFullNumber(fullNumber, options) {
    const value = String(fullNumber || "").trim();
    if (!value.startsWith("+")) {
      return { dial: "", national: value };
    }
    const compact = value.replace(/\s+/g, "");
    const dials = options.map((item) => item.dial).sort((a, b) => b.length - a.length);
    const dial = dials.find((code) => compact.startsWith(code)) || "";
    return { dial, national: (dial ? compact.slice(dial.length) : value).trim() };
  }

  function setup(fieldEl) {
    const form = fieldEl.closest("form");
    const selectEl = fieldEl.querySelector("[data-phone-country-select-v1]");
    const nationalEl = fieldEl.querySelector("[data-phone-national-v1]");
    const countryNameEl = fieldEl.querySelector("[data-phone-country-name-v1]");
    const fullEl = fieldEl.querySelector("[data-phone-full-v1]");
    if (!form || !selectEl || !nationalEl || !countryNameEl || !fullEl) return;

    const options = readOptions(selectEl);
    const storedCountry = String(countryNameEl.value || "").trim();
    const initial = splitFullNumber(fullEl.value, options);
    const current = findByCountry(options, storedCountry)
      || (storedCountry ? null : findByCountry(options, DEFAULT_COUNTRY));
    const byDial = options.find((item) => item.dial === initial.dial) || null;
    const start = current || byDial;
    if (start) selectEl.value = start.el.value;
    nationalEl.value = initial.national;

    let dialCode = initial.dial || (start ? start.dial : DEFAULT_DIAL);

    function syncFromSelect() {
      const selected = selectEl.selectedOptions[0];
      if (!selected) return;
      const [dial, country] = selected.value.split("|");
      dialCode = dial;
      countryNameEl.value = country || "";
    }

    function render() {
      const national = nationalEl.value.trim();
      fullEl.value = national && dialCode ? `${dialCode} ${national}` : "";
    }

    selectEl.addEventListener("change", () => { syncFromSelect(); render(); });
    nationalEl.addEventListener("input", render);
    form.addEventListener("submit", () => { syncFromSelect(); render(); });
    // form.reset() limpa o select e o numero: repor a partir do telefone guardado.
    form.addEventListener("reset", () => {
      setTimeout(() => {
        const restored = findByCountry(options, countryNameEl.value);
        if (restored) selectEl.value = restored.el.value;
        nationalEl.value = splitFullNumber(fullEl.value, options).national;
        syncFromSelect();
        render();
      }, 0);
    });

    syncFromSelect();
    render();
  }

  document.querySelectorAll("[data-phone-field-v1]").forEach(setup);
})();
