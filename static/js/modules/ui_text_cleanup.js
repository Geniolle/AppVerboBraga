
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
