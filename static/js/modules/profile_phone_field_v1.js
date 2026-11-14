// Campo de telefone com indicativo: o indicativo segue o pais escolhido, o utilizador
// escreve so o numero nacional e o valor guardado (primary_phone) fica em formato
// internacional, por exemplo "+351 910000000".
(function initProfilePhoneFieldV1() {
  const DEFAULT_DIAL_CODE = "+351";

  function readCountryOptions(datalistEl) {
    if (!datalistEl) return [];
    return Array.from(datalistEl.options).map((option) => ({
      country: option.value,
      dial: option.getAttribute("label") || ""
    }));
  }

  function findDialForCountry(options, countryName) {
    const clean = String(countryName || "").trim().toLowerCase();
    const match = options.find((item) => item.country.toLowerCase() === clean);
    return match ? match.dial : "";
  }

  function splitFullNumber(fullNumber, options) {
    const value = String(fullNumber || "").trim();
    if (!value.startsWith("+")) {
      return { dial: "", national: value };
    }
    const sorted = options
      .map((item) => item.dial)
      .filter(Boolean)
      .sort((a, b) => b.length - a.length);
    const dial = sorted.find((code) => value.replace(/\s+/g, "").startsWith(code.replace(/\s+/g, ""))) || "";
    const national = dial ? value.replace(/\s+/g, "").slice(dial.replace(/\s+/g, "").length) : value;
    return { dial, national: national.trim() };
  }

  function setup(fieldEl) {
    const form = fieldEl.closest("form");
    if (!form) return;
    const countryEl = form.querySelector("#edit_country");
    const datalistEl = form.querySelector("#edit-country-options");
    const dialEl = fieldEl.querySelector("[data-phone-dial-v1]");
    const nationalEl = fieldEl.querySelector("[data-phone-national-v1]");
    const fullEl = fieldEl.querySelector("[data-phone-full-v1]");
    if (!countryEl || !dialEl || !nationalEl || !fullEl) return;

    const options = readCountryOptions(datalistEl);
    const initial = splitFullNumber(fullEl.value, options);
    let dial = initial.dial || findDialForCountry(options, countryEl.value) || DEFAULT_DIAL_CODE;
    nationalEl.value = initial.national;

    function render() {
      dialEl.textContent = dial;
      const national = nationalEl.value.trim();
      fullEl.value = national ? `${dial} ${national}` : "";
    }

    countryEl.addEventListener("input", () => {
      const matched = findDialForCountry(options, countryEl.value);
      if (matched) {
        dial = matched;
        render();
      }
    });
    nationalEl.addEventListener("input", render);
    form.addEventListener("submit", render);
    render();
  }

  document.querySelectorAll("[data-phone-field-v1]").forEach(setup);
})();
