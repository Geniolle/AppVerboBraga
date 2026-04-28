//###################################################################################
// (1) EQUALIZAR LINHAS DOS CAMPOS ADICIONAIS
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (2) FUNÇÕES AUXILIARES
  //###################################################################################

  function normalizarTexto(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function obterFormularioCamposAdicionais() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      const texto = normalizarTexto(formulario.textContent);

      return (
        texto.includes("nome do campo adicional") &&
        texto.includes("tipo do campo") &&
        texto.includes("obrigatorio")
      );
    }) || null;
  }

  function obterTextoLabel(elemento) {
    const label = elemento ? elemento.querySelector("label") : null;
    return normalizarTexto(label ? label.textContent : "");
  }

  function ehInicioDeLinha(elemento) {
    return obterTextoLabel(elemento).includes("nome do campo adicional");
  }

  function ehBotaoRemover(elemento) {
    if (!elemento) {
      return false;
    }

    if (elemento.matches && elemento.matches("button")) {
      const texto = normalizarTexto(elemento.textContent);
      const title = normalizarTexto(elemento.getAttribute("title"));

      return texto === "x" || texto === "×" || title.includes("remover") || title.includes("excluir");
    }

    return Boolean(
      elemento.querySelector &&
      elemento.querySelector("button, .btn-danger, .remove-field, [data-remove]")
    );
  }

  function jaEstaEqualizado(formulario) {
    return Boolean(formulario.querySelector(".additional-field-row-equalized"));
  }

  //###################################################################################
  // (3) AGRUPAR CADA CAMPO ADICIONAL EM UMA LINHA REAL
  //###################################################################################

  function equalizarLinhasCamposAdicionais() {
    const formulario = obterFormularioCamposAdicionais();

    if (!formulario || jaEstaEqualizado(formulario)) {
      return;
    }

    const container =
      formulario.querySelector(".additional-fields-grid") ||
      formulario.querySelector(".form-grid") ||
      formulario.querySelector(".personal-grid") ||
      formulario;

    const filhos = Array.from(container.children);

    let indice = 0;

    while (indice < filhos.length) {
      const elementoAtual = filhos[indice];

      if (!elementoAtual || !ehInicioDeLinha(elementoAtual)) {
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

        if (ehInicioDeLinha(proximoElemento)) {
          break;
        }

        elementosLinha.push(proximoElemento);
        proximoIndice += 1;

        if (ehBotaoRemover(proximoElemento)) {
          break;
        }
      }

      const linha = document.createElement("div");
      linha.className = "additional-field-row additional-field-row-equalized";

      container.insertBefore(linha, elementoAtual);

      elementosLinha.forEach(function (elemento) {
        linha.appendChild(elemento);
      });

      indice = proximoIndice;
    }
  }

  //###################################################################################
  // (4) NORMALIZAR COLUNAS DENTRO DA LINHA
  //###################################################################################

  function classificarColunas() {
    const linhas = Array.from(document.querySelectorAll(".additional-field-row-equalized"));

    linhas.forEach(function (linha) {
      const campos = Array.from(linha.children);

      campos.forEach(function (campo) {
        const label = obterTextoLabel(campo);

        campo.classList.remove(
          "additional-field-name-col",
          "additional-field-type-col",
          "additional-field-required-col",
          "additional-field-size-col",
          "additional-field-action-col"
        );

        if (label.includes("nome do campo adicional")) {
          campo.classList.add("additional-field-name-col");
          return;
        }

        if (label.includes("tipo do campo")) {
          campo.classList.add("additional-field-type-col");
          return;
        }

        if (label.includes("obrigatorio")) {
          campo.classList.add("additional-field-required-col");
          return;
        }

        if (label.includes("tamanho")) {
          campo.classList.add("additional-field-size-col");
          return;
        }

        if (ehBotaoRemover(campo)) {
          campo.classList.add("additional-field-action-col");
        }
      });
    });
  }

  //###################################################################################
  // (5) INICIALIZAÇÃO
  //###################################################################################

  function iniciar() {
    equalizarLinhasCamposAdicionais();
    classificarColunas();

    window.setTimeout(function () {
      equalizarLinhasCamposAdicionais();
      classificarColunas();
    }, 200);

    window.setTimeout(function () {
      equalizarLinhasCamposAdicionais();
      classificarColunas();
    }, 800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
