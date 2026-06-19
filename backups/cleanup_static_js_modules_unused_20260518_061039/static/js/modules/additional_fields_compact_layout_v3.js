//###################################################################################
// APPVERBOBRAGA - CAMPOS ADICIONAIS EM MODO FECHADO / SIMPLIFICADO - V3
//###################################################################################

(function () {
  "use strict";

  let aplicandoLayoutCompacto_v3 = false;

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizarTexto_v3(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  function escaparHtml_v3(valor) {
    return String(valor || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULÁRIO DOS CAMPOS ADICIONAIS
  //###################################################################################

  function obterFormularioCamposAdicionais_v3() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      const action = String(formulario.getAttribute("action") || "");

      if (action.includes("/settings/menu/process-additional-fields")) {
        return true;
      }

      const texto = normalizarTexto_v3(formulario.textContent);

      return (
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("obrigatorio")
      );
    }) || null;
  }

  function obterContainerCampos_v3(formulario) {
    return (
      formulario.querySelector(".additional-fields-grid") ||
      formulario.querySelector(".form-grid") ||
      formulario.querySelector(".personal-grid") ||
      formulario
    );
  }

  //###################################################################################
  // (3) IDENTIFICAR ELEMENTOS DA LINHA
  //###################################################################################

  function obterTextoLabelElemento_v3(elemento) {
    const label = elemento ? elemento.querySelector("label") : null;
    return normalizarTexto_v3(label ? label.textContent : "");
  }

  function elementoEhNomeCampo_v3(elemento) {
    if (!elemento) {
      return false;
    }

    return obterTextoLabelElemento_v3(elemento).includes("nome do campo adicional");
  }

  function elementoEhTipoCampo_v3(elemento) {
    if (!elemento) {
      return false;
    }

    return obterTextoLabelElemento_v3(elemento).includes("tipo do campo");
  }

  function elementoEhBotaoAdicionar_v3(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector && elemento.querySelector("button");

    return Boolean(botao && normalizarTexto_v3(botao.textContent) === "+");
  }

  function elementoEhAcoesFormulario_v3(elemento) {
    if (!elemento) {
      return false;
    }

    if (elemento.classList && elemento.classList.contains("form-action-row")) {
      return true;
    }

    if (elemento.classList && elemento.classList.contains("profile-edit-actions")) {
      return true;
    }

    return Boolean(elemento.querySelector && elemento.querySelector("button[type='submit']"));
  }

  //###################################################################################
  // (4) OBTER VALORES DA LINHA
  //###################################################################################

  function obterValorInput_v3(elemento) {
    const input = elemento ? elemento.querySelector("input") : null;

    if (!input) {
      return "";
    }

    return String(input.value || input.getAttribute("value") || "").trim();
  }

  function obterSelectTipoDaLinha_v3(elementosLinha) {
    for (const elemento of elementosLinha) {
      if (!elementoEhTipoCampo_v3(elemento)) {
        continue;
      }

      const select = elemento.querySelector("select");

      if (select) {
        return select;
      }
    }

    return null;
  }

  function tipoEhCabecalho_v3(selectTipo) {
    if (!selectTipo) {
      return false;
    }

    const option = selectTipo.options[selectTipo.selectedIndex];
    const valor = normalizarTexto_v3(selectTipo.value);
    const texto = normalizarTexto_v3(option ? option.textContent : "");

    return (
      valor === "header" ||
      valor.includes("header") ||
      valor.includes("cabecalho") ||
      texto.includes("cabecalho")
    );
  }

  //###################################################################################
  // (5) MONTAR LINHAS PELOS LABELS DA TELA
  //###################################################################################

  function obterLinhasLogicasCampos_v3(container) {
    const filhos = Array.from(container.children).filter(function (elemento) {
      return !elemento.classList.contains("additional-fields-compact-layout-v3");
    });

    const linhas = [];
    let indice = 0;

    while (indice < filhos.length) {
      const elementoAtual = filhos[indice];

      if (!elementoEhNomeCampo_v3(elementoAtual)) {
        indice += 1;
        continue;
      }

      const elementosLinha = [elementoAtual];
      let proximoIndice = indice + 1;

      while (proximoIndice < filhos.length) {
        const proximoElemento = filhos[proximoIndice];

        if (!proximoElemento) {
          break;
        }

        if (elementoEhNomeCampo_v3(proximoElemento)) {
          break;
        }

        if (elementoEhBotaoAdicionar_v3(proximoElemento) || elementoEhAcoesFormulario_v3(proximoElemento)) {
          break;
        }

        elementosLinha.push(proximoElemento);
        proximoIndice += 1;
      }

      const nome = obterValorInput_v3(elementoAtual);
      const selectTipo = obterSelectTipoDaLinha_v3(elementosLinha);

      linhas.push({
        nome: nome,
        ehCabecalho: tipoEhCabecalho_v3(selectTipo),
        elementos: elementosLinha
      });

      indice = proximoIndice;
    }

    return linhas;
  }

  //###################################################################################
  // (6) CRIAR RESUMO
  //###################################################################################

  function criarResumoCampos_v3(linhasLogicas) {
    const cabecalhos = [];
    const campos = [];
    let cabecalhoAtual = "";

    linhasLogicas.forEach(function (linha) {
      if (!linha.nome) {
        return;
      }

      if (linha.ehCabecalho) {
        cabecalhoAtual = linha.nome;

        cabecalhos.push({
          ordem: cabecalhos.length + 1,
          nome: linha.nome
        });

        return;
      }

      campos.push({
        ordem: campos.length + 1,
        nome: linha.nome,
        cabecalho: cabecalhoAtual || "-"
      });
    });

    return {
      cabecalhos: cabecalhos,
      campos: campos
    };
  }

  //###################################################################################
  // (7) CSS DO MODO FECHADO
  //###################################################################################

  function injetarCssCompacto_v3() {
    const styleId = "additional-fields-compact-layout-style-v3";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      ".additional-fields-compact-layout-v3 {",
      "  margin: 12px 0 18px 0 !important;",
      "  padding: 0 !important;",
      "  width: 100% !important;",
      "}",

      ".additional-fields-compact-toolbar-v3 {",
      "  display: flex !important;",
      "  align-items: center !important;",
      "  justify-content: flex-start !important;",
      "  margin: 0 0 10px 0 !important;",
      "}",

      ".additional-fields-compact-edit-btn-v3 {",
      "  border: 0 !important;",
      "  background: transparent !important;",
      "  color: #244db3 !important;",
      "  padding: 0 !important;",
      "  font-size: 12px !important;",
      "  font-weight: 700 !important;",
      "  text-decoration: underline !important;",
      "  cursor: pointer !important;",
      "}",

      ".additional-fields-compact-card-v3 {",
      "  border: 0 !important;",
      "  background: transparent !important;",
      "  margin-bottom: 22px !important;",
      "}",

      ".additional-fields-compact-title-v3 {",
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

      ".additional-fields-compact-count-v3 {",
      "  color: #244db3 !important;",
      "  font-size: 11px !important;",
      "  font-weight: 700 !important;",
      "}",

      ".additional-fields-compact-table-v3 {",
      "  width: 100% !important;",
      "  border-collapse: collapse !important;",
      "  font-size: 12px !important;",
      "}",

      ".additional-fields-compact-table-v3 th {",
      "  text-align: left !important;",
      "  padding: 9px 8px !important;",
      "  border-bottom: 1px solid #cbd7ef !important;",
      "  color: #34476a !important;",
      "  font-size: 11px !important;",
      "  font-weight: 700 !important;",
      "  text-transform: uppercase !important;",
      "}",

      ".additional-fields-compact-table-v3 td {",
      "  padding: 9px 8px !important;",
      "  border-bottom: 1px solid #e2e9f8 !important;",
      "  color: #0f1f3d !important;",
      "}",

      ".additional-fields-detail-hidden-v3 {",
      "  display: none !important;",
      "}",

      ".additional-fields-detail-visible-v3 {",
      "  display: grid !important;",
      "  grid-template-columns: repeat(5, minmax(120px, 1fr)) auto auto auto !important;",
      "  gap: 8px !important;",
      "  align-items: end !important;",
      "}"
    ].join("\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (8) RENDERIZAR TABELAS
  //###################################################################################

  function renderizarTabelaCabecalhos_v3(cabecalhos) {
    const linhas = cabecalhos.length
      ? cabecalhos.map(function (item) {
          return [
            "<tr>",
            "<td style=\"width:90px\">" + item.ordem + "</td>",
            "<td>" + escaparHtml_v3(item.nome) + "</td>",
            "</tr>"
          ].join("");
        }).join("")
      : '<tr><td colspan="2">Sem cabeçalhos configurados.</td></tr>';

    return [
      '<div class="additional-fields-compact-card-v3">',
      '  <div class="additional-fields-compact-title-v3">',
      '    <span>Grupo Cabeçalho da aba</span>',
      '    <span class="additional-fields-compact-count-v3">' + cabecalhos.length + ' cabeçalho(s)</span>',
      '  </div>',
      '  <table class="additional-fields-compact-table-v3">',
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

  function renderizarTabelaCampos_v3(campos) {
    const linhas = campos.length
      ? campos.map(function (item) {
          return [
            "<tr>",
            "<td style=\"width:90px\">" + item.ordem + "</td>",
            "<td>" + escaparHtml_v3(item.nome) + "</td>",
            "<td>" + escaparHtml_v3(item.cabecalho) + "</td>",
            "</tr>"
          ].join("");
        }).join("")
      : '<tr><td colspan="3">Sem campos configurados.</td></tr>';

    return [
      '<div class="additional-fields-compact-card-v3">',
      '  <div class="additional-fields-compact-title-v3">',
      '    <span>Grupo de campos</span>',
      '    <span class="additional-fields-compact-count-v3">' + campos.length + ' campo(s)</span>',
      '  </div>',
      '  <table class="additional-fields-compact-table-v3">',
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
  // (9) MOSTRAR / ESCONDER DETALHES
  //###################################################################################

  function aplicarVisibilidadeDetalhes_v3(formulario, linhasLogicas, detalhesVisiveis) {
    linhasLogicas.forEach(function (linha) {
      linha.elementos.forEach(function (elemento) {
        elemento.classList.toggle("additional-fields-detail-hidden-v3", !detalhesVisiveis);
        elemento.classList.toggle("additional-fields-detail-visible-v3", detalhesVisiveis);
      });
    });

    const container = obterContainerCampos_v3(formulario);

    Array.from(container.children).forEach(function (elemento) {
      if (elementoEhBotaoAdicionar_v3(elemento) || elementoEhAcoesFormulario_v3(elemento)) {
        elemento.classList.toggle("additional-fields-detail-hidden-v3", !detalhesVisiveis);
      }
    });
  }

  //###################################################################################
  // (10) APLICAR LAYOUT COMPACTO
  //###################################################################################

  function aplicarLayoutCompacto_v3() {
    if (aplicandoLayoutCompacto_v3) {
      return;
    }

    const formulario = obterFormularioCamposAdicionais_v3();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v3(formulario);

    if (!container) {
      return;
    }

    aplicandoLayoutCompacto_v3 = true;

    try {
      injetarCssCompacto_v3();

      Array.from(
        container.querySelectorAll(
          ".additional-fields-compact-layout-v1, .additional-fields-compact-layout-v2, .additional-fields-compact-layout-v3"
        )
      ).forEach(function (layout) {
        layout.remove();
      });

      const linhasLogicas = obterLinhasLogicasCampos_v3(container);
      const resumo = criarResumoCampos_v3(linhasLogicas);

      const blocoCompacto = document.createElement("div");
      blocoCompacto.className = "additional-fields-compact-layout-v3";

      blocoCompacto.innerHTML = [
        '<div class="additional-fields-compact-toolbar-v3">',
        '  <button type="button" class="additional-fields-compact-edit-btn-v3" data-compact-edit-toggle-v3="1">Editar campos adicionais</button>',
        '</div>',
        renderizarTabelaCabecalhos_v3(resumo.cabecalhos),
        renderizarTabelaCampos_v3(resumo.campos)
      ].join("");

      if (linhasLogicas.length && linhasLogicas[0].elementos.length) {
        container.insertBefore(blocoCompacto, linhasLogicas[0].elementos[0]);
      } else {
        container.prepend(blocoCompacto);
      }

      const detalhesVisiveis = formulario.dataset.additionalFieldsDetailsOpen === "1";

      aplicarVisibilidadeDetalhes_v3(formulario, linhasLogicas, detalhesVisiveis);

      const botaoToggle = blocoCompacto.querySelector("[data-compact-edit-toggle-v3='1']");

      if (botaoToggle) {
        botaoToggle.textContent = detalhesVisiveis ? "Fechar edição" : "Editar campos adicionais";
        botaoToggle.addEventListener("click", function () {
          formulario.dataset.additionalFieldsDetailsOpen = detalhesVisiveis ? "0" : "1";
          aplicarLayoutCompacto_v3();
        });
      }
    } finally {
      aplicandoLayoutCompacto_v3 = false;
    }
  }

  //###################################################################################
  // (11) OBSERVAR ALTERAÇÕES
  //###################################################################################

  function observarAlteracoes_v3() {
    const formulario = obterFormularioCamposAdicionais_v3();

    if (!formulario || formulario.dataset.compactLayoutObserverV3 === "1") {
      return;
    }

    formulario.dataset.compactLayoutObserverV3 = "1";

    formulario.addEventListener("change", function () {
      window.setTimeout(aplicarLayoutCompacto_v3, 80);
    });

    formulario.addEventListener("input", function () {
      window.setTimeout(aplicarLayoutCompacto_v3, 80);
    });
  }

  //###################################################################################
  // (12) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v3() {
    aplicarLayoutCompacto_v3();
    observarAlteracoes_v3();

    window.setTimeout(aplicarLayoutCompacto_v3, 100);
    window.setTimeout(aplicarLayoutCompacto_v3, 400);
    window.setTimeout(aplicarLayoutCompacto_v3, 1000);
    window.setTimeout(aplicarLayoutCompacto_v3, 1800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v3);
  } else {
    inicializar_v3();
  }
})();
