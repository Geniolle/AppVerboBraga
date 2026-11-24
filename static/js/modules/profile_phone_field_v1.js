// Campo de telefone com seletor de pais: o botao mostra so o indicativo (ex. "+351"); a lista mostra "+351 Portugal".
// Guardamos o pais por nome (country) e o telefone completo em formato internacional (primary_phone), ex. "+351 910000000".
(function initProfilePhoneFieldV1() {
  const DEFAULT_COUNTRY = "Portugal";
  const DEFAULT_DIAL = "+351";

  function readItems(listEl) {
    return Array.from(listEl.querySelectorAll("[role=option]")).map((el) => ({
      el,
      dial: el.dataset.dial,
      country: el.dataset.country || ""
    }));
  }

  function findByCountry(items, countryName) {
    const clean = String(countryName || "").trim().toLowerCase();
    return items.find((item) => item.country.toLowerCase() === clean) || null;
  }

  function splitFullNumber(fullNumber, items) {
    const value = String(fullNumber || "").trim();
    if (!value.startsWith("+")) {
      return { dial: "", national: value };
    }
    const compact = value.replace(/\s+/g, "");
    const dials = items.map((item) => item.dial).sort((a, b) => b.length - a.length);
    const dial = dials.find((code) => compact.startsWith(code)) || "";
    return { dial, national: (dial ? compact.slice(dial.length) : value).trim() };
  }

  function setup(fieldEl) {
    const form = fieldEl.closest("form");
    const triggerEl = fieldEl.querySelector("[data-phone-trigger-v1]");
    const listEl = fieldEl.querySelector("[data-phone-listbox-v1]");
    const nationalEl = fieldEl.querySelector("[data-phone-national-v1]");
    const countryNameEl = fieldEl.querySelector("[data-phone-country-name-v1]");
    const fullEl = fieldEl.querySelector("[data-phone-full-v1]");
    if (!form || !triggerEl || !listEl || !nationalEl || !countryNameEl || !fullEl) return;

    const items = readItems(listEl);
    const storedCountry = String(countryNameEl.value || "").trim();
    const initial = splitFullNumber(fullEl.value, items);
    const current = findByCountry(items, storedCountry)
      || (storedCountry ? null : findByCountry(items, DEFAULT_COUNTRY));
    const start = current || items.find((item) => item.dial === initial.dial) || null;

    let dialCode = initial.dial || (start ? start.dial : DEFAULT_DIAL);
    let countryName = start ? start.country : storedCountry;
    nationalEl.value = initial.national;

    function showSelection() {
      triggerEl.textContent = dialCode;
      countryNameEl.value = countryName;
    }

    function render() {
      const national = nationalEl.value.trim();
      fullEl.value = national && dialCode ? `${dialCode} ${national}` : "";
    }

    function closeList() {
      listEl.hidden = true;
      triggerEl.setAttribute("aria-expanded", "false");
    }

    function choose(item) {
      dialCode = item.dial;
      countryName = item.country;
      showSelection();
      render();
      closeList();
    }

    triggerEl.addEventListener("click", () => {
      const willOpen = listEl.hidden;
      listEl.hidden = !willOpen;
      triggerEl.setAttribute("aria-expanded", String(willOpen));
    });
    items.forEach((item) => {
      item.el.addEventListener("click", () => choose(item));
    });
    triggerEl.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeList();
    });
    document.addEventListener("mousedown", (event) => {
      if (!fieldEl.contains(event.target)) closeList();
    });
    nationalEl.addEventListener("input", render);
    form.addEventListener("submit", render);
    // form.reset() limpa o numero: repor a partir do telefone guardado.
    form.addEventListener("reset", () => {
      setTimeout(() => {
        const restored = findByCountry(items, countryNameEl.value);
        if (restored) {
          dialCode = restored.dial;
          countryName = restored.country;
        }
        nationalEl.value = splitFullNumber(fullEl.value, items).national;
        showSelection();
        render();
        closeList();
      }, 0);
    });

    showSelection();
    render();
  }

  document.querySelectorAll("[data-phone-field-v1]").forEach(setup);
})();
