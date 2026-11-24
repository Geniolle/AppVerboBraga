// Cidade dependente do Pais da morada: ao escolher o pais, a Cidade mostra as cidades desse pais numa lista
// propria (filtrada ao digitar). Dados: GeoNames (https://www.geonames.org, licenca CC BY 4.0),
// static/data/cidades_por_pais.json; nomes dos paises em static/data/paises_pt.json.
(function initCidadePorPaisV1() {
  const COUNTRY_SELECT_ID = "edit_custom_pais_da_morada";
  const CITY_INPUT_ID = "edit_custom_cidade";
  const MAX_ITEMS = 50;
  const CITIES_URL = "/static/data/cidades_por_pais.json";
  const COUNTRIES_URL = "/static/data/paises_pt.json";

  let citiesPromise = null;
  let countriesPromise = null;

  function loadCities() {
    if (!citiesPromise) {
      citiesPromise = fetch(CITIES_URL).then((res) => res.json()).catch(() => ({}));
    }
    return citiesPromise;
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

  function setup(countryEl, cityEl) {
    const comboEl = document.createElement("div");
    comboEl.className = "cidade-combo-v1";
    cityEl.parentNode.insertBefore(comboEl, cityEl);
    comboEl.appendChild(cityEl);
    const listEl = document.createElement("ul");
    listEl.className = "cidade-listbox-v1";
    listEl.setAttribute("role", "listbox");
    listEl.hidden = true;
    comboEl.appendChild(listEl);
    cityEl.setAttribute("autocomplete", "off");
    cityEl.setAttribute("role", "combobox");
    cityEl.setAttribute("aria-expanded", "false");

    let cities = [];

    function renderList() {
      const query = cityEl.value.trim().toLowerCase();
      const matches = query
        ? cities.filter((name) => name.toLowerCase().includes(query))
        : cities;
      listEl.innerHTML = "";
      matches.slice(0, MAX_ITEMS).forEach((name) => {
        const li = document.createElement("li");
        li.setAttribute("role", "option");
        li.textContent = name;
        li.addEventListener("mousedown", (event) => {
          event.preventDefault();
          cityEl.value = name;
          closeList();
        });
        listEl.appendChild(li);
      });
      listEl.hidden = matches.length === 0;
      cityEl.setAttribute("aria-expanded", String(!listEl.hidden));
    }

    function closeList() {
      listEl.hidden = true;
      cityEl.setAttribute("aria-expanded", "false");
    }

    function refresh() {
      Promise.all([loadIsoByLabel(), loadCities()]).then(([isoByLabel, data]) => {
        const iso = isoByLabel[countryEl.value] || "";
        cities = data[iso] || [];
        if (document.activeElement === cityEl) renderList();
      });
    }

    countryEl.addEventListener("change", refresh);
    cityEl.addEventListener("focus", () => { renderList(); });
    cityEl.addEventListener("input", renderList);
    cityEl.addEventListener("blur", closeList);
    cityEl.addEventListener("keydown", (event) => {
      // Enter nesta lista so fecha a lista: nao pode submeter o formulario de morada.
      if (event.key === "Enter") {
        event.preventDefault();
        closeList();
      } else if (event.key === "Escape") {
        closeList();
      }
    });
    refresh();
  }

  const countryEl = document.getElementById(COUNTRY_SELECT_ID);
  const cityEl = document.getElementById(CITY_INPUT_ID);
  if (countryEl && cityEl) {
    setup(countryEl, cityEl);
  }
})();
