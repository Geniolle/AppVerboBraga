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
    const statusInput = criarCampoOcultoSessoesLayout_v2("section_status", sessao.status || (sessao.is_active === false ? "inativo" : "ativo"));

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
    tdMenu.appendChild(statusInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterSistemaSessoesLayout_v2(sessao);

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";

    const badge = document.createElement("span");
    const estadoSessao = normalizarEstadoSessoesCreate_v5(statusInput.value);
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-" + estadoSessao + "-v5";
    badge.textContent = obterLabelEstadoSessoesCreate_v5(estadoSessao);
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
    aplicarFormularioCriacaoCompletoSessoes_v4(formulario, wrapper);
    removerFooterListaSessoes_v4(wrapper);

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
      createCard.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v3";
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

  // APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_START
  function obterLabelVisibilidadeSessoesCreate_v5(valor) {
    const cleanValor = normalizarTextoSessoesLayout_v2(valor);

    if (cleanValor === "owner") {
      return "Owner";
    }

    if (cleanValor === "legado") {
      return "Legado";
    }

    return "Owner e Legado";
  }

  function normalizarEstadoSessoesCreate_v5(valor) {
    const cleanValor = normalizarTextoSessoesLayout_v2(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  function obterLabelEstadoSessoesCreate_v5(valor) {
    return normalizarEstadoSessoesCreate_v5(valor) === "inativo" ? "Inativo" : "Ativo";
  }

  function criarFieldCriacaoSessoes_v5(id, labelTexto, inputElement) {
    const field = document.createElement("div");
    field.className = "field appverbo-create-entry-field-v5";

    const label = document.createElement("label");
    label.setAttribute("for", id);
    label.textContent = labelTexto;

    inputElement.id = id;

    field.appendChild(label);
    field.appendChild(inputElement);

    return field;
  }

  function removerFooterListaSessoes_v5(wrapper) {
    if (!wrapper) {
      return;
    }

    Array.from(wrapper.querySelectorAll(".appverbo-sidebar-sections-footer-v2")).forEach(function (footer) {
      footer.remove();
    });
  }

  function criarChaveUnicaSessoesCreate_v5(tbody, nomeSessao, linhaAtual) {
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

  function aplicarFormularioCriacaoCompletoSessoes_v4(formulario, wrapper) {
    if (!formulario || !wrapper || wrapper.dataset.createFieldsNomeSistemaEstadoV5 === "1") {
      removerFooterListaSessoes_v5(wrapper);
      return;
    }

    const tbody = wrapper.querySelector(".appverbo-sidebar-sections-body-v2");
    const createBlock = document.querySelector("#admin-sidebar-sections-create-card .appverbo-create-entry-block-v1") ||
      wrapper.querySelector(".appverbo-create-entry-block-v1");

    if (!tbody || !createBlock) {
      removerFooterListaSessoes_v5(wrapper);
      return;
    }

    wrapper.dataset.createFieldsNomeSistemaEstadoV5 = "1";
    removerFooterListaSessoes_v5(wrapper);

    const toolbar = createBlock.querySelector(".appverbo-create-entry-toolbar-v1") || document.createElement("div");
    toolbar.className = "appverbo-create-entry-toolbar-v1";

    let abrirBtnAtual = toolbar.querySelector(".appverbo-create-entry-open-btn-v1, .action-btn");

    if (!abrirBtnAtual) {
      abrirBtnAtual = document.createElement("button");
      abrirBtnAtual.type = "button";
      toolbar.appendChild(abrirBtnAtual);
    }

    const abrirBtn = abrirBtnAtual.cloneNode(true);
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";
    abrirBtnAtual.replaceWith(abrirBtn);

    let formPanel = createBlock.querySelector(".appverbo-create-entry-panel-v1");

    if (!formPanel) {
      formPanel = document.createElement("div");
      formPanel.className = "appverbo-create-entry-panel-v1";
      createBlock.appendChild(formPanel);
    }

    formPanel.innerHTML = "";
    formPanel.hidden = true;

    if (!toolbar.parentElement) {
      createBlock.insertBefore(toolbar, createBlock.firstChild);
    }

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v5";

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";
    nomeInput.required = true;

    const sistemaSelect = document.createElement("select");
    sistemaSelect.required = true;

    [
      ["all", "Owner e Legado"],
      ["owner", "Owner"],
      ["legado", "Legado"]
    ].forEach(function (item) {
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];
      sistemaSelect.appendChild(option);
    });

    const estadoSelect = document.createElement("select");
    estadoSelect.required = true;

    [
      ["ativo", "Ativo"],
      ["inativo", "Inativo"]
    ].forEach(function (item) {
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];
      estadoSelect.appendChild(option);
    });

    grid.appendChild(criarFieldCriacaoSessoes_v5(
      "appverbo-create-entry-session-name-v5",
      "Nome da sessão *",
      nomeInput
    ));

    grid.appendChild(criarFieldCriacaoSessoes_v5(
      "appverbo-create-entry-session-system-v5",
      "Sistema *",
      sistemaSelect
    ));

    grid.appendChild(criarFieldCriacaoSessoes_v5(
      "appverbo-create-entry-session-status-v5",
      "Estado *",
      estadoSelect
    ));

    const error = document.createElement("p");
    error.className = "appverbo-create-entry-error-v5";
    error.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v5";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-create-entry-save-btn-v5";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-create-entry-cancel-btn-v5";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    formPanel.appendChild(grid);
    formPanel.appendChild(error);
    formPanel.appendChild(actions);

    function limparErros() {
      error.hidden = true;
      error.textContent = "";
      nomeInput.classList.remove("appverbo-create-entry-input-error-v5");
      sistemaSelect.classList.remove("appverbo-create-entry-input-error-v5");
      estadoSelect.classList.remove("appverbo-create-entry-input-error-v5");
    }

    function abrirFormulario() {
      limparErros();
      formPanel.hidden = false;
      abrirBtn.hidden = true;
      nomeInput.focus();
    }

    function fecharFormulario() {
      nomeInput.value = "";
      sistemaSelect.value = "all";
      estadoSelect.value = "ativo";
      limparErros();
      formPanel.hidden = true;
      abrirBtn.hidden = false;
    }

    function validarFormulario() {
      limparErros();

      const nomeSessao = String(nomeInput.value || "").trim();
      const sistema = String(sistemaSelect.value || "all").trim();
      const estado = normalizarEstadoSessoesCreate_v5(estadoSelect.value);

      if (!nomeSessao) {
        error.textContent = "Informe o nome da sessão.";
        error.hidden = false;
        nomeInput.classList.add("appverbo-create-entry-input-error-v5");
        nomeInput.focus();
        return null;
      }

      if (!sistema) {
        error.textContent = "Informe o sistema da sessão.";
        error.hidden = false;
        sistemaSelect.classList.add("appverbo-create-entry-input-error-v5");
        sistemaSelect.focus();
        return null;
      }

      if (!estado) {
        error.textContent = "Informe o estado da sessão.";
        error.hidden = false;
        estadoSelect.classList.add("appverbo-create-entry-input-error-v5");
        estadoSelect.focus();
        return null;
      }

      return {
        label: nomeSessao,
        key: criarChaveUnicaSessoesCreate_v5(tbody, nomeSessao, null),
        visibility_scope_mode: sistema,
        visibility_scope_label: obterLabelVisibilidadeSessoesCreate_v5(sistema),
        status: estado,
        is_active: estado === "ativo",
        status_label: obterLabelEstadoSessoesCreate_v5(estado)
      };
    }

    [nomeInput, sistemaSelect, estadoSelect].forEach(function (campo) {
      campo.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
          event.preventDefault();
          guardarBtn.click();
        }

        if (event.key === "Escape") {
          event.preventDefault();
          cancelarBtn.click();
        }
      });
    });

    abrirBtn.addEventListener("click", abrirFormulario);
    cancelarBtn.addEventListener("click", fecharFormulario);

    guardarBtn.addEventListener("click", function () {
      const dados = validarFormulario();

      if (!dados) {
        return;
      }

      const novaLinha = criarLinhaTabelaSessoesLayout_v2(dados);
      tbody.appendChild(novaLinha.row);
      tbody.appendChild(novaLinha.detailRow);

      atualizarDetalheSessoesLayout_v2(novaLinha.row);
      atualizarEstadoBotoesSessoesLayout_v2(tbody);
      marcarAlteradoSessoesLayout_v2(formulario);

      fecharFormulario();

      if (typeof formulario.requestSubmit === "function") {
        formulario.requestSubmit();
      } else {
        formulario.submit();
      }
    });
  }
  // APPVERBO_SESSOES_CREATE_FIELDS_BD_V4_END

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

// APPVERBO_SESSOES_REIDRATAR_LISTA_BD_V6_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV6(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesV6(valor) {
    return normalizarTextoSessoesV6(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesV6(valor) {
    const cleanValor = normalizarTextoSessoesV6(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  function obterLabelEstadoSessoesV6(valor) {
    return normalizarEstadoSessoesV6(valor) === "inativo" ? "Inativo" : "Ativo";
  }

  function obterLabelSistemaSessoesV6(valor, fallback) {
    const cleanValor = normalizarTextoSessoesV6(valor);

    if (cleanValor === "owner") {
      return "Owner";
    }

    if (cleanValor === "legado") {
      return "Legado";
    }

    return fallback || "Owner e Legado";
  }

  function criarCampoOcultoSessoesV6(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  //###################################################################################
  // (2) LER SESSOES DO TEMPLATE OU DO ENDPOINT
  //###################################################################################

  function lerSessoesDoTemplateSessoesV6() {
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("APPVERBO V6: não foi possível ler sessões do template.", error);
      return [];
    }
  }

  async function carregarSessoesBdSessoesV6() {
    const sessoesTemplate = lerSessoesDoTemplateSessoesV6();

    if (sessoesTemplate.length) {
      return sessoesTemplate;
    }

    try {
      const response = await fetch("/settings/menu/sidebar-sections-data", {
        headers: {
          Accept: "application/json"
        },
        credentials: "same-origin"
      });

      if (!response.ok) {
        console.warn("APPVERBO V6: endpoint de sessões respondeu com erro.", response.status);
        return [];
      }

      const payload = await response.json();

      if (payload && Array.isArray(payload.sections)) {
        return payload.sections;
      }
    } catch (error) {
      console.warn("APPVERBO V6: falha ao consultar sessões do BD.", error);
    }

    return [];
  }

  function normalizarSessaoSessoesV6(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesV6(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    const sistema = String(sessao.visibility_scope_mode || sessao.scope_mode || sessao.scope || "all").trim() || "all";
    const estado = normalizarEstadoSessoesV6(
      sessao.status || (sessao.is_active === false ? "inativo" : "ativo")
    );

    return {
      key: key,
      label: label,
      visibility_scope_mode: sistema,
      visibility_scope_label: obterLabelSistemaSessoesV6(sistema, sessao.visibility_scope_label || ""),
      status: estado,
      is_active: estado === "ativo",
      status_label: obterLabelEstadoSessoesV6(estado)
    };
  }

  //###################################################################################
  // (3) CRIAR TABELA DA LISTAGEM
  //###################################################################################

  function criarBotaoAcaoSessoesV6(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2 appverbo-sidebar-section-action-btn-v6";
    botao.dataset.sidebarSectionActionV6 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  // APPVERBO_SESSOES_EDIT_INLINE_V8_START
  function criarSelectSistemaSessoesV8(valorAtual) {
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v8";

    [
      ["all", "Owner e Legado"],
      ["owner", "Owner"],
      ["legado", "Legado"]
    ].forEach(function (item) {
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];

      if (String(valorAtual || "all") === item[0]) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function criarSelectEstadoSessoesV8(valorAtual) {
    const estadoAtual = normalizarEstadoSessoesV6(valorAtual);
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v8";

    [
      ["ativo", "Ativo"],
      ["inativo", "Inativo"]
    ].forEach(function (item) {
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];

      if (estadoAtual === item[0]) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function obterCamposLinhaSessoesV8(linha) {
    return {
      keyInput: linha.querySelector('[name="section_key"]'),
      labelInput: linha.querySelector('[name="section_label"]'),
      scopeInput: linha.querySelector('[name="section_visibility_scope_mode"]'),
      statusInput: linha.querySelector('[name="section_status"]')
    };
  }

  function criarBadgeEstadoSessoesV8(estado) {
    const estadoNormalizado = normalizarEstadoSessoesV6(estado);
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-" + estadoNormalizado + "-v6";
    badge.textContent = obterLabelEstadoSessoesV6(estadoNormalizado);
    return badge;
  }

  function restaurarAcoesLinhaSessoesV8(linha, tbody) {
    const tdAcoes = linha.querySelector(".appverbo-sidebar-section-actions-cell-v2");

    if (!tdAcoes) {
      return;
    }

    tdAcoes.innerHTML = "";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoSessoesV6("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoSessoesV6("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoSessoesV6("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoSessoesV6("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);
    atualizarEstadoBotoesSessoesV6(tbody);
  }

  function restaurarLinhaSessoesV8(linha, valores, tbody) {
    const campos = obterCamposLinhaSessoesV8(linha);
    const tdMenu = linha.querySelector(".appverbo-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appverbo-sidebar-section-state-cell-v2");

    if (!campos.keyInput || !campos.labelInput || !campos.scopeInput || !campos.statusInput || !tdMenu || !tdSistema || !tdEstado) {
      return;
    }

    campos.keyInput.value = valores.key;
    campos.labelInput.value = valores.label;
    campos.scopeInput.value = valores.scope;
    campos.statusInput.value = valores.status;

    tdMenu.innerHTML = "";
    tdMenu.textContent = valores.label;
    tdMenu.appendChild(campos.keyInput);
    tdMenu.appendChild(campos.labelInput);
    tdMenu.appendChild(campos.scopeInput);
    tdMenu.appendChild(campos.statusInput);

    tdSistema.innerHTML = "";
    tdSistema.textContent = obterLabelSistemaSessoesV6(valores.scope, valores.scopeLabel || "");

    tdEstado.innerHTML = "";
    tdEstado.appendChild(criarBadgeEstadoSessoesV8(valores.status));

    linha.dataset.editingV8 = "0";
    restaurarAcoesLinhaSessoesV8(linha, tbody);
  }

  function abrirEdicaoLinhaSessoesV8(linha, formulario, tbody) {
    if (!linha || linha.dataset.editingV8 === "1") {
      return;
    }

    const campos = obterCamposLinhaSessoesV8(linha);
    const tdMenu = linha.querySelector(".appverbo-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appverbo-sidebar-section-state-cell-v2");
    const tdAcoes = linha.querySelector(".appverbo-sidebar-section-actions-cell-v2");

    if (!campos.keyInput || !campos.labelInput || !campos.scopeInput || !campos.statusInput || !tdMenu || !tdSistema || !tdEstado || !tdAcoes) {
      return;
    }

    linha.dataset.editingV8 = "1";

    const valoresOriginais = {
      key: String(campos.keyInput.value || "").trim(),
      label: String(campos.labelInput.value || "").trim(),
      scope: String(campos.scopeInput.value || "all").trim(),
      scopeLabel: obterLabelSistemaSessoesV6(campos.scopeInput.value || "all", ""),
      status: normalizarEstadoSessoesV6(campos.statusInput.value || "ativo")
    };

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.className = "appverbo-sidebar-section-edit-input-v8";
    nomeInput.value = valoresOriginais.label;
    nomeInput.maxLength = 80;

    const sistemaSelect = criarSelectSistemaSessoesV8(valoresOriginais.scope);
    const estadoSelect = criarSelectEstadoSessoesV8(valoresOriginais.status);

    tdMenu.innerHTML = "";
    tdMenu.appendChild(nomeInput);
    tdMenu.appendChild(campos.keyInput);
    tdMenu.appendChild(campos.labelInput);
    tdMenu.appendChild(campos.scopeInput);
    tdMenu.appendChild(campos.statusInput);

    tdSistema.innerHTML = "";
    tdSistema.appendChild(sistemaSelect);

    tdEstado.innerHTML = "";
    tdEstado.appendChild(estadoSelect);

    tdAcoes.innerHTML = "";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-edit-actions-v8";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-sidebar-section-edit-save-v8";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-sidebar-section-edit-cancel-v8";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);
    tdAcoes.appendChild(actions);

    function validarNome() {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        nomeInput.classList.add("appverbo-sidebar-section-edit-input-error-v8");
        nomeInput.focus();
        return "";
      }

      nomeInput.classList.remove("appverbo-sidebar-section-edit-input-error-v8");
      return nome;
    }

    guardarBtn.addEventListener("click", function () {
      const nome = validarNome();

      if (!nome) {
        return;
      }

      const valoresAtualizados = {
        key: valoresOriginais.key || criarChaveSessoesV6(nome),
        label: nome,
        scope: String(sistemaSelect.value || "all").trim(),
        scopeLabel: obterLabelSistemaSessoesV6(sistemaSelect.value || "all", ""),
        status: normalizarEstadoSessoesV6(estadoSelect.value || "ativo")
      };

      restaurarLinhaSessoesV8(linha, valoresAtualizados, tbody);
      submeterFormularioSessoesV6(formulario);
    });

    cancelarBtn.addEventListener("click", function () {
      restaurarLinhaSessoesV8(linha, valoresOriginais, tbody);
    });

    nomeInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        guardarBtn.click();
      }

      if (event.key === "Escape") {
        event.preventDefault();
        cancelarBtn.click();
      }
    });

    sistemaSelect.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        cancelarBtn.click();
      }
    });

    estadoSelect.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        cancelarBtn.click();
      }
    });

    nomeInput.focus();
    nomeInput.select();
  }

  // APPVERBO_SESSOES_EDIT_INLINE_V8_END

  function criarLinhaSessoesV6(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2 appverbo-sidebar-section-row-v6";

    const keyInput = criarCampoOcultoSessoesV6("section_key", sessao.key);
    const labelInput = document.createElement("input");
    labelInput.type = "hidden";
    labelInput.name = "section_label";
    labelInput.value = sessao.label;

    const scopeInput = criarCampoOcultoSessoesV6("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");
    const statusInput = criarCampoOcultoSessoesV6("section_status", sessao.status || "ativo");

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(scopeInput);
    tdMenu.appendChild(statusInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterLabelSistemaSessoesV6(
      sessao.visibility_scope_mode,
      sessao.visibility_scope_label || "Owner e Legado"
    );

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";

    const estado = normalizarEstadoSessoesV6(sessao.status);
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-" + estado + "-v6";
    badge.textContent = obterLabelEstadoSessoesV6(estado);
    tdEstado.appendChild(badge);

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoSessoesV6("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoSessoesV6("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoSessoesV6("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoSessoesV6("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }

  function atualizarEstadoBotoesSessoesV6(tbody) {
    const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v6"));

    linhas.forEach(function (linha, indice) {
      const subir = linha.querySelector('[data-sidebar-section-action-v6="up"]');
      const descer = linha.querySelector('[data-sidebar-section-action-v6="down"]');

      if (subir) {
        subir.disabled = indice === 0;
      }

      if (descer) {
        descer.disabled = indice === linhas.length - 1;
      }
    });
  }

  function submeterFormularioSessoesV6(formulario) {
    if (!formulario) {
      return;
    }

    if (typeof formulario.requestSubmit === "function") {
      formulario.requestSubmit();
    } else {
      formulario.submit();
    }
  }

  function moverLinhaSessoesV6(linha, direcao) {
    const tbody = linha && linha.parentElement;

    if (!tbody) {
      return;
    }

    if (direcao === "up") {
      const anterior = linha.previousElementSibling;

      if (anterior && anterior.classList.contains("appverbo-sidebar-section-row-v6")) {
        tbody.insertBefore(linha, anterior);
      }
    }

    if (direcao === "down") {
      const proxima = linha.nextElementSibling;

      if (proxima && proxima.classList.contains("appverbo-sidebar-section-row-v6")) {
        tbody.insertBefore(proxima, linha);
      }
    }

    atualizarEstadoBotoesSessoesV6(tbody);
    submeterFormularioSessoesV6(linha.closest("form"));
  }

  function criarTabelaSessoesV6(formulario, sessoes) {
    formulario.innerHTML = "";
    formulario.method = "post";
    formulario.action = "/settings/menu/sidebar-sections";

    formulario.appendChild(criarCampoOcultoSessoesV6("redirect_menu", "administrativo"));
    formulario.appendChild(criarCampoOcultoSessoesV6("redirect_target", "#admin-sidebar-sections-card"));

    const descricao = document.createElement("p");
    descricao.className = "appverbo-sidebar-sections-list-description-v6";
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";

    const tableWrap = document.createElement("div");
    tableWrap.className = "appverbo-sidebar-sections-table-wrap-v2 appverbo-sidebar-sections-table-wrap-v6";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2 appverbo-sidebar-sections-table-v6";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2 appverbo-sidebar-sections-body-v6";

    sessoes.forEach(function (sessao) {
      tbody.appendChild(criarLinhaSessoesV6(sessao));
    });

    tbody.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v6]");

      if (!botao) {
        return;
      }

      const linha = botao.closest("tr.appverbo-sidebar-section-row-v6");
      const acao = botao.dataset.sidebarSectionActionV6;

      if (!linha) {
        return;
      }

      if (acao === "up" || acao === "down") {
        moverLinhaSessoesV6(linha, acao);
      }

      if (acao === "view") {
        const label = linha.querySelector('[name="section_label"]');
        const key = linha.querySelector('[name="section_key"]');
        const sistema = linha.querySelector('[name="section_visibility_scope_mode"]');
        const estado = linha.querySelector('[name="section_status"]');

        alert(
          "Nome da sessão: " + ((label && label.value) || "") +
          "\nChave: " + ((key && key.value) || "") +
          "\nSistema: " + obterLabelSistemaSessoesV6(sistema && sistema.value, "") +
          "\nEstado: " + obterLabelEstadoSessoesV6(estado && estado.value)
        );
      }

      if (acao === "edit") {
        abrirEdicaoLinhaSessoesV8(linha, formulario, tbody);
      }
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);

    formulario.appendChild(descricao);
    formulario.appendChild(tableWrap);

    atualizarEstadoBotoesSessoesV6(tbody);

    return tbody;
  }

  //###################################################################################
  // (4) CRIAR FORMULARIO DE CRIACAO GARANTINDO BD
  //###################################################################################

  function obterOuCriarCardCriacaoSessoesV6(cardLista) {
    if (!cardLista || !cardLista.parentElement) {
      return null;
    }

    let createCard = document.getElementById("admin-sidebar-sections-create-card");

    if (!createCard) {
      createCard = document.createElement("section");
      createCard.id = "admin-sidebar-sections-create-card";
      createCard.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v3";
      cardLista.parentElement.insertBefore(createCard, cardLista);
    }

    return createCard;
  }

  function criarOpcaoSelectSessoesV6(valor, texto) {
    const option = document.createElement("option");
    option.value = valor;
    option.textContent = texto;
    return option;
  }

  function instalarCriacaoSessoesV6(cardLista, formulario, tbody) {
    const createCard = obterOuCriarCardCriacaoSessoesV6(cardLista);

    if (!createCard || !formulario || !tbody || createCard.dataset.createRepairV6 === "1") {
      return;
    }

    createCard.dataset.createRepairV6 = "1";
    createCard.innerHTML = "";

    const block = document.createElement("div");
    block.className = "appverbo-create-entry-block-v1 appverbo-create-entry-block-v6";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-create-entry-toolbar-v1";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appverbo-create-entry-panel-v1 appverbo-create-entry-panel-v6";
    panel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v5 appverbo-create-entry-grid-v6";

    const nomeField = document.createElement("div");
    nomeField.className = "field appverbo-create-entry-field-v5";

    const nomeLabel = document.createElement("label");
    nomeLabel.textContent = "Nome da sessão *";

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";

    nomeField.appendChild(nomeLabel);
    nomeField.appendChild(nomeInput);

    const sistemaField = document.createElement("div");
    sistemaField.className = "field appverbo-create-entry-field-v5";

    const sistemaLabel = document.createElement("label");
    sistemaLabel.textContent = "Sistema *";

    const sistemaSelect = document.createElement("select");
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV6("all", "Owner e Legado"));
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV6("owner", "Owner"));
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV6("legado", "Legado"));

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-create-entry-field-v5";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = document.createElement("select");
    estadoSelect.appendChild(criarOpcaoSelectSessoesV6("ativo", "Ativo"));
    estadoSelect.appendChild(criarOpcaoSelectSessoesV6("inativo", "Inativo"));

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const erro = document.createElement("p");
    erro.className = "appverbo-create-entry-error-v5";
    erro.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v5";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    panel.appendChild(grid);
    panel.appendChild(erro);
    panel.appendChild(actions);

    block.appendChild(toolbar);
    block.appendChild(panel);
    createCard.appendChild(block);

    function limparCriacao() {
      nomeInput.value = "";
      sistemaSelect.value = "all";
      estadoSelect.value = "ativo";
      erro.hidden = true;
      erro.textContent = "";
      panel.hidden = true;
      abrirBtn.hidden = false;
    }

    abrirBtn.addEventListener("click", function () {
      erro.hidden = true;
      panel.hidden = false;
      abrirBtn.hidden = true;
      nomeInput.focus();
    });

    cancelarBtn.addEventListener("click", limparCriacao);

    guardarBtn.addEventListener("click", function () {
      const nomeSessao = String(nomeInput.value || "").trim();

      if (!nomeSessao) {
        erro.textContent = "Informe o nome da sessão.";
        erro.hidden = false;
        nomeInput.focus();
        return;
      }

      const novaSessao = {
        label: nomeSessao,
        key: criarChaveSessoesV6(nomeSessao),
        visibility_scope_mode: sistemaSelect.value || "all",
        visibility_scope_label: obterLabelSistemaSessoesV6(sistemaSelect.value || "all", ""),
        status: normalizarEstadoSessoesV6(estadoSelect.value || "ativo"),
        is_active: normalizarEstadoSessoesV6(estadoSelect.value || "ativo") === "ativo"
      };

      tbody.appendChild(criarLinhaSessoesV6(novaSessao));
      atualizarEstadoBotoesSessoesV6(tbody);
      limparCriacao();
      submeterFormularioSessoesV6(formulario);
    });
  }

  //###################################################################################
  // (5) INSTALAR REIDRATACAO
  //###################################################################################

  async function reidratarSessoesBdV6(force) {
    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card) {
      return;
    }

    const linhasAtuais = card.querySelectorAll("tr.appverbo-sidebar-section-row-v2, tr.appverbo-sidebar-section-row-v6");

    if (!force && linhasAtuais.length > 0 && card.dataset.rehydratedFromBdV6 === "1") {
      return;
    }

    const sessoesRaw = await carregarSessoesBdSessoesV6();
    const sessoes = sessoesRaw.map(normalizarSessaoSessoesV6).filter(Boolean);

    if (!sessoes.length) {
      console.warn("APPVERBO V6: nenhuma sessão retornada do BD/template.");
      return;
    }

    card.dataset.rehydratedFromBdV6 = "1";

    let formulario = card.querySelector('form[action*="/settings/menu/sidebar-sections"], form[action*="sidebar-sections"]');

    if (!formulario) {
      formulario = document.createElement("form");
      card.appendChild(formulario);
    }

    const tituloExistente = card.querySelector("h1, h2, h3");

    if (!tituloExistente) {
      const titulo = document.createElement("h2");
      titulo.textContent = "Sessoes do sidebar";
      card.insertBefore(titulo, formulario);
    }

    const tbody = criarTabelaSessoesV6(formulario, sessoes);
    instalarCriacaoSessoesV6(card, formulario, tbody);
  }

  function iniciarReidratacaoSessoesV6() {
    window.setTimeout(function () {
      reidratarSessoesBdV6(false);
    }, 300);

    window.setTimeout(function () {
      const card = document.getElementById("admin-sidebar-sections-card");
      const linhas = card ? card.querySelectorAll("tr.appverbo-sidebar-section-row-v2, tr.appverbo-sidebar-section-row-v6") : [];

      if (!linhas || linhas.length === 0) {
        reidratarSessoesBdV6(true);
      }
    }, 900);

    window.setTimeout(function () {
      const card = document.getElementById("admin-sidebar-sections-card");
      const linhas = card ? card.querySelectorAll("tr.appverbo-sidebar-section-row-v2, tr.appverbo-sidebar-section-row-v6") : [];

      if (!linhas || linhas.length === 0) {
        reidratarSessoesBdV6(true);
      }
    }, 1600);

    document.addEventListener("click", function () {
      window.setTimeout(function () {
        const card = document.getElementById("admin-sidebar-sections-card");
        const linhas = card ? card.querySelectorAll("tr.appverbo-sidebar-section-row-v2, tr.appverbo-sidebar-section-row-v6") : [];

        if (!linhas || linhas.length === 0) {
          reidratarSessoesBdV6(true);
        }
      }, 120);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarReidratacaoSessoesV6);
  } else {
    iniciarReidratacaoSessoesV6();
  }
})();
// APPVERBO_SESSOES_REIDRATAR_LISTA_BD_V6_END

// APPVERBO_SESSOES_ESTADO_BLOCOS_V9_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesEstadoV9(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesEstadoV9(valor) {
    return normalizarTextoSessoesEstadoV9(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesEstadoV9(valor) {
    const cleanValor = normalizarTextoSessoesEstadoV9(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  function obterLabelEstadoSessoesEstadoV9(valor) {
    return normalizarEstadoSessoesEstadoV9(valor) === "inativo" ? "Inativo" : "Ativo";
  }

  function obterLabelSistemaSessoesEstadoV9(valor, fallback) {
    const cleanValor = normalizarTextoSessoesEstadoV9(valor);

    if (cleanValor === "owner") {
      return "Owner";
    }

    if (cleanValor === "legado") {
      return "Legado";
    }

    return fallback || "Owner e Legado";
  }

  function criarCampoOcultoSessoesEstadoV9(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  //###################################################################################
  // (2) ESTADO LOCAL E LEITURA DO BD/TEMPLATE
  //###################################################################################

  let sessoesEstadoV9 = [];
  let instaladoEstadoV9 = false;

  function lerSessoesTemplateEstadoV9() {
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn("APPVERBO V9: não foi possível ler sessões do template.", error);
      return [];
    }
  }

  async function carregarSessoesEstadoV9() {
    const sessoesTemplate = lerSessoesTemplateEstadoV9();

    if (sessoesTemplate.length) {
      return sessoesTemplate;
    }

    try {
      const response = await fetch("/settings/menu/sidebar-sections-data", {
        headers: {
          Accept: "application/json"
        },
        credentials: "same-origin"
      });

      if (!response.ok) {
        return [];
      }

      const payload = await response.json();

      if (payload && Array.isArray(payload.sections)) {
        return payload.sections;
      }
    } catch (error) {
      console.warn("APPVERBO V9: falha ao carregar sessões do BD.", error);
    }

    return [];
  }

  function normalizarSessaoEstadoV9(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesEstadoV9(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    const sistema = String(sessao.visibility_scope_mode || sessao.scope_mode || "all").trim() || "all";
    const estado = normalizarEstadoSessoesEstadoV9(
      sessao.status || (sessao.is_active === false ? "inativo" : "ativo")
    );

    return {
      key: key,
      label: label,
      visibility_scope_mode: sistema,
      visibility_scope_label: obterLabelSistemaSessoesEstadoV9(sistema, sessao.visibility_scope_label || ""),
      status: estado,
      is_active: estado === "ativo",
      status_label: obterLabelEstadoSessoesEstadoV9(estado)
    };
  }

  function encontrarIndiceSessaoEstadoV9(chave) {
    const cleanChave = criarChaveSessoesEstadoV9(chave);

    return sessoesEstadoV9.findIndex(function (sessao) {
      return criarChaveSessoesEstadoV9(sessao.key) === cleanChave;
    });
  }

  function gerarChaveUnicaEstadoV9(nomeSessao) {
    const baseKey = criarChaveSessoesEstadoV9(nomeSessao) || "nova_sessao";
    const usadas = new Set(
      sessoesEstadoV9.map(function (sessao) {
        return criarChaveSessoesEstadoV9(sessao.key);
      })
    );

    if (!usadas.has(baseKey)) {
      return baseKey;
    }

    let contador = 2;
    let chaveFinal = baseKey + "_" + contador;

    while (usadas.has(chaveFinal)) {
      contador += 1;
      chaveFinal = baseKey + "_" + contador;
    }

    return chaveFinal;
  }

  //###################################################################################
  // (3) ELEMENTOS BASE
  //###################################################################################

  function obterCardListaEstadoV9() {
    return document.getElementById("admin-sidebar-sections-card");
  }

  function obterOuCriarFormularioEstadoV9(cardLista) {
    let formulario = cardLista.querySelector('form[action*="/settings/menu/sidebar-sections"], form[action*="sidebar-sections"]');

    if (!formulario) {
      formulario = document.createElement("form");
      cardLista.appendChild(formulario);
    }

    formulario.method = "post";
    formulario.action = "/settings/menu/sidebar-sections";

    return formulario;
  }

  function obterOuCriarCardCriacaoEstadoV9(cardLista) {
    let createCard = document.getElementById("admin-sidebar-sections-create-card");

    if (!createCard) {
      createCard = document.createElement("section");
      createCard.id = "admin-sidebar-sections-create-card";
      createCard.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v3 appverbo-sessoes-create-card-v9";
      cardLista.parentElement.insertBefore(createCard, cardLista);
    }

    return createCard;
  }

  function submeterFormularioEstadoV9() {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista) {
      return;
    }

    const formulario = obterOuCriarFormularioEstadoV9(cardLista);

    if (typeof formulario.requestSubmit === "function") {
      formulario.requestSubmit();
    } else {
      formulario.submit();
    }
  }

  //###################################################################################
  // (4) CONTROLES
  //###################################################################################

  function criarBotaoAcaoEstadoV9(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v2 appverbo-sidebar-section-action-btn-v9";
    botao.dataset.sidebarSectionActionV9 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function criarSelectSistemaEstadoV9(valorAtual) {
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v9";

    [
      ["all", "Owner e Legado"],
      ["owner", "Owner"],
      ["legado", "Legado"]
    ].forEach(function (item) {
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];

      if (String(valorAtual || "all") === item[0]) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function criarSelectEstadoEstadoV9(valorAtual) {
    const select = document.createElement("select");
    select.className = "appverbo-sidebar-section-edit-select-v9";
    const estadoAtual = normalizarEstadoSessoesEstadoV9(valorAtual);

    [
      ["ativo", "Ativo"],
      ["inativo", "Inativo"]
    ].forEach(function (item) {
      const option = document.createElement("option");
      option.value = item[0];
      option.textContent = item[1];

      if (estadoAtual === item[0]) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function criarBadgeEstadoV9(estado) {
    const estadoNormalizado = normalizarEstadoSessoesEstadoV9(estado);
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v2 appverbo-sidebar-section-state-badge-" + estadoNormalizado + "-v9";
    badge.textContent = obterLabelEstadoSessoesEstadoV9(estadoNormalizado);
    return badge;
  }

  //###################################################################################
  // (5) LINHAS E TABELAS
  //###################################################################################

  function criarLinhaEstadoV9(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v2 appverbo-sidebar-section-row-v9";
    tr.dataset.sectionKeyV9 = sessao.key;
    tr.dataset.sectionStatusV9 = normalizarEstadoSessoesEstadoV9(sessao.status);

    const keyInput = criarCampoOcultoSessoesEstadoV9("section_key", sessao.key);
    const labelInput = criarCampoOcultoSessoesEstadoV9("section_label", sessao.label);
    const scopeInput = criarCampoOcultoSessoesEstadoV9("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");
    const statusInput = criarCampoOcultoSessoesEstadoV9("section_status", normalizarEstadoSessoesEstadoV9(sessao.status));

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(scopeInput);
    tdMenu.appendChild(statusInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterLabelSistemaSessoesEstadoV9(sessao.visibility_scope_mode, sessao.visibility_scope_label || "");

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v2";
    tdEstado.appendChild(criarBadgeEstadoV9(sessao.status));

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoEstadoV9("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoEstadoV9("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoEstadoV9("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoEstadoV9("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }

  function criarTabelaEstadoV9(titulo, sessoes, tipo) {
    const bloco = document.createElement("div");
    bloco.className = "appverbo-sidebar-section-list-block-v9 appverbo-sidebar-section-list-block-" + tipo + "-v9";

    if (titulo) {
      const h3 = document.createElement("h3");
      h3.className = "appverbo-sidebar-section-list-title-v9";
      h3.textContent = titulo;
      bloco.appendChild(h3);
    }

    const tableWrap = document.createElement("div");
    tableWrap.className = "appverbo-sidebar-sections-table-wrap-v2 appverbo-sidebar-sections-table-wrap-v9";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v2 appverbo-sidebar-sections-table-v9";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v2 appverbo-sidebar-sections-body-v9";
    tbody.dataset.statusGroupV9 = tipo;

    sessoes.forEach(function (sessao) {
      tbody.appendChild(criarLinhaEstadoV9(sessao));
    });

    if (!sessoes.length) {
      const emptyRow = document.createElement("tr");
      emptyRow.className = "appverbo-sidebar-section-empty-row-v9";

      const emptyCell = document.createElement("td");
      emptyCell.colSpan = 4;
      emptyCell.textContent = tipo === "inativo" ? "Sem sessões inativas." : "Sem sessões ativas.";

      emptyRow.appendChild(emptyCell);
      tbody.appendChild(emptyRow);
    }

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    bloco.appendChild(tableWrap);

    return bloco;
  }

  function atualizarEstadoBotoesEstadoV9(container) {
    const grupos = Array.from(container.querySelectorAll("tbody.appverbo-sidebar-sections-body-v9"));

    grupos.forEach(function (tbody) {
      const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v9"));

      linhas.forEach(function (linha, indice) {
        const subir = linha.querySelector('[data-sidebar-section-action-v9="up"]');
        const descer = linha.querySelector('[data-sidebar-section-action-v9="down"]');

        if (subir) {
          subir.disabled = indice === 0;
        }

        if (descer) {
          descer.disabled = indice === linhas.length - 1;
        }
      });
    });
  }

  function renderizarListaEstadoV9() {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista) {
      return;
    }

    const formulario = obterOuCriarFormularioEstadoV9(cardLista);

    formulario.innerHTML = "";
    formulario.appendChild(criarCampoOcultoSessoesEstadoV9("redirect_menu", "administrativo"));
    formulario.appendChild(criarCampoOcultoSessoesEstadoV9("redirect_target", "#admin-sidebar-sections-card"));

    let titulo = cardLista.querySelector(".appverbo-sidebar-section-list-main-title-v9");

    cardLista.innerHTML = "";

    titulo = document.createElement("h2");
    titulo.className = "appverbo-sidebar-section-list-main-title-v9";
    titulo.textContent = "Sessoes do sidebar";

    const descricao = document.createElement("p");
    descricao.className = "appverbo-sidebar-sections-list-description-v9";
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";

    const ativas = sessoesEstadoV9.filter(function (sessao) {
      return normalizarEstadoSessoesEstadoV9(sessao.status) === "ativo";
    });

    const inativas = sessoesEstadoV9.filter(function (sessao) {
      return normalizarEstadoSessoesEstadoV9(sessao.status) !== "ativo";
    });

    formulario.appendChild(descricao);
    formulario.appendChild(criarTabelaEstadoV9("", ativas, "ativo"));
    formulario.appendChild(criarTabelaEstadoV9("Sessões inativas", inativas, "inativo"));

    cardLista.appendChild(titulo);
    cardLista.appendChild(formulario);

    atualizarEstadoBotoesEstadoV9(cardLista);
  }

  //###################################################################################
  // (6) CRIACAO
  //###################################################################################

  function instalarCriacaoEstadoV9() {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista || !cardLista.parentElement) {
      return;
    }

    const createCard = obterOuCriarCardCriacaoEstadoV9(cardLista);
    createCard.innerHTML = "";

    const block = document.createElement("div");
    block.className = "appverbo-create-entry-block-v1 appverbo-create-entry-block-v9";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-create-entry-toolbar-v1 appverbo-create-entry-toolbar-v9";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appverbo-create-entry-panel-v1 appverbo-create-entry-panel-v9";
    panel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appverbo-create-entry-grid-v5 appverbo-create-entry-grid-v9";

    const nomeField = document.createElement("div");
    nomeField.className = "field appverbo-create-entry-field-v5";

    const nomeLabel = document.createElement("label");
    nomeLabel.textContent = "Nome da sessão *";

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";

    nomeField.appendChild(nomeLabel);
    nomeField.appendChild(nomeInput);

    const sistemaField = document.createElement("div");
    sistemaField.className = "field appverbo-create-entry-field-v5";

    const sistemaLabel = document.createElement("label");
    sistemaLabel.textContent = "Sistema *";

    const sistemaSelect = criarSelectSistemaEstadoV9("all");

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-create-entry-field-v5";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = criarSelectEstadoEstadoV9("ativo");

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const erro = document.createElement("p");
    erro.className = "appverbo-create-entry-error-v5 appverbo-create-entry-error-v9";
    erro.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appverbo-create-entry-actions-v5 appverbo-create-entry-actions-v9";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    panel.appendChild(grid);
    panel.appendChild(erro);
    panel.appendChild(actions);

    block.appendChild(toolbar);
    block.appendChild(panel);
    createCard.appendChild(block);

    function fechar() {
      nomeInput.value = "";
      sistemaSelect.value = "all";
      estadoSelect.value = "ativo";
      erro.hidden = true;
      erro.textContent = "";
      panel.hidden = true;
      abrirBtn.hidden = false;
    }

    abrirBtn.addEventListener("click", function () {
      panel.hidden = false;
      abrirBtn.hidden = true;
      erro.hidden = true;
      nomeInput.focus();
    });

    cancelarBtn.addEventListener("click", fechar);

    guardarBtn.addEventListener("click", function () {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        erro.textContent = "Informe o nome da sessão.";
        erro.hidden = false;
        nomeInput.focus();
        return;
      }

      const estado = normalizarEstadoSessoesEstadoV9(estadoSelect.value);

      sessoesEstadoV9.push({
        key: gerarChaveUnicaEstadoV9(nome),
        label: nome,
        visibility_scope_mode: sistemaSelect.value || "all",
        visibility_scope_label: obterLabelSistemaSessoesEstadoV9(sistemaSelect.value || "all", ""),
        status: estado,
        is_active: estado === "ativo",
        status_label: obterLabelEstadoSessoesEstadoV9(estado)
      });

      fechar();
      renderizarListaEstadoV9();
      submeterFormularioEstadoV9();
    });
  }

  //###################################################################################
  // (7) EDICAO E ACOES
  //###################################################################################

  function moverSessaoEstadoV9(chave, direcao) {
    const indice = encontrarIndiceSessaoEstadoV9(chave);

    if (indice < 0) {
      return;
    }

    const sessao = sessoesEstadoV9[indice];
    const statusAtual = normalizarEstadoSessoesEstadoV9(sessao.status);

    const indicesMesmoGrupo = sessoesEstadoV9
      .map(function (item, index) {
        return {
          item: item,
          index: index
        };
      })
      .filter(function (entry) {
        return normalizarEstadoSessoesEstadoV9(entry.item.status) === statusAtual;
      })
      .map(function (entry) {
        return entry.index;
      });

    const posicaoGrupo = indicesMesmoGrupo.indexOf(indice);

    if (direcao === "up" && posicaoGrupo > 0) {
      const indiceAnterior = indicesMesmoGrupo[posicaoGrupo - 1];
      const temp = sessoesEstadoV9[indiceAnterior];
      sessoesEstadoV9[indiceAnterior] = sessoesEstadoV9[indice];
      sessoesEstadoV9[indice] = temp;
    }

    if (direcao === "down" && posicaoGrupo < indicesMesmoGrupo.length - 1) {
      const indiceProximo = indicesMesmoGrupo[posicaoGrupo + 1];
      const temp = sessoesEstadoV9[indiceProximo];
      sessoesEstadoV9[indiceProximo] = sessoesEstadoV9[indice];
      sessoesEstadoV9[indice] = temp;
    }

    renderizarListaEstadoV9();
    submeterFormularioEstadoV9();
  }

  function abrirEdicaoEstadoV9(linha) {
    const chave = linha.dataset.sectionKeyV9;
    const indice = encontrarIndiceSessaoEstadoV9(chave);

    if (indice < 0) {
      return;
    }

    const sessao = Object.assign({}, sessoesEstadoV9[indice]);

    const tdMenu = linha.querySelector(".appverbo-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appverbo-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appverbo-sidebar-section-state-cell-v2");
    const tdAcoes = linha.querySelector(".appverbo-sidebar-section-actions-cell-v2");

    if (!tdMenu || !tdSistema || !tdEstado || !tdAcoes) {
      return;
    }

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.className = "appverbo-sidebar-section-edit-input-v9";
    nomeInput.value = sessao.label;
    nomeInput.maxLength = 80;

    const sistemaSelect = criarSelectSistemaEstadoV9(sessao.visibility_scope_mode);
    const estadoSelect = criarSelectEstadoEstadoV9(sessao.status);

    tdMenu.innerHTML = "";
    tdMenu.appendChild(nomeInput);

    tdSistema.innerHTML = "";
    tdSistema.appendChild(sistemaSelect);

    tdEstado.innerHTML = "";
    tdEstado.appendChild(estadoSelect);

    tdAcoes.innerHTML = "";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-edit-actions-v9";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appverbo-sidebar-section-edit-save-v9";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appverbo-sidebar-section-edit-cancel-v9";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);
    tdAcoes.appendChild(actions);

    guardarBtn.addEventListener("click", function () {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        nomeInput.classList.add("appverbo-sidebar-section-edit-input-error-v9");
        nomeInput.focus();
        return;
      }

      const estado = normalizarEstadoSessoesEstadoV9(estadoSelect.value);

      sessoesEstadoV9[indice] = {
        key: sessao.key,
        label: nome,
        visibility_scope_mode: sistemaSelect.value || "all",
        visibility_scope_label: obterLabelSistemaSessoesEstadoV9(sistemaSelect.value || "all", ""),
        status: estado,
        is_active: estado === "ativo",
        status_label: obterLabelEstadoSessoesEstadoV9(estado)
      };

      renderizarListaEstadoV9();
      submeterFormularioEstadoV9();
    });

    cancelarBtn.addEventListener("click", function () {
      renderizarListaEstadoV9();
    });

    nomeInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        guardarBtn.click();
      }

      if (event.key === "Escape") {
        event.preventDefault();
        cancelarBtn.click();
      }
    });

    nomeInput.focus();
    nomeInput.select();
  }

  function instalarEventosListaEstadoV9() {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista || cardLista.dataset.eventsEstadoV9 === "1") {
      return;
    }

    cardLista.dataset.eventsEstadoV9 = "1";

    cardLista.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v9]");

      if (!botao) {
        return;
      }

      const linha = botao.closest("tr.appverbo-sidebar-section-row-v9");

      if (!linha) {
        return;
      }

      const acao = botao.dataset.sidebarSectionActionV9;
      const chave = linha.dataset.sectionKeyV9;
      const indice = encontrarIndiceSessaoEstadoV9(chave);
      const sessao = indice >= 0 ? sessoesEstadoV9[indice] : null;

      if (acao === "up" || acao === "down") {
        moverSessaoEstadoV9(chave, acao);
      }

      if (acao === "view" && sessao) {
        alert(
          "Nome da sessão: " + sessao.label +
          "\nSistema: " + obterLabelSistemaSessoesEstadoV9(sessao.visibility_scope_mode, sessao.visibility_scope_label || "") +
          "\nEstado: " + obterLabelEstadoSessoesEstadoV9(sessao.status)
        );
      }

      if (acao === "edit") {
        abrirEdicaoEstadoV9(linha);
      }
    });
  }

  //###################################################################################
  // (8) INSTALAR
  //###################################################################################

  async function instalarSessoesEstadoV9(force) {
    const cardLista = obterCardListaEstadoV9();

    if (!cardLista) {
      return;
    }

    if (instaladoEstadoV9 && !force) {
      return;
    }

    const raw = await carregarSessoesEstadoV9();
    const normalizadas = raw.map(normalizarSessaoEstadoV9).filter(Boolean);

    if (!normalizadas.length) {
      return;
    }

    sessoesEstadoV9 = normalizadas;
    instaladoEstadoV9 = true;

    instalarCriacaoEstadoV9();
    renderizarListaEstadoV9();
    instalarEventosListaEstadoV9();
  }

  function iniciarSessoesEstadoV9() {
    window.setTimeout(function () {
      instalarSessoesEstadoV9(true);
    }, 500);

    window.setTimeout(function () {
      instalarSessoesEstadoV9(true);
    }, 1200);

    window.setTimeout(function () {
      instalarSessoesEstadoV9(true);
    }, 2000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarSessoesEstadoV9);
  } else {
    iniciarSessoesEstadoV9();
  }
})();
// APPVERBO_SESSOES_ESTADO_BLOCOS_V9_END


// APPVERBO_SESSOES_SCOPE_CORRETO_V12_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesScopeV12(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  //###################################################################################
  // (2) UTILITARIOS DE VISIBILIDADE
  //###################################################################################

  function elementoVisivelSessoesScopeV12(elemento) {
    if (!elemento) {
      return false;
    }

    if (elemento.hidden || elemento.getAttribute("aria-hidden") === "true") {
      return false;
    }

    const estilo = window.getComputedStyle(elemento);

    if (estilo.display === "none" || estilo.visibility === "hidden") {
      return false;
    }

    return Boolean(elemento.offsetWidth || elemento.offsetHeight || elemento.getClientRects().length);
  }

  function estaAtivoPorClasseSessoesScopeV12(elemento) {
    const className = normalizarTextoSessoesScopeV12(elemento.className || "");

    return className.includes("active") ||
      className.includes("ativo") ||
      className.includes("selected") ||
      className.includes("current") ||
      className.includes("is-active");
  }

  function tabSessoesEstaAtivoV12() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoSessoesScopeV12(elemento.textContent);

      if (texto !== "sessoes") {
        return false;
      }

      if (!elementoVisivelSessoesScopeV12(elemento)) {
        return false;
      }

      if (elemento.getAttribute("aria-selected") === "true") {
        return true;
      }

      if (estaAtivoPorClasseSessoesScopeV12(elemento)) {
        return true;
      }

      const parent = elemento.parentElement;

      if (parent && estaAtivoPorClasseSessoesScopeV12(parent)) {
        return true;
      }

      return false;
    });
  }

  function tabEntidadeOuOutraEstaAtivaV12() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoSessoesScopeV12(elemento.textContent);

      if (!["entidade", "utilizador", "menu"].includes(texto)) {
        return false;
      }

      if (!elementoVisivelSessoesScopeV12(elemento)) {
        return false;
      }

      if (elemento.getAttribute("aria-selected") === "true") {
        return true;
      }

      if (estaAtivoPorClasseSessoesScopeV12(elemento)) {
        return true;
      }

      const parent = elemento.parentElement;

      if (parent && estaAtivoPorClasseSessoesScopeV12(parent)) {
        return true;
      }

      return false;
    });
  }

  function cardListaSessoesExisteEVisivelV12() {
    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card || !elementoVisivelSessoesScopeV12(card)) {
      return false;
    }

    const texto = normalizarTextoSessoesScopeV12(card.textContent);

    return texto.includes("sessoes do sidebar") ||
      texto.includes("criar sessao") ||
      texto.includes("menu lateral") ||
      Boolean(card.querySelector(".appverbo-sidebar-section-row-v10, .appverbo-sidebar-section-row-v9, .appverbo-sidebar-section-row-v6, .appverbo-sidebar-section-row-v2"));
  }

  function urlApontaParaSessoesV12() {
    const hash = normalizarTextoSessoesScopeV12(window.location.hash);
    const search = normalizarTextoSessoesScopeV12(window.location.search);
    const href = normalizarTextoSessoesScopeV12(window.location.href);

    return hash.includes("admin-sidebar-sections-card") ||
      search.includes("admin_tab=sessoes") ||
      search.includes("admin_tab=sessões") ||
      href.includes("dynamic_process_section=sidebar") ||
      href.includes("dynamic_process_section=sessoes") ||
      href.includes("dynamic_process_section=sessões");
  }

  function abaSessoesEstaAtivaV12() {
    if (urlApontaParaSessoesV12()) {
      return true;
    }

    if (tabSessoesEstaAtivoV12()) {
      return true;
    }

    if (tabEntidadeOuOutraEstaAtivaV12()) {
      return false;
    }

    return cardListaSessoesExisteEVisivelV12();
  }

  //###################################################################################
  // (3) REMOVER SOMENTE ORFAOS
  //###################################################################################

  function cardEstaDentroAreaSessoesV12(card) {
    if (!card) {
      return false;
    }

    const cardLista = document.getElementById("admin-sidebar-sections-card");

    if (!cardLista || !cardLista.parentElement) {
      return false;
    }

    if (card.id === "admin-sidebar-sections-create-card") {
      return card.parentElement === cardLista.parentElement;
    }

    if (card.id === "admin-sidebar-sections-inactive-card") {
      return card.parentElement === cardLista.parentElement;
    }

    return false;
  }

  function removerCardsOrfaosSessoesV12() {
    const sessoesAtiva = abaSessoesEstaAtivaV12();

    Array.from(document.querySelectorAll("#admin-sidebar-sections-create-card, #admin-sidebar-sections-inactive-card")).forEach(function (card) {
      if (!sessoesAtiva) {
        card.remove();
        return;
      }

      if (!cardEstaDentroAreaSessoesV12(card)) {
        card.remove();
      }
    });
  }

  function marcarEstadoBodySessoesV12() {
    if (abaSessoesEstaAtivaV12()) {
      document.body.classList.add("appverbo-admin-sessoes-active-v12");
      document.body.classList.remove("appverbo-admin-sessoes-inactive-v12");
    }
    else {
      document.body.classList.remove("appverbo-admin-sessoes-active-v12");
      document.body.classList.add("appverbo-admin-sessoes-inactive-v12");
    }
  }

  //###################################################################################
  // (4) INSTALAR
  //###################################################################################

  function executarScopeCorretoSessoesV12() {
    marcarEstadoBodySessoesV12();
    removerCardsOrfaosSessoesV12();
  }

  function instalarScopeCorretoSessoesV12() {
    executarScopeCorretoSessoesV12();

    window.setTimeout(executarScopeCorretoSessoesV12, 80);
    window.setTimeout(executarScopeCorretoSessoesV12, 250);
    window.setTimeout(executarScopeCorretoSessoesV12, 700);
    window.setTimeout(executarScopeCorretoSessoesV12, 1300);
  }

  document.addEventListener("click", function () {
    window.setTimeout(instalarScopeCorretoSessoesV12, 80);
    window.setTimeout(instalarScopeCorretoSessoesV12, 300);
  });

  window.addEventListener("hashchange", instalarScopeCorretoSessoesV12);
  window.addEventListener("popstate", instalarScopeCorretoSessoesV12);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarScopeCorretoSessoesV12);
  }
  else {
    instalarScopeCorretoSessoesV12();
  }
})();
// APPVERBO_SESSOES_SCOPE_CORRETO_V12_END

// APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_START
// Desativado pela refatoração V18.
// Motivo: V18 controla o card Criar/Editar sessão no padrão Entidade.
// APPVERBO_SESSOES_RECREATE_CREATE_CARD_V14_END

// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZAR E VALIDAR ESCOPO
  //###################################################################################

  function normalizarTextoSessoesInativasV15(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function elementoVisivelSessoesInativasV15(elemento) {
    if (!elemento) {
      return false;
    }

    if (elemento.hidden || elemento.getAttribute("aria-hidden") === "true") {
      return false;
    }

    const estilo = window.getComputedStyle(elemento);

    if (estilo.display === "none" || estilo.visibility === "hidden") {
      return false;
    }

    return Boolean(elemento.offsetWidth || elemento.offsetHeight || elemento.getClientRects().length);
  }

  function tabSessoesAtivaInativasV15() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoSessoesInativasV15(elemento.textContent);

      if (texto !== "sessoes") {
        return false;
      }

      if (!elementoVisivelSessoesInativasV15(elemento)) {
        return false;
      }

      const className = normalizarTextoSessoesInativasV15(elemento.className || "");
      const parentClass = elemento.parentElement
        ? normalizarTextoSessoesInativasV15(elemento.parentElement.className || "")
        : "";

      return elemento.getAttribute("aria-selected") === "true" ||
        className.includes("active") ||
        className.includes("ativo") ||
        className.includes("selected") ||
        parentClass.includes("active") ||
        parentClass.includes("ativo") ||
        parentClass.includes("selected");
    });
  }

  function outraAbaAtivaInativasV15() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      const texto = normalizarTextoSessoesInativasV15(elemento.textContent);

      if (!["entidade", "utilizador", "menu"].includes(texto)) {
        return false;
      }

      if (!elementoVisivelSessoesInativasV15(elemento)) {
        return false;
      }

      const className = normalizarTextoSessoesInativasV15(elemento.className || "");
      const parentClass = elemento.parentElement
        ? normalizarTextoSessoesInativasV15(elemento.parentElement.className || "")
        : "";

      return elemento.getAttribute("aria-selected") === "true" ||
        className.includes("active") ||
        className.includes("ativo") ||
        className.includes("selected") ||
        parentClass.includes("active") ||
        parentClass.includes("ativo") ||
        parentClass.includes("selected");
    });
  }

  function abaSessoesAtivaInativasV15() {
    if (tabSessoesAtivaInativasV15()) {
      return true;
    }

    if (outraAbaAtivaInativasV15()) {
      return false;
    }

    const cardAtivas = document.getElementById("admin-sidebar-sections-card");

    if (!cardAtivas || !elementoVisivelSessoesInativasV15(cardAtivas)) {
      return false;
    }

    const textoCard = normalizarTextoSessoesInativasV15(cardAtivas.textContent);

    return textoCard.includes("sessoes do sidebar") ||
      textoCard.includes("sessoes inativas") ||
      textoCard.includes("menu lateral");
  }

  //###################################################################################
  // (2) LOCALIZAR BLOCO/TABELA DE SESSÕES INATIVAS DENTRO DO CARD PRINCIPAL
  //###################################################################################

  function encontrarTituloInativasDentroDoCardV15(cardAtivas) {
    const titulos = Array.from(cardAtivas.querySelectorAll("h1, h2, h3, h4, strong, .appverbo-sidebar-section-list-title-v9"));

    return titulos.find(function (titulo) {
      return normalizarTextoSessoesInativasV15(titulo.textContent) === "sessoes inativas";
    }) || null;
  }

  function encontrarTabelaInativasAposTituloV15(titulo) {
    let atual = titulo ? titulo.nextElementSibling : null;

    while (atual) {
      if (
        atual.matches &&
        (
          atual.matches(".appverbo-sidebar-section-list-block-inativo-v9") ||
          atual.matches(".appverbo-sidebar-sections-table-wrap-v10") ||
          atual.matches(".appverbo-sidebar-sections-table-wrap-v9") ||
          atual.matches(".appverbo-sidebar-sections-table-wrap-v2") ||
          atual.querySelector("table")
        )
      ) {
        return atual;
      }

      atual = atual.nextElementSibling;
    }

    return null;
  }

  function encontrarBlocoInativasLegadoV15(cardAtivas) {
    return cardAtivas.querySelector(".appverbo-sidebar-section-list-block-inativo-v9") ||
      cardAtivas.querySelector(".appverbo-sidebar-section-list-block-inativo-v10") ||
      null;
  }

  //###################################################################################
  // (3) CRIAR CARD SEPARADO
  //###################################################################################

  function obterOuCriarCardInativasSeparadoV15(cardAtivas) {
    let cardInativas = document.getElementById("admin-sidebar-sections-inactive-card");

    if (!cardInativas) {
      cardInativas = document.createElement("section");
      cardInativas.id = "admin-sidebar-sections-inactive-card";
    }

    cardInativas.className = "card appverbo-sidebar-sections-inactive-card-v10 appverbo-sidebar-sections-inactive-card-v15";
    cardInativas.hidden = false;
    cardInativas.style.display = "";
    cardInativas.style.visibility = "";

    if (cardInativas.parentElement !== cardAtivas.parentElement) {
      cardAtivas.parentElement.insertBefore(cardInativas, cardAtivas.nextSibling);
    }
    else if (cardInativas.previousElementSibling !== cardAtivas) {
      cardAtivas.parentElement.insertBefore(cardInativas, cardAtivas.nextSibling);
    }

    return cardInativas;
  }

  function criarTituloInativasV15() {
    const titulo = document.createElement("h2");
    titulo.className = "appverbo-sidebar-section-list-main-title-v10 appverbo-sidebar-section-list-main-title-v15";
    titulo.textContent = "Sessões inativas";
    return titulo;
  }

  function criarMensagemSemInativasV15() {
    const mensagem = document.createElement("p");
    mensagem.className = "appverbo-sidebar-section-empty-text-v10 appverbo-sidebar-section-empty-text-v15";
    mensagem.textContent = "Sem sessões inativas.";
    return mensagem;
  }

  function tabelaEstaVaziaInativasV15(elemento) {
    if (!elemento) {
      return true;
    }

    const linhas = Array.from(elemento.querySelectorAll("tbody tr"));

    if (!linhas.length) {
      return true;
    }

    const linhasComDados = linhas.filter(function (linha) {
      const texto = normalizarTextoSessoesInativasV15(linha.textContent);

      return texto &&
        !texto.includes("sem sessoes inativas") &&
        !texto.includes("sem sessões inativas");
    });

    return linhasComDados.length === 0;
  }

  //###################################################################################
  // (4) SEPARAR INATIVAS DO CARD PRINCIPAL
  //###################################################################################

  function limparRestosInativasNoCardPrincipalV15(cardAtivas) {
    const titulos = Array.from(cardAtivas.querySelectorAll("h1, h2, h3, h4, strong, .appverbo-sidebar-section-list-title-v9"));

    titulos.forEach(function (titulo) {
      if (normalizarTextoSessoesInativasV15(titulo.textContent) === "sessoes inativas") {
        titulo.remove();
      }
    });

    Array.from(cardAtivas.querySelectorAll(".appverbo-sidebar-section-list-block-inativo-v9, .appverbo-sidebar-section-list-block-inativo-v10")).forEach(function (bloco) {
      bloco.remove();
    });
  }

  function separarSessaoInativasParaCardV15() {
    if (!abaSessoesAtivaInativasV15()) {
      const cardInativasFora = document.getElementById("admin-sidebar-sections-inactive-card");

      if (cardInativasFora) {
        cardInativasFora.remove();
      }

      return;
    }

    const cardAtivas = document.getElementById("admin-sidebar-sections-card");

    if (!cardAtivas || !cardAtivas.parentElement) {
      return;
    }

    const cardInativas = obterOuCriarCardInativasSeparadoV15(cardAtivas);
    const blocoLegado = encontrarBlocoInativasLegadoV15(cardAtivas);
    const tituloDentro = encontrarTituloInativasDentroDoCardV15(cardAtivas);
    const tabelaDentro = blocoLegado || encontrarTabelaInativasAposTituloV15(tituloDentro);

    cardInativas.innerHTML = "";
    cardInativas.appendChild(criarTituloInativasV15());

    if (tabelaDentro) {
      if (blocoLegado) {
        const tabela = blocoLegado.querySelector(".appverbo-sidebar-sections-table-wrap-v2, .appverbo-sidebar-sections-table-wrap-v9, .appverbo-sidebar-sections-table-wrap-v10, table");

        if (tabela) {
          cardInativas.appendChild(tabela);
        }
        else if (!tabelaEstaVaziaInativasV15(blocoLegado)) {
          cardInativas.appendChild(blocoLegado);
        }
        else {
          cardInativas.appendChild(criarMensagemSemInativasV15());
        }
      }
      else if (!tabelaEstaVaziaInativasV15(tabelaDentro)) {
        cardInativas.appendChild(tabelaDentro);
      }
      else {
        cardInativas.appendChild(criarMensagemSemInativasV15());
      }
    }
    else {
      cardInativas.appendChild(criarMensagemSemInativasV15());
    }

    limparRestosInativasNoCardPrincipalV15(cardAtivas);

    cardAtivas.classList.add("appverbo-sidebar-sections-active-card-v15");
    cardInativas.classList.add("appverbo-sidebar-sections-inactive-card-separated-v15");
  }

  //###################################################################################
  // (5) OBSERVAR RENDERIZAÇÕES E RETORNO À ABA
  //###################################################################################

  function agendarSepararInativasV15() {
    window.setTimeout(separarSessaoInativasParaCardV15, 60);
    window.setTimeout(separarSessaoInativasParaCardV15, 180);
    window.setTimeout(separarSessaoInativasParaCardV15, 420);
    window.setTimeout(separarSessaoInativasParaCardV15, 900);
    window.setTimeout(separarSessaoInativasParaCardV15, 1600);
  }

  function instalarSeparadorInativasV15() {
    if (window.__appverboSessoesInactiveCardV15Installed === true) {
      return;
    }

    window.__appverboSessoesInactiveCardV15Installed = true;

    document.addEventListener("click", function () {
      agendarSepararInativasV15();
    });

    window.addEventListener("hashchange", agendarSepararInativasV15);
    window.addEventListener("popstate", agendarSepararInativasV15);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesInactiveCardV15Timer);

      window.__appverboSessoesInactiveCardV15Timer = window.setTimeout(function () {
        separarSessaoInativasParaCardV15();
      }, 120);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    agendarSepararInativasV15();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarSeparadorInativasV15);
  }
  else {
    instalarSeparadorInativasV15();
  }
})();
// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END

// APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_START
// Desativado pela refatoração V18.
// Motivo: V16 criava conflito de URL com o subprocesso Menu.
// APPVERBO_SESSOES_FLUXO_IGUAL_ENTIDADE_V16_END

// APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_START
// Desativado pela refatoração V18.
// Motivo: V17 era apenas interceptador; V18 passa a ser o controlador único do fluxo.
// APPVERBO_SESSOES_EDITAR_NAO_SALTAR_MENU_V17_END

// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV18(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesV18(valor) {
    return normalizarTextoSessoesV18(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function normalizarEstadoSessoesV18(valor) {
    const cleanValor = normalizarTextoSessoesV18(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  function normalizarSistemaSessoesV18(valor) {
    const cleanValor = normalizarTextoSessoesV18(valor);

    if (["owner", "legado"].includes(cleanValor)) {
      return cleanValor;
    }

    return "all";
  }

  //###################################################################################
  // (2) URL DA ABA SESSOES SEM PARAMETROS DO MENU
  //###################################################################################

  function limparParametrosMenuSessoesV18(url) {
    url.searchParams.delete("settings_edit_key");
    url.searchParams.delete("settings_action");
    url.searchParams.delete("settings_tab");
    url.searchParams.delete("sidebar_section_return_url");
    url.searchParams.delete("success");
    url.searchParams.delete("error");
    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.hash = "admin-sidebar-sections-card";
    return url;
  }

  function obterUrlBaseSessaoV18() {
    const url = new URL(window.location.href);
    limparParametrosMenuSessoesV18(url);
    return url;
  }

  function obterUrlRetornoSessaoV18() {
    const url = obterUrlBaseSessaoV18();
    url.searchParams.delete("sidebar_section_edit_key");
    return url.pathname + url.search + url.hash;
  }

  function obterEditKeySessaoV18() {
    const url = new URL(window.location.href);
    return criarChaveSessoesV18(url.searchParams.get("sidebar_section_edit_key") || "");
  }

  function navegarEditarSessaoV18(chave) {
    const cleanChave = criarChaveSessoesV18(chave);

    if (!cleanChave) {
      return;
    }

    const url = obterUrlBaseSessaoV18();
    url.searchParams.set("sidebar_section_edit_key", cleanChave);
    window.location.href = url.pathname + url.search + url.hash;
  }

  function cancelarEdicaoSessaoV18() {
    window.location.href = obterUrlRetornoSessaoV18();
  }

  //###################################################################################
  // (3) DETETAR E FORCAR ABA SESSOES
  //###################################################################################

  function elementoVisivelSessoesV18(elemento) {
    if (!elemento) {
      return false;
    }

    if (elemento.hidden || elemento.getAttribute("aria-hidden") === "true") {
      return false;
    }

    const estilo = window.getComputedStyle(elemento);

    if (estilo.display === "none" || estilo.visibility === "hidden") {
      return false;
    }

    return Boolean(elemento.offsetWidth || elemento.offsetHeight || elemento.getClientRects().length);
  }

  function elementoAtivoSessoesV18(elemento) {
    const className = normalizarTextoSessoesV18(elemento.className || "");
    const parentClass = elemento.parentElement
      ? normalizarTextoSessoesV18(elemento.parentElement.className || "")
      : "";

    return elemento.getAttribute("aria-selected") === "true" ||
      className.includes("active") ||
      className.includes("ativo") ||
      className.includes("selected") ||
      className.includes("current") ||
      className.includes("is-active") ||
      parentClass.includes("active") ||
      parentClass.includes("ativo") ||
      parentClass.includes("selected") ||
      parentClass.includes("current") ||
      parentClass.includes("is-active");
  }

  function encontrarTabPorTextoSessoesV18(textoEsperado) {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.find(function (elemento) {
      return normalizarTextoSessoesV18(elemento.textContent) === textoEsperado &&
        elementoVisivelSessoesV18(elemento);
    }) || null;
  }

  function tabAtivaPorTextoSessoesV18(textoEsperado) {
    const tab = encontrarTabPorTextoSessoesV18(textoEsperado);
    return Boolean(tab && elementoAtivoSessoesV18(tab));
  }

  function outraAbaAdministrativaAtivaSessoesV18() {
    return ["entidade", "utilizador", "menu"].some(function (texto) {
      return tabAtivaPorTextoSessoesV18(texto);
    });
  }

  function cardListaSessoesVisivelV18() {
    const card = document.getElementById("admin-sidebar-sections-card");

    if (!card || !elementoVisivelSessoesV18(card)) {
      return false;
    }

    const textoCard = normalizarTextoSessoesV18(card.textContent);

    return textoCard.includes("sessoes do sidebar") ||
      textoCard.includes("menu lateral") ||
      Boolean(card.querySelector(".appverbo-sidebar-section-row-v10, .appverbo-sidebar-section-row-v9, .appverbo-sidebar-section-row-v6, .appverbo-sidebar-section-row-v2"));
  }

  function deveForcarAbaSessoesV18() {
    const url = new URL(window.location.href);
    return Boolean(
      url.searchParams.get("sidebar_section_edit_key") ||
      url.searchParams.get("sidebar_sections_tab") === "sessoes" ||
      url.searchParams.get("admin_tab") === "sessoes"
    );
  }

  function abaSessoesAtivaV18() {
    if (tabAtivaPorTextoSessoesV18("sessoes")) {
      return true;
    }

    if (outraAbaAdministrativaAtivaSessoesV18()) {
      return false;
    }

    if (deveForcarAbaSessoesV18()) {
      return true;
    }

    return cardListaSessoesVisivelV18();
  }

  function forcarAbaSessoesV18() {
    if (!deveForcarAbaSessoesV18()) {
      return;
    }

    const tabSessoes = encontrarTabPorTextoSessoesV18("sessoes");

    if (tabSessoes && !elementoAtivoSessoesV18(tabSessoes)) {
      tabSessoes.click();
    }

    document.body.classList.add("appverbo-admin-sessoes-active-v18");
    document.body.classList.remove("appverbo-admin-sessoes-inactive-v18");
  }

  //###################################################################################
  // (4) LER SESSOES DO BD/TEMPLATE
  //###################################################################################

  function lerSessoesTemplateV18() {
    const script = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    }
    catch (error) {
      return [];
    }
  }

  async function carregarSessoesV18() {
    try {
      const response = await fetch("/settings/menu/sidebar-sections-data", {
        headers: {
          Accept: "application/json"
        },
        credentials: "same-origin"
      });

      if (response.ok) {
        const payload = await response.json();

        if (payload && Array.isArray(payload.sections)) {
          return payload.sections;
        }
      }
    }
    catch (error) {
      console.warn("APPVERBO V18: falha ao carregar sessões do BD.", error);
    }

    return lerSessoesTemplateV18();
  }

  function normalizarSessaoV18(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesV18(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    return {
      key: key,
      label: label,
      visibility_scope_mode: normalizarSistemaSessoesV18(sessao.visibility_scope_mode || sessao.scope_mode || "all"),
      status: normalizarEstadoSessoesV18(sessao.status || (sessao.is_active === false ? "inativo" : "ativo"))
    };
  }

  async function obterSessaoPorChaveV18(chave) {
    const cleanChave = criarChaveSessoesV18(chave);
    const sessoes = await carregarSessoesV18();

    return sessoes
      .map(normalizarSessaoV18)
      .filter(Boolean)
      .find(function (sessao) {
        return criarChaveSessoesV18(sessao.key) === cleanChave;
      }) || null;
  }

  //###################################################################################
  // (5) CARD SUPERIOR PADRAO ENTIDADE
  //###################################################################################

  function obterCardListaSessoesV18() {
    return document.getElementById("admin-sidebar-sections-card");
  }

  function obterOuCriarCardSuperiorSessoesV18() {
    const cardLista = obterCardListaSessoesV18();

    if (!cardLista || !cardLista.parentElement) {
      return null;
    }

    let cardSuperior = document.getElementById("admin-sidebar-sections-create-card");

    if (!cardSuperior) {
      cardSuperior = document.createElement("section");
      cardSuperior.id = "admin-sidebar-sections-create-card";
      cardLista.parentElement.insertBefore(cardSuperior, cardLista);
    }
    else if (cardSuperior.parentElement !== cardLista.parentElement) {
      cardLista.parentElement.insertBefore(cardSuperior, cardLista);
    }

    cardSuperior.className = "card appverbo-standard-create-card-v4 appverbo-sessoes-create-card-v18";
    cardSuperior.hidden = false;
    cardSuperior.style.display = "";
    cardSuperior.style.visibility = "";

    return cardSuperior;
  }

  function criarCampoHiddenV18(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  function criarOpcaoV18(valor, texto, valorAtual) {
    const option = document.createElement("option");
    option.value = valor;
    option.textContent = texto;

    if (valor === valorAtual) {
      option.selected = true;
    }

    return option;
  }

  function renderizarFormularioSuperiorSessoesV18(cardSuperior, modo, sessao) {
    const isEdit = modo === "edit";
    const editKey = isEdit && sessao ? sessao.key : "";

    if (
      cardSuperior.dataset.appverboSessoesModeV18 === modo &&
      cardSuperior.dataset.appverboSessoesKeyV18 === editKey &&
      cardSuperior.querySelector(".appverbo-sessoes-form-wrapper-v18")
    ) {
      return;
    }

    cardSuperior.dataset.appverboSessoesModeV18 = modo;
    cardSuperior.dataset.appverboSessoesKeyV18 = editKey;
    cardSuperior.innerHTML = "";

    const container = document.createElement("div");
    container.className = "appverbo-sessoes-form-wrapper-v18";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-sessoes-toolbar-v18";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appverbo-sessoes-open-create-v18";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appverbo-sessoes-panel-v18";
    panel.hidden = !isEdit;

    if (isEdit) {
      toolbar.hidden = true;
    }

    const title = document.createElement("h2");
    title.className = "appverbo-sessoes-form-title-v18";
    title.textContent = isEdit ? "Editar sessão" : "Criar sessão";

    const form = document.createElement("form");
    form.method = "post";
    form.action = "/settings/menu/sidebar-section-save";
    form.className = "appverbo-sessoes-form-v18";

    form.appendChild(criarCampoHiddenV18("section_mode", isEdit ? "edit" : "create"));
    form.appendChild(criarCampoHiddenV18("original_section_key", isEdit && sessao ? sessao.key : ""));
    form.appendChild(criarCampoHiddenV18("sidebar_section_return_url", obterUrlRetornoSessaoV18()));

    const grid = document.createElement("div");
    grid.className = "appverbo-sessoes-grid-v18";

    const nomeField = document.createElement("div");
    nomeField.className = "field appverbo-sessoes-field-v18";

    const nomeLabel = document.createElement("label");
    nomeLabel.textContent = "Nome da sessão *";

    const nomeInput = document.createElement("input");
    nomeInput.name = "section_label";
    nomeInput.required = true;
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";
    nomeInput.value = sessao ? sessao.label : "";

    nomeField.appendChild(nomeLabel);
    nomeField.appendChild(nomeInput);

    const sistemaField = document.createElement("div");
    sistemaField.className = "field appverbo-sessoes-field-v18";

    const sistemaLabel = document.createElement("label");
    sistemaLabel.textContent = "Sistema *";

    const sistemaSelect = document.createElement("select");
    sistemaSelect.name = "section_visibility_scope_mode";

    const sistemaAtual = sessao ? normalizarSistemaSessoesV18(sessao.visibility_scope_mode) : "all";
    sistemaSelect.appendChild(criarOpcaoV18("all", "Owner e Legado", sistemaAtual));
    sistemaSelect.appendChild(criarOpcaoV18("owner", "Owner", sistemaAtual));
    sistemaSelect.appendChild(criarOpcaoV18("legado", "Legado", sistemaAtual));

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-sessoes-field-v18";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = document.createElement("select");
    estadoSelect.name = "section_status";

    const estadoAtual = sessao ? normalizarEstadoSessoesV18(sessao.status) : "ativo";
    estadoSelect.appendChild(criarOpcaoV18("ativo", "Ativo", estadoAtual));
    estadoSelect.appendChild(criarOpcaoV18("inativo", "Inativo", estadoAtual));

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const actions = document.createElement("div");
    actions.className = "appverbo-sessoes-actions-v18";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "submit";
    guardarBtn.className = "action-btn";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    form.appendChild(grid);
    form.appendChild(actions);

    panel.appendChild(title);
    panel.appendChild(form);

    container.appendChild(toolbar);
    container.appendChild(panel);
    cardSuperior.appendChild(container);

    abrirBtn.addEventListener("click", function () {
      toolbar.hidden = true;
      panel.hidden = false;
      nomeInput.focus();
    });

    cancelarBtn.addEventListener("click", function () {
      if (isEdit) {
        cancelarEdicaoSessaoV18();
        return;
      }

      form.reset();
      panel.hidden = true;
      toolbar.hidden = false;
    });

    form.addEventListener("submit", function () {
      const returnInput = form.querySelector('[name="sidebar_section_return_url"]');

      if (returnInput) {
        returnInput.value = obterUrlRetornoSessaoV18();
      }
    });

    if (isEdit) {
      window.setTimeout(function () {
        nomeInput.focus();
        nomeInput.select();
      }, 120);
    }
  }

  async function montarCardSuperiorSessoesV18() {
    forcarAbaSessoesV18();

    if (!abaSessoesAtivaV18()) {
      document.body.classList.remove("appverbo-admin-sessoes-active-v18");
      document.body.classList.add("appverbo-admin-sessoes-inactive-v18");
      return;
    }

    document.body.classList.add("appverbo-admin-sessoes-active-v18");
    document.body.classList.remove("appverbo-admin-sessoes-inactive-v18");

    const cardSuperior = obterOuCriarCardSuperiorSessoesV18();

    if (!cardSuperior) {
      return;
    }

    const editKey = obterEditKeySessaoV18();

    if (editKey) {
      const sessao = await obterSessaoPorChaveV18(editKey);

      if (sessao) {
        renderizarFormularioSuperiorSessoesV18(cardSuperior, "edit", sessao);
        return;
      }
    }

    renderizarFormularioSuperiorSessoesV18(cardSuperior, "create", null);
  }

  //###################################################################################
  // (6) CAPTURAR EDITAR E IMPEDIR INLINE
  //###################################################################################

  function obterChaveLinhaSessoesV18(linha) {
    if (!linha) {
      return "";
    }

    const datasetKey = linha.dataset.sectionKeyV10 ||
      linha.dataset.sectionKeyV9 ||
      linha.dataset.sectionKeyV6 ||
      linha.dataset.sectionKeyV2 ||
      "";

    if (datasetKey) {
      return criarChaveSessoesV18(datasetKey);
    }

    const hiddenKey = linha.querySelector('[name="section_key"]');

    if (hiddenKey && hiddenKey.value) {
      return criarChaveSessoesV18(hiddenKey.value);
    }

    const primeiraCelula = linha.querySelector("td");

    return primeiraCelula ? criarChaveSessoesV18(primeiraCelula.textContent) : "";
  }

  function encontrarBotaoEditarSessoesV18(target) {
    if (!target || !target.closest) {
      return null;
    }

    const explicitButton = target.closest(
      '[data-sidebar-section-action-v10="edit"], ' +
      '[data-sidebar-section-action-v9="edit"], ' +
      '[data-sidebar-section-action-v6="edit"], ' +
      '[data-sidebar-section-action-v2="edit"], ' +
      '[data-sidebar-section-action="edit"]'
    );

    if (explicitButton) {
      return explicitButton;
    }

    const possibleButton = target.closest("button, a");

    if (!possibleButton) {
      return null;
    }

    const label = normalizarTextoSessoesV18(
      possibleButton.getAttribute("title") ||
      possibleButton.getAttribute("aria-label") ||
      possibleButton.textContent ||
      ""
    );

    if (label.includes("editar") || label === "✎") {
      return possibleButton;
    }

    return null;
  }

  function instalarCapturaEditarSessoesV18() {
    if (window.__appverboSessoesEditCaptureV18 === true) {
      return;
    }

    window.__appverboSessoesEditCaptureV18 = true;

    document.addEventListener("click", function (event) {
      const botaoEditar = encontrarBotaoEditarSessoesV18(event.target);

      if (!botaoEditar) {
        return;
      }

      const card = botaoEditar.closest("#admin-sidebar-sections-card, #admin-sidebar-sections-inactive-card");

      if (!card) {
        return;
      }

      const linha = botaoEditar.closest("tr");
      const chave = obterChaveLinhaSessoesV18(linha);

      if (!chave) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();

      navegarEditarSessaoV18(chave);
    }, true);
  }

  //###################################################################################
  // (7) INSTALAR OBSERVADORES
  //###################################################################################

  function agendarMontagemSessoesV18() {
    window.setTimeout(montarCardSuperiorSessoesV18, 80);
    window.setTimeout(montarCardSuperiorSessoesV18, 250);
    window.setTimeout(montarCardSuperiorSessoesV18, 600);
    window.setTimeout(montarCardSuperiorSessoesV18, 1200);
  }

  function instalarSessoesPadraoEntidadeV18() {
    instalarCapturaEditarSessoesV18();

    document.addEventListener("click", function () {
      agendarMontagemSessoesV18();
    });

    window.addEventListener("hashchange", agendarMontagemSessoesV18);
    window.addEventListener("popstate", agendarMontagemSessoesV18);

    const observer = new MutationObserver(function () {
      window.clearTimeout(window.__appverboSessoesPadraoEntidadeTimerV18);

      window.__appverboSessoesPadraoEntidadeTimerV18 = window.setTimeout(function () {
        if (abaSessoesAtivaV18() || deveForcarAbaSessoesV18()) {
          montarCardSuperiorSessoesV18();
        }
      }, 140);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class", "hidden", "style", "aria-selected", "aria-hidden"]
    });

    agendarMontagemSessoesV18();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarSessoesPadraoEntidadeV18);
  }
  else {
    instalarSessoesPadraoEntidadeV18();
  }
})();
// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END

