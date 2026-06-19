//###################################################################################
// APPVERBOBRAGA - AGRUPAR CAMPOS ADICIONAIS EM CABEÇALHOS E CAMPOS - V4
//###################################################################################

(function () {
  "use strict";

  let aplicandoAgrupamento_v4 = false;

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizarTexto_v4(valor) {
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

  function obterFormularioCamposAdicionais_v4() {
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

      const texto = normalizarTexto_v4(formulario.textContent);

      return (
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("obrigatorio")
      );
    }) || null;
  }

  function obterContainerCampos_v4(formulario) {
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

  function obterLabelDoElemento_v4(elemento) {
    const label = elemento ? elemento.querySelector("label") : null;
    return normalizarTexto_v4(label ? label.textContent : "");
  }

  function elementoEhCampoNome_v4(elemento) {
    const label = obterLabelDoElemento_v4(elemento);

    if (label.includes("nome do campo adicional")) {
      return true;
    }

    return Boolean(
      elemento &&
      elemento.querySelector &&
      (
        elemento.querySelector("input[name='additional_field_label']") ||
        elemento.querySelector("input[name='additional_field_label[]']")
      )
    );
  }

  function elementoEhBotaoAdicionar_v4(elemento) {
    if (!elemento) {
      return false;
    }

    const texto = normalizarTexto_v4(elemento.textContent);

    if (texto === "+") {
      return true;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector && elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    return normalizarTexto_v4(botao.textContent) === "+";
  }

  function elementoEhAreaAcoesFormulario_v4(elemento) {
    if (!elemento) {
      return false;
    }

    if (elemento.classList && elemento.classList.contains("form-action-row")) {
      return true;
    }

    if (elemento.classList && elemento.classList.contains("profile-edit-actions")) {
      return true;
    }

    if (elemento.querySelector && elemento.querySelector("button[type='submit']")) {
      return true;
    }

    return false;
  }

  function elementoEhBotaoRemover_v4(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector && elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    const texto = normalizarTexto_v4(botao.textContent);
    const titulo = normalizarTexto_v4(botao.getAttribute("title"));

    return (
      texto === "x" ||
      texto === "×" ||
      titulo.includes("remover") ||
      titulo.includes("excluir") ||
      botao.classList.contains("remove-field-btn") ||
      botao.classList.contains("btn-danger")
    );
  }

  //###################################################################################
  // (4) DESMONTAR GRUPOS EXISTENTES
  //###################################################################################

  function desmontarGruposExistentes_v4(container) {
    const grupos = Array.from(container.querySelectorAll(".additional-fields-group-v4"));

    grupos.forEach(function (grupo) {
      const linhas = Array.from(grupo.querySelectorAll(".additional-field-row-equalized"));

      linhas.forEach(function (linha) {
        container.insertBefore(linha, grupo);
      });

      grupo.remove();
    });
  }

  //###################################################################################
  // (5) MONTAR LINHAS QUANDO A TELA AINDA ESTÁ EM GRID SOLTO
  //###################################################################################

  function montarLinhasEqualizadasSeNecessario_v4(container) {
    if (container.querySelector(".additional-field-row-equalized")) {
      return;
    }

    const filhos = Array.from(container.children);
    let indice = 0;

    while (indice < filhos.length) {
      const elementoAtual = filhos[indice];

      if (!elementoAtual || !elementoEhCampoNome_v4(elementoAtual)) {
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

        if (elementoEhCampoNome_v4(proximoElemento)) {
          break;
        }

        if (elementoEhBotaoAdicionar_v4(proximoElemento) || elementoEhAreaAcoesFormulario_v4(proximoElemento)) {
          break;
        }

        elementosDaLinha.push(proximoElemento);
        proximoIndice += 1;

        if (elementoEhBotaoRemover_v4(proximoElemento)) {
          break;
        }
      }

      const linha = document.createElement("div");
      linha.className = "additional-field-row-equalized additional-field-row-generated-v4";
      linha.setAttribute("data-additional-field-row", "1");

      container.insertBefore(linha, elementoAtual);

      elementosDaLinha.forEach(function (elemento) {
        linha.appendChild(elemento);
      });

      indice = proximoIndice;
    }
  }

  //###################################################################################
  // (6) OBTER LINHAS
  //###################################################################################

  function obterLinhasCamposAdicionais_v4(container) {
    return Array.from(container.querySelectorAll(".additional-field-row-equalized"));
  }

  //###################################################################################
  // (7) IDENTIFICAR CABEÇALHO
  //###################################################################################

  function obterSelectTipoDaLinha_v4(linha) {
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
        return normalizarTexto_v4(label ? label.textContent : "").includes("tipo do campo");
      }) ||
      null
    );
  }

  function linhaEhCabecalho_v4(linha) {
    const selectTipo = obterSelectTipoDaLinha_v4(linha);

    if (!selectTipo) {
      return false;
    }

    const option = selectTipo.options[selectTipo.selectedIndex];
    const valor = normalizarTexto_v4(selectTipo.value);
    const texto = normalizarTexto_v4(option ? option.textContent : "");

    return (
      valor === "header" ||
      valor.includes("header") ||
      valor.includes("cabecalho") ||
      texto.includes("cabecalho")
    );
  }

  //###################################################################################
  // (8) CSS DOS GRUPOS
  //###################################################################################

  function injetarCssGrupos_v4() {
    const styleId = "additional-fields-header-groups-style-v4";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      ".additional-fields-group-v4 {",
      "  grid-column: 1 / -1 !important;",
      "  width: 100% !important;",
      "  margin: 16px 0 12px 0 !important;",
      "}",

      ".additional-fields-group-title-v4 {",
      "  display: flex !important;",
      "  align-items: center !important;",
      "  justify-content: space-between !important;",
      "  gap: 10px !important;",
      "  padding: 10px 12px !important;",
      "  border: 1px solid #b8c8ed !important;",
      "  border-left: 5px solid #244db3 !important;",
      "  border-radius: 10px !important;",
      "  background: #eef4ff !important;",
      "  color: #0f1f3d !important;",
      "  font-size: 13px !important;",
      "  font-weight: 800 !important;",
      "}",

      ".additional-fields-group-badge-v4 {",
      "  display: inline-flex !important;",
      "  align-items: center !important;",
      "  justify-content: center !important;",
      "  min-height: 20px !important;",
      "  padding: 2px 8px !important;",
      "  border: 1px solid #b8c8ed !important;",
      "  border-radius: 999px !important;",
      "  background: #ffffff !important;",
      "  color: #244db3 !important;",
      "  font-size: 10px !important;",
      "  font-weight: 800 !important;",
      "  text-transform: uppercase !important;",
      "  white-space: nowrap !important;",
      "}",

      ".additional-fields-group-body-v4 {",
      "  display: flex !important;",
      "  flex-direction: column !important;",
      "  gap: 8px !important;",
      "  padding: 10px 0 0 0 !important;",
      "}",

      ".additional-fields-group-body-v4 > .additional-field-row-equalized {",
      "  width: 100% !important;",
      "  margin-bottom: 0 !important;",
      "}",

      ".additional-fields-group-headers-v4 .additional-field-row-equalized {",
      "  padding: 8px !important;",
      "  border: 1px solid #d7e1f5 !important;",
      "  border-radius: 10px !important;",
      "  background: #f8fbff !important;",
      "}",

      ".additional-fields-group-fields-v4 {",
      "  margin-top: 20px !important;",
      "  padding-top: 20px !important;",
      "  border-top: 2px solid #d7e1f5 !important;",
      "}",

      ".additional-fields-group-fields-v4 .additional-field-row-equalized {",
      "  padding-left: 10px !important;",
      "  border-left: 4px solid #edf3ff !important;",
      "}",

      ".additional-fields-group-headers-v4 input,",
      ".additional-fields-group-headers-v4 label {",
      "  font-weight: 800 !important;",
      "}",

      ".additional-fields-group-fields-v4 input,",
      ".additional-fields-group-fields-v4 select {",
      "  background-color: #ffffff !important;",
      "}",

      ".additional-fields-group-v3,",
      ".additional-fields-subgroup-marker-v2,",
      ".additional-field-row-is-header-v1::before {",
      "  display: none !important;",
      "  content: none !important;",
      "}",

      "@media (max-width: 900px) {",
      "  .additional-fields-group-title-v4 {",
      "    align-items: flex-start !important;",
      "    flex-direction: column !important;",
      "  }",
      "}"
    ].join("\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (9) CRIAR GRUPO
  //###################################################################################

  function criarGrupo_v4(classeExtra, titulo, badge) {
    const grupo = document.createElement("div");
    grupo.className = "additional-fields-group-v4 " + classeExtra;

    grupo.innerHTML = [
      '<div class="additional-fields-group-title-v4">',
      '  <span>' + titulo + '</span>',
      '  <span class="additional-fields-group-badge-v4">' + badge + '</span>',
      '</div>',
      '<div class="additional-fields-group-body-v4"></div>'
    ].join("");

    return grupo;
  }

  function obterCorpoGrupo_v4(grupo) {
    return grupo.querySelector(".additional-fields-group-body-v4");
  }

  //###################################################################################
  // (10) APLICAR AGRUPAMENTO
  //###################################################################################

  function aplicarAgrupamento_v4() {
    if (aplicandoAgrupamento_v4) {
      return;
    }

    const formulario = obterFormularioCamposAdicionais_v4();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v4(formulario);

    if (!container) {
      return;
    }

    aplicandoAgrupamento_v4 = true;

    try {
      injetarCssGrupos_v4();
      desmontarGruposExistentes_v4(container);
      montarLinhasEqualizadasSeNecessario_v4(container);

      const linhas = obterLinhasCamposAdicionais_v4(container);

      if (!linhas.length) {
        return;
      }

      const linhasCabecalho = [];
      const linhasCampos = [];

      linhas.forEach(function (linha) {
        if (linhaEhCabecalho_v4(linha)) {
          linhasCabecalho.push(linha);
        } else {
          linhasCampos.push(linha);
        }
      });

      const primeiraLinha = linhas[0];

      const grupoCabecalhos = criarGrupo_v4(
        "additional-fields-group-headers-v4",
        "Grupo Cabeçalho da aba:",
        String(linhasCabecalho.length) + " cabeçalho(s)"
      );

      const grupoCampos = criarGrupo_v4(
        "additional-fields-group-fields-v4",
        "Grupo de campos:",
        String(linhasCampos.length) + " campo(s)"
      );

      container.insertBefore(grupoCabecalhos, primeiraLinha);
      container.insertBefore(grupoCampos, primeiraLinha);

      const corpoCabecalhos = obterCorpoGrupo_v4(grupoCabecalhos);
      const corpoCampos = obterCorpoGrupo_v4(grupoCampos);

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
    } finally {
      aplicandoAgrupamento_v4 = false;
    }
  }

  //###################################################################################
  // (11) OBSERVAR ALTERAÇÕES
  //###################################################################################

  function observarAlteracoes_v4() {
    const formulario = obterFormularioCamposAdicionais_v4();

    if (!formulario || formulario.dataset.headerGroupsObserverV4 === "1") {
      return;
    }

    formulario.dataset.headerGroupsObserverV4 = "1";

    const observer = new MutationObserver(function () {
      if (aplicandoAgrupamento_v4) {
        return;
      }

      window.requestAnimationFrame(aplicarAgrupamento_v4);
    });

    observer.observe(formulario, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["value", "class"]
    });

    formulario.addEventListener("change", aplicarAgrupamento_v4);
    formulario.addEventListener("input", aplicarAgrupamento_v4);
  }

  //###################################################################################
  // (12) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v4() {
    aplicarAgrupamento_v4();
    observarAlteracoes_v4();

    window.setTimeout(aplicarAgrupamento_v4, 100);
    window.setTimeout(aplicarAgrupamento_v4, 400);
    window.setTimeout(aplicarAgrupamento_v4, 1000);
    window.setTimeout(aplicarAgrupamento_v4, 1800);
    window.setTimeout(aplicarAgrupamento_v4, 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v4);
  } else {
    inicializar_v4();
  }
})();
