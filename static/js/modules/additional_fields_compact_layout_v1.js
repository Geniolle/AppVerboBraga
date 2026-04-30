//###################################################################################
// APPVERBOBRAGA - CAMPOS ADICIONAIS EM MODO FECHADO / SIMPLIFICADO - V1
//###################################################################################

(function () {
  "use strict";

  let aplicandoLayoutCompacto_v1 = false;

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizarTexto_v1(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  function escaparHtml_v1(valor) {
    return String(valor || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULÁRIO DOS CAMPOS ADICIONAIS
  //###################################################################################

  function obterFormularioCamposAdicionais_v1() {
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

      const texto = normalizarTexto_v1(formulario.textContent);

      return (
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("obrigatorio")
      );
    }) || null;
  }

  function obterContainerCampos_v1(formulario) {
    return (
      formulario.querySelector(".additional-fields-grid") ||
      formulario.querySelector(".form-grid") ||
      formulario.querySelector(".personal-grid") ||
      formulario
    );
  }

  //###################################################################################
  // (3) DETETAR E MONTAR LINHAS
  //###################################################################################

  function obterTextoLabel_v1(elemento) {
    const label = elemento ? elemento.querySelector("label") : null;
    return normalizarTexto_v1(label ? label.textContent : "");
  }

  function elementoEhCampoNome_v1(elemento) {
    if (!elemento) {
      return false;
    }

    if (obterTextoLabel_v1(elemento).includes("nome do campo adicional")) {
      return true;
    }

    return Boolean(
      elemento.querySelector &&
      (
        elemento.querySelector("input[name='additional_field_label']") ||
        elemento.querySelector("input[name='additional_field_label[]']")
      )
    );
  }

  function elementoEhBotaoRemover_v1(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector && elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    const texto = normalizarTexto_v1(botao.textContent);
    const titulo = normalizarTexto_v1(botao.getAttribute("title"));

    return (
      texto === "x" ||
      texto === "×" ||
      titulo.includes("remover") ||
      titulo.includes("excluir") ||
      botao.classList.contains("remove-field-btn") ||
      botao.classList.contains("btn-danger")
    );
  }

  function elementoEhBotaoAdicionar_v1(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector && elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    return normalizarTexto_v1(botao.textContent) === "+";
  }

  function elementoEhAcoesFormulario_v1(elemento) {
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

  function desmontarLayoutsAntigos_v1(container) {
    Array.from(
      container.querySelectorAll(
        ".additional-fields-compact-layout-v1, .additional-fields-group-v3, .additional-fields-group-v4, .additional-fields-group-v5, .additional-fields-subgroup-marker-v2"
      )
    ).forEach(function (bloco) {
      bloco.remove();
    });
  }

  function montarLinhasEqualizadasSeNecessario_v1(container) {
    if (container.querySelector(".additional-field-row-equalized")) {
      return;
    }

    const filhos = Array.from(container.children);
    let indice = 0;

    while (indice < filhos.length) {
      const elementoAtual = filhos[indice];

      if (!elementoAtual || !elementoEhCampoNome_v1(elementoAtual)) {
        indice += 1;
        continue;
      }

      const elementosDaLinha = [elementoAtual];
      let proximoIndice = indice + 1;

      while (proximoIndice < filhos.length) {
        const proximoElemento = filhos[proximoIndice];

        if (!proximoElemento) {
          break;
        }

        if (elementoEhCampoNome_v1(proximoElemento)) {
          break;
        }

        if (elementoEhBotaoAdicionar_v1(proximoElemento) || elementoEhAcoesFormulario_v1(proximoElemento)) {
          break;
        }

        elementosDaLinha.push(proximoElemento);
        proximoIndice += 1;

        if (elementoEhBotaoRemover_v1(proximoElemento)) {
          break;
        }
      }

      const linha = document.createElement("div");
      linha.className = "additional-field-row-equalized additional-field-row-generated-compact-v1";
      linha.setAttribute("data-additional-field-row", "1");

      container.insertBefore(linha, elementoAtual);

      elementosDaLinha.forEach(function (elemento) {
        linha.appendChild(elemento);
      });

      indice = proximoIndice;
    }
  }

  function obterLinhasCamposAdicionais_v1(container) {
    return Array.from(container.querySelectorAll(".additional-field-row-equalized"));
  }

  //###################################################################################
  // (4) LER VALORES DA LINHA
  //###################################################################################

  function obterInputNomeDaLinha_v1(linha) {
    return (
      linha.querySelector("input[name='additional_field_label']") ||
      linha.querySelector("input[name='additional_field_label[]']") ||
      Array.from(linha.querySelectorAll("input")).find(function (input) {
        const field = input.closest(".field");
        const label = field ? field.querySelector("label") : null;
        return normalizarTexto_v1(label ? label.textContent : "").includes("nome do campo adicional");
      }) ||
      linha.querySelector("input")
    );
  }

  function obterSelectTipoDaLinha_v1(linha) {
    return (
      linha.querySelector("select[name='additional_field_type']") ||
      linha.querySelector("select[name='additional_field_type[]']") ||
      Array.from(linha.querySelectorAll("select")).find(function (select) {
        const field = select.closest(".field");
        const label = field ? field.querySelector("label") : null;
        return normalizarTexto_v1(label ? label.textContent : "").includes("tipo do campo");
      }) ||
      null
    );
  }

  function obterNomeLinha_v1(linha) {
    const input = obterInputNomeDaLinha_v1(linha);
    return String(input ? input.value || input.getAttribute("value") || "" : "").trim();
  }

  function linhaEhCabecalho_v1(linha) {
    const selectTipo = obterSelectTipoDaLinha_v1(linha);

    if (!selectTipo) {
      return false;
    }

    const option = selectTipo.options[selectTipo.selectedIndex];
    const valor = normalizarTexto_v1(selectTipo.value);
    const texto = normalizarTexto_v1(option ? option.textContent : "");

    return (
      valor === "header" ||
      valor.includes("header") ||
      valor.includes("cabecalho") ||
      texto.includes("cabecalho")
    );
  }

  //###################################################################################
  // (5) CRIAR DADOS DO RESUMO
  //###################################################################################

  function criarResumoCampos_v1(linhas) {
    const cabecalhos = [];
    const campos = [];
    let cabecalhoAtual = "";

    linhas.forEach(function (linha) {
      const nome = obterNomeLinha_v1(linha);

      if (!nome) {
        return;
      }

      if (linhaEhCabecalho_v1(linha)) {
        cabecalhoAtual = nome;
        cabecalhos.push({
          ordem: cabecalhos.length + 1,
          nome: nome
        });
        return;
      }

      campos.push({
        ordem: campos.length + 1,
        nome: nome,
        cabecalho: cabecalhoAtual || "-"
      });
    });

    return {
      cabecalhos: cabecalhos,
      campos: campos
    };
  }

  //###################################################################################
  // (6) CSS
  //###################################################################################

  function injetarCssCompacto_v1() {
    const styleId = "additional-fields-compact-layout-style-v1";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      ".additional-fields-compact-layout-v1 {",
      "  margin: 12px 0 16px 0 !important;",
      "  padding: 0 !important;",
      "}",

      ".additional-fields-compact-toolbar-v1 {",
      "  display: flex !important;",
      "  justify-content: flex-start !important;",
      "  gap: 8px !important;",
      "  margin: 0 0 12px 0 !important;",
      "}",

      ".additional-fields-compact-edit-btn-v1 {",
      "  border: 0 !important;",
      "  background: transparent !important;",
      "  color: #244db3 !important;",
      "  border-radius: 0 !important;",
      "  padding: 0 !important;",
      "  font-size: 12px !important;",
      "  font-weight: 700 !important;",
      "  text-decoration: underline !important;",
      "  cursor: pointer !important;",
      "  box-shadow: none !important;",
      "}",

      ".additional-fields-compact-card-v1 {",
      "  border: 0 !important;",
      "  border-radius: 0 !important;",
      "  background: transparent !important;",
      "  margin: 0 0 18px 0 !important;",
      "  overflow: visible !important;",
      "  box-shadow: none !important;",
      "}",

      ".additional-fields-compact-title-v1 {",
      "  display: flex !important;",
      "  justify-content: space-between !important;",
      "  align-items: center !important;",
      "  padding: 0 0 10px 0 !important;",
      "  background: transparent !important;",
      "  border: 0 !important;",
      "  border-bottom: 1px solid #d7e1f5 !important;",
      "  font-size: 14px !important;",
      "  font-weight: 700 !important;",
      "  color: #0f1f3d !important;",
      "}",

      ".additional-fields-compact-count-v1 {",
      "  border: 0 !important;",
      "  background: transparent !important;",
      "  color: #5c6f91 !important;",
      "  border-radius: 0 !important;",
      "  padding: 0 !important;",
      "  font-size: 11px !important;",
      "  font-weight: 600 !important;",
      "}",

      ".additional-fields-compact-table-v1 {",
      "  width: 100% !important;",
      "  border-collapse: collapse !important;",
      "  font-size: 12px !important;",
      "  background: transparent !important;",
      "}",

      ".additional-fields-compact-table-v1 th {",
      "  text-align: left !important;",
      "  padding: 12px 8px !important;",
      "  border-bottom: 1px solid #d7e1f5 !important;",
      "  color: #34476a !important;",
      "  font-size: 11px !important;",
      "  text-transform: uppercase !important;",
      "  letter-spacing: 0.02em !important;",
      "  background: transparent !important;",
      "}",

      ".additional-fields-compact-table-v1 td {",
      "  padding: 14px 8px !important;",
      "  border-bottom: 1px solid #e3eaf5 !important;",
      "  color: #0f1f3d !important;",
      "  background: transparent !important;",
      "}",

      ".additional-fields-compact-table-v1 tr:last-child td {",
      "  border-bottom: 0 !important;",
      "}",

      ".additional-fields-detail-hidden-v1 {",
      "  display: none !important;",
      "}",

      ".additional-fields-detail-visible-v1 .additional-field-row-equalized {",
      "  display: grid !important;",
      "  grid-template-columns: minmax(220px, 1.6fr) minmax(180px, 1.1fr) minmax(120px, 0.8fr) minmax(120px, 0.7fr) minmax(220px, 1.3fr) auto auto auto !important;",
      "  gap: 8px !important;",
      "  align-items: end !important;",
      "  margin-bottom: 8px !important;",
      "}",

      "@media (max-width: 900px) {",
      "  .additional-fields-detail-visible-v1 .additional-field-row-equalized {",
      "    grid-template-columns: 1fr !important;",
      "  }",
      "}"
    ].join("\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (7) RENDERIZAR TABELAS
  //###################################################################################

  function renderizarTabelaCabecalhos_v1(cabecalhos) {
    const linhas = cabecalhos.length
      ? cabecalhos.map(function (item) {
          return [
            "<tr>",
            "<td style=\"width:90px\">" + item.ordem + "</td>",
            "<td>" + escaparHtml_v1(item.nome) + "</td>",
            "</tr>"
          ].join("");
        }).join("")
      : '<tr><td colspan="2">Sem cabeçalhos configurados.</td></tr>';

    return [
      '<div class="additional-fields-compact-card-v1">',
      '  <div class="additional-fields-compact-title-v1">',
      '    <span>Grupo Cabeçalho da aba</span>',
      '    <span class="additional-fields-compact-count-v1">' + cabecalhos.length + ' cabeçalho(s)</span>',
      '  </div>',
      '  <table class="additional-fields-compact-table-v1">',
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

  function renderizarTabelaCampos_v1(campos) {
    const linhas = campos.length
      ? campos.map(function (item) {
          return [
            "<tr>",
            "<td style=\"width:90px\">" + item.ordem + "</td>",
            "<td>" + escaparHtml_v1(item.nome) + "</td>",
            "<td>" + escaparHtml_v1(item.cabecalho) + "</td>",
            "</tr>"
          ].join("");
        }).join("")
      : '<tr><td colspan="3">Sem campos configurados.</td></tr>';

    return [
      '<div class="additional-fields-compact-card-v1">',
      '  <div class="additional-fields-compact-title-v1">',
      '    <span>Grupo de campos</span>',
      '    <span class="additional-fields-compact-count-v1">' + campos.length + ' campo(s)</span>',
      '  </div>',
      '  <table class="additional-fields-compact-table-v1">',
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
  // (8) APLICAR LAYOUT COMPACTO
  //###################################################################################

  function aplicarLayoutCompacto_v1() {
    if (aplicandoLayoutCompacto_v1) {
      return;
    }

    const formulario = obterFormularioCamposAdicionais_v1();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v1(formulario);

    if (!container) {
      return;
    }

    aplicandoLayoutCompacto_v1 = true;

    try {
      injetarCssCompacto_v1();
      desmontarLayoutsAntigos_v1(container);
      montarLinhasEqualizadasSeNecessario_v1(container);

      const linhas = obterLinhasCamposAdicionais_v1(container);

      if (!linhas.length) {
        return;
      }

      const resumo = criarResumoCampos_v1(linhas);

      let blocoCompacto = container.querySelector(".additional-fields-compact-layout-v1");

      if (!blocoCompacto) {
        blocoCompacto = document.createElement("div");
        blocoCompacto.className = "additional-fields-compact-layout-v1";
        container.insertBefore(blocoCompacto, linhas[0]);
      }

      blocoCompacto.innerHTML = [
        '<div class="additional-fields-compact-toolbar-v1">',
        '  <button type="button" class="additional-fields-compact-edit-btn-v1" data-compact-edit-toggle="1">Editar campos adicionais</button>',
        '</div>',
        renderizarTabelaCabecalhos_v1(resumo.cabecalhos),
        renderizarTabelaCampos_v1(resumo.campos)
      ].join("");

      const detalhesVisiveis = formulario.dataset.additionalFieldsDetailsOpen === "1";

      linhas.forEach(function (linha) {
        linha.classList.toggle("additional-fields-detail-hidden-v1", !detalhesVisiveis);
      });

      const botaoAdicionar = Array.from(container.children).find(elementoEhBotaoAdicionar_v1);
      const acoesFormulario = Array.from(container.children).find(elementoEhAcoesFormulario_v1);

      if (botaoAdicionar) {
        botaoAdicionar.classList.toggle("additional-fields-detail-hidden-v1", !detalhesVisiveis);
      }

      if (acoesFormulario) {
        acoesFormulario.classList.toggle("additional-fields-detail-hidden-v1", !detalhesVisiveis);
      }

      container.classList.toggle("additional-fields-detail-visible-v1", detalhesVisiveis);

      const botaoToggle = blocoCompacto.querySelector("[data-compact-edit-toggle='1']");

      if (botaoToggle) {
        botaoToggle.textContent = detalhesVisiveis ? "Fechar edição" : "Editar campos adicionais";
        botaoToggle.addEventListener("click", function () {
          formulario.dataset.additionalFieldsDetailsOpen = detalhesVisiveis ? "0" : "1";
          aplicarLayoutCompacto_v1();
        });
      }
    } finally {
      aplicandoLayoutCompacto_v1 = false;
    }
  }

  //###################################################################################
  // (9) OBSERVAR ALTERAÇÕES
  //###################################################################################

  function observarAlteracoes_v1() {
    const formulario = obterFormularioCamposAdicionais_v1();

    if (!formulario || formulario.dataset.compactLayoutObserverV1 === "1") {
      return;
    }

    formulario.dataset.compactLayoutObserverV1 = "1";

    formulario.addEventListener("change", function () {
      window.setTimeout(aplicarLayoutCompacto_v1, 80);
    });

  }

  //###################################################################################
  // (10) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v1() {
    aplicarLayoutCompacto_v1();
    observarAlteracoes_v1();

    window.setTimeout(aplicarLayoutCompacto_v1, 100);
    window.setTimeout(aplicarLayoutCompacto_v1, 400);
    window.setTimeout(aplicarLayoutCompacto_v1, 1000);
    window.setTimeout(aplicarLayoutCompacto_v1, 1800);
    window.setTimeout(aplicarLayoutCompacto_v1, 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v1);
  } else {
    inicializar_v1();
  }
})();
