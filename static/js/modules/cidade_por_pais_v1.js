// Cidade dependente do Pais da morada: ao escolher o pais, a Cidade sugere as cidades desse pais.
// Dados: GeoNames (https://www.geonames.org, licenca CC BY 4.0), ficheiro static/data/cidades_por_pais.json.
(function initCidadePorPaisV1() {
  const COUNTRY_SELECT_ID = "edit_custom_pais_da_morada";
  const CITY_INPUT_ID = "edit_custom_cidade";
  const LIST_ID = "edit_custom_cidade_list";
  const DATA_URL = "/static/data/cidades_por_pais.json";
  const COUNTRIES_URL = "/static/data/paises_pt.json";
  let countriesPromise = null;
  // Nome do pais (pt) -> codigo ISO 3166-1 alpha-2, a partir de static/data/paises_pt.json.
  function loadIsoByLabel() {
    if (!countriesPromise) {
      countriesPromise = fetch(COUNTRIES_URL)
        .then((res) => res.json())
        .then((rows) => Object.fromEntries(rows.map(([iso, name]) => [name, iso])))
        .catch(() => ({}));
    }
    return countriesPromise;
  }

  let citiesPromise = null;
  function loadCities() {
    if (!citiesPromise) {
      citiesPromise = fetch(DATA_URL).then((res) => res.json()).catch(() => ({}));
    }
    return citiesPromise;
  }

  function setup(countryEl, cityEl) {
    let datalist = document.getElementById(LIST_ID);
    if (!datalist) {
      datalist = document.createElement("datalist");
      datalist.id = LIST_ID;
      document.body.appendChild(datalist);
    }
    cityEl.setAttribute("list", LIST_ID);
    cityEl.setAttribute("autocomplete", "off");

    function refresh() {
      Promise.all([loadIsoByLabel(), loadCities()]).then(([isoByLabel, data]) => {
        const iso = isoByLabel[countryEl.value] || "";
        datalist.innerHTML = "";
        (data[iso] || []).forEach((name) => {
          const option = document.createElement("option");
          option.value = name;
          datalist.appendChild(option);
        });
      });
    }

    countryEl.addEventListener("change", refresh);
    refresh();
  }

  const countryEl = document.getElementById(COUNTRY_SELECT_ID);
  const cityEl = document.getElementById(CITY_INPUT_ID);
  if (countryEl && cityEl) {
    setup(countryEl, cityEl);
  }
})();
