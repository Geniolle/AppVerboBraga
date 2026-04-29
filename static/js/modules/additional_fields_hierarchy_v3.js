//###################################################################################
// (1) CAMPOS ADICIONAIS - HIERARQUIA GLOBAL POR SETAS - V3
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) FUNÇÕES AUXILIARES
  //###################################################################################

  function normalizarTexto_v3(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function obterFormularioCamposAdicionais_v3() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      const action = String(formulario.getAttribute("action") || "").trim();

      if (action.includes("/settings/menu/process-additional-fields")) {
        return true;
      }

      const texto = normalizarTexto_v3(formulario.textContent);

      return (
        texto.includes("campos adicionais") &&
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("tamanho")
      );
    }) || null;
  }

  function obterTextoLabel_v3(elemento) {
    const label = elemento ? elemento.querySelector("label") : null;
    return normalizarTexto_v3(label ? label.textContent : "");
  }

  function ehCampoNome_v3(elemento) {
    return obterTextoLabel_v3(elemento).includes("nome do campo adicional");
  }

  function ehCampoTipo_v3(elemento) {
    return obterTextoLabel_v3(elemento).includes("tipo do campo");
  }

  function ehCampoObrigatorio_v3(elemento) {
    return obterTextoLabel_v3(elemento).includes("obrigatorio");
  }

  function ehCampoTamanho_v3(elemento) {
    return obterTextoLabel_v3(elemento).includes("tamanho");
  }

  function ehBotaoRemover_v3(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    const texto = normalizarTexto_v3(botao.textContent);
    const titulo = normalizarTexto_v3(botao.getAttribute("title"));

    return (
      texto === "x" ||
      texto === "×" ||
      titulo.includes("remover") ||
      titulo.includes("excluir") ||
      botao.classList.contains("btn-danger")
    );
  }

  function obterContainerCampos_v3(formulario) {
    return (
      formulario.querySelector(".additional-fields-grid") ||
      formulario.querySelector(".form-grid") ||
      formulario.querySelector(".personal-grid") ||
      formulario
    );
  }

  function obterCampoTipoDaLinha_v3(linha) {
    const colunaTipo = linha.querySelector(".additional-field-type-col");

    if (colunaTipo) {
      return colunaTipo.querySelector("select");
    }

    const selects = Array.from(linha.querySelectorAll("select"));

    return selects.find(function (select) {
      const field = select.closest(".field");
      return obterTextoLabel_v3(field).includes("tipo do campo");
    }) || null;
  }

  function ehLinhaCabecalho_v3(linha) {
    const selectTipo = obterCampoTipoDaLinha_v3(linha);

    if (!selectTipo) {
      return false;
    }

    const opcaoSelecionada = selectTipo.options[selectTipo.selectedIndex];
    const textoSelecionado = normalizarTexto_v3(opcaoSelecionada ? opcaoSelecionada.textContent : "");
    const valorSelecionado = normalizarTexto_v3(selectTipo.value);

    return (
      textoSelecionado.includes("cabecalho") ||
      valorSelecionado.includes("cabecalho") ||
      valorSelecionado.includes("header")
    );
  }

  function obterLinhas_v3(formulario) {
    return Array.from(formulario.querySelectorAll(".additional-field-row-equalized"));
  }

  //###################################################################################
  // (3) EQUALIZAR LINHAS PARA QUE A ORDEM DO DOM SEJA A ORDEM GRAVADA
  //###################################################################################

  function montarLinhasEqualizadas_v3() {
    const formulario = obterFormularioCamposAdicionais_v3();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v3(formulario);

    if (container.querySelector(".additional-field-row-equalized")) {
      return;
    }

    const filhos = Array.from(container.children);
    let indice = 0;

    while (indice < filhos.length) {
      const elementoAtual = filhos[indice];

      if (!elementoAtual || !ehCampoNome_v3(elementoAtual)) {
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

        if (ehCampoNome_v3(proximoElemento)) {
          break;
        }

        elementosDaLinha.push(proximoElemento);
        proximoIndice += 1;

        if (ehBotaoRemover_v3(proximoElemento)) {
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
  // (4) CLASSIFICAR COLUNAS
  //###################################################################################

  function classificarColunas_v3() {
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

        if (ehCampoNome_v3(coluna)) {
          coluna.classList.add("additional-field-name-col");
          return;
        }

        if (ehCampoTipo_v3(coluna)) {
          coluna.classList.add("additional-field-type-col");
          return;
        }

        if (ehCampoObrigatorio_v3(coluna)) {
          coluna.classList.add("additional-field-required-col");
          return;
        }

        if (ehCampoTamanho_v3(coluna)) {
          coluna.classList.add("additional-field-size-col");
          return;
        }

        if (ehBotaoRemover_v3(coluna)) {
          coluna.classList.add("additional-field-action-col");
        }
      });
    });
  }

  //###################################################################################
  // (5) COLUNA DAS SETAS
  //###################################################################################

  function obterOuCriarColunaHierarquia_v3(linha) {
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
  // (6) BLOCOS DE HIERARQUIA
  //###################################################################################

  function obterBlocoDaLinha_v3(linha) {
    if (!ehLinhaCabecalho_v3(linha)) {
      return [linha];
    }

    const bloco = [linha];
    let proxima = linha.nextElementSibling;

    while (proxima && proxima.classList.contains("additional-field-row-equalized")) {
      if (ehLinhaCabecalho_v3(proxima)) {
        break;
      }

      bloco.push(proxima);
      proxima = proxima.nextElementSibling;
    }

    return bloco;
  }

  function obterPrimeiraLinhaDoBlocoAnterior_v3(linha) {
    let anterior = linha.previousElementSibling;

    if (!anterior || !anterior.classList.contains("additional-field-row-equalized")) {
      return null;
    }

    if (!ehLinhaCabecalho_v3(linha)) {
      return anterior;
    }

    while (
      anterior.previousElementSibling &&
      anterior.previousElementSibling.classList.contains("additional-field-row-equalized")
    ) {
      const candidato = anterior.previousElementSibling;

      if (ehLinhaCabecalho_v3(candidato)) {
        anterior = candidato;
        break;
      }

      anterior = candidato;
    }

    return anterior;
  }

  function obterUltimaLinhaDoProximoBloco_v3(linha) {
    const blocoAtual = obterBlocoDaLinha_v3(linha);
    const ultimaAtual = blocoAtual[blocoAtual.length - 1];
    const primeiraProxima = ultimaAtual.nextElementSibling;

    if (!primeiraProxima || !primeiraProxima.classList.contains("additional-field-row-equalized")) {
      return null;
    }

    if (!ehLinhaCabecalho_v3(linha)) {
      return primeiraProxima;
    }

    const blocoProximo = obterBlocoDaLinha_v3(primeiraProxima);
    return blocoProximo[blocoProximo.length - 1] || primeiraProxima;
  }

  //###################################################################################
  // (7) MOVER LINHAS OU BLOCOS
  //###################################################################################

  function moverLinhaParaCima_v3(linha) {
    const formulario = obterFormularioCamposAdicionais_v3();

    if (!formulario || !linha) {
      return;
    }

    const container = linha.parentNode;
    const bloco = obterBlocoDaLinha_v3(linha);
    const primeiraAnterior = obterPrimeiraLinhaDoBlocoAnterior_v3(linha);

    if (!primeiraAnterior) {
      return;
    }

    bloco.forEach(function (item) {
      container.insertBefore(item, primeiraAnterior);
    });

    atualizarHierarquia_v3();
  }

  function moverLinhaParaBaixo_v3(linha) {
    const formulario = obterFormularioCamposAdicionais_v3();

    if (!formulario || !linha) {
      return;
    }

    const container = linha.parentNode;
    const bloco = obterBlocoDaLinha_v3(linha);
    const ultimaProxima = obterUltimaLinhaDoProximoBloco_v3(linha);

    if (!ultimaProxima) {
      return;
    }

    const referencia = ultimaProxima.nextSibling;

    bloco.forEach(function (item) {
      container.insertBefore(item, referencia);
    });

    atualizarHierarquia_v3();
  }

  //###################################################################################
  // (8) CRIAR CONTROLES DE SETAS
  //###################################################################################

  function criarControlesNaLinha_v3(linha, indice, total) {
    const colunaHierarquia = obterOuCriarColunaHierarquia_v3(linha);

    colunaHierarquia.classList.remove("is-empty");
    colunaHierarquia.innerHTML = "";

    const isCabecalho = ehLinhaCabecalho_v3(linha);
    const label = isCabecalho ? "Hierarquia" : "Ordem";

    const controles = document.createElement("div");
    controles.className = "header-hierarchy-controls";
    controles.innerHTML = [
      '<span class="header-hierarchy-label">' + label + '</span>',
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
        moverLinhaParaCima_v3(linha);
      }

      if (direcao === "down") {
        moverLinhaParaBaixo_v3(linha);
      }
    });

    colunaHierarquia.appendChild(controles);
  }

  //###################################################################################
  // (9) ATUALIZAR HIERARQUIA
  //###################################################################################

  function atualizarHierarquia_v3() {
    const formulario = obterFormularioCamposAdicionais_v3();

    if (!formulario) {
      return;
    }

    montarLinhasEqualizadas_v3();
    classificarColunas_v3();

    const linhas = obterLinhas_v3(formulario);

    linhas.forEach(function (linha, indice) {
      criarControlesNaLinha_v3(linha, indice, linhas.length);

      const selectTipo = obterCampoTipoDaLinha_v3(linha);

      if (selectTipo && selectTipo.dataset.hierarchyBoundV3 !== "1") {
        selectTipo.dataset.hierarchyBoundV3 = "1";
        selectTipo.addEventListener("change", atualizarHierarquia_v3);
      }
    });
  }

  //###################################################################################
  // (10) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v3() {
    atualizarHierarquia_v3();

    window.setTimeout(atualizarHierarquia_v3, 100);
    window.setTimeout(atualizarHierarquia_v3, 400);
    window.setTimeout(atualizarHierarquia_v3, 1000);
    window.setTimeout(atualizarHierarquia_v3, 1800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v3);
  } else {
    inicializar_v3();
  }
})();
