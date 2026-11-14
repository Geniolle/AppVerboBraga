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

  function readOptions(listEl) {
    if (!listEl) return [];
    return Array.from(listEl.querySelectorAll("[role=option]"))
      .map((itemEl) => parseOption(itemEl.dataset.value))
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
    const listEl = fieldEl.querySelector("[data-phone-listbox-v1]");
    const nationalEl = fieldEl.querySelector("[data-phone-national-v1]");
    const countryNameEl = fieldEl.querySelector("[data-phone-country-name-v1]");
    const fullEl = fieldEl.querySelector("[data-phone-full-v1]");
    if (!countryInputEl || !nationalEl || !countryNameEl || !fullEl) return;

    const options = readOptions(listEl);
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

    const comboEl = fieldEl.querySelector("[data-phone-combo-v1]");
    const itemEls = listEl ? Array.from(listEl.querySelectorAll("[role=option]")) : [];

    function filterItems() {
      const query = countryInputEl.value.trim().toLowerCase();
      itemEls.forEach((itemEl) => {
        const visible = !query || itemEl.textContent.toLowerCase().includes(query);
        itemEl.hidden = !visible;
      });
    }

    function openList() {
      if (!listEl) return;
      itemEls.forEach((itemEl) => { itemEl.hidden = false; });
      listEl.hidden = false;
      countryInputEl.setAttribute("aria-expanded", "true");
    }

    function closeList() {
      if (!listEl) return;
      listEl.hidden = true;
      countryInputEl.setAttribute("aria-expanded", "false");
    }

    function chooseItem(itemEl) {
      countryInputEl.value = itemEl.dataset.value;
      syncFromSelector();
      render();
      closeList();
    }

    countryInputEl.addEventListener("focus", openList);
    countryInputEl.addEventListener("click", openList);
    countryInputEl.addEventListener("input", () => {
      listEl.hidden = false;
      filterItems();
      syncFromSelector();
      render();
    });
    countryInputEl.addEventListener("blur", () => {
      syncFromSelector();
      render();
      closeList();
    });
    countryInputEl.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeList();
      if (event.key === "Enter") {
        const first = itemEls.find((itemEl) => !itemEl.hidden);
        if (first && !listEl.hidden) {
          event.preventDefault();
          chooseItem(first);
        }
      }
    });
    itemEls.forEach((itemEl) => {
      itemEl.addEventListener("mousedown", (event) => {
        event.preventDefault();
        chooseItem(itemEl);
      });
    });
    if (comboEl) {
      document.addEventListener("mousedown", (event) => {
        if (!comboEl.contains(event.target)) closeList();
      });
    }
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
