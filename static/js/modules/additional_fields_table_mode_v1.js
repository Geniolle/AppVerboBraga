//###################################################################################
// APPVERBOBRAGA - CAMPOS ADICIONAIS EM TABELA FECHADA / SIMPLIFICADA - V1
//###################################################################################

(function () {
  "use strict";

  let aplicandoTabela_v1 = false;

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
  // (2) LOCALIZAR FORMULÁRIO E CONTAINER
  //###################################################################################

  function obterFormularioCamposAdicionais_v1() {
    const formularios = Array.from(document.querySelectorAll("form"));

    return formularios.find(function (formulario) {
      if (formulario.hasAttribute("data-additional-fields-manager-v2")) {
        return false;
      }
      const action = String(formulario.getAttribute("action") || "");
      const texto = normalizarTexto_v1(formulario.textContent);

      return (
        action.includes("/settings/menu/process-additional-fields") ||
        (
          texto.includes("nome do campo adicional") &&
          texto.includes("tipo do campo") &&
          texto.includes("obrigatorio")
        )
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
  // (3) LEITURA DOS BLOCOS VISUAIS
  //###################################################################################

  function obterLabelCampo_v1(campo) {
    const label = campo ? campo.querySelector("label") : null;
    return normalizarTexto_v1(label ? label.textContent : "");
  }

  function obterInputVisivel_v1(campo) {
    if (!campo) {
      return null;
    }

    return Array.from(campo.querySelectorAll("input")).find(function (input) {
      return String(input.type || "").toLowerCase() !== "hidden";
    }) || null;
  }

  function obterSelect_v1(campo) {
    return campo ? campo.querySelector("select") : null;
  }

  function obterValorInput_v1(campo) {
    const input = obterInputVisivel_v1(campo);

    if (!input) {
      return "";
    }

    return String(input.value || input.getAttribute("value") || "").trim();
  }

  function obterTextoSelect_v1(select) {
    if (!select) {
      return "";
    }

    const option = select.options[select.selectedIndex];

    return String(
      option ? option.textContent || option.value || "" : select.value || ""
    ).trim();
  }

  function obterValorSelect_v1(select) {
    if (!select) {
      return "";
    }

    return String(select.value || "").trim();
  }

  function campoEhNome_v1(campo) {
    return obterLabelCampo_v1(campo).includes("nome do campo adicional");
  }

  function campoEhTipo_v1(campo) {
    return obterLabelCampo_v1(campo).includes("tipo do campo");
  }

  function campoEhObrigatorio_v1(campo) {
    return obterLabelCampo_v1(campo).includes("obrigatorio");
  }

  function campoEhTamanho_v1(campo) {
    return obterLabelCampo_v1(campo).includes("tamanho");
  }

  function campoEhLista_v1(campo) {
    return obterLabelCampo_v1(campo) === "lista";
  }

  function tipoEhCabecalho_v1(valorTipo, textoTipo) {
    const valor = normalizarTexto_v1(valorTipo);
    const texto = normalizarTexto_v1(textoTipo);

    return (
      valor === "header" ||
      valor.includes("header") ||
      valor.includes("cabecalho") ||
      texto.includes("cabecalho")
    );
  }

  //###################################################################################
  // (4) MONTAR LINHAS LÓGICAS
  //###################################################################################

  function obterCamposVisuais_v1(container) {
    return Array.from(container.querySelectorAll(".field")).filter(function (campo) {
      return !campo.closest(".additional-fields-table-mode-v1");
    });
  }

  function obterLinhasLogicas_v1(container) {
    const camposVisuais = obterCamposVisuais_v1(container);
    const linhas = [];

    let indice = 0;

    while (indice < camposVisuais.length) {
      const campoAtual = camposVisuais[indice];

      if (!campoEhNome_v1(campoAtual)) {
        indice += 1;
        continue;
      }

      const camposDaLinha = [campoAtual];
      let proximoIndice = indice + 1;

      while (proximoIndice < camposVisuais.length) {
        const proximoCampo = camposVisuais[proximoIndice];

        if (!proximoCampo) {
          break;
        }

        if (campoEhNome_v1(proximoCampo)) {
          break;
        }

        camposDaLinha.push(proximoCampo);
        proximoIndice += 1;
      }

      const campoNome = campoAtual;
      const campoTipo = camposDaLinha.find(campoEhTipo_v1);
      const campoObrigatorio = camposDaLinha.find(campoEhObrigatorio_v1);
      const campoTamanho = camposDaLinha.find(campoEhTamanho_v1);
      const campoLista = camposDaLinha.find(campoEhLista_v1);

      const selectTipo = obterSelect_v1(campoTipo);
      const selectObrigatorio = obterSelect_v1(campoObrigatorio);
      const selectLista = obterSelect_v1(campoLista);

      const nome = obterValorInput_v1(campoNome);
      const tipoValor = obterValorSelect_v1(selectTipo);
      const tipoTexto = obterTextoSelect_v1(selectTipo);
      const obrigatorio = obterTextoSelect_v1(selectObrigatorio) || "-";
      const tamanho = obterValorInput_v1(campoTamanho) || "-";
      const lista = obterTextoSelect_v1(selectLista);

      linhas.push({
        nome: nome,
        tipoValor: tipoValor,
        tipoTexto: tipoTexto || "-",
        obrigatorio: obrigatorio,
        tamanho: tamanho,
        lista: lista && !normalizarTexto_v1(lista).includes("selecione") ? lista : "-",
        ehCabecalho: tipoEhCabecalho_v1(tipoValor, tipoTexto),
        camposDaLinha: camposDaLinha
      });

      indice = proximoIndice;
    }

    return linhas.filter(function (linha) {
      return linha.nome;
    });
  }

  function criarDadosTabela_v1(linhasLogicas) {
    let cabecalhoAtual = "";

    return linhasLogicas.map(function (linha, indice) {
      if (linha.ehCabecalho) {
        cabecalhoAtual = linha.nome;
      }

      return {
        ordem: indice + 1,
        campo: linha.nome,
        tipo: linha.tipoTexto,
        cabecalho: linha.ehCabecalho ? linha.nome : cabecalhoAtual || "-",
        obrigatorio: linha.obrigatorio,
        tamanho: linha.tamanho,
        lista: linha.lista,
        ehCabecalho: linha.ehCabecalho,
        camposDaLinha: linha.camposDaLinha
      };
    });
  }

  //###################################################################################
  // (5) CSS DA TABELA
  //###################################################################################

  function injetarCssTabela_v1() {
    const styleId = "additional-fields-table-mode-style-v1";

    if (document.getElementById(styleId)) {
      return;
    }

    const style = document.createElement("style");
    style.id = styleId;

    style.textContent = [
      ".additional-fields-table-mode-v1 {",
      "  width: 100% !important;",
      "  margin: 12px 0 18px 0 !important;",
      "}",

      ".additional-fields-table-toolbar-v1 {",
      "  display: flex !important;",
      "  justify-content: space-between !important;",
      "  align-items: center !important;",
      "  gap: 12px !important;",
      "  margin-bottom: 10px !important;",
      "}",

      ".additional-fields-table-title-v1 {",
      "  font-size: 14px !important;",
      "  font-weight: 800 !important;",
      "  color: #0f1f3d !important;",
      "}",

      ".additional-fields-table-edit-btn-v1 {",
      "  border: 1px solid #b8c8ed !important;",
      "  background: #eef4ff !important;",
      "  color: #244db3 !important;",
      "  border-radius: 8px !important;",
      "  padding: 7px 10px !important;",
      "  font-size: 12px !important;",
      "  font-weight: 700 !important;",
      "  cursor: pointer !important;",
      "}",

      ".additional-fields-table-v1 {",
      "  width: 100% !important;",
      "  border-collapse: collapse !important;",
      "  font-size: 12px !important;",
      "  background: #ffffff !important;",
      "}",

      ".additional-fields-table-v1 th {",
      "  text-align: left !important;",
      "  padding: 9px 8px !important;",
      "  border-bottom: 1px solid #cbd7ef !important;",
      "  color: #34476a !important;",
      "  font-size: 11px !important;",
      "  font-weight: 700 !important;",
      "  text-transform: uppercase !important;",
      "}",

      ".additional-fields-table-v1 td {",
      "  padding: 9px 8px !important;",
      "  border-bottom: 1px solid #e2e9f8 !important;",
      "  color: #0f1f3d !important;",
      "  vertical-align: middle !important;",
      "}",

      ".additional-fields-table-v1 tr.additional-fields-table-header-row-v1 td {",
      "  font-weight: 800 !important;",
      "  background: #f8fbff !important;",
      "}",

      ".additional-fields-table-type-badge-v1 {",
      "  display: inline-flex !important;",
      "  align-items: center !important;",
      "  border: 1px solid #b8c8ed !important;",
      "  border-radius: 999px !important;",
      "  padding: 2px 8px !important;",
      "  background: #eef4ff !important;",
      "  color: #244db3 !important;",
      "  font-size: 11px !important;",
      "  font-weight: 700 !important;",
      "}",

      ".additional-fields-table-actions-v1 {",
      "  display: inline-flex !important;",
      "  gap: 6px !important;",
      "}",

      ".additional-fields-table-limiter-v1 {",
      "  display: flex !important;",
      "  align-items: center !important;",
      "  justify-content: space-between !important;",
      "  gap: 12px !important;",
      "  margin-top: 10px !important;",
      "}",

      ".additional-fields-table-limiter-side-v1 {",
      "  display: inline-flex !important;",
      "  align-items: center !important;",
      "  gap: 8px !important;",
      "  flex-wrap: wrap !important;",
      "}",

      ".additional-fields-table-page-size-v1 {",
      "  min-width: 72px !important;",
      "  padding: 6px 28px 6px 10px !important;",
      "  border: 1px solid #c7d4ef !important;",
      "  border-radius: 8px !important;",
      "  background: #ffffff !important;",
      "  color: #1f3660 !important;",
      "}",

      ".additional-fields-table-nav-btn-v1 {",
      "  width: 32px !important;",
      "  height: 32px !important;",
      "  border: 1px solid #cbd7ef !important;",
      "  border-radius: 999px !important;",
      "  background: #ffffff !important;",
      "  color: #244db3 !important;",
      "  font-size: 16px !important;",
      "  line-height: 1 !important;",
      "  cursor: pointer !important;",
      "}",

      ".additional-fields-table-nav-btn-v1:disabled {",
      "  opacity: 0.45 !important;",
      "  cursor: not-allowed !important;",
      "}",

      ".additional-fields-table-page-v1 {",
      "  min-width: 18px !important;",
      "  text-align: center !important;",
      "  font-weight: 700 !important;",
      "  color: #1f3660 !important;",
      "}",

      ".additional-fields-table-action-btn-v1 {",
      "  border: 1px solid #cbd7ef !important;",
      "  background: #f8fbff !important;",
      "  color: #244db3 !important;",
      "  border-radius: 7px !important;",
      "  padding: 5px 7px !important;",
      "  font-size: 11px !important;",
      "  font-weight: 700 !important;",
      "  cursor: pointer !important;",
      "}",

      ".additional-fields-table-hidden-v1 {",
      "  display: none !important;",
      "}",

      ".additional-fields-table-detail-open-v1 .field {",
      "  display: block !important;",
      "}",

      ".additional-fields-table-detail-open-v1 .additional-field-row-equalized {",
      "  display: grid !important;",
      "  grid-template-columns: minmax(220px, 1.6fr) minmax(180px, 1.1fr) minmax(120px, 0.8fr) minmax(120px, 0.7fr) minmax(220px, 1.3fr) auto auto auto !important;",
      "  gap: 8px !important;",
      "  align-items: end !important;",
      "  margin-bottom: 8px !important;",
      "}",

      "@media (max-width: 1000px) {",
      "  .additional-fields-table-v1 {",
      "    min-width: 900px !important;",
      "  }",
      "  .additional-fields-table-mode-v1 {",
      "    overflow-x: auto !important;",
      "  }",
      "  .additional-fields-table-limiter-v1 {",
      "    min-width: 900px !important;",
      "  }",
      "}"
    ].join("\n");

    document.head.appendChild(style);
  }

  //###################################################################################
  // (6) RENDERIZAR TABELA
  //###################################################################################

  function renderizarLinhasTabela_v1(dadosTabela) {
    if (!dadosTabela.length) {
      return '<tr><td colspan="8">Sem campos adicionais configurados.</td></tr>';
    }

    return dadosTabela.map(function (item) {
      return [
        '<tr class="' + (item.ehCabecalho ? 'additional-fields-table-header-row-v1' : '') + '">',
        '  <td style="width:70px">' + item.ordem + '</td>',
        '  <td>' + escaparHtml_v1(item.campo) + '</td>',
        '  <td><span class="additional-fields-table-type-badge-v1">' + escaparHtml_v1(item.tipo) + '</span></td>',
        '  <td>' + escaparHtml_v1(item.cabecalho) + '</td>',
        '  <td>' + escaparHtml_v1(item.obrigatorio) + '</td>',
        '  <td>' + escaparHtml_v1(item.tamanho) + '</td>',
        '  <td>' + escaparHtml_v1(item.lista) + '</td>',
        '  <td>',
        '    <span class="additional-fields-table-actions-v1">',
        '      <button type="button" class="additional-fields-table-action-btn-v1" data-table-edit-fields-v1="1">Editar</button>',
        '    </span>',
        '  </td>',
        '</tr>'
      ].join("");
    }).join("");
  }

  function renderizarTabela_v1(dadosTabela, detalhesVisiveis) {
    return [
      '<div class="additional-fields-table-toolbar-v1">',
      '  <div class="additional-fields-table-title-v1">Campos configurados</div>',
      '  <button type="button" class="additional-fields-table-edit-btn-v1" data-table-toggle-fields-v1="1">',
      detalhesVisiveis ? 'Fechar edição' : 'Editar campos adicionais',
      '  </button>',
      '</div>',
      '<table class="additional-fields-table-v1">',
      '  <thead>',
      '    <tr>',
      '      <th>Ordem</th>',
      '      <th>Campo</th>',
      '      <th>Tipo</th>',
      '      <th>Cabeçalho</th>',
      '      <th>Obrigatório</th>',
      '      <th>Tamanho</th>',
      '      <th>Lista</th>',
      '      <th>Ações</th>',
      '    </tr>',
      '  </thead>',
      '  <tbody>',
      renderizarLinhasTabela_v1(dadosTabela),
      '  </tbody>',
      '</table>',
      '<div class="additional-fields-table-limiter-v1" data-table-limiter-v1="1">',
      '  <div class="additional-fields-table-limiter-side-v1">',
      '    <select class="additional-fields-table-page-size-v1" aria-label="Entradas por pagina (campos adicionais)" data-table-page-size-v1="1">',
      '      <option value="5" selected>5</option>',
      '      <option value="10">10</option>',
      '      <option value="20">20</option>',
      '    </select>',
      '    <span>entradas por pagina</span>',
      '  </div>',
      '  <div class="additional-fields-table-limiter-side-v1">',
      '    <button type="button" class="additional-fields-table-nav-btn-v1" aria-label="Pagina anterior" data-table-prev-v1="1">&#8249;</button>',
      '    <span class="additional-fields-table-page-v1" data-table-page-v1="1">1</span>',
      '    <button type="button" class="additional-fields-table-nav-btn-v1" aria-label="Proxima pagina" data-table-next-v1="1">&#8250;</button>',
      '  </div>',
      '</div>'
    ].join("");
  }

  //###################################################################################
  // (6.1) PAGINACAO DA TABELA
  //###################################################################################

  function inicializarPaginacaoTabela_v1(blocoTabela) {
    if (!blocoTabela) {
      return;
    }

    const tableEl = blocoTabela.querySelector(".additional-fields-table-v1");
    const limiterEl = blocoTabela.querySelector("[data-table-limiter-v1='1']");
    const pageSizeEl = blocoTabela.querySelector("[data-table-page-size-v1='1']");
    const prevEl = blocoTabela.querySelector("[data-table-prev-v1='1']");
    const nextEl = blocoTabela.querySelector("[data-table-next-v1='1']");
    const pageEl = blocoTabela.querySelector("[data-table-page-v1='1']");

    if (!tableEl || !limiterEl || !pageSizeEl || !prevEl || !nextEl || !pageEl) {
      return;
    }

    const rows = Array.from(tableEl.querySelectorAll("tbody tr"));

    if (!rows.length) {
      limiterEl.style.display = "none";
      return;
    }

    let pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
    let currentPage = 1;

    function getTotalPages() {
      return Math.max(1, Math.ceil(rows.length / pageSize));
    }

    function render() {
      const totalPages = getTotalPages();

      if (currentPage > totalPages) {
        currentPage = totalPages;
      }

      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize;

      rows.forEach(function (row, index) {
        row.style.display = index >= start && index < end ? "" : "none";
      });

      pageEl.textContent = String(currentPage);
      prevEl.disabled = currentPage <= 1;
      nextEl.disabled = currentPage >= totalPages;
      limiterEl.style.display = rows.length > pageSize ? "flex" : "none";
    }

    pageSizeEl.addEventListener("change", function () {
      pageSize = Number.parseInt(pageSizeEl.value, 10) || 5;
      currentPage = 1;
      render();
    });

    prevEl.addEventListener("click", function () {
      if (currentPage <= 1) {
        return;
      }

      currentPage -= 1;
      render();
    });

    nextEl.addEventListener("click", function () {
      const totalPages = getTotalPages();

      if (currentPage >= totalPages) {
        return;
      }

      currentPage += 1;
      render();
    });

    render();
  }

  //###################################################################################
  // (7) VISIBILIDADE DO FORMULÁRIO COMPLETO
  //###################################################################################

  function obterElementosDetalhe_v1(formulario, linhasLogicas) {
    const elementos = [];

    linhasLogicas.forEach(function (linha) {
      linha.camposDaLinha.forEach(function (campo) {
        const linhaWrapper =
          campo.closest(".additional-field-row-equalized") ||
          campo.closest(".process-additional-field-row") ||
          campo;

        if (linhaWrapper && !elementos.includes(linhaWrapper)) {
          elementos.push(linhaWrapper);
        }
      });
    });

    Array.from(formulario.querySelectorAll("button")).forEach(function (botao) {
      const texto = normalizarTexto_v1(botao.textContent);
      const wrapper = botao.closest(".field") || botao.parentElement || botao;

      if ((texto === "+" || botao.type === "submit") && wrapper && !elementos.includes(wrapper)) {
        elementos.push(wrapper);
      }
    });

    Array.from(formulario.querySelectorAll(".form-action-row, .profile-edit-actions")).forEach(function (acao) {
      if (acao && !elementos.includes(acao)) {
        elementos.push(acao);
      }
    });

    return elementos;
  }

  function aplicarVisibilidadeDetalhe_v1(formulario, container, linhasLogicas, detalhesVisiveis) {
    const elementosDetalhe = obterElementosDetalhe_v1(formulario, linhasLogicas);

    elementosDetalhe.forEach(function (elemento) {
      elemento.classList.toggle("additional-fields-table-hidden-v1", !detalhesVisiveis);
    });

    container.classList.toggle("additional-fields-table-detail-open-v1", detalhesVisiveis);
  }

  //###################################################################################
  // (8) APLICAR TABELA
  //###################################################################################

  function aplicarTabela_v1() {
    if (aplicandoTabela_v1) {
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

    aplicandoTabela_v1 = true;

    try {
      injetarCssTabela_v1();

      Array.from(
        container.querySelectorAll(
          ".additional-fields-table-mode-v1, .additional-fields-compact-layout-v1, .additional-fields-compact-layout-v2, .additional-fields-compact-layout-v3, .additional-fields-group-v3, .additional-fields-group-v4, .additional-fields-group-v5, .additional-fields-subgroup-marker-v2"
        )
      ).forEach(function (layoutAntigo) {
        layoutAntigo.remove();
      });

      const linhasLogicas = obterLinhasLogicas_v1(container);
      const dadosTabela = criarDadosTabela_v1(linhasLogicas);
      const detalhesVisiveis = formulario.dataset.additionalFieldsDetailsOpen === "1";

      const blocoTabela = document.createElement("div");
      blocoTabela.className = "additional-fields-table-mode-v1";
      blocoTabela.innerHTML = renderizarTabela_v1(dadosTabela, detalhesVisiveis);
      inicializarPaginacaoTabela_v1(blocoTabela);

      if (linhasLogicas.length && linhasLogicas[0].camposDaLinha.length) {
        const primeiroCampo = linhasLogicas[0].camposDaLinha[0];
        const primeiroWrapper =
          primeiroCampo.closest(".additional-field-row-equalized") ||
          primeiroCampo.closest(".process-additional-field-row") ||
          primeiroCampo;

        container.insertBefore(blocoTabela, primeiroWrapper);
      } else {
        container.prepend(blocoTabela);
      }

      aplicarVisibilidadeDetalhe_v1(formulario, container, linhasLogicas, detalhesVisiveis);

      Array.from(blocoTabela.querySelectorAll("[data-table-toggle-fields-v1], [data-table-edit-fields-v1]")).forEach(function (botao) {
        botao.addEventListener("click", function () {
          formulario.dataset.additionalFieldsDetailsOpen = detalhesVisiveis ? "0" : "1";
          aplicarTabela_v1();
        });
      });
    } finally {
      aplicandoTabela_v1 = false;
    }
  }

  //###################################################################################
  // (9) EVENTOS
  //###################################################################################

  function observarAlteracoes_v1() {
    const formulario = obterFormularioCamposAdicionais_v1();

    if (!formulario || formulario.dataset.additionalFieldsTableObserverV1 === "1") {
      return;
    }

    formulario.dataset.additionalFieldsTableObserverV1 = "1";

    formulario.addEventListener("change", function () {
      window.setTimeout(aplicarTabela_v1, 80);
    });

    formulario.addEventListener("input", function () {
      window.setTimeout(aplicarTabela_v1, 80);
    });
  }

  //###################################################################################
  // (10) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v1() {
    aplicarTabela_v1();
    observarAlteracoes_v1();

    window.setTimeout(aplicarTabela_v1, 100);
    window.setTimeout(aplicarTabela_v1, 400);
    window.setTimeout(aplicarTabela_v1, 1000);
    window.setTimeout(aplicarTabela_v1, 1800);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v1);
  } else {
    inicializar_v1();
  }
})();
