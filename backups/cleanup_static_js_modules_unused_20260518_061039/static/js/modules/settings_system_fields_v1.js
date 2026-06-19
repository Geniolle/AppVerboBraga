// APPVERBO_SETTINGS_SYSTEM_FIELDS_V2_START
(function () {
  "use strict";

  //###################################################################################
  // (1) CAMPOS DE SISTEMA DO PROCESSO MEU PERFIL
  //###################################################################################

  const CAMPOS_SISTEMA_MEU_PERFIL_V2 = [
    { key: "nome", label: "Nome", typeLabel: "Texto", requiredLabel: "Sim", sizeLabel: "200", listLabel: "-", group: "Dados pessoais" },
    { key: "telefone", label: "Telefone", typeLabel: "Texto", requiredLabel: "Sim", sizeLabel: "30", listLabel: "-", group: "Dados pessoais" },
    { key: "email", label: "Email", typeLabel: "Email", requiredLabel: "Sim", sizeLabel: "150", listLabel: "-", group: "Dados pessoais" },
    { key: "pais", label: "País", typeLabel: "Texto", requiredLabel: "Não", sizeLabel: "120", listLabel: "-", group: "Dados pessoais" },
    { key: "data_nascimento", label: "Data de nascimento", typeLabel: "Data", requiredLabel: "Não", sizeLabel: "-", listLabel: "-", group: "Dados pessoais" },
    { key: "whatsapp", label: "WhatsApp", typeLabel: "Texto", requiredLabel: "Não", sizeLabel: "20", listLabel: "-", group: "Dados pessoais" },
    { key: "autorizacao_whatsapp", label: "Autorização para avisos por WhatsApp", typeLabel: "Flag", requiredLabel: "Não", sizeLabel: "-", listLabel: "-", group: "Dados pessoais" },
    { key: "conta", label: "Conta", typeLabel: "Texto", requiredLabel: "Não", sizeLabel: "20", listLabel: "-", group: "Dados pessoais" },
    { key: "estado_membro", label: "Estado de membro", typeLabel: "Texto", requiredLabel: "Não", sizeLabel: "20", listLabel: "-", group: "Dados pessoais" },
    { key: "colaborador", label: "Colaborador", typeLabel: "Flag", requiredLabel: "Não", sizeLabel: "-", listLabel: "-", group: "Dados pessoais" },
    { key: "entidades", label: "Entidades", typeLabel: "Texto", requiredLabel: "Não", sizeLabel: "-", listLabel: "-", group: "Dados pessoais" },
    { key: "ultima_verificacao_whatsapp", label: "Última verificação WhatsApp", typeLabel: "Data", requiredLabel: "Não", sizeLabel: "-", listLabel: "-", group: "Dados pessoais" },
    { key: "detalhe_verificacao", label: "Detalhe da verificação", typeLabel: "Texto", requiredLabel: "Não", sizeLabel: "-", listLabel: "-", group: "Dados pessoais" }
  ];

  //###################################################################################
  // (2) NORMALIZAR TEXTO E VALIDAR CONTEXTO DA PÁGINA
  //###################################################################################

  function normalizarTextoSistemaMeuPerfil_v2(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterParametroUrlSistemaMeuPerfil_v2(nome) {
    const params = new URLSearchParams(window.location.search || "");
    return String(params.get(nome) || "").trim().toLowerCase();
  }

  function paginaConfiguracaoMeuPerfil_v2() {
    const settingsEditKey = obterParametroUrlSistemaMeuPerfil_v2("settings_edit_key");
    const textoPagina = normalizarTextoSistemaMeuPerfil_v2(document.body ? document.body.textContent : "");

    if (settingsEditKey !== "meu_perfil") {
      return false;
    }

    return textoPagina.includes("editar processo: meu perfil") &&
      textoPagina.includes("campos adicionais") &&
      textoPagina.includes("campos criados");
  }

  //###################################################################################
  // (3) LOCALIZAR CARD E TABELA DE CAMPOS CRIADOS
  //###################################################################################

  function localizarCardCamposCriadosMeuPerfil_v2() {
    const candidatos = Array.from(document.querySelectorAll("section, .card, div"));

    return candidatos.find(function (elemento) {
      const texto = normalizarTextoSistemaMeuPerfil_v2(elemento.textContent);
      return texto.includes("campos criados") &&
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        elemento.querySelector("table tbody");
    }) || null;
  }

  function localizarTabelaCamposCriadosMeuPerfil_v2() {
    const card = localizarCardCamposCriadosMeuPerfil_v2();

    if (card) {
      return card.querySelector("table");
    }

    const tabelas = Array.from(document.querySelectorAll("table"));

    return tabelas.find(function (tabela) {
      const texto = normalizarTextoSistemaMeuPerfil_v2(tabela.textContent);
      return texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        tabela.querySelector("tbody");
    }) || null;
  }

  function obterCamposExistentesMeuPerfil_v2(tbody) {
    const existentes = new Set();

    Array.from(tbody.querySelectorAll("tr")).forEach(function (linha) {
      const primeiraCelula = linha.querySelector("td");

      if (!primeiraCelula) {
        return;
      }

      const texto = normalizarTextoSistemaMeuPerfil_v2(primeiraCelula.textContent);

      if (texto) {
        existentes.add(texto);
      }
    });

    return existentes;
  }

  //###################################################################################
  // (4) CRIAR LINHAS DE SISTEMA SEM AÇÕES EDITÁVEIS
  //###################################################################################

  function criarCelulaSistemaMeuPerfil_v2(texto) {
    const td = document.createElement("td");
    td.textContent = texto || "-";
    return td;
  }

  function criarCelulaAcoesSistemaMeuPerfil_v2() {
    const td = document.createElement("td");
    const badge = document.createElement("span");

    badge.className = "appverbo-system-field-badge-v2";
    badge.textContent = "Sistema";
    badge.title = "Campo de sistema: não pode ser editado, ordenado ou eliminado.";

    td.appendChild(badge);
    return td;
  }

  function criarLinhaSistemaMeuPerfil_v2(campo) {
    const tr = document.createElement("tr");

    tr.className = "appverbo-system-field-row-v2";
    tr.dataset.systemFieldKeyV2 = campo.key;

    tr.appendChild(criarCelulaSistemaMeuPerfil_v2(campo.label));
    tr.appendChild(criarCelulaSistemaMeuPerfil_v2(campo.typeLabel));
    tr.appendChild(criarCelulaSistemaMeuPerfil_v2(campo.requiredLabel));
    tr.appendChild(criarCelulaSistemaMeuPerfil_v2(campo.sizeLabel));
    tr.appendChild(criarCelulaSistemaMeuPerfil_v2(campo.listLabel));
    tr.appendChild(criarCelulaAcoesSistemaMeuPerfil_v2());

    return tr;
  }

  //###################################################################################
  // (5) ESTILO E NOTA
  //###################################################################################

  function instalarEstiloSistemaMeuPerfil_v2() {
    if (document.getElementById("appverbo-system-fields-style-v2")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "appverbo-system-fields-style-v2";
    style.textContent = [
      ".appverbo-system-field-row-v2 td { background: #f8fafc; color: #334155; }",
      ".appverbo-system-field-row-v2 td:first-child { font-weight: 700; }",
      ".appverbo-system-field-badge-v2 { display: inline-flex; align-items: center; justify-content: center; min-width: 70px; padding: 5px 8px; border-radius: 8px; border: 1px solid #cbd5e1; background: #e2e8f0; color: #334155; font-size: 11px; font-weight: 700; }",
      ".appverbo-system-field-note-v2 { margin: 8px 0 12px; color: #475569; font-size: 12px; }"
    ].join("\n");

    document.head.appendChild(style);
  }

  function inserirNotaSistemaMeuPerfil_v2(tabela) {
    const card = localizarCardCamposCriadosMeuPerfil_v2();

    if (!card || card.querySelector(".appverbo-system-field-note-v2")) {
      return;
    }

    const nota = document.createElement("p");
    nota.className = "appverbo-system-field-note-v2";
    nota.textContent = "Campos de sistema são exibidos apenas para referência e não podem ser editados, ordenados ou eliminados.";

    const wrapperTabela = tabela.parentElement || tabela;
    card.insertBefore(nota, wrapperTabela);
  }

  //###################################################################################
  // (6) APLICAR CAMPOS DE SISTEMA
  //###################################################################################

  function aplicarCamposSistemaMeuPerfil_v2() {
    if (!paginaConfiguracaoMeuPerfil_v2()) {
      return;
    }

    const tabela = localizarTabelaCamposCriadosMeuPerfil_v2();

    if (!tabela) {
      return;
    }

    const tbody = tabela.querySelector("tbody");

    if (!tbody) {
      return;
    }

    instalarEstiloSistemaMeuPerfil_v2();
    inserirNotaSistemaMeuPerfil_v2(tabela);

    const existentes = obterCamposExistentesMeuPerfil_v2(tbody);

    CAMPOS_SISTEMA_MEU_PERFIL_V2
      .slice()
      .reverse()
      .forEach(function (campo) {
        const labelNormalizado = normalizarTextoSistemaMeuPerfil_v2(campo.label);

        if (existentes.has(labelNormalizado)) {
          return;
        }

        tbody.insertBefore(criarLinhaSistemaMeuPerfil_v2(campo), tbody.firstChild);
        existentes.add(labelNormalizado);
      });
  }

  //###################################################################################
  // (7) INICIAR COM REPROCESSAMENTO CURTO
  //###################################################################################

  function iniciarSistemaMeuPerfil_v2() {
    aplicarCamposSistemaMeuPerfil_v2();

    window.setTimeout(aplicarCamposSistemaMeuPerfil_v2, 250);
    window.setTimeout(aplicarCamposSistemaMeuPerfil_v2, 750);
    window.setTimeout(aplicarCamposSistemaMeuPerfil_v2, 1500);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarSistemaMeuPerfil_v2);
  }
  else {
    iniciarSistemaMeuPerfil_v2();
  }

  window.addEventListener("pageshow", iniciarSistemaMeuPerfil_v2);
})();
// APPVERBO_SETTINGS_SYSTEM_FIELDS_V2_END
