// Cidade dependente do Pais da morada: ao escolher o pais, a Cidade sugere as cidades desse pais.
// Dados: GeoNames (https://www.geonames.org, licenca CC BY 4.0), ficheiro static/data/cidades_por_pais.json.
(function initCidadePorPaisV1() {
  const COUNTRY_SELECT_ID = "edit_custom_pais_da_morada";
  const CITY_INPUT_ID = "edit_custom_cidade";
  const LIST_ID = "edit_custom_cidade_list";
  const DATA_URL = "/static/data/cidades_por_pais.json";
  // Nomes dos paises da lista (pt) -> codigo ISO 3166-1 alpha-2.
  const ISO_BY_LABEL = {
    "Albânia": "AL", "Alemanha": "DE", "Andorra": "AD", "Áustria": "AT", "Bélgica": "BE",
    "Bielorrússia": "BY", "Bósnia e Herzegovina": "BA", "Bulgária": "BG", "Chipre": "CY",
    "Croácia": "HR", "Dinamarca": "DK", "Eslováquia": "SK", "Eslovénia": "SI", "Espanha": "ES",
    "Estónia": "EE", "Finlândia": "FI", "França": "FR", "Grécia": "GR", "Hungria": "HU",
    "Irlanda": "IE", "Islândia": "IS", "Itália": "IT", "Kosovo": "XK", "Letónia": "LV",
    "Liechtenstein": "LI", "Lituânia": "LT", "Luxemburgo": "LU", "Macedónia do Norte": "MK",
    "Malta": "MT", "Moldávia": "MD", "Mónaco": "MC", "Montenegro": "ME", "Noruega": "NO",
    "Países Baixos": "NL", "Polónia": "PL", "Portugal": "PT", "Reino Unido": "GB",
    "República Checa": "CZ", "Roménia": "RO", "Rússia": "RU", "San Marino": "SM", "Sérvia": "RS",
    "Suécia": "SE", "Suíça": "CH", "Ucrânia": "UA"
  };

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
      const iso = ISO_BY_LABEL[countryEl.value] || "";
      loadCities().then((data) => {
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
