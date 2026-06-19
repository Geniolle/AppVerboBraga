// APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) LOCALIZAR TABELA DO RODAPE
  //###################################################################################

  function obterTabelaDoRodapeAdminTableFooterStandard_v1(footer) {
    let cursor = footer.previousElementSibling;

    while (cursor) {
      if (cursor.matches && cursor.matches("table")) {
        return cursor;
      }

      if (cursor.querySelector) {
        const tabelaInterna = cursor.querySelector("table");

        if (tabelaInterna) {
          return tabelaInterna;
        }
      }

      cursor = cursor.previousElementSibling;
    }

    return null;
  }

  //###################################################################################
  // (2) LOCALIZAR CONTROLOS DO RODAPE
  //###################################################################################

  function obterControlesRodapeAdminTableFooterStandard_v1(footer) {
    const select = footer.querySelector("select");
    const botoes = Array.from(footer.querySelectorAll("button"));

    let botaoAnterior = footer.querySelector(".table-limiter-nav-btn:first-of-type");
    let botaoSeguinte = footer.querySelector(".table-limiter-nav-btn:last-of-type");

    if (!botaoAnterior && botoes.length > 0) {
      botaoAnterior = botoes[0];
    }

    if (!botaoSeguinte && botoes.length > 1) {
      botaoSeguinte = botoes[botoes.length - 1];
    }

    let paginaAtual = footer.querySelector(".table-limiter-page");

    if (!paginaAtual) {
      paginaAtual = footer.querySelector(".pagination .active");
    }

    return {
      select,
      botaoAnterior,
      botaoSeguinte,
      paginaAtual
    };
  }

  //###################################################################################
  // (3) NORMALIZAR OPCOES DO SELECT
  //###################################################################################

  function normalizarOpcoesSelectAdminTableFooterStandard_v1(select) {
    if (!select) {
      return;
    }

    const valoresPadrao = ["5", "10", "20"];
    const valorAtual = select.value || "5";
    const valoresExistentes = new Set();

    Array.from(select.options).forEach(function (option) {
      if (!option.value) {
        option.value = option.textContent.trim();
      }

      valoresExistentes.add(option.value);
    });

    valoresPadrao.forEach(function (valor) {
      if (!valoresExistentes.has(valor)) {
        const option = document.createElement("option");
        option.value = valor;
        option.textContent = valor;
        select.appendChild(option);
      }
    });

    if (valoresPadrao.includes(valorAtual)) {
      select.value = valorAtual;
    }
    else {
      select.value = "5";
    }
  }

  //###################################################################################
  // (4) APLICAR PAGINA NA TABELA
  //###################################################################################

  function aplicarPaginaAdminTableFooterStandard_v1(tabela, footer, estado) {
    const linhas = Array.from(tabela.querySelectorAll("tbody tr"));
    const controles = obterControlesRodapeAdminTableFooterStandard_v1(footer);

    estado.pageSize = Number.parseInt(controles.select ? controles.select.value : "5", 10) || 5;

    const totalPaginas = Math.max(1, Math.ceil(linhas.length / estado.pageSize));

    if (estado.page > totalPaginas) {
      estado.page = totalPaginas;
    }

    if (estado.page < 1) {
      estado.page = 1;
    }

    const inicio = (estado.page - 1) * estado.pageSize;
    const fim = inicio + estado.pageSize;

    linhas.forEach(function (linha, index) {
      linha.style.display = index >= inicio && index < fim ? "" : "none";
    });

    if (controles.paginaAtual) {
      controles.paginaAtual.textContent = String(estado.page);
    }

    if (controles.botaoAnterior) {
      controles.botaoAnterior.disabled = estado.page <= 1;
    }

    if (controles.botaoSeguinte) {
      controles.botaoSeguinte.disabled = estado.page >= totalPaginas;
    }
  }

  //###################################################################################
  // (5) INICIAR UM RODAPE
  //###################################################################################

  function iniciarRodapeAdminTableFooterStandard_v1(footer) {
    if (footer.dataset.appverboAdminTableFooterStandardReadyV1 === "1") {
      return;
    }

    const tabela = obterTabelaDoRodapeAdminTableFooterStandard_v1(footer);

    if (!tabela) {
      return;
    }

    const controles = obterControlesRodapeAdminTableFooterStandard_v1(footer);

    if (!controles.select) {
      return;
    }

    normalizarOpcoesSelectAdminTableFooterStandard_v1(controles.select);

    const estado = {
      page: 1,
      pageSize: Number.parseInt(controles.select.value || "5", 10) || 5
    };

    footer.dataset.appverboAdminTableFooterStandardReadyV1 = "1";

    controles.select.addEventListener("change", function () {
      estado.page = 1;
      aplicarPaginaAdminTableFooterStandard_v1(tabela, footer, estado);
    });

    if (controles.botaoAnterior) {
      controles.botaoAnterior.addEventListener("click", function (event) {
        event.preventDefault();
        estado.page -= 1;
        aplicarPaginaAdminTableFooterStandard_v1(tabela, footer, estado);
      });
    }

    if (controles.botaoSeguinte) {
      controles.botaoSeguinte.addEventListener("click", function (event) {
        event.preventDefault();
        estado.page += 1;
        aplicarPaginaAdminTableFooterStandard_v1(tabela, footer, estado);
      });
    }

    aplicarPaginaAdminTableFooterStandard_v1(tabela, footer, estado);
  }

  //###################################################################################
  // (6) INSTALAR EM TODAS AS TABELAS ADMINISTRATIVAS
  //###################################################################################

  function instalarRodapesAdminTableFooterStandard_v1() {
    const seletores = [
      ".table-limiter",
      ".admin-status-table-footer-v1",
      ".admin-subprocess-table-footer-v1"
    ];

    document.querySelectorAll(seletores.join(",")).forEach(function (footer) {
      iniciarRodapeAdminTableFooterStandard_v1(footer);
    });
  }

  //###################################################################################
  // (7) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarRodapesAdminTableFooterStandard_v1);
  }
  else {
    instalarRodapesAdminTableFooterStandard_v1();
  }
})();
// APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_END
