//###################################################################################
// APPVERBOBRAGA - AGRUPAR CAMPOS ADICIONAIS EM CABEÇALHOS E CAMPOS - V5
//###################################################################################

(function () {
  "use strict";

  let aplicandoAgrupamento_v5 = false;

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizarTexto_v5(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ");
  }

  //###################################################################################
  // (2) LOCALIZAR FORMULÁRIO DOS CAMPOS ADICIONAIS
  //###################################################################################

  function obterFormularioCamposAdicionais_v5() {
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

      const texto = normalizarTexto_v5(formulario.textContent);

      return (
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("obrigatorio")
      );
    }) || null;
  }

  function obterContainerCampos_v5(formulario) {
    return (
      formulario.querySelector("#process-additional-fields-container") ||
      formulario.querySelector(".process-additional-fields-grid") ||
      formulario.querySelector(".process-visible-fields") ||
      formulario.querySelector(".additional-fields-grid") ||
      formulario.querySelector(".form-grid") ||
      formulario.querySelector(".personal-grid") ||
      formulario
    );
  }

  //###################################################################################
  // (3) IDENTIFICAR ELEMENTOS
  //###################################################################################

  function obterTextoLabel_v5(elemento) {
    const label = elemento ? elemento.querySelector("label") : null;
    return normalizarTexto_v5(label ? label.textContent : "");
  }

  function elementoEhCampoNome_v5(elemento) {
    if (!elemento) {
      return false;
    }

    if (obterTextoLabel_v5(elemento).includes("nome do campo adicional")) {
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

  function elementoEhBotaoRemover_v5(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector && elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    const texto = normalizarTexto_v5(botao.textContent);
    const titulo = normalizarTexto_v5(botao.getAttribute("title"));

    return (
      texto === "x" ||
      texto === "×" ||
      titulo.includes("remover") ||
      titulo.includes("excluir") ||
      botao.classList.contains("remove-field-btn") ||
      botao.classList.contains("btn-danger")
    );
  }

  function elementoEhBotaoAdicionar_v5(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector && elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    return normalizarTexto_v5(botao.textContent) === "+";
  }

  function elementoEhAcoesFormulario_v5(elemento) {
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
  // (4) DESMONTAR AGRUPAMENTOS ANTERIORES
  //###################################################################################

  function desmontarGruposExistentes_v5(container) {
    const grupos = Array.from(
      container.querySelectorAll(
        ".additional-fields-group-v3, .additional-fields-group-v4, .additional-fields-group-v5"
      )
    );

    grupos.forEach(function (grupo) {
      const linhas = Array.from(
        grupo.querySelectorAll(".process-additional-field-row, .additional-field-row-equalized")
      );

      linhas.forEach(function (linha) {
        container.insertBefore(linha, grupo);
      });

      grupo.remove();
    });

    Array.from(container.querySelectorAll(".additional-fields-subgroup-marker-v2")).forEach(function (marker) {
      marker.remove();
    });
  }

  //###################################################################################
  // (5) MONTAR LINHAS QUANDO A TELA AINDA ESTÁ EM GRID SOLTO
  //###################################################################################

  function montarLinhasEqualizadasSeNecessario_v5(container) {
    if (container.querySelector(".process-additional-field-row")) {
      return;
    }

    if (container.querySelector(".additional-field-row-equalized")) {
      return;
    }

    const filhos = Array.from(container.children);
    let indice = 0;

    while (indice < filhos.length) {
      const elementoAtual = filhos[indice];

      if (!elementoAtual || !elementoEhCampoNome_v5(elementoAtual)) {
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

        if (elementoEhCampoNome_v5(proximoElemento)) {
          break;
        }

        if (elementoEhBotaoAdicionar_v5(proximoElemento) || elementoEhAcoesFormulario_v5(proximoElemento)) {
          break;
        }

        elementosDaLinha.push(proximoElemento);
        proximoIndice += 1;

        if (elementoEhBotaoRemover_v5(proximoElemento)) {
          break;
        }
      }

      const linha = document.createElement("div");
      linha.className = "additional-field-row-equalized additional-field-row-generated-v5";
      linha.setAttribute("data-additional-field-row", "1");

      container.insertBefore(linha, elementoAtual);

      elementosDaLinha.forEach(function (elemento) {
        linha.appendChild(elemento);
      });

      indice = proximoIndice;
    }
  }

  function obterLinhasCamposAdicionais_v5(container) {
    const linhasProcesso = Array.from(container.querySelectorAll(":scope > .process-additional-field-row"));
    if (linhasProcesso.length) {
      return linhasProcesso;
    }

    return Array.from(container.querySelectorAll(":scope > .additional-field-row-equalized"));
  }

  //###################################################################################
  // (6) IDENTIFICAR CABEÇALHO
  //###################################################################################

  function obterSelectTipoDaLinha_v5(linha) {
    if (!linha) {
      return null;
    }

    return (
      linha.querySelector("select[name='additional_field_type']") ||
      linha.querySelector("select[name='additional_field_type[]']") ||
      linha.querySelector(".additional-field-type-col select") ||
      Array.from(linha.querySelectorAll("select")).find(function (select) {
        const field = select.closest(".field");
        const label = field ? field.querySelector("label") : null;
        return normalizarTexto_v5(label ? label.textContent : "").includes("tipo do campo");
      }) ||
      null
    );
  }

  function linhaEhCabecalho_v5(linha) {
    const selectTipo = obterSelectTipoDaLinha_v5(linha);

    if (!selectTipo) {
      return false;
    }

    const option = selectTipo.options[selectTipo.selectedIndex];
    const valor = normalizarTexto_v5(selectTipo.value);
    const texto = normalizarTexto_v5(option ? option.textContent : "");

    return (
      valor === "header" ||
      valor.includes("header") ||
      valor.includes("cabecalho") ||
      texto.includes("cabecalho")
    );
  }

  //###################################################################################
  // (7) CSS DOS DOIS GRUPOS
  //###################################################################################

  function injetarCssGrupos_v5() {
    const styleId = "additional-fields-header-groups-style-v5";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      ".additional-fields-group-v5 {",
      "  grid-column: 1 / -1 !important;",
      "  width: 100% !important;",
      "  box-sizing: border-box !important;",
      "  margin: 18px 0 22px 0 !important;",
      "  padding: 0 !important;",
      "}",

      ".additional-fields-group-title-v5 {",
      "  display: flex !important;",
      "  align-items: center !important;",
      "  justify-content: space-between !important;",
      "  gap: 10px !important;",
      "  padding: 0 0 8px 0 !important;",
      "  border: 0 !important;",
      "  border-bottom: 1px solid #d8e0f1 !important;",
      "  border-radius: 0 !important;",
      "  background: transparent !important;",
      "  color: #1f3660 !important;",
      "  font-size: 14px !important;",
      "  font-weight: 800 !important;",
      "}",

      ".additional-fields-group-badge-v5 {",
      "  display: inline-flex !important;",
      "  align-items: center !important;",
      "  justify-content: center !important;",
      "  min-height: auto !important;",
      "  padding: 0 !important;",
      "  border: 0 !important;",
      "  border-radius: 0 !important;",
      "  background: transparent !important;",
      "  color: #61708f !important;",
      "  font-size: 11px !important;",
      "  font-weight: 700 !important;",
      "  text-transform: uppercase !important;",
      "  white-space: nowrap !important;",
      "}",

      ".additional-fields-group-body-v5 {",
      "  display: flex !important;",
      "  flex-direction: column !important;",
      "  gap: 0 !important;",
      "  padding: 8px 0 0 0 !important;",
      "  width: 100% !important;",
      "  border-top: 0 !important;",
      "}",

      ".additional-fields-group-column-head-v5 {",
      "  display: grid !important;",
      "  grid-template-columns: minmax(260px, 1.2fr) minmax(180px, 0.8fr) minmax(140px, 0.5fr) minmax(140px, 0.4fr) minmax(180px, 0.8fr) auto auto !important;",
      "  gap: 8px !important;",
      "  align-items: end !important;",
      "  padding: 0 0 8px 0 !important;",
      "  border-bottom: 1px solid #d8e0f1 !important;",
      "  margin-bottom: 4px !important;",
      "}",

      ".additional-fields-group-column-head-item-v5 {",
      "  color: #52627f !important;",
      "  font-size: 11px !important;",
      "  font-weight: 800 !important;",
      "  line-height: 1.2 !important;",
      "  text-transform: uppercase !important;",
      "}",

      ".additional-fields-group-v5 .additional-field-row-equalized {",
      "  display: grid !important;",
      "  grid-template-columns: minmax(220px, 1.6fr) minmax(180px, 1.1fr) minmax(120px, 0.8fr) minmax(120px, 0.7fr) minmax(220px, 1.3fr) auto auto auto !important;",
      "  gap: 8px !important;",
      "  align-items: end !important;",
      "  width: 100% !important;",
      "  box-sizing: border-box !important;",
      "  margin: 0 !important;",
      "}",

      ".additional-fields-group-v5 .process-additional-field-row {",
      "  margin: 0 !important;",
      "  padding: 8px 0 !important;",
      "  border: 0 !important;",
      "  border-bottom: 1px solid #e3e8f5 !important;",
      "  border-radius: 0 !important;",
      "  background: transparent !important;",
      "  box-shadow: none !important;",
      "}",

      ".additional-fields-group-v5 .process-additional-field-row .field label {",
      "  display: none !important;",
      "}",

      ".additional-fields-group-v5 .process-additional-field-row .field-move-buttons {",
      "  justify-content: flex-end !important;",
      "}",

      ".additional-fields-group-headers-v5 {",
      "  padding-bottom: 14px !important;",
      "  border-bottom: 1px solid #d7e1f5 !important;",
      "}",

      ".additional-fields-group-headers-v5 .additional-field-row-equalized,",
      ".additional-fields-group-headers-v5 .process-additional-field-row {",
      "  padding: 8px 0 !important;",
      "  border: 0 !important;",
      "  border-bottom: 1px solid #e3e8f5 !important;",
      "  border-radius: 0 !important;",
      "  background: transparent !important;",
      "}",

      ".additional-fields-group-fields-v5 {",
      "  margin-top: 18px !important;",
      "}",

      ".additional-fields-group-fields-v5 .additional-field-row-equalized,",
      ".additional-fields-group-fields-v5 .process-additional-field-row {",
      "  padding: 8px 0 !important;",
      "  border-left: 0 !important;",
      "}",

      ".additional-fields-group-v5 .process-additional-field-row:last-child {",
      "  border-bottom: 1px solid #d8e0f1 !important;",
      "}",

      ".additional-fields-group-v5 .process-additional-field-row input,",
      ".additional-fields-group-v5 .process-additional-field-row select {",
      "  background: #ffffff !important;",
      "  border-color: #cfd9ee !important;",
      "  box-shadow: none !important;",
      "  border-radius: 6px !important;",
      "  min-height: 34px !important;",
      "}",

      ".additional-fields-group-v5 .process-additional-field-row .table-icon-btn {",
      "  width: 30px !important;",
      "  height: 30px !important;",
      "  min-width: 30px !important;",
      "  min-height: 30px !important;",
      "}",

      ".additional-fields-group-headers-v5 input,",
      ".additional-fields-group-headers-v5 label,",
      ".additional-fields-group-headers-v5 .process-additional-field-row input,",
      ".additional-fields-group-headers-v5 .process-additional-field-row label {",
      "  font-weight: 800 !important;",
      "}",

      ".additional-fields-group-v3,",
      ".additional-fields-group-v4,",
      ".additional-fields-subgroup-marker-v2,",
      ".additional-field-row-is-header-v1::before {",
      "  display: none !important;",
      "  content: none !important;",
      "}",

      "@media (max-width: 1100px) {",
      "  .additional-fields-group-column-head-v5 {",
      "    display: none !important;",
      "  }",
      "  .additional-fields-group-v5 .additional-field-row-equalized {",
      "    grid-template-columns: 1fr !important;",
      "  }",
      "}"
    ].join("\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (8) CRIAR GRUPO
  //###################################################################################

  function criarGrupo_v5(classeExtra, titulo, totalTexto) {
    const grupo = document.createElement("div");
    grupo.className = "additional-fields-group-v5 " + classeExtra;

    grupo.innerHTML = [
      '<div class="additional-fields-group-title-v5">',
      '  <span>' + titulo + '</span>',
      '  <span class="additional-fields-group-badge-v5">' + totalTexto + '</span>',
      '</div>',
      '<div class="additional-fields-group-body-v5"></div>'
    ].join("");

    return grupo;
  }

  function obterCorpoGrupo_v5(grupo) {
    return grupo.querySelector(".additional-fields-group-body-v5");
  }

  function criarLinhaCabecalhos_v5() {
    const linha = document.createElement("div");
    linha.className = "additional-fields-group-column-head-v5";

    [
      "Nome do campo adicional",
      "Tipo do campo",
      "Obrigatório",
      "Tamanho",
      "Lista",
      "",
      ""
    ].forEach(function (texto) {
      const item = document.createElement("div");
      item.className = "additional-fields-group-column-head-item-v5";
      item.textContent = texto;
      linha.appendChild(item);
    });

    return linha;
  }

  function atualizarEstadoSetasHierarquia_v5(container) {
    const botoesMover = Array.from(
      container.querySelectorAll(".process-additional-field-move-btn")
    );

    botoesMover.forEach(function (botao) {
      botao.disabled = true;
      botao.classList.add("table-icon-btn-disabled");
      botao.title = "Hierarquia indisponível nesta visualização agrupada";
      botao.setAttribute("aria-label", "Hierarquia indisponível nesta visualização agrupada");
    });
  }

  //###################################################################################
  // (9) APLICAR AGRUPAMENTO
  //###################################################################################

  function aplicarAgrupamento_v5() {
    if (aplicandoAgrupamento_v5) {
      return;
    }

    const formulario = obterFormularioCamposAdicionais_v5();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v5(formulario);

    if (!container) {
      return;
    }

    aplicandoAgrupamento_v5 = true;

    try {
      injetarCssGrupos_v5();
      desmontarGruposExistentes_v5(container);
      montarLinhasEqualizadasSeNecessario_v5(container);

      const linhas = obterLinhasCamposAdicionais_v5(container);

      if (!linhas.length) {
        return;
      }

      const linhasCabecalho = [];
      const linhasCampos = [];

      linhas.forEach(function (linha) {
        if (linhaEhCabecalho_v5(linha)) {
          linhasCabecalho.push(linha);
        } else {
          linhasCampos.push(linha);
        }
      });

      const primeiraLinha = linhas[0];

      const grupoCabecalhos = criarGrupo_v5(
        "additional-fields-group-headers-v5",
        "Grupo Cabeçalho da aba:",
        String(linhasCabecalho.length) + " cabeçalho(s)"
      );

      const grupoCampos = criarGrupo_v5(
        "additional-fields-group-fields-v5",
        "Grupo de campos:",
        String(linhasCampos.length) + " campo(s)"
      );

      container.insertBefore(grupoCabecalhos, primeiraLinha);
      container.insertBefore(grupoCampos, primeiraLinha);

      const corpoCabecalhos = obterCorpoGrupo_v5(grupoCabecalhos);
      const corpoCampos = obterCorpoGrupo_v5(grupoCampos);

      corpoCabecalhos.appendChild(criarLinhaCabecalhos_v5());
      corpoCampos.appendChild(criarLinhaCabecalhos_v5());

      linhasCabecalho.forEach(function (linha) {
        corpoCabecalhos.appendChild(linha);
      });

      linhasCampos.forEach(function (linha) {
        corpoCampos.appendChild(linha);
      });

      if (!linhasCabecalho.length) {
        grupoCabecalhos.style.display = "none";
      }

      if (!linhasCampos.length) {
        grupoCampos.style.display = "none";
      }

      atualizarEstadoSetasHierarquia_v5(container);
    } finally {
      aplicandoAgrupamento_v5 = false;
    }
  }

  //###################################################################################
  // (10) OBSERVAR ALTERAÇÕES
  //###################################################################################

  function observarAlteracoes_v5() {
    const formulario = obterFormularioCamposAdicionais_v5();

    if (!formulario || formulario.dataset.headerGroupsObserverV5 === "1") {
      return;
    }

    formulario.dataset.headerGroupsObserverV5 = "1";

    formulario.addEventListener("change", function () {
      window.setTimeout(aplicarAgrupamento_v5, 50);
    });
  }

  //###################################################################################
  // (11) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v5() {
    aplicarAgrupamento_v5();
    observarAlteracoes_v5();

    window.setTimeout(aplicarAgrupamento_v5, 100);
    window.setTimeout(aplicarAgrupamento_v5, 400);
    window.setTimeout(aplicarAgrupamento_v5, 1000);
    window.setTimeout(aplicarAgrupamento_v5, 1800);
    window.setTimeout(aplicarAgrupamento_v5, 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v5);
  } else {
    inicializar_v5();
  }
})();
