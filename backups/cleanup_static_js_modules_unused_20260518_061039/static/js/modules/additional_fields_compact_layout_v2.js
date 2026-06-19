//###################################################################################
// APPVERBOBRAGA - CAMPOS ADICIONAIS EM MODO FECHADO / SIMPLIFICADO - V2
//###################################################################################

(function () {
  "use strict";

  let aplicandoLayoutCompacto_v2 = false;

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizarTexto_v2(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  function escaparHtml_v2(valor) {
    return String(valor || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULÁRIO DOS CAMPOS ADICIONAIS
  //###################################################################################

  function obterFormularioCamposAdicionais_v2() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      const action = String(formulario.getAttribute("action") || "");

      if (action.includes("/settings/menu/process-additional-fields")) {
        return true;
      }

      if (
        formulario.querySelector("input[name='additional_field_label']") ||
        formulario.querySelector("input[name='additional_field_label[]']") ||
        formulario.querySelector("select[name='additional_field_type']") ||
        formulario.querySelector("select[name='additional_field_type[]']")
      ) {
        return true;
      }

      const texto = normalizarTexto_v2(formulario.textContent);

      return (
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("obrigatorio")
      );
    }) || null;
  }

  function obterContainerCampos_v2(formulario) {
    return (
      formulario.querySelector(".additional-fields-grid") ||
      formulario.querySelector(".form-grid") ||
      formulario.querySelector(".personal-grid") ||
      formulario
    );
  }

  //###################################################################################
  // (3) OBTER CONTROLES REAIS DO FORMULÁRIO
  //###################################################################################

  function elementoEstaNoResumo_v2(elemento) {
    return Boolean(elemento && elemento.closest(".additional-fields-compact-layout-v2"));
  }

  function obterInputsNomeCampos_v2(formulario) {
    return Array.from(
      formulario.querySelectorAll(
        "input[name='additional_field_label'], input[name='additional_field_label[]']"
      )
    ).filter(function (input) {
      return !elementoEstaNoResumo_v2(input);
    });
  }

  function obterSelectsTipoCampos_v2(formulario) {
    return Array.from(
      formulario.querySelectorAll(
        "select[name='additional_field_type'], select[name='additional_field_type[]']"
      )
    ).filter(function (select) {
      return !elementoEstaNoResumo_v2(select);
    });
  }

  function obterValorTipo_v2(selectTipo) {
    if (!selectTipo) {
      return "";
    }

    const option = selectTipo.options[selectTipo.selectedIndex];

    const valor = normalizarTexto_v2(selectTipo.value);
    const texto = normalizarTexto_v2(option ? option.textContent : "");

    if (
      valor === "header" ||
      valor.includes("header") ||
      valor.includes("cabecalho") ||
      texto.includes("cabecalho")
    ) {
      return "header";
    }

    return valor || texto;
  }

  function tipoEhCabecalho_v2(selectTipo) {
    return obterValorTipo_v2(selectTipo) === "header";
  }

  //###################################################################################
  // (4) CRIAR RESUMO DOS CAMPOS
  //###################################################################################

  function criarResumoCampos_v2(formulario) {
    const inputsNome = obterInputsNomeCampos_v2(formulario);
    const selectsTipo = obterSelectsTipoCampos_v2(formulario);

    const cabecalhos = [];
    const campos = [];

    let cabecalhoAtual = "";

    inputsNome.forEach(function (inputNome, indice) {
      const nomeCampo = String(inputNome.value || inputNome.getAttribute("value") || "").trim();

      if (!nomeCampo) {
        return;
      }

      const selectTipo = selectsTipo[indice] || null;

      if (tipoEhCabecalho_v2(selectTipo)) {
        cabecalhoAtual = nomeCampo;

        cabecalhos.push({
          ordem: cabecalhos.length + 1,
          nome: nomeCampo
        });

        return;
      }

      campos.push({
        ordem: campos.length + 1,
        nome: nomeCampo,
        cabecalho: cabecalhoAtual || "-"
      });
    });

    return {
      cabecalhos: cabecalhos,
      campos: campos
    };
  }

  //###################################################################################
  // (5) DETETAR ELEMENTOS DE DETALHE PARA ESCONDER / MOSTRAR
  //###################################################################################

  function obterLinhaDoInput_v2(input) {
    if (!input) {
      return null;
    }

    return (
      input.closest(".additional-field-row-equalized") ||
      input.closest(".process-additional-field-row") ||
      input.closest("[data-additional-field-row]") ||
      input.closest(".field")
    );
  }

  function obterElementosDetalhe_v2(formulario) {
    const inputsNome = obterInputsNomeCampos_v2(formulario);
    const elementos = [];

    inputsNome.forEach(function (input) {
      const linha = obterLinhaDoInput_v2(input);

      if (linha && !elementos.includes(linha)) {
        elementos.push(linha);
      }
    });

    const botoesAdicionar = Array.from(formulario.querySelectorAll("button")).filter(function (botao) {
      return normalizarTexto_v2(botao.textContent) === "+";
    });

    botoesAdicionar.forEach(function (botao) {
      const wrapper = botao.closest(".field") || botao.parentElement || botao;

      if (wrapper && !elementos.includes(wrapper)) {
        elementos.push(wrapper);
      }
    });

    const acoes = Array.from(
      formulario.querySelectorAll(".form-action-row, .profile-edit-actions")
    );

    acoes.forEach(function (acao) {
      if (acao && !elementos.includes(acao)) {
        elementos.push(acao);
      }
    });

    return elementos;
  }

  //###################################################################################
  // (6) CSS
  //###################################################################################

  function injetarCssCompacto_v2() {
    const styleId = "additional-fields-compact-layout-style-v2";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      ".additional-fields-compact-layout-v2 {",
      "  margin: 12px 0 18px 0 !important;",
      "  padding: 0 !important;",
      "  width: 100% !important;",
      "}",

      ".additional-fields-compact-toolbar-v2 {",
      "  display: flex !important;",
      "  align-items: center !important;",
      "  justify-content: flex-start !important;",
      "  margin: 0 0 10px 0 !important;",
      "}",

      ".additional-fields-compact-edit-btn-v2 {",
      "  border: 0 !important;",
      "  background: transparent !important;",
      "  color: #244db3 !important;",
      "  padding: 0 !important;",
      "  font-size: 12px !important;",
      "  font-weight: 700 !important;",
      "  text-decoration: underline !important;",
      "  cursor: pointer !important;",
      "}",

      ".additional-fields-compact-card-v2 {",
      "  border: 0 !important;",
      "  border-radius: 0 !important;",
      "  background: transparent !important;",
      "  margin-bottom: 22px !important;",
      "  overflow: visible !important;",
      "}",

      ".additional-fields-compact-title-v2 {",
      "  display: flex !important;",
      "  align-items: center !important;",
      "  justify-content: space-between !important;",
      "  gap: 12px !important;",
      "  padding: 0 0 8px 0 !important;",
      "  border-bottom: 1px solid #cbd7ef !important;",
      "  color: #0f1f3d !important;",
      "  font-size: 14px !important;",
      "  font-weight: 800 !important;",
      "}",

      ".additional-fields-compact-count-v2 {",
      "  color: #244db3 !important;",
      "  font-size: 11px !important;",
      "  font-weight: 700 !important;",
      "}",

      ".additional-fields-compact-table-v2 {",
      "  width: 100% !important;",
      "  border-collapse: collapse !important;",
      "  font-size: 12px !important;",
      "}",

      ".additional-fields-compact-table-v2 th {",
      "  text-align: left !important;",
      "  padding: 9px 8px !important;",
      "  border-bottom: 1px solid #cbd7ef !important;",
      "  color: #34476a !important;",
      "  font-size: 11px !important;",
      "  font-weight: 700 !important;",
      "  text-transform: uppercase !important;",
      "}",

      ".additional-fields-compact-table-v2 td {",
      "  padding: 9px 8px !important;",
      "  border-bottom: 1px solid #e2e9f8 !important;",
      "  color: #0f1f3d !important;",
      "}",

      ".additional-fields-compact-table-v2 tr:last-child td {",
      "  border-bottom: 1px solid #e2e9f8 !important;",
      "}",

      ".additional-fields-detail-hidden-v2 {",
      "  display: none !important;",
      "}",

      ".additional-fields-detail-visible-v2 .additional-field-row-equalized {",
      "  display: grid !important;",
      "  grid-template-columns: minmax(220px, 1.6fr) minmax(180px, 1.1fr) minmax(120px, 0.8fr) minmax(120px, 0.7fr) minmax(220px, 1.3fr) auto auto auto !important;",
      "  gap: 8px !important;",
      "  align-items: end !important;",
      "  margin-bottom: 8px !important;",
      "}",

      "@media (max-width: 900px) {",
      "  .additional-fields-detail-visible-v2 .additional-field-row-equalized {",
      "    grid-template-columns: 1fr !important;",
      "  }",
      "}"
    ].join("\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (7) RENDERIZAR HTML
  //###################################################################################

  function renderizarTabelaCabecalhos_v2(cabecalhos) {
    const linhas = cabecalhos.length
      ? cabecalhos.map(function (item) {
          return [
            "<tr>",
            "<td style=\"width:90px\">" + item.ordem + "</td>",
            "<td>" + escaparHtml_v2(item.nome) + "</td>",
            "</tr>"
          ].join("");
        }).join("")
      : '<tr><td colspan="2">Sem cabeçalhos configurados.</td></tr>';

    return [
      '<div class="additional-fields-compact-card-v2">',
      '  <div class="additional-fields-compact-title-v2">',
      '    <span>Grupo Cabeçalho da aba</span>',
      '    <span class="additional-fields-compact-count-v2">' + cabecalhos.length + ' cabeçalho(s)</span>',
      '  </div>',
      '  <table class="additional-fields-compact-table-v2">',
      '    <thead>',
      '      <tr>',
      '        <th style="width:90px">Ordem</th>',
      '        <th>Cabeçalho</th>',
      '      </tr>',
      '    </thead>',
      '    <tbody>' + linhas + '</tbody>',
      '  </table>',
      '</div>'
    ].join("");
  }

  function renderizarTabelaCampos_v2(campos) {
    const linhas = campos.length
      ? campos.map(function (item) {
          return [
            "<tr>",
            "<td style=\"width:90px\">" + item.ordem + "</td>",
            "<td>" + escaparHtml_v2(item.nome) + "</td>",
            "<td>" + escaparHtml_v2(item.cabecalho) + "</td>",
            "</tr>"
          ].join("");
        }).join("")
      : '<tr><td colspan="3">Sem campos configurados.</td></tr>';

    return [
      '<div class="additional-fields-compact-card-v2">',
      '  <div class="additional-fields-compact-title-v2">',
      '    <span>Grupo de campos</span>',
      '    <span class="additional-fields-compact-count-v2">' + campos.length + ' campo(s)</span>',
      '  </div>',
      '  <table class="additional-fields-compact-table-v2">',
      '    <thead>',
      '      <tr>',
      '        <th style="width:90px">Ordem</th>',
      '        <th>Campo</th>',
      '        <th>Cabeçalho</th>',
      '      </tr>',
      '    </thead>',
      '    <tbody>' + linhas + '</tbody>',
      '  </table>',
      '</div>'
    ].join("");
  }

  //###################################################################################
  // (8) APLICAR LAYOUT
  //###################################################################################

  function aplicarLayoutCompacto_v2() {
    if (aplicandoLayoutCompacto_v2) {
      return;
    }

    const formulario = obterFormularioCamposAdicionais_v2();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v2(formulario);

    if (!container) {
      return;
    }

    aplicandoLayoutCompacto_v2 = true;

    try {
      injetarCssCompacto_v2();

      Array.from(container.querySelectorAll(".additional-fields-compact-layout-v1, .additional-fields-compact-layout-v2")).forEach(function (layout) {
        layout.remove();
      });

      const resumo = criarResumoCampos_v2(formulario);

      const blocoCompacto = document.createElement("div");
      blocoCompacto.className = "additional-fields-compact-layout-v2";

      blocoCompacto.innerHTML = [
        '<div class="additional-fields-compact-toolbar-v2">',
        '  <button type="button" class="additional-fields-compact-edit-btn-v2" data-compact-edit-toggle-v2="1">Editar campos adicionais</button>',
        '</div>',
        renderizarTabelaCabecalhos_v2(resumo.cabecalhos),
        renderizarTabelaCampos_v2(resumo.campos)
      ].join("");

      const inputsNome = obterInputsNomeCampos_v2(formulario);
      const primeiroInput = inputsNome[0];

      if (primeiroInput) {
        const primeiroBloco = obterLinhaDoInput_v2(primeiroInput) || primeiroInput.closest(".field") || primeiroInput;
        container.insertBefore(blocoCompacto, primeiroBloco);
      } else {
        container.prepend(blocoCompacto);
      }

      const detalhesVisiveis = formulario.dataset.additionalFieldsDetailsOpen === "1";
      const elementosDetalhe = obterElementosDetalhe_v2(formulario);

      elementosDetalhe.forEach(function (elemento) {
        elemento.classList.toggle("additional-fields-detail-hidden-v2", !detalhesVisiveis);
      });

      container.classList.toggle("additional-fields-detail-visible-v2", detalhesVisiveis);

      const botaoToggle = blocoCompacto.querySelector("[data-compact-edit-toggle-v2='1']");

      if (botaoToggle) {
        botaoToggle.textContent = detalhesVisiveis ? "Fechar edição" : "Editar campos adicionais";
        botaoToggle.addEventListener("click", function () {
          formulario.dataset.additionalFieldsDetailsOpen = detalhesVisiveis ? "0" : "1";
          aplicarLayoutCompacto_v2();
        });
      }
    } finally {
      aplicandoLayoutCompacto_v2 = false;
    }
  }

  //###################################################################################
  // (9) OBSERVAR ALTERAÇÕES
  //###################################################################################

  function observarAlteracoes_v2() {
    const formulario = obterFormularioCamposAdicionais_v2();

    if (!formulario || formulario.dataset.compactLayoutObserverV2 === "1") {
      return;
    }

    formulario.dataset.compactLayoutObserverV2 = "1";

    formulario.addEventListener("change", function () {
      window.setTimeout(aplicarLayoutCompacto_v2, 80);
    });

    formulario.addEventListener("input", function () {
      window.setTimeout(aplicarLayoutCompacto_v2, 80);
    });
  }

  //###################################################################################
  // (10) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v2() {
    aplicarLayoutCompacto_v2();
    observarAlteracoes_v2();

    window.setTimeout(aplicarLayoutCompacto_v2, 100);
    window.setTimeout(aplicarLayoutCompacto_v2, 400);
    window.setTimeout(aplicarLayoutCompacto_v2, 1000);
    window.setTimeout(aplicarLayoutCompacto_v2, 1800);
    window.setTimeout(aplicarLayoutCompacto_v2, 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v2);
  } else {
    inicializar_v2();
  }
})();
