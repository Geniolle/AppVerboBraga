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
const descricao = document.createElement("p");
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";
tituloBloco.appendChild(descricao);

    const criarBtn = document.createElement("button");
    criarBtn.type = "button";
    criarBtn.className = "appverbo-sidebar-section-create-btn-v2";
    criarBtn.textContent = "Criar sessão";

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
    gravar.textContent = "Guardar";

    const cancelar = document.createElement("button");
    cancelar.type = "button";
    cancelar.className = "action-btn-cancel appverbo-sidebar-section-cancel-btn-v3";
    cancelar.textContent = "Cancelar";
    cancelar.addEventListener("click", function () {
      window.location.assign("/users/new?menu=administrativo&admin_tab=contas#admin-sidebar-sections-card");
    });

    footer.appendChild(gravar);
    if (typeof cancelar !== "undefined" && cancelar) {
      footer.appendChild(cancelar);
    }
    footer.appendChild(nota);

    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_menu", "administrativo"));
    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_target", "#admin-sidebar-sections-card"));
    wrapper.appendChild(cabecalho);

    const createEntrySlot = document.createElement("div");
    createEntrySlot.className = "appverbo-create-entry-slot-v2";
    wrapper.appendChild(createEntrySlot);

    const listBlock = document.createElement("div");
    listBlock.className = "appverbo-list-block-v2";
    listBlock.appendChild(tableWrap);
    listBlock.appendChild(footer);
    wrapper.appendChild(listBlock);

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
    aplicarBlocoCriacaoSessoes_v1(formulario, wrapper);

    const cardListaSessoesV3 = formulario.closest(".card, section");
    moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardListaSessoesV3, wrapper);

    return wrapper;
  }

  // APPVERBO_SESSOES_BOTOES_V3_START
  function removerBotaoVoltarListaSessoes_v3(card) {
    if (!card) {
      return;
    }

    const candidatos = Array.from(card.querySelectorAll("button, a"));

    candidatos.forEach(function (elemento) {
      const texto = normalizarTextoSessoesLayout_v2(elemento.textContent);

      if (texto === "voltar a lista" || texto === "voltar lista") {
        elemento.remove();
      }
    });
  }
  // APPVERBO_SESSOES_BOTOES_V3_END

  // APPVERBO_CREATE_ENTRY_BLOCK_SESSOES_V1_START
  function criarChaveUnicaSessoesCreateBlock_v1(tbody, nomeSessao, linhaAtual) {
    const baseKey = criarChaveSessoesLayout_v2(nomeSessao) || "nova_sessao";
    const keysExistentes = new Set();

    Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v2")).forEach(function (linha) {
      if (linha === linhaAtual) {
        return;
      }

      const keyInput = linha.querySelector('[name="section_key"]');
      const chave = String((keyInput && keyInput.value) || "").trim().toLowerCase();

      if (chave) {
        keysExistentes.add(chave);
      }
    });

    if (!keysExistentes.has(baseKey)) {
      return baseKey;
    }

    let contador = 2;
    let chaveFinal = baseKey + "_" + contador;

    while (keysExistentes.has(chaveFinal)) {
      contador += 1;
      chaveFinal = baseKey + "_" + contador;
    }

    return chaveFinal;
  }

  function aplicarBlocoCriacaoSessoes_v1(formulario, wrapper) {
    if (!formulario || !wrapper || wrapper.dataset.createEntryBlockV1 === "1") {
      return;
    }

    const originalCreateBtn = wrapper.querySelector(".appverbo-sidebar-section-create-btn-v2");
    const tableWrap = wrapper.querySelector(".appverbo-sidebar-sections-table-wrap-v2");
    const tbody = wrapper.querySelector(".appverbo-sidebar-sections-body-v2");

    if (!originalCreateBtn || !tableWrap || !tbody) {
      return;
    }

    wrapper.dataset.createEntryBlockV1 = "1";

    originalCreateBtn.hidden = true;
    originalCreateBtn.setAttribute("aria-hidden", "true");
    originalCreateBtn.classList.add("appverbo-create-entry-original-hidden-v1");

    const createBlock = document.createElement("div");
    createBlock.className = "appverbo-create-entry-block-v1";
    createBlock.dataset.createEntryBlock = "sessoes";

    const createToolbar = document.createElement("div");
    createToolbar.className = "appverbo-create-entry-toolbar-v1";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    createToolbar.appendChild(abrirBtn);

    const formPanel = document.createElement("div");
    formPanel.className = "appverbo-create-entry-panel-v1";
    formPanel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v1";

    const field = document.createElement("div");
    field.className = "field appverbo-create-entry-field-v1";

    const label = document.createElement("label");
    label.setAttribute("for", "appverbo-create-entry-session-name-v1");
    label.textContent = "Nome da sessão *";

    const input = document.createElement("input");
    input.id = "appverbo-create-entry-session-name-v1";
    input.type = "text";
    input.maxLength = 80;
    input.placeholder = "Informe o nome da sessão";

    const error = document.createElement("p");
    error.className = "appverbo-create-entry-error-v1";
    error.hidden = true;
    error.textContent = "Informe o nome da sessão.";

    field.appendChild(label);
    field.appendChild(input);
    field.appendChild(error);
    grid.appendChild(field);

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v1";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-create-entry-save-btn-v1";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-create-entry-cancel-btn-v1";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    formPanel.appendChild(grid);
    formPanel.appendChild(actions);

    createBlock.appendChild(createToolbar);
    createBlock.appendChild(formPanel);

    const createEntrySlot = wrapper.querySelector(".appverbo-create-entry-slot-v2");

    if (createEntrySlot) {
      createEntrySlot.appendChild(createBlock);
    } else {
      const createEntrySlot = wrapper.querySelector(".appverbo-create-entry-slot-v2");

    if (createEntrySlot) {
      createEntrySlot.appendChild(createBlock);
    } else {
      wrapper.insertBefore(createBlock, tableWrap);
    }
    }

    function abrirFormularioCriacao() {
      formPanel.hidden = false;
      abrirBtn.hidden = true;
      error.hidden = true;
      input.classList.remove("appverbo-create-entry-input-error-v1");
      input.focus();
    }

    function fecharFormularioCriacao() {
      input.value = "";
      error.hidden = true;
      input.classList.remove("appverbo-create-entry-input-error-v1");
      formPanel.hidden = true;
      abrirBtn.hidden = false;
    }

    abrirBtn.addEventListener("click", abrirFormularioCriacao);

    cancelarBtn.addEventListener("click", function () {
      fecharFormularioCriacao();
    });

    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        guardarBtn.click();
      }

      if (event.key === "Escape") {
        event.preventDefault();
        cancelarBtn.click();
      }
    });

    guardarBtn.addEventListener("click", function () {
      const nomeSessao = String(input.value || "").trim();

      if (!nomeSessao) {
        error.hidden = false;
        input.classList.add("appverbo-create-entry-input-error-v1");
        input.focus();
        return;
      }

      originalCreateBtn.click();

      const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v2"));
      const novaLinha = linhas[linhas.length - 1];

      if (!novaLinha) {
        return;
      }

      const labelInput = novaLinha.querySelector('[name="section_label"]');
      const keyInput = novaLinha.querySelector('[name="section_key"]');
      const novaChave = criarChaveUnicaSessoesCreateBlock_v1(tbody, nomeSessao, novaLinha);

      if (labelInput) {
        labelInput.value = nomeSessao;
        labelInput.readOnly = true;
        labelInput.classList.remove("appverbo-sidebar-section-label-input-editing-v2");
        labelInput.dispatchEvent(new Event("input", {
          bubbles: true,
          cancelable: true
        }));
        labelInput.dispatchEvent(new Event("blur", {
          bubbles: true,
          cancelable: true
        }));
      }

      if (keyInput) {
        keyInput.value = novaChave;
        keyInput.dataset.generatedV2 = "1";
      }

      sincronizarLinhaSessoesLayout_v2(novaLinha);
      atualizarDetalheSessoesLayout_v2(novaLinha);
      atualizarEstadoBotoesSessoesLayout_v2(tbody);
      marcarAlteradoSessoesLayout_v2(formulario);

      fecharFormularioCriacao();

      if (typeof formulario.requestSubmit === "function") {
        formulario.requestSubmit();
      } else {
        formulario.submit();
      }
    });
  }
  // APPVERBO_CREATE_ENTRY_BLOCK_SESSOES_V1_END

  // APPVERBO_SESSOES_CREATE_CARD_SEPARADO_V3_START
  function obterOuCriarCardCriacaoSessoes_v3(cardLista) {
    if (!cardLista || !cardLista.parentElement) {
      return null;
    }

    let createCard = document.getElementById("admin-sidebar-sections-create-card");

    if (!createCard) {
      createCard = document.createElement("section");
      createCard.id = "admin-sidebar-sections-create-card";
      createCard.className = "card appverbo-sessoes-create-card-v3";
      createCard.dataset.menuScope = "administrativo";
      cardLista.parentElement.insertBefore(createCard, cardLista);
    }

    return createCard;
  }

  function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {
    const createBlock = wrapper && wrapper.querySelector(".appverbo-create-entry-block-v1");

    if (!cardLista || !wrapper || !createBlock) {
      return;
    }

    const createCard = obterOuCriarCardCriacaoSessoes_v3(cardLista);

    if (!createCard) {
      return;
    }

    if (createBlock.parentElement !== createCard) {
      createCard.appendChild(createBlock);
    }

    createCard.hidden = false;
    createCard.style.display = "";

    const slotsVazios = Array.from(wrapper.querySelectorAll(".appverbo-create-entry-slot-v2"));

    slotsVazios.forEach(function (slot) {
      if (!slot.children.length) {
        slot.remove();
      }
    });
  }
  // APPVERBO_SESSOES_CREATE_CARD_SEPARADO_V3_END

  //###################################################################################
  // (6) INSTALAR LAYOUT
  //###################################################################################

  function instalarLayoutSessoes_v2() {
    const card = obterCardSessoesLayout_v2();

    if (!card) {
      return;
    }

    removerBotaoVoltarListaSessoes_v3(card);

    if (card.dataset.sidebarSectionsLayoutV2 === "1") {
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
