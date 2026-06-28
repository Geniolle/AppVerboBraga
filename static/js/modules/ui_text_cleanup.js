
//###################################################################################
// (1) CORRECAO VISUAL DE TEXTOS E REMOCAO DE BOTAO INDEVIDO
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) MAPA DE TEXTOS COM MOJIBAKE
  //###################################################################################

  const replacements = new Map([
    ["Definições", "Definições"],
    ["DefiniÃ§Ã£o", "Definição"],
    ["Configuração", "Configuração"],
    ["Configurações", "Configurações"],
    ["configuração", "configuração"],
    ["configurações", "configurações"],
    ["Cabeçalho", "Cabeçalho"],
    ["cabeçalho", "cabeçalho"],
    ["Sem cabeçalho", "Sem cabeçalho"],
    ["InformaÃ§Ãµes", "Informações"],
    ["informaÃ§Ãµes", "informações"],
    ["AÇÕES", "AÇÕES"],
    ["AÃ§Ãµes", "Ações"],
    ["aÃ§Ãµes", "ações"],
    ["só", "só"],
    ["SÃ³", "Só"],
    ["página", "página"],
    ["PÃ¡gina", "Página"],
    ["NÃ£o", "Não"],
    ["nÃ£o", "não"],
    ["Entidades criadas", "Entidades criadas"],
    ["Entidades criadas", "Entidades criadas"],
    ["Entidades criadas", "Entidades criadas"]
  ]);

  replacements.set("ObrigatÃ³rio", "Obrigatório");
  replacements.set("obrigatÃ³rio", "obrigatório");
  replacements.set("ObrigatÃƒÂ³rio", "Obrigatório");
  replacements.set("obrigatÃƒÂ³rio", "obrigatório");
  replacements.set("NÃ£o", "Não");
  replacements.set("nÃ£o", "não");

  //###################################################################################
  // (3) FUNCOES AUXILIARES
  //###################################################################################

  function normalizeText(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function repairString(value) {
    let result = String(value || "");

    replacements.forEach(function (correctValue, wrongValue) {
      result = result.split(wrongValue).join(correctValue);
    });

    return result;
  }

  //###################################################################################
  // (4) CORRIGIR NOS DE TEXTO
  //###################################################################################

  function repairTextNodes(root) {
    const walker = document.createTreeWalker(
      root || document.body,
      NodeFilter.SHOW_TEXT
    );

    const nodes = [];

    while (walker.nextNode()) {
      nodes.push(walker.currentNode);
    }

    nodes.forEach(function (node) {
      const originalValue = node.nodeValue || "";
      const repairedValue = repairString(originalValue);

      if (repairedValue !== originalValue) {
        node.nodeValue = repairedValue;
      }
    });
  }

  //###################################################################################
  // (5) CORRIGIR ATRIBUTOS VISIVEIS
  //###################################################################################

  function repairAttributes(root) {
    const elements = (root || document).querySelectorAll("[title], [aria-label], [placeholder], [value]");

    elements.forEach(function (element) {
      ["title", "aria-label", "placeholder", "value"].forEach(function (attributeName) {
        if (!element.hasAttribute(attributeName)) {
          return;
        }

        const originalValue = element.getAttribute(attributeName) || "";
        const repairedValue = repairString(originalValue);

        if (repairedValue !== originalValue) {
          element.setAttribute(attributeName, repairedValue);
        }
      });
    });
  }

  //###################################################################################
  // (6) REMOVER BOTAO "SESSOES DO SIDEBAR"
  //###################################################################################

  function removeSessoesDoSidebarButton() {
    const candidates = document.querySelectorAll("a, button");

    candidates.forEach(function (element) {
      const text = normalizeText(element.textContent);

      if (text === "sessoes do sidebar" || text === "sessao do sidebar") {
        element.remove();
      }
    });
  }

  //###################################################################################
  // (7) EXECUTAR CORRECOES
  //###################################################################################

  function runCleanup() {
    repairTextNodes(document.body);
    repairAttributes(document);
    removeSessoesDoSidebarButton();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runCleanup);
  } else {
    runCleanup();
  }

  window.setTimeout(runCleanup, 100);
  window.setTimeout(runCleanup, 400);
  window.setTimeout(runCleanup, 1000);
})();

//###################################################################################
// APPVERBO_STANDARD_LIST_PROCESS_LOADER_V1_START
//###################################################################################

(function loadStandardListProcessRuntimeV1() {
  "use strict";

  if (!window.location || window.location.pathname !== "/users/new") {
    return;
  }

  function appendRuntimeScript() {
    if (document.querySelector("script[data-standard-list-process-runtime-v1='1']")) {
      return;
    }

    const scriptEl = document.createElement("script");
    scriptEl.src = "/static/js/modules/standard_list_process_v1.js?v=20260627-standard-list-v1";
    scriptEl.defer = true;
    scriptEl.setAttribute("data-standard-list-process-runtime-v1", "1");
    document.body.appendChild(scriptEl);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", appendRuntimeScript);
  } else {
    appendRuntimeScript();
  }
})();

//###################################################################################
// APPVERBO_STANDARD_LIST_PROCESS_SUBMIT_V1_START
//###################################################################################

(function setupStandardListProcessSubmitV1() {
  "use strict";

  if (!window.location || window.location.pathname !== "/users/new") {
    return;
  }

  function ensureHidden(formEl, name, value) {
    let inputEl = formEl.querySelector("input[name='" + name + "']");

    if (!inputEl) {
      inputEl = document.createElement("input");
      inputEl.type = "hidden";
      inputEl.name = name;
      formEl.appendChild(inputEl);
    }

    inputEl.value = value || "";
  }

  document.addEventListener("submit", function interceptStandardListSubmit(event) {
    const formEl = event.target && event.target.closest
      ? event.target.closest(".standard-list-process-create-card-v1 form")
      : null;

    if (!formEl) {
      return;
    }

    formEl.action = "/users/profile/standard-list-process-save";
    ensureHidden(formEl, "process_return_url", window.location.pathname + window.location.search + window.location.hash);
  }, true);
})();

//###################################################################################
// APPVERBO_STANDARD_LIST_PROCESS_V1_END
//###################################################################################
