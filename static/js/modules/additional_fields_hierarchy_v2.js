//###################################################################################
// (1) CAMPOS ADICIONAIS - LINHAS EQUALIZADAS + HIERARQUIA
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) FUNCOES AUXILIARES
  //###################################################################################

  function normalizarTexto_v2(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function obterFormularioCamposAdicionais_v2() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      const texto = normalizarTexto_v2(formulario.textContent);

      return (
        texto.includes("campos adicionais") &&
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("tamanho")
      );
    }) || null;
  }

  function obterTextoLabel_v2(elemento) {
    const label = elemento ? elemento.querySelector("label") : null;
    return normalizarTexto_v2(label ? label.textContent : "");
  }

  function ehCampoNome_v2(elemento) {
    return obterTextoLabel_v2(elemento).includes("nome do campo adicional");
  }

  function ehCampoTipo_v2(elemento) {
    return obterTextoLabel_v2(elemento).includes("tipo do campo");
  }

  function ehCampoObrigatorio_v2(elemento) {
    return obterTextoLabel_v2(elemento).includes("obrigatorio");
  }

  function ehCampoTamanho_v2(elemento) {
    return obterTextoLabel_v2(elemento).includes("tamanho");
  }

  function ehBotaoRemover_v2(elemento) {
    if (!elemento) {
      return false;
    }

    const botao = elemento.matches && elemento.matches("button")
      ? elemento
      : elemento.querySelector("button");

    if (!botao) {
      return false;
    }

    const texto = normalizarTexto_v2(botao.textContent);
    const titulo = normalizarTexto_v2(botao.getAttribute("title"));

    return (
      texto === "x" ||
      texto === "×" ||
      titulo.includes("remover") ||
      titulo.includes("excluir") ||
      botao.classList.contains("btn-danger")
    );
  }

  function isTipoCabecalho_v2(select) {
    if (!select) {
      return false;
    }

    const opcaoSelecionada = select.options[select.selectedIndex];
    const textoSelecionado = normalizarTexto_v2(opcaoSelecionada ? opcaoSelecionada.textContent : "");
    const valorSelecionado = normalizarTexto_v2(select.value);

    return (
      textoSelecionado.includes("cabecalho") ||
      valorSelecionado.includes("cabecalho") ||
      valorSelecionado.includes("header")
    );
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
  // (3) CRIAR LINHAS EQUALIZADAS
  //###################################################################################

  function montarLinhasEqualizadas_v2() {
    const formulario = obterFormularioCamposAdicionais_v2();

    if (!formulario) {
      return;
    }

    const container = obterContainerCampos_v2(formulario);

    if (container.querySelector(".additional-field-row-equalized")) {
      return;
    }

    const filhos = Array.from(container.children);
    let indice = 0;

    while (indice < filhos.length) {
      const elementoAtual = filhos[indice];

      if (!elementoAtual || !ehCampoNome_v2(elementoAtual)) {
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

        if (ehCampoNome_v2(proximoElemento)) {
          break;
        }

        elementosDaLinha.push(proximoElemento);
        proximoIndice += 1;

        if (ehBotaoRemover_v2(proximoElemento)) {
          break;
        }
      }

      const linha = document.createElement("div");
      linha.className = "additional-field-row-equalized";

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

  function classificarColunas_v2() {
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

        if (ehCampoNome_v2(coluna)) {
          coluna.classList.add("additional-field-name-col");
          return;
        }

        if (ehCampoTipo_v2(coluna)) {
          coluna.classList.add("additional-field-type-col");
          return;
        }

        if (ehCampoObrigatorio_v2(coluna)) {
          coluna.classList.add("additional-field-required-col");
          return;
        }

        if (ehCampoTamanho_v2(coluna)) {
          coluna.classList.add("additional-field-size-col");
          return;
        }

        if (ehBotaoRemover_v2(coluna)) {
          coluna.classList.add("additional-field-action-col");
        }
      });
    });
  }

  //###################################################################################
  // (5) LOCALIZAR CAMPOS DA LINHA
  //###################################################################################

  function obterCampoTipoDaLinha_v2(linha) {
    const colunaTipo = linha.querySelector(".additional-field-type-col");

    if (!colunaTipo) {
      return null;
    }

    return colunaTipo.querySelector("select");
  }

  function obterColunaTamanhoDaLinha_v2(linha) {
    return linha.querySelector(".additional-field-size-col");
  }

  function obterColunaAcaoDaLinha_v2(linha) {
    return linha.querySelector(".additional-field-action-col");
  }

  function obterOuCriarColunaHierarquia_v2(linha) {
    let colunaHierarquia = linha.querySelector(".additional-field-hierarchy-col");

    if (colunaHierarquia) {
      return colunaHierarquia;
    }

    colunaHierarquia = document.createElement("div");
    colunaHierarquia.className = "additional-field-hierarchy-col";

    const colunaAcao = obterColunaAcaoDaLinha_v2(linha);
    const colunaTamanho = obterColunaTamanhoDaLinha_v2(linha);

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
  // (6) MOVER LINHAS
  //###################################################################################

  function moverLinhaParaCima_v2(linha) {
    const linhaAnterior = linha.previousElementSibling;

    if (!linhaAnterior || !linhaAnterior.classList.contains("additional-field-row-equalized")) {
      return;
    }

    linha.parentNode.insertBefore(linha, linhaAnterior);
    atualizarHierarquia_v2();
  }

  function moverLinhaParaBaixo_v2(linha) {
    const proximaLinha = linha.nextElementSibling;

    if (!proximaLinha || !proximaLinha.classList.contains("additional-field-row-equalized")) {
      return;
    }

    if (proximaLinha.nextSibling) {
      linha.parentNode.insertBefore(linha, proximaLinha.nextSibling);
    } else {
      linha.parentNode.appendChild(linha);
    }

    atualizarHierarquia_v2();
  }

  //###################################################################################
  // (7) CRIAR HIERARQUIA
  //###################################################################################

  function criarHierarquiaNaLinha_v2(linha) {
    const selectTipo = obterCampoTipoDaLinha_v2(linha);
    const colunaHierarquia = obterOuCriarColunaHierarquia_v2(linha);

    colunaHierarquia.innerHTML = "";

    if (!isTipoCabecalho_v2(selectTipo)) {
      colunaHierarquia.classList.add("is-empty");
      return;
    }

    colunaHierarquia.classList.remove("is-empty");

    const controles = document.createElement("div");
    controles.className = "header-hierarchy-controls";
    controles.innerHTML = [
      '<span class="header-hierarchy-label">Hierarquia</span>',
      '<div class="header-hierarchy-buttons">',
      '  <button type="button" class="header-hierarchy-btn" data-header-move="up" title="Mover cabeçalho para cima">↑</button>',
      '  <button type="button" class="header-hierarchy-btn" data-header-move="down" title="Mover cabeçalho para baixo">↓</button>',
      '</div>'
    ].join("");

    controles.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-header-move]");

      if (!botao) {
        return;
      }

      const direcao = botao.getAttribute("data-header-move");

      if (direcao === "up") {
        moverLinhaParaCima_v2(linha);
      }

      if (direcao === "down") {
        moverLinhaParaBaixo_v2(linha);
      }
    });

    colunaHierarquia.appendChild(controles);

    if (selectTipo && selectTipo.dataset.hierarchyBoundV2 !== "1") {
      selectTipo.dataset.hierarchyBoundV2 = "1";
      selectTipo.addEventListener("change", atualizarHierarquia_v2);
    }
  }

  //###################################################################################
  // (8) ATUALIZAR TUDO
  //###################################################################################

  function atualizarHierarquia_v2() {
    montarLinhasEqualizadas_v2();
    classificarColunas_v2();

    const linhas = Array.from(document.querySelectorAll(".additional-field-row-equalized"));

    linhas.forEach(function (linha) {
      criarHierarquiaNaLinha_v2(linha);
    });
  }

  //###################################################################################
  // (9) INICIALIZACAO
  //###################################################################################

  function inicializar_v2() {
    atualizarHierarquia_v2();

    window.setTimeout(atualizarHierarquia_v2, 100);
    window.setTimeout(atualizarHierarquia_v2, 400);
    window.setTimeout(atualizarHierarquia_v2, 1000);
    window.setTimeout(atualizarHierarquia_v2, 1800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v2);
  } else {
    inicializar_v2();
  }
})();
