// Cidade dependente do Pais da morada: ao escolher o pais, a Cidade mostra as cidades desse pais numa lista
// propria (filtrada ao digitar). Dados: GeoNames (https://www.geonames.org, licenca CC BY 4.0),
// static/data/cidades_por_pais.json; nomes dos paises em static/data/paises_pt.json.
// Freguesia dependente da Cidade (so Portugal): static/data/freguesias_pt.json (concelho -> freguesias),
// dados: Aldeias Portuguesas (CC BY-SA 4.0) com limites CAOP 2025 (DGT). Chave = nome do concelho sem acentos.
(function initCidadePorPaisV1() {
  const COUNTRY_SELECT_ID = "edit_custom_pais_da_morada";
  const CITY_INPUT_ID = "edit_custom_cidade";
  const FREGUESIA_INPUT_ID = "edit_custom_freguesia";
  const MAX_ITEMS = 50;
  const CITIES_URL = "/static/data/cidades_por_pais.json";
  const COUNTRIES_URL = "/static/data/paises_pt.json";
  const FREGUESIAS_URL = "/static/data/freguesias_pt.json";

  let citiesPromise = null;
  let countriesPromise = null;
  let freguesiasPromise = null;

  function normalizeKey(text) {
    return String(text || "").normalize("NFD").replace(/[̀-ͯ]/g, "").trim().toLowerCase();
  }

  function loadCities() {
    if (!citiesPromise) {
      citiesPromise = fetch(CITIES_URL).then((res) => res.json()).catch(() => ({}));
    }
    return citiesPromise;
  }

  function loadFreguesias() {
    if (!freguesiasPromise) {
      freguesiasPromise = fetch(FREGUESIAS_URL).then((res) => res.json()).catch(() => ({}));
    }
    return freguesiasPromise;
  }

  // Nome do pais (pt) -> codigo ISO 3166-1 alpha-2.
  function loadIsoByLabel() {
    if (!countriesPromise) {
      countriesPromise = fetch(COUNTRIES_URL)
        .then((res) => res.json())
        .then((rows) => Object.fromEntries(rows.map(([iso, name]) => [name, iso])))
        .catch(() => ({}));
    }
    return countriesPromise;
  }

  // Lista propria filtrada ao digitar; texto livre continua permitido.
  function attachList(inputEl) {
    const comboEl = document.createElement("div");
    comboEl.className = "cidade-combo-v1";
    inputEl.parentNode.insertBefore(comboEl, inputEl);
    comboEl.appendChild(inputEl);
    const listEl = document.createElement("ul");
    listEl.className = "cidade-listbox-v1";
    listEl.setAttribute("role", "listbox");
    listEl.hidden = true;
    comboEl.appendChild(listEl);
    inputEl.setAttribute("autocomplete", "off");
    inputEl.setAttribute("role", "combobox");
    inputEl.setAttribute("aria-expanded", "false");

    let items = [];

    function renderList() {
      const query = inputEl.value.trim().toLowerCase();
      const matches = query
        ? items.filter((name) => name.toLowerCase().includes(query))
        : items;
      listEl.innerHTML = "";
      matches.slice(0, MAX_ITEMS).forEach((name) => {
        const li = document.createElement("li");
        li.setAttribute("role", "option");
        li.textContent = name;
        li.addEventListener("mousedown", (event) => {
          event.preventDefault();
          inputEl.value = name;
          closeList();
          inputEl.dispatchEvent(new Event("change"));
        });
        listEl.appendChild(li);
      });
      listEl.hidden = matches.length === 0;
      inputEl.setAttribute("aria-expanded", String(!listEl.hidden));
    }

    function closeList() {
      listEl.hidden = true;
      inputEl.setAttribute("aria-expanded", "false");
    }

    inputEl.addEventListener("focus", renderList);
    inputEl.addEventListener("input", renderList);
    inputEl.addEventListener("blur", closeList);
    inputEl.addEventListener("keydown", (event) => {
      // Enter nesta lista so fecha a lista: nao pode submeter o formulario de morada.
      if (event.key === "Enter") {
        event.preventDefault();
        closeList();
      } else if (event.key === "Escape") {
        closeList();
      }
    });

    return {
      setItems(next) {
        items = next;
        if (document.activeElement === inputEl) renderList();
      },
    };
  }

  function setup(countryEl, cityEl, freguesiaEl) {
    const cityList = attachList(cityEl);
    const freguesiaList = freguesiaEl ? attachList(freguesiaEl) : null;

    function refresh() {
      Promise.all([loadIsoByLabel(), loadCities(), loadFreguesias()]).then(
        ([isoByLabel, citiesData, freguesiasData]) => {
          const iso = isoByLabel[countryEl.value] || "";
          cityList.setItems(citiesData[iso] || []);
          if (freguesiaList) {
            freguesiaList.setItems(
              iso === "PT" ? freguesiasData[normalizeKey(cityEl.value)] || [] : []
            );
          }
        }
      );
    }

    countryEl.addEventListener("change", refresh);
    cityEl.addEventListener("change", refresh);
    cityEl.addEventListener("input", refresh);
    refresh();
  }

  const countryEl = document.getElementById(COUNTRY_SELECT_ID);
  const cityEl = document.getElementById(CITY_INPUT_ID);
  const freguesiaEl = document.getElementById(FREGUESIA_INPUT_ID);
  if (countryEl && cityEl) {
    setup(countryEl, cityEl, freguesiaEl);
  }
})();
