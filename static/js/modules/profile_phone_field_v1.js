// Campo de telefone com seletor de indicativo: o seletor mostra "+351 (Portugal)", o utilizador
// pesquisa o pais e escreve so o numero nacional. Guardamos o pais por nome (country) e o
// telefone completo em formato internacional (primary_phone), por exemplo "+351 910000000".
(function initProfilePhoneFieldV1() {
  const DEFAULT_COUNTRY = "Portugal";
  const DEFAULT_DIAL = "+351";
  const OPTION_PATTERN = /^(\+\d+)\s*\((.+)\)$/;

  function parseOption(text) {
    const match = OPTION_PATTERN.exec(String(text || "").trim());
    if (!match) return null;
    return { dial: match[1], country: match[2].trim(), text: String(text).trim() };
  }

  function readOptions(datalistEl) {
    if (!datalistEl) return [];
    return Array.from(datalistEl.options)
      .map((option) => parseOption(option.value))
      .filter(Boolean);
  }

  function findByCountry(options, countryName) {
    const clean = String(countryName || "").trim().toLowerCase();
    return options.find((item) => item.country.toLowerCase() === clean) || null;
  }

  function findByText(options, text) {
    const clean = String(text || "").trim().toLowerCase();
    return options.find((item) => item.text.toLowerCase() === clean) || null;
  }

  function splitFullNumber(fullNumber, options) {
    const value = String(fullNumber || "").trim();
    if (!value.startsWith("+")) {
      return { dial: "", national: value };
    }
    const compact = value.replace(/\s+/g, "");
    const dials = options
      .map((item) => item.dial)
      .sort((a, b) => b.length - a.length);
    const dial = dials.find((code) => compact.startsWith(code)) || "";
    const national = dial ? compact.slice(dial.length) : value;
    return { dial, national: national.trim() };
  }

  function setup(fieldEl) {
    const form = fieldEl.closest("form");
    if (!form) return;
    const countryInputEl = fieldEl.querySelector("[data-phone-country-v1]");
    const datalistEl = form.querySelector("#edit-country-options");
    const nationalEl = fieldEl.querySelector("[data-phone-national-v1]");
    const countryNameEl = fieldEl.querySelector("[data-phone-country-name-v1]");
    const fullEl = fieldEl.querySelector("[data-phone-full-v1]");
    if (!countryInputEl || !nationalEl || !countryNameEl || !fullEl) return;

    const options = readOptions(datalistEl);
    const current = findByCountry(options, countryNameEl.value)
      || findByCountry(options, DEFAULT_COUNTRY);
    const initial = splitFullNumber(fullEl.value, options);
    let selected = current;
    if (initial.dial) {
      selected = options.find((item) => item.dial === initial.dial && item.country === (current ? current.country : "")) || options.find((item) => item.dial === initial.dial) || current;
    }

    countryInputEl.value = selected ? selected.text : `${DEFAULT_DIAL} (${DEFAULT_COUNTRY})`;
    nationalEl.value = initial.national;

    function syncFromSelector() {
      const matched = findByText(options, countryInputEl.value);
      if (matched) {
        selected = matched;
        countryNameEl.value = matched.country;
      }
    }

    function render() {
      const dial = selected ? selected.dial : DEFAULT_DIAL;
      const national = nationalEl.value.trim();
      fullEl.value = national ? `${dial} ${national}` : "";
    }

    countryInputEl.addEventListener("change", () => {
      syncFromSelector();
      render();
    });
    countryInputEl.addEventListener("input", () => {
      syncFromSelector();
      render();
    });
    nationalEl.addEventListener("input", render);
    form.addEventListener("submit", () => {
      syncFromSelector();
      render();
    });

    syncFromSelector();
    render();
  }

  document.querySelectorAll("[data-phone-field-v1]").forEach(setup);
})();
