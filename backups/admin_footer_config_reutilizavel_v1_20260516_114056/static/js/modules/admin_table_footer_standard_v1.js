// APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_START
(function () {
  "use strict";

  //###################################################################################
  // (1) CONFIGURACAO
  //###################################################################################

  const FOOTER_SELECTOR = [
    ".table-limiter",
    ".admin-status-table-footer-v1",
    ".admin-subprocess-table-footer-v1"
  ].join(",");

  const LEGACY_SESSOES_SELECTOR = [
    ".appverbo-sessoes-entries-per-page-v1",
    ".appverbo_sessoes_entries_per_page_v1",
    ".appverbo-sessoes-entries-per-page-footer-v1",
    ".appverbo_sessoes_entries_per_page_footer_v1",
    ".sessoes-entries-per-page-footer-v1",
    ".sessoes_entries_per_page_footer_v1",
    "[data-appverbo-sessoes-entries-per-page-v1]",
    "[data-sessoes-entries-per-page]",
    "[data-sessoes-entries-per-page-v1]"
  ].join(",");

  //###################################################################################
  // (2) LIMPAR DUPLICADOS
  //###################################################################################

  function removerRodapesLegadosSessoesAdminTableFooterStandard_v2b() {
    document.querySelectorAll(LEGACY_SESSOES_SELECTOR).forEach(function (elemento) {
      if (elemento.closest(".admin-subprocess-table-footer-v1")) {
        return;
      }

      elemento.remove();
    });
  }

  function obterTabelaDoRodapeAdminTableFooterStandard_v2b(footer) {
    let cursor = footer.previousElementSibling;

    while (cursor) {
      if (cursor.matches && cursor.matches(FOOTER_SELECTOR)) {
        cursor = cursor.previousElementSibling;
        continue;
      }

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

  function removerRodapesDuplicadosAdminTableFooterStandard_v2b() {
    const mapa = new Map();

    document.querySelectorAll(FOOTER_SELECTOR).forEach(function (footer) {
      const tabela = obterTabelaDoRodapeAdminTableFooterStandard_v2b(footer);

      if (!tabela) {
        return;
      }

      if (!mapa.has(tabela)) {
        mapa.set(tabela, []);
      }

      mapa.get(tabela).push(footer);
    });

    mapa.forEach(function (rodapes) {
      if (rodapes.length <= 1) {
        return;
      }

      const preferido = rodapes.find(function (footer) {
        return footer.classList.contains("admin-subprocess-table-footer-v1");
      }) || rodapes.find(function (footer) {
        return footer.classList.contains("table-limiter");
      }) || rodapes[0];

      rodapes.forEach(function (footer) {
        if (footer !== preferido) {
          footer.remove();
        }
      });
    });
  }

  //###################################################################################
  // (3) CONTROLOS DO RODAPE
  //###################################################################################

  function obterControlesRodapeAdminTableFooterStandard_v2b(footer) {
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
  // (4) NORMALIZAR SELECT E TEXTO
  //###################################################################################

  function normalizarOpcoesSelectAdminTableFooterStandard_v2b(select) {
    if (!select) {
      return;
    }

    const valoresPadrao = ["5", "10", "20"];
    const valorAtual = select.value || "5";
    const existentes = new Set();

    Array.from(select.options).forEach(function (option) {
      if (!option.value) {
        option.value = option.textContent.trim();
      }

      existentes.add(option.value);
    });

    valoresPadrao.forEach(function (valor) {
      if (!existentes.has(valor)) {
        const option = document.createElement("option");
        option.value = valor;
        option.textContent = valor;
        select.appendChild(option);
      }
    });

    select.value = valoresPadrao.includes(valorAtual) ? valorAtual : "5";
  }

  function normalizarTextoAdminTableFooterStandard_v2b(footer) {
    footer.querySelectorAll("span").forEach(function (span) {
      const texto = (span.textContent || "").replace(/\s+/g, " ").trim();

      if (texto.toLowerCase() === "entradas por página") {
        span.textContent = "entradas por página";
      }
    });
  }

  //###################################################################################
  // (5) PAGINACAO
  //###################################################################################

  function aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado) {
    const linhas = Array.from(tabela.querySelectorAll("tbody tr"));
    const controles = obterControlesRodapeAdminTableFooterStandard_v2b(footer);

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

  function iniciarRodapeAdminTableFooterStandard_v2b(footer) {
    if (footer.dataset.appverboAdminTableFooterStandardReadyV2b === "1") {
      return;
    }

    const tabela = obterTabelaDoRodapeAdminTableFooterStandard_v2b(footer);

    if (!tabela) {
      return;
    }

    const controles = obterControlesRodapeAdminTableFooterStandard_v2b(footer);

    if (!controles.select) {
      return;
    }

    normalizarTextoAdminTableFooterStandard_v2b(footer);
    normalizarOpcoesSelectAdminTableFooterStandard_v2b(controles.select);

    const estado = {
      page: 1,
      pageSize: Number.parseInt(controles.select.value || "5", 10) || 5
    };

    footer.dataset.appverboAdminTableFooterStandardReadyV2b = "1";

    controles.select.addEventListener("change", function () {
      estado.page = 1;
      aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado);
    });

    if (controles.botaoAnterior) {
      controles.botaoAnterior.addEventListener("click", function (event) {
        event.preventDefault();
        estado.page -= 1;
        aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado);
      });
    }

    if (controles.botaoSeguinte) {
      controles.botaoSeguinte.addEventListener("click", function (event) {
        event.preventDefault();
        estado.page += 1;
        aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado);
      });
    }

    aplicarPaginaAdminTableFooterStandard_v2b(tabela, footer, estado);
  }

  //###################################################################################
  // (6) INSTALAR
  //###################################################################################

  function instalarRodapesAdminTableFooterStandard_v2b() {
    removerRodapesLegadosSessoesAdminTableFooterStandard_v2b();
    removerRodapesDuplicadosAdminTableFooterStandard_v2b();

    document.querySelectorAll(FOOTER_SELECTOR).forEach(function (footer) {
      iniciarRodapeAdminTableFooterStandard_v2b(footer);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarRodapesAdminTableFooterStandard_v2b);
  }
  else {
    instalarRodapesAdminTableFooterStandard_v2b();
  }

  window.addEventListener("load", instalarRodapesAdminTableFooterStandard_v2b);
})();
// APPVERBO_ADMIN_TABLE_FOOTER_STANDARD_V1_END
