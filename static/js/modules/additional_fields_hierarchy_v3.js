//###################################################################################
// (1) CAMPOS ADICIONAIS - HIERARQUIA GLOBAL POR SETAS - V5
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) NORMALIZAÇÃO E LOCALIZAÇÃO DO FORMULÁRIO
  //###################################################################################

  function normalizarTexto_v5(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function obterFormularioCamposAdicionais_v5() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      const action = String(formulario.getAttribute("action") || "").trim();

      if (action.includes("/settings/menu/process-additional-fields")) {
        return true;
      }

      const texto = normalizarTexto_v5(formulario.textContent);

      return (
        texto.includes("campos adicionais") &&
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("tamanho")
      );
    }) || null;
  }

  function obterContainerCampos_v5(formulario) {
    return (
      formulario.querySelector(".additional-fields-grid") ||
      formulario.querySelector(".form-grid") ||
      formulario.querySelector(".personal-grid") ||
      formulario
    );
  }

  function obterTextoLabel_v5(elemento) {
    const label = elemento ? elemento.querySelector("label") : null;
    return normalizarTexto_v5(label ? label.textContent : "");
  }

  //###################################################################################
  // (3) IDENTIFICAÇÃO DAS COLUNAS
  //###################################################################################

  function ehCampoNome_v5(elemento) {
    return obterTextoLabel_v5(elemento).includes("nome do campo adicional");
  }

  function ehCampoTipo_v5(elemento) {
    return obterTextoLabel_v5(elemento).includes("tipo do campo");
  }

  function ehCampoObrigatorio_v5(elemento) {
    return obterTextoLabel_v5(elemento).includes("obrigatorio");
  }

  function ehCampoTamanho_v5(elemento) {
    return obterTextoLabel_v5(elemento).includes("tamanho");
  }

  function obterBotao_v5(elemento) {
    if (!elemento) {
      return null;
    }

    if (elemento.matches && elemento.matches("button")) {
      return elemento;
    }

    return elemento.querySelector("button");
  }

  function ehBotaoRemover_v5(elemento) {
    const botao = obterBotao_v5(elemento);

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

  function ehFormularioMovimentoAntigo_v5(elemento) {
    if (!elemento || !elemento.matches) {
      return false;
    }

    if (!elemento.matches('form[action*="/settings/menu/field-move"]')) {
      return false;
    }

    return true;
  }

  //###################################################################################
  // (4) TIPO DO CAMPO E CABEÇALHO
  //###################################################################################

  function obterCampoTipoDaLinha_v5(linha) {
    const colunaTipo = linha.querySelector(".additional-field-type-col");

    if (colunaTipo) {
      return colunaTipo.querySelector("select");
    }

    const selects = Array.from(linha.querySelectorAll("select"));

    return selects.find(function (select) {
      const field = select.closest(".field");
      return obterTextoLabel_v5(field).includes("tipo do campo");
    }) || null;
  }

  function ehLinhaCabecalho_v5(linha) {
    const selectTipo = obterCampoTipoDaLinha_v5(linha);

    if (!selectTipo) {
      return false;
    }

    const opcaoSelecionada = selectTipo.options[selectTipo.selectedIndex];
    const textoSelecionado = normalizarTexto_v5(opcaoSelecionada ? opcaoSelecionada.textContent : "");
    const valorSelecionado = normalizarTexto_v5(selectTipo.value);

    return (
      textoSelecionado.includes("cabecalho") ||
      valorSelecionado.includes("cabecalho") ||
      valorSelecionado.includes("header")
    );
  }

  //###################################################################################
  // (5) CSS DEFINITIVO DAS SETAS
  //###################################################################################

  function injetarCssHierarquia_v5() {
    const styleId = "additional-fields-hierarchy-style-v5";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      'form[action*="/settings/menu/field-move"] {',
      '  display: none !important;',
      '}',

      ".additional-field-row-equalized {",
      "  display: grid !important;",
      "  grid-template-columns: minmax(190px, 1.4fr) minmax(140px, 1fr) minmax(110px, 0.8fr) minmax(90px, 0.7fr) auto auto !important;",
      "  align-items: end !important;",
      "  gap: 6px !important;",
      "  margin-bottom: 10px !important;",
      "}",

      ".additional-field-hierarchy-col {",
      "  display: inline-flex !important;",
      "  align-items: end !important;",
      "  justify-content: flex-start !important;",
      "  width: auto !important;",
      "  min-width: 62px !important;",
      "  margin: 0 !important;",
      "  padding: 0 !important;",
      "}",

      ".header-hierarchy-controls {",
      "  display: inline-flex !important;",
      "  align-items: center !important;",
      "  justify-content: flex-start !important;",
      "  margin: 0 !important;",
      "  padding: 0 !important;",
      "  width: auto !important;",
      "}",

      ".header-hierarchy-label {",
      "  display: none !important;",
      "}",

      ".header-hierarchy-buttons {",
      "  display: inline-flex !important;",
      "  flex-direction: row !important;",
      "  align-items: center !important;",
      "  justify-content: flex-start !important;",
      "  flex-wrap: nowrap !important;",
      "  gap: 4px !important;",
      "  margin: 0 !important;",
      "  padding: 0 !important;",
      "  width: auto !important;",
      "}",

      ".header-hierarchy-btn {",
      "  width: 28px !important;",
      "  height: 28px !important;",
      "  min-width: 28px !important;",
      "  min-height: 28px !important;",
      "  max-width: 28px !important;",
      "  max-height: 28px !important;",
      "  display: inline-flex !important;",
      "  align-items: center !important;",
      "  justify-content: center !important;",
      "  margin: 0 !important;",
      "  padding: 0 !important;",
      "  border: 1px solid #b8c8ed !important;",
      "  border-radius: 7px !important;",
      "  background: #eef4ff !important;",
      "  color: #1f4f9d !important;",
      "  font-size: 14px !important;",
      "  font-weight: 700 !important;",
      "  line-height: 1 !important;",
      "  cursor: pointer !important;",
      "}",

      ".header-hierarchy-btn:hover:not(:disabled) {",
      "  background: #dfeaff !important;",
      "  border-color: #8ea9e0 !important;",
      "}",

      ".header-hierarchy-btn:disabled {",
      "  opacity: 0.45 !important;",
      "  cursor: not-allowed !important;",
      "}",

      ".additional-field-action-col {",
      "  display: inline-flex !important;",
      "  align-items: end !important;",
      "  justify-content: flex-start !important;",
      "  margin: 0 !important;",
      "  padding: 0 !important;",
      "}",

      ".additional-field-action-col button,",
      ".remove-field-btn {",
      "  width: 28px !important;",
      "  height: 28px !important;",
      "  min-width: 28px !important;",
      "  min-height: 28px !important;",
      "  display: inline-flex !important;",
      "  align-items: center !important;",
      "  justify-content: center !important;",
      "  margin: 0 !important;",
      "  padding: 0 !important;",
      "}"
    ].join("\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (6) MONTAGEM DAS LINHAS
  //###################################################################################

  function montarLinhasEqualizadas_v5() {
    const formulario = obterFormularioCamposAdicionais_v5();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v5(formulario);

    if (container.querySelector(".additional-field-row-equalized")) {
      return;
    }

    const filhos = Array.from(container.children);
    let indice = 0;

    while (indice < filhos.length) {
      const elementoAtual = filhos[indice];

      if (!elementoAtual || !ehCampoNome_v5(elementoAtual)) {
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

        if (ehCampoNome_v5(proximoElemento)) {
          break;
        }

        elementosDaLinha.push(proximoElemento);
        proximoIndice += 1;

        if (ehBotaoRemover_v5(proximoElemento)) {
          break;
        }
      }

      const linha = document.createElement("div");
      linha.className = "additional-field-row-equalized";
      linha.setAttribute("data-additional-field-row", "1");

      container.insertBefore(linha, elementoAtual);

      elementosDaLinha.forEach(function (elemento) {
        linha.appendChild(elemento);
      });

      indice = proximoIndice;
    }
  }

  //###################################################################################
  // (7) CLASSIFICAÇÃO DAS COLUNAS
  //###################################################################################

  function classificarColunas_v5() {
    const linhas = Array.from(document.querySelectorAll(".additional-field-row-equalized"));

    linhas.forEach(function (linha) {
      Array.from(linha.children).forEach(function (coluna) {
        coluna.classList.remove(
          "additional-field-name-col",
          "additional-field-type-col",
          "additional-field-required-col",
          "additional-field-size-col",
          "additional-field-hierarchy-col",
          "additional-field-action-col"
        );

        if (ehFormularioMovimentoAntigo_v5(coluna)) {
          coluna.style.display = "none";
          return;
        }

        if (ehCampoNome_v5(coluna)) {
          coluna.classList.add("additional-field-name-col");
          return;
        }

        if (ehCampoTipo_v5(coluna)) {
          coluna.classList.add("additional-field-type-col");
          return;
        }

        if (ehCampoObrigatorio_v5(coluna)) {
          coluna.classList.add("additional-field-required-col");
          return;
        }

        if (ehCampoTamanho_v5(coluna)) {
          coluna.classList.add("additional-field-size-col");
          return;
        }

        if (ehBotaoRemover_v5(coluna)) {
          coluna.classList.add("additional-field-action-col");
        }
      });
    });
  }

  //###################################################################################
  // (8) COLUNA NOVA DAS SETAS
  //###################################################################################

  function obterOuCriarColunaHierarquia_v5(linha) {
    let colunaHierarquia = linha.querySelector(".additional-field-hierarchy-col");

    if (colunaHierarquia) {
      return colunaHierarquia;
    }

    colunaHierarquia = document.createElement("div");
    colunaHierarquia.className = "additional-field-hierarchy-col";

    const colunaAcao = linha.querySelector(".additional-field-action-col");
    const colunaTamanho = linha.querySelector(".additional-field-size-col");

    if (colunaAcao) {
      linha.insertBefore(colunaHierarquia, colunaAcao);
      return colunaHierarquia;
    }

    if (colunaTamanho && colunaTamanho.nextSibling) {
      linha.insertBefore(colunaHierarquia, colunaTamanho.nextSibling);
      return colunaHierarquia;
    }

    linha.appendChild(colunaHierarquia);
    return colunaHierarquia;
  }

  //###################################################################################
  // (9) BLOCOS DE CABEÇALHO
  //###################################################################################

  function obterBlocoDaLinha_v5(linha) {
    if (!ehLinhaCabecalho_v5(linha)) {
      return [linha];
    }

    const bloco = [linha];
    let proxima = linha.nextElementSibling;

    while (proxima && proxima.classList.contains("additional-field-row-equalized")) {
      if (ehLinhaCabecalho_v5(proxima)) {
        break;
      }

      bloco.push(proxima);
      proxima = proxima.nextElementSibling;
    }

    return bloco;
  }

  function obterPrimeiraLinhaDoBlocoAnterior_v5(linha) {
    let anterior = linha.previousElementSibling;

    if (!anterior || !anterior.classList.contains("additional-field-row-equalized")) {
      return null;
    }

    if (!ehLinhaCabecalho_v5(linha)) {
      return anterior;
    }

    while (
      anterior.previousElementSibling &&
      anterior.previousElementSibling.classList.contains("additional-field-row-equalized")
    ) {
      const candidato = anterior.previousElementSibling;

      if (ehLinhaCabecalho_v5(candidato)) {
        anterior = candidato;
        break;
      }

      anterior = candidato;
    }

    return anterior;
  }

  function obterUltimaLinhaDoProximoBloco_v5(linha) {
    const blocoAtual = obterBlocoDaLinha_v5(linha);
    const ultimaAtual = blocoAtual[blocoAtual.length - 1];
    const primeiraProxima = ultimaAtual.nextElementSibling;

    if (!primeiraProxima || !primeiraProxima.classList.contains("additional-field-row-equalized")) {
      return null;
    }

    if (!ehLinhaCabecalho_v5(linha)) {
      return primeiraProxima;
    }

    const blocoProximo = obterBlocoDaLinha_v5(primeiraProxima);
    return blocoProximo[blocoProximo.length - 1] || primeiraProxima;
  }

  //###################################################################################
  // (10) MOVIMENTO DAS LINHAS
  //###################################################################################

  function moverLinhaParaCima_v5(linha) {
    if (!linha) {
      return;
    }

    const container = linha.parentNode;
    const bloco = obterBlocoDaLinha_v5(linha);
    const primeiraAnterior = obterPrimeiraLinhaDoBlocoAnterior_v5(linha);

    if (!primeiraAnterior) {
      return;
    }

    bloco.forEach(function (item) {
      container.insertBefore(item, primeiraAnterior);
    });

    atualizarHierarquia_v5();
  }

  function moverLinhaParaBaixo_v5(linha) {
    if (!linha) {
      return;
    }

    const container = linha.parentNode;
    const bloco = obterBlocoDaLinha_v5(linha);
    const ultimaProxima = obterUltimaLinhaDoProximoBloco_v5(linha);

    if (!ultimaProxima) {
      return;
    }

    const referencia = ultimaProxima.nextSibling;

    bloco.forEach(function (item) {
      container.insertBefore(item, referencia);
    });

    atualizarHierarquia_v5();
  }

  //###################################################################################
  // (11) CRIAÇÃO DOS BOTÕES HORIZONTAIS
  //###################################################################################

  function criarControlesNaLinha_v5(linha, indice, total) {
    const colunaHierarquia = obterOuCriarColunaHierarquia_v5(linha);

    colunaHierarquia.innerHTML = "";

    const controles = document.createElement("div");
    controles.className = "header-hierarchy-controls";

    controles.innerHTML = [
      '<span class="header-hierarchy-label">Hierarquia</span>',
      '<div class="header-hierarchy-buttons">',
      '  <button type="button" class="header-hierarchy-btn" data-header-move="up" title="Subir">↑</button>',
      '  <button type="button" class="header-hierarchy-btn" data-header-move="down" title="Descer">↓</button>',
      '</div>'
    ].join("");

    const subir = controles.querySelector('[data-header-move="up"]');
    const descer = controles.querySelector('[data-header-move="down"]');

    if (subir) {
      subir.disabled = indice === 0;
    }

    if (descer) {
      descer.disabled = indice === total - 1;
    }

    controles.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-header-move]");

      if (!botao) {
        return;
      }

      event.preventDefault();

      const direcao = botao.getAttribute("data-header-move");

      if (direcao === "up") {
        moverLinhaParaCima_v5(linha);
      }

      if (direcao === "down") {
        moverLinhaParaBaixo_v5(linha);
      }
    });

    colunaHierarquia.appendChild(controles);
  }

  //###################################################################################
  // (12) ATUALIZAÇÃO GERAL
  //###################################################################################

  function atualizarHierarquia_v5() {
    const formulario = obterFormularioCamposAdicionais_v5();

    if (!formulario) {
      return;
    }

    injetarCssHierarquia_v5();
    montarLinhasEqualizadas_v5();
    classificarColunas_v5();

    const linhas = Array.from(formulario.querySelectorAll(".additional-field-row-equalized"));

    linhas.forEach(function (linha, indice) {
      criarControlesNaLinha_v5(linha, indice, linhas.length);

      const selectTipo = obterCampoTipoDaLinha_v5(linha);

      if (selectTipo && selectTipo.dataset.hierarchyBoundV5 !== "1") {
        selectTipo.dataset.hierarchyBoundV5 = "1";
        selectTipo.addEventListener("change", atualizarHierarquia_v5);
      }
    });
  }

  //###################################################################################
  // (13) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v5() {
    injetarCssHierarquia_v5();
    atualizarHierarquia_v5();

    window.setTimeout(atualizarHierarquia_v5, 100);
    window.setTimeout(atualizarHierarquia_v5, 400);
    window.setTimeout(atualizarHierarquia_v5, 1000);
    window.setTimeout(atualizarHierarquia_v5, 1800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v5);
  } else {
    inicializar_v5();
  }
})();
