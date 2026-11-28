// Codigo postal (so Portugal): ao preencher NNNN-EEE, preenche a Cidade (se vazia) e oferece a lista de
// arruamentos na Morada (preenche se houver so um). Dados: CTT via centraldedados/codigos_postais (PDDL),
// static/data/codigos_postais/<2 primeiros digitos>.json = {"NNNN-EEE": {"l": localidade, "r": [arruamentos]}}.
(function initCodigoPostalV1() {
  const COUNTRY_SELECT_ID = "edit_custom_pais_da_morada";
  const CP_INPUT_ID = "edit_custom_codigo_postal";
  const CITY_INPUT_ID = "edit_custom_cidade";
  const MORADA_INPUT_ID = "edit_custom_morada";
  const BASE_URL = "/static/data/codigos_postais/";
  const CP_RE = /^\d{4}-\d{3}$/;

  const prefixCache = {};

  function loadPrefix(prefix) {
    if (!prefixCache[prefix]) {
      prefixCache[prefix] = fetch(BASE_URL + prefix + ".json")
        .then((res) => (res.ok ? res.json() : {}))
        .catch(() => ({}));
    }
    return prefixCache[prefix];
  }

  function setup(countryEl, cpEl, cityEl, moradaEl) {
    const moradaList = window.appgenesisAttachListV1(moradaEl);

    function lookup() {
      const cp = cpEl.value.trim();
      if (countryEl.value !== "Portugal" || !CP_RE.test(cp)) {
        moradaList.setItems([]);
        return;
      }
      loadPrefix(cp.slice(0, 2)).then((data) => {
        if (cpEl.value.trim() !== cp) return; // codigo mudou entretanto
        const entry = data[cp];
        if (!entry) {
          moradaList.setItems([]);
          return;
        }
        if (!cityEl.value.trim()) cityEl.value = entry.l;
        const ruas = entry.r || [];
        moradaList.setItems(ruas);
        if (!moradaEl.value.trim() && ruas.length === 1) moradaEl.value = ruas[0];
      });
    }

    cpEl.addEventListener("input", lookup);
    cpEl.addEventListener("change", lookup);
    countryEl.addEventListener("change", lookup);
    lookup();
  }

  const countryEl = document.getElementById(COUNTRY_SELECT_ID);
  const cpEl = document.getElementById(CP_INPUT_ID);
  const cityEl = document.getElementById(CITY_INPUT_ID);
  const moradaEl = document.getElementById(MORADA_INPUT_ID);
  if (countryEl && cpEl && cityEl && moradaEl && window.appgenesisAttachListV1) {
    setup(countryEl, cpEl, cityEl, moradaEl);
  }
})();
