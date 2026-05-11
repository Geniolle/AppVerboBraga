(function () {
  "use strict";

  //###################################################################################
  // (1) CONFIGURACAO
  //###################################################################################

  var VERSION = "20260511-sessoes-entries-per-page-v1";
  var ROOT_SELECTOR = [
    '[data-admin-subprocess="sessoes"]',
    '[data-admin-subprocess-key="sessoes"]',
    '[data-subprocess-key="sessoes"]',
    '#admin-sidebar-sections-card',
    '#admin-sidebar-sections-card-active',
    '#admin-sidebar-sections-card-inactive',
    '#admin-sidebar-sections-card-create'
  ].join(",");

  var FOOTER_CLASS = "appverbo-sessoes-entries-per-page-v1";
  var TABLE_ATTR = "data-appverbo-sessoes-pagination-table-v1";
  var ROW_HIDDEN_ATTR = "data-appverbo-sessoes-pagination-hidden-v1";
  var DEFAULT_PAGE_SIZE = 5;
  var PAGE_SIZE_OPTIONS = [5, 10, 25, 50];

  var initializationTimer = null;
  var observer = null;
  var tableSequence = 0;

  //###################################################################################
  // (2) FUNCOES BASE
  //###################################################################################

  function normalizarTextoSessoesEntriesPerPage_v1(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/\s+/g, " ")
      .trim();
  }

  function obterParametroUrlSessoesEntriesPerPage_v1(nome) {
    try {
      var params = new URLSearchParams(window.location.search || "");
      return normalizarTextoSessoesEntriesPerPage_v1(params.get(nome) || "");
    }
    catch (erro) {
      return "";
    }
  }

  function paginaAtualPodeTerSessoesEntriesPerPage_v1() {
    var adminTab = obterParametroUrlSessoesEntriesPerPage_v1("admin_tab");
    var sidebarTab = obterParametroUrlSessoesEntriesPerPage_v1("sidebar_sections_tab");

    if (adminTab === "sessoes" || sidebarTab === "sessoes") {
      return true;
    }

    return document.querySelector('[data-admin-subprocess="sessoes"], [data-subprocess-key="sessoes"]') !== null;
  }

  function gerarIdTabelaSessoesEntriesPerPage_v1(table) {
    var atual = table.getAttribute(TABLE_ATTR);
    if (atual) {
      return atual;
    }

    tableSequence += 1;
    var novoId = "sessoes-pagination-table-" + tableSequence;
    table.setAttribute(TABLE_ATTR, novoId);
    return novoId;
  }

  function obterTbodySessoesEntriesPerPage_v1(table) {
    if (!table) {
      return null;
    }

    return table.tBodies && table.tBodies.length ? table.tBodies[0] : null;
  }

  function obterTodasLinhasSessoesEntriesPerPage_v1(table) {
    var tbody = obterTbodySessoesEntriesPerPage_v1(table);
    if (!tbody) {
      return [];
    }

    return Array.prototype.slice.call(tbody.querySelectorAll("tr"));
  }

  function linhaOcultaPorOutroCodigoSessoesEntriesPerPage_v1(row) {
    if (!row) {
      return true;
    }

    if (row.getAttribute(ROW_HIDDEN_ATTR) === "1") {
      return false;
    }

    if (row.hidden) {
      return true;
    }

    if (row.getAttribute("aria-hidden") === "true") {
      return true;
    }

    if (row.classList.contains("hidden") || row.classList.contains("is-hidden")) {
      return true;
    }

    try {
      return window.getComputedStyle(row).display === "none";
    }
    catch (erro) {
      return false;
    }
  }

  function obterLinhasPaginaveisSessoesEntriesPerPage_v1(table) {
    return obterTodasLinhasSessoesEntriesPerPage_v1(table).filter(function (row) {
      return !linhaOcultaPorOutroCodigoSessoesEntriesPerPage_v1(row);
    });
  }

  function encontrarContainerInsercaoSessoesEntriesPerPage_v1(table) {
    if (!table) {
      return null;
    }

    var wrapper = table.closest(".table-responsive, .admin-table-scroll, .admin-table-wrapper, .admin-subprocess-table-wrapper-v1");
    if (wrapper && wrapper.parentNode) {
      return wrapper;
    }

    return table;
  }

  function tabelaTemRodapeProprioSessoesEntriesPerPage_v1(table) {
    var container = encontrarContainerInsercaoSessoesEntriesPerPage_v1(table);
    var parent = container && container.parentNode ? container.parentNode : null;

    if (!parent) {
      return false;
    }

    return parent.querySelector("." + FOOTER_CLASS) !== null;
  }

  function tabelaPareceSerDeSessoesEntriesPerPage_v1(table) {
    if (!table) {
      return false;
    }

    var root = table.closest(ROOT_SELECTOR);
    if (root) {
      return true;
    }

    var textoContexto = "";
    var card = table.closest(".card, section, article, div");
    if (card) {
      textoContexto = normalizarTextoSessoesEntriesPerPage_v1(card.textContent || "");
    }

    return textoContexto.indexOf("sessao") >= 0 || textoContexto.indexOf("sessoes") >= 0;
  }

  //###################################################################################
  // (3) CRIAR RODAPE
  //###################################################################################

  function criarSelectSessoesEntriesPerPage_v1(table, state) {
    var select = document.createElement("select");
    select.className = "appverbo-sessoes-page-size-select-v1";
    select.setAttribute("aria-label", "Entradas por página");

    PAGE_SIZE_OPTIONS.forEach(function (value) {
      var option = document.createElement("option");
      option.value = String(value);
      option.textContent = String(value);
      if (value === state.pageSize) {
        option.selected = true;
      }
      select.appendChild(option);
    });

    select.addEventListener("change", function () {
      var parsed = parseInt(select.value, 10);
      state.pageSize = PAGE_SIZE_OPTIONS.indexOf(parsed) >= 0 ? parsed : DEFAULT_PAGE_SIZE;
      state.page = 1;
      aplicarPaginacaoSessoesEntriesPerPage_v1(table, state);
    });

    return select;
  }

  function criarBotaoSessoesEntriesPerPage_v1(label, ariaLabel, onClick) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "appverbo-sessoes-page-button-v1";
    button.textContent = label;
    button.setAttribute("aria-label", ariaLabel);
    button.addEventListener("click", onClick);
    return button;
  }

  function criarRodapeSessoesEntriesPerPage_v1(table) {
    var state = {
      page: 1,
      pageSize: DEFAULT_PAGE_SIZE,
      totalPages: 1,
      prevButton: null,
      nextButton: null,
      pageIndicator: null,
      totalIndicator: null
    };

    var footer = document.createElement("div");
    footer.className = FOOTER_CLASS;
    footer.setAttribute("data-appverbo-version", VERSION);

    var left = document.createElement("div");
    left.className = "appverbo-sessoes-page-size-v1";

    var select = criarSelectSessoesEntriesPerPage_v1(table, state);

    var label = document.createElement("span");
    label.className = "appverbo-sessoes-page-size-label-v1";
    label.textContent = "entradas por página";

    left.appendChild(select);
    left.appendChild(label);

    var right = document.createElement("div");
    right.className = "appverbo-sessoes-pager-v1";

    state.prevButton = criarBotaoSessoesEntriesPerPage_v1("‹", "Página anterior", function () {
      if (state.page > 1) {
        state.page -= 1;
        aplicarPaginacaoSessoesEntriesPerPage_v1(table, state);
      }
    });

    state.pageIndicator = document.createElement("span");
    state.pageIndicator.className = "appverbo-sessoes-page-indicator-v1";
    state.pageIndicator.textContent = "1";

    state.nextButton = criarBotaoSessoesEntriesPerPage_v1("›", "Página seguinte", function () {
      if (state.page < state.totalPages) {
        state.page += 1;
        aplicarPaginacaoSessoesEntriesPerPage_v1(table, state);
      }
    });

    state.totalIndicator = document.createElement("span");
    state.totalIndicator.className = "appverbo-sessoes-total-indicator-v1";
    state.totalIndicator.setAttribute("aria-live", "polite");

    right.appendChild(state.prevButton);
    right.appendChild(state.pageIndicator);
    right.appendChild(state.nextButton);
    right.appendChild(state.totalIndicator);

    footer.appendChild(left);
    footer.appendChild(right);

    footer.__appverboSessoesPaginationState_v1 = state;

    return footer;
  }

  //###################################################################################
  // (4) APLICAR PAGINACAO
  //###################################################################################

  function aplicarPaginacaoSessoesEntriesPerPage_v1(table, state) {
    if (!table || !state) {
      return;
    }

    var linhas = obterLinhasPaginaveisSessoesEntriesPerPage_v1(table);
    var total = linhas.length;
    var totalPages = Math.max(1, Math.ceil(total / state.pageSize));

    if (state.page > totalPages) {
      state.page = totalPages;
    }

    if (state.page < 1) {
      state.page = 1;
    }

    state.totalPages = totalPages;

    var start = (state.page - 1) * state.pageSize;
    var end = start + state.pageSize;

    obterTodasLinhasSessoesEntriesPerPage_v1(table).forEach(function (row) {
      if (row.getAttribute(ROW_HIDDEN_ATTR) === "1") {
        row.removeAttribute(ROW_HIDDEN_ATTR);
        row.style.display = "";
      }
    });

    linhas.forEach(function (row, index) {
      if (index >= start && index < end) {
        row.removeAttribute(ROW_HIDDEN_ATTR);
        row.style.display = "";
      }
      else {
        row.setAttribute(ROW_HIDDEN_ATTR, "1");
        row.style.display = "none";
      }
    });

    if (state.pageIndicator) {
      state.pageIndicator.textContent = String(state.page);
    }

    if (state.prevButton) {
      state.prevButton.disabled = state.page <= 1;
    }

    if (state.nextButton) {
      state.nextButton.disabled = state.page >= totalPages;
    }

    if (state.totalIndicator) {
      state.totalIndicator.textContent = total > 0 ? "Total: " + total : "";
    }
  }

  function anexarRodapeSessoesEntriesPerPage_v1(table) {
    if (!table || tabelaTemRodapeProprioSessoesEntriesPerPage_v1(table)) {
      return;
    }

    if (!tabelaPareceSerDeSessoesEntriesPerPage_v1(table)) {
      return;
    }

    var linhas = obterTodasLinhasSessoesEntriesPerPage_v1(table);
    if (!linhas.length) {
      return;
    }

    gerarIdTabelaSessoesEntriesPerPage_v1(table);

    var container = encontrarContainerInsercaoSessoesEntriesPerPage_v1(table);
    if (!container || !container.parentNode) {
      return;
    }

    var footer = criarRodapeSessoesEntriesPerPage_v1(table);
    container.parentNode.insertBefore(footer, container.nextSibling);

    aplicarPaginacaoSessoesEntriesPerPage_v1(table, footer.__appverboSessoesPaginationState_v1);
  }

  //###################################################################################
  // (5) INICIALIZACAO
  //###################################################################################

  function inicializarSessoesEntriesPerPage_v1() {
    if (!paginaAtualPodeTerSessoesEntriesPerPage_v1()) {
      return;
    }

    var roots = Array.prototype.slice.call(document.querySelectorAll(ROOT_SELECTOR));

    if (!roots.length) {
      roots = [document.body];
    }

    roots.forEach(function (root) {
      Array.prototype.slice.call(root.querySelectorAll("table")).forEach(function (table) {
        anexarRodapeSessoesEntriesPerPage_v1(table);
      });
    });
  }

  function agendarInicializacaoSessoesEntriesPerPage_v1() {
    window.clearTimeout(initializationTimer);
    initializationTimer = window.setTimeout(function () {
      inicializarSessoesEntriesPerPage_v1();
    }, 120);
  }

  function observarMudancasSessoesEntriesPerPage_v1() {
    if (observer || !window.MutationObserver || !document.body) {
      return;
    }

    observer = new MutationObserver(function () {
      agendarInicializacaoSessoesEntriesPerPage_v1();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  function ligarEventosDeFiltroSessoesEntriesPerPage_v1() {
    document.addEventListener("input", function (event) {
      var target = event.target;
      if (!target) {
        return;
      }

      if (target.matches('input[type="search"], input[placeholder*="Procur"], input[placeholder*="procur"]')) {
        window.setTimeout(function () {
          document.querySelectorAll("." + FOOTER_CLASS).forEach(function (footer) {
            var state = footer.__appverboSessoesPaginationState_v1;
            var tableId = footer.previousElementSibling && footer.previousElementSibling.querySelector
              ? footer.previousElementSibling.querySelector("table")
              : null;

            if (state) {
              state.page = 1;
            }

            if (tableId) {
              aplicarPaginacaoSessoesEntriesPerPage_v1(tableId, state);
            }
          });
        }, 180);
      }
    }, true);
  }

  //###################################################################################
  // (6) ARRANQUE
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      inicializarSessoesEntriesPerPage_v1();
      observarMudancasSessoesEntriesPerPage_v1();
      ligarEventosDeFiltroSessoesEntriesPerPage_v1();
    });
  }
  else {
    inicializarSessoesEntriesPerPage_v1();
    observarMudancasSessoesEntriesPerPage_v1();
    ligarEventosDeFiltroSessoesEntriesPerPage_v1();
  }

  window.addEventListener("load", function () {
    agendarInicializacaoSessoesEntriesPerPage_v1();
  });
})();