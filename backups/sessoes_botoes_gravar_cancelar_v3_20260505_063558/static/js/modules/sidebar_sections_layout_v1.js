(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesLayout_v2(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesLayout_v2(valor) {
    return normalizarTextoSessoesLayout_v2(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function tituloSessoesLayout_v2(valor, padrao) {
    const texto = String(valor || "").trim();
    return texto || padrao || "";
  }

  function labelPorChaveSessoesLayout_v2(chave) {
    const mapa = {
      sistema: "Sistema",
      geral: "Geral",
      dados_gerais: "Dados gerais",
      igreja: "Igreja",
      tesouraria: "Tesouraria"
    };

    const cleanChave = criarChaveSessoesLayout_v2(chave);

    if (mapa[cleanChave]) {
      return mapa[cleanChave];
    }

    return String(cleanChave || "nova_pasta")
      .replace(/_/g, " ")
      .replace(/^./, function (letra) {
        return letra.toUpperCase();
      });
  }

  //###################################################################################
  // (2) LER CONFIGURACAO VINDO DO BD
  //###################################################################################

  function lerSessoesDoTemplate_v2() {
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("Não foi possível ler sidebar_section_options do template.", error);
      return [];
    }
  }

  function normalizarSessaoSessoesLayout_v2(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = tituloSessoesLayout_v2(
      sessao.label || sessao.name || sessao.title,
      ""
    );
    const key = criarChaveSessoesLayout_v2(
      sessao.key || sessao.section_key || sessao.menu_section || label
    );

    if (!label || !key) {
      return null;
    }

    return {
      key: key,
      label: label,
      visibility_scope_mode: tituloSessoesLayout_v2(
        sessao.visibility_scope_mode || sessao.scope_mode || sessao.scope || sessao.visibility,
        "all"
      ),
      visibility_scope_label: tituloSessoesLayout_v2(
        sessao.visibility_scope_label,
        ""
      )
    };
  }

  function obterSessoesBaseSessoesLayout_v2() {
    const sessoesDoBd = lerSessoesDoTemplate_v2()
      .map(normalizarSessaoSessoesLayout_v2)
      .filter(Boolean);

    if (sessoesDoBd.length) {
      return sessoesDoBd;
    }

    return [
      { key: "sistema", label: "Sistema", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" },
      { key: "geral", label: "Geral", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" },
      { key: "dados_gerais", label: "Dados gerais", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" },
      { key: "igreja", label: "Igreja", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" },
      { key: "tesouraria", label: "Tesouraria", visibility_scope_mode: "all", visibility_scope_label: "Owner e Legado" }
    ];
  }

  //###################################################################################
  // (3) LOCALIZAR CARD E FORMULARIO
  //###################################################################################

  function obterCardSessoesLayout_v2() {
    const cardPorId = document.getElementById("admin-sidebar-sections-card");

    if (cardPorId) {
      return cardPorId;
    }

    const cards = Array.from(document.querySelectorAll(".card, section"));

    return cards.find(function (card) {
      const texto = normalizarTextoSessoesLayout_v2(card.textContent);
      return texto.includes("sessoes do sidebar") || texto.includes("sessões do sidebar");
    }) || null;
  }

  function obterFormularioSessoesLayout_v2(card) {
    let formulario = card.querySelector('form[action*="/settings/menu/sidebar-sections"]') ||
      card.querySelector('form[action*="sidebar-sections"]');

    if (!formulario) {
      formulario = document.createElement("form");
      formulario.method = "post";
      formulario.action = "/settings/menu/sidebar-sections";
      card.appendChild(formulario);
    }

    formulario.method = "post";
    formulario.action = "/settings/menu/sidebar-sections";

    return formulario;
  }

  function criarCampoOcultoSessoesLayout_v2(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  //###################################################################################
  // (4) SISTEMA, ESTADO E ACOES
  //###################################################################################

  function obterSistemaSessoesLayout_v2(sessao) {
    const scope = normalizarTextoSessoesLayout_v2(
      sessao.visibility_scope_mode || sessao.visibility_scope_label
    );

    if (scope === "owner") {
      return "Owner";
    }

    if (scope === "legado") {
      return "Legado";
    }

    return sessao.visibility_scope_label || "Owner e Legado";
  }

  function criarBotaoAcaoSessoesLayout_v2(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2";
    botao.dataset.sidebarSectionActionV2 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function atualizarEstadoBotoesSessoesLayout_v2(tbody) {
    const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v2"));

    linhas.forEach(function (linha, indice) {
      const botaoSubir = linha.querySelector('[data-sidebar-section-action-v2="up"]');
      const botaoDescer = linha.querySelector('[data-sidebar-section-action-v2="down"]');

      if (botaoSubir) {
        botaoSubir.disabled = indice === 0;
      }

      if (botaoDescer) {
        botaoDescer.disabled = indice === linhas.length - 1;
      }
    });
  }

  function marcarAlteradoSessoesLayout_v2(formulario) {
    const aviso = formulario.querySelector(".appverbo-sidebar-section-change-note-v2");

    formulario.dataset.sidebarSectionsChangedV2 = "1";

    if (aviso) {
      aviso.hidden = false;
    }
  }

  function sincronizarLinhaSessoesLayout_v2(linha) {
    const labelInput = linha.querySelector('[name="section_label"]');
    const keyInput = linha.querySelector('[name="section_key"]');
    const sistemaCell = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");

    if (!labelInput || !keyInput) {
      return;
    }

    if (!String(keyInput.value || "").trim() || keyInput.dataset.generatedV2 === "1") {
      keyInput.value = criarChaveSessoesLayout_v2(labelInput.value);
      keyInput.dataset.generatedV2 = "1";
    }

    if (sistemaCell) {
      sistemaCell.textContent = obterSistemaSessoesLayout_v2({
        visibility_scope_mode: linha.dataset.visibilityScopeModeV2 || "all",
        visibility_scope_label: linha.dataset.visibilityScopeLabelV2 || ""
      });
    }
  }

  function atualizarDetalheSessoesLayout_v2(linha) {
    const detalhe = linha.nextElementSibling;

    if (!detalhe || !detalhe.classList.contains("appverbo-sidebar-section-detail-row-v2")) {
      return;
    }

    const keyInput = linha.querySelector('[name="section_key"]');
    const labelInput = linha.querySelector('[name="section_label"]');
    const scopeInput = linha.querySelector('[name="section_visibility_scope_mode"]');
    const texto = detalhe.querySelector(".appverbo-sidebar-section-detail-text-v2");

    if (!texto) {
      return;
    }

    texto.textContent =
      "Chave: " +
      tituloSessoesLayout_v2(keyInput && keyInput.value, criarChaveSessoesLayout_v2(labelInput && labelInput.value)) +
      " | Visibilidade: " +
      tituloSessoesLayout_v2(scopeInput && scopeInput.value, "all");
  }

  function moverLinhaSessoesLayout_v2(linha, direcao) {
    const tbody = linha && linha.parentElement;

    if (!tbody) {
      return;
    }

    const detalhe = linha.nextElementSibling &&
      linha.nextElementSibling.classList.contains("appverbo-sidebar-section-detail-row-v2")
      ? linha.nextElementSibling
      : null;

    if (direcao === "up") {
      const detalheAnterior = linha.previousElementSibling;
      const linhaAnterior = detalheAnterior && detalheAnterior.classList.contains("appverbo-sidebar-section-detail-row-v2")
        ? detalheAnterior.previousElementSibling
        : detalheAnterior;

      if (linhaAnterior && linhaAnterior.classList.contains("appverbo-sidebar-section-row-v2")) {
        tbody.insertBefore(linha, linhaAnterior);
        if (detalhe) {
          tbody.insertBefore(detalhe, linha.nextElementSibling);
        }
      }
    }

    if (direcao === "down") {
      const proximaLinha = detalhe ? detalhe.nextElementSibling : linha.nextElementSibling;

      if (proximaLinha && proximaLinha.classList.contains("appverbo-sidebar-section-row-v2")) {
        const proximoDetalhe = proximaLinha.nextElementSibling &&
          proximaLinha.nextElementSibling.classList.contains("appverbo-sidebar-section-detail-row-v2")
          ? proximaLinha.nextElementSibling
          : null;

        tbody.insertBefore(proximaLinha, linha);
        if (proximoDetalhe) {
          tbody.insertBefore(proximoDetalhe, linha);
        }
      }
    }

    atualizarEstadoBotoesSessoesLayout_v2(tbody);
    marcarAlteradoSessoesLayout_v2(linha.closest("form"));
  }

  function alternarDetalheSessoesLayout_v2(linha) {
    const detalhe = linha.nextElementSibling;

    if (!detalhe || !detalhe.classList.contains("appverbo-sidebar-section-detail-row-v2")) {
      return;
    }

    atualizarDetalheSessoesLayout_v2(linha);
    detalhe.hidden = !detalhe.hidden;
  }

  function editarLinhaSessoesLayout_v2(linha) {
    const labelInput = linha.querySelector('[name="section_label"]');

    if (!labelInput) {
      return;
    }

    labelInput.readOnly = false;
    labelInput.classList.add("appverbo-sidebar-section-label-input-editing-v2");
    labelInput.focus();
    labelInput.select();
  }

  //###################################################################################
  // (5) CRIAR TABELA
  //###################################################################################

  function criarLinhaTabelaSessoesLayout_v2(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2";
    tr.dataset.visibilityScopeModeV2 = sessao.visibility_scope_mode || "all";
    tr.dataset.visibilityScopeLabelV2 = sessao.visibility_scope_label || "";

    const keyInput = criarCampoOcultoSessoesLayout_v2("section_key", sessao.key);
    const scopeInput = criarCampoOcultoSessoesLayout_v2("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");

    const labelInput = document.createElement("input");
    labelInput.type = "text";
    labelInput.name = "section_label";
    labelInput.value = sessao.label;
    labelInput.readOnly = true;
    labelInput.className = "appverbo-sidebar-section-label-input-v2";

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(scopeInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterSistemaSessoesLayout_v2(sessao);

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";

    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2";
    badge.textContent = "Ativo";
    tdEstado.appendChild(badge);

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    const detalhe = document.createElement("tr");
    detalhe.className = "appverbo-sidebar-section-detail-row-v2";
    detalhe.hidden = true;

    const detalheCelula = document.createElement("td");
    detalheCelula.colSpan = 4;

    const detalheTexto = document.createElement("div");
    detalheTexto.className = "appverbo-sidebar-section-detail-text-v2";
    detalheCelula.appendChild(detalheTexto);
    detalhe.appendChild(detalheCelula);

    labelInput.addEventListener("input", function () {
      sincronizarLinhaSessoesLayout_v2(tr);
      atualizarDetalheSessoesLayout_v2(tr);
      marcarAlteradoSessoesLayout_v2(tr.closest("form"));
    });

    labelInput.addEventListener("blur", function () {
      labelInput.readOnly = true;
      labelInput.classList.remove("appverbo-sidebar-section-label-input-editing-v2");
      sincronizarLinhaSessoesLayout_v2(tr);
      atualizarDetalheSessoesLayout_v2(tr);
    });

    atualizarDetalheSessoesLayout_v2(tr);

    return {
      row: tr,
      detailRow: detalhe
    };
  }

  function criarTabelaSessoesLayout_v2(formulario, sessoes) {
    const wrapper = document.createElement("div");
    wrapper.className = "appverbo-sidebar-sections-layout-v2";

    const cabecalho = document.createElement("div");
    cabecalho.className = "appverbo-sidebar-sections-header-v2";

    const tituloBloco = document.createElement("div");
    tituloBloco.className = "appverbo-sidebar-sections-title-block-v2";

    const titulo = document.createElement("h2");
    titulo.textContent = "Definições";

    const descricao = document.createElement("p");
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";

    tituloBloco.appendChild(titulo);
    tituloBloco.appendChild(descricao);

    const criarBtn = document.createElement("button");
    criarBtn.type = "button";
    criarBtn.className = "appverbo-sidebar-section-create-btn-v2";
    criarBtn.textContent = "Criar pasta";

    cabecalho.appendChild(tituloBloco);
    cabecalho.appendChild(criarBtn);

    const tableWrap = document.createElement("div");
    tableWrap.className = "appverbo-sidebar-sections-table-wrap-v2";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2";

    sessoes.forEach(function (sessao) {
      const linha = criarLinhaTabelaSessoesLayout_v2(sessao);
      tbody.appendChild(linha.row);
      tbody.appendChild(linha.detailRow);
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);

    const footer = document.createElement("div");
    footer.className = "appverbo-sidebar-sections-footer-v2";

    const nota = document.createElement("p");
    nota.className = "appverbo-sidebar-section-change-note-v2";
    nota.hidden = true;
    nota.textContent = "Existem alterações por gravar.";

    const gravar = document.createElement("button");
    gravar.type = "submit";
    gravar.className = "action-btn";
    gravar.textContent = "Gravar alterações";

    footer.appendChild(nota);
    footer.appendChild(gravar);

    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_menu", "administrativo"));
    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_target", "#admin-sidebar-sections-card"));
    wrapper.appendChild(cabecalho);
    wrapper.appendChild(tableWrap);
    wrapper.appendChild(footer);

    criarBtn.addEventListener("click", function () {
      const contador = tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v2").length + 1;
      const novaSessao = {
        key: "nova_pasta_" + contador,
        label: "Nova pasta",
        visibility_scope_mode: "all",
        visibility_scope_label: "Owner e Legado"
      };

      const linha = criarLinhaTabelaSessoesLayout_v2(novaSessao);
      const keyInput = linha.row.querySelector('[name="section_key"]');

      if (keyInput) {
        keyInput.dataset.generatedV2 = "1";
      }

      tbody.appendChild(linha.row);
      tbody.appendChild(linha.detailRow);
      atualizarEstadoBotoesSessoesLayout_v2(tbody);
      editarLinhaSessoesLayout_v2(linha.row);
      marcarAlteradoSessoesLayout_v2(formulario);
    });

    tbody.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v2]");

      if (!botao) {
        return;
      }

      const acao = botao.dataset.sidebarSectionActionV2;
      const linha = botao.closest("tr.appverbo-sidebar-section-row-v2");

      if (!linha) {
        return;
      }

      if (acao === "up" || acao === "down") {
        moverLinhaSessoesLayout_v2(linha, acao);
      }

      if (acao === "view") {
        alternarDetalheSessoesLayout_v2(linha);
      }

      if (acao === "edit") {
        editarLinhaSessoesLayout_v2(linha);
      }
    });

    atualizarEstadoBotoesSessoesLayout_v2(tbody);

    return wrapper;
  }

  //###################################################################################
  // (6) INSTALAR LAYOUT
  //###################################################################################

  function instalarLayoutSessoes_v2() {
    const card = obterCardSessoesLayout_v2();

    if (!card || card.dataset.sidebarSectionsLayoutV2 === "1") {
      return;
    }

    const formulario = obterFormularioSessoesLayout_v2(card);
    const sessoes = obterSessoesBaseSessoesLayout_v2();

    if (!sessoes.length) {
      return;
    }

    card.dataset.sidebarSectionsLayoutV2 = "1";
    card.classList.add("appverbo-sidebar-sections-card-v2");

    Array.from(card.querySelectorAll(".appverbo-sidebar-sections-layout-v1, .appverbo-sidebar-sections-layout-v2"))
      .forEach(function (elemento) {
        elemento.remove();
      });

    while (formulario.firstChild) {
      formulario.removeChild(formulario.firstChild);
    }

    formulario.appendChild(criarTabelaSessoesLayout_v2(formulario, sessoes));
  }

  function iniciarSessoesLayout_v2() {
    instalarLayoutSessoes_v2();

    window.setTimeout(instalarLayoutSessoes_v2, 100);
    window.setTimeout(instalarLayoutSessoes_v2, 300);
    window.setTimeout(instalarLayoutSessoes_v2, 700);

    document.addEventListener("click", function () {
      window.setTimeout(instalarLayoutSessoes_v2, 50);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarSessoesLayout_v2);
  } else {
    iniciarSessoesLayout_v2();
  }
})();
