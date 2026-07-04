// APPVERBO_LEGACY_SESSOES_GUARD_V31_START
// Guard único que detecta renderização nativa de Sessões (admin_subprocess "sessoes").
// Todos os blocos legados que injetam/criam conteúdo devem verificar esta função antes de correr.
// Seletores: [data-admin-subprocess="sessoes"] é o atributo definido pelo macro render_admin_subprocess_state.
function shouldDisableLegacySidebarSectionsRuntimeV1() {
  return Boolean(
    document.querySelector('[data-admin-subprocess="sessoes"]') ||
    document.querySelector("[data-admin-subprocess-key='sessoes']") ||
    document.querySelector("[data-appgenesis-native-admin-subprocess='sessoes']") ||
    document.querySelector("[data-admin-tab-pane='sessoes']") ||
    document.querySelector("#admin-sidebar-sections-card[data-appgenesis-native-render='1']")
  );
}
// APPVERBO_LEGACY_SESSOES_GUARD_V31_END

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

  function marcarBotaoCancelarGlobalSessoesV1(botao) {
    if (!botao) {
      return;
    }

    botao.dataset.appgenesisCancel = "1";
    botao.dataset.appgenesisCancelLocal = "1";
  }

  function vincularReacaoCancelarGlobalSessoesV1(botao, listenerRoot, callback) {
    if (!botao || botao.dataset.appgenesisCancelReactionBoundV1 === "1") {
      return;
    }

    const root = listenerRoot || botao.parentElement || document;

    marcarBotaoCancelarGlobalSessoesV1(botao);
    botao.dataset.appgenesisCancelReactionBoundV1 = "1";

    root.addEventListener("appverbo:cancelled", function (event) {
      const detail = event && event.detail ? event.detail : {};

      if (detail.trigger !== botao) {
        return;
      }

      if (typeof callback === "function") {
        callback(event);
      }
    });
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
    const script = document.getElementById("appgenesis-sidebar-section-options-v2") ||
      document.getElementById("appgenesis-sidebar-section-options-v1");

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
      { key: "sistema", label: "Sistema", visibility_scope_mode: "all", visibility_scope_label: "Default" },
      { key: "geral", label: "Geral", visibility_scope_mode: "all", visibility_scope_label: "Default" },
      { key: "dados_gerais", label: "Dados gerais", visibility_scope_mode: "all", visibility_scope_label: "Default" },
      { key: "igreja", label: "Igreja", visibility_scope_mode: "all", visibility_scope_label: "Default" },
      { key: "tesouraria", label: "Tesouraria", visibility_scope_mode: "all", visibility_scope_label: "Default" }
    ];
  }


  //###################################################################################
  // APPVERBO_SESSOES_SERVER_RENDER_GUARD_V32
  //###################################################################################

  function existeServerRenderSessoes_v32() {
    return Boolean(
      document.getElementById("admin-sidebar-sections-form-card") ||
      document.getElementById("admin-sidebar-sections-card") ||
      document.getElementById("admin-sidebar-sections-inactive-card") ||
      document.querySelector('[data-admin-tab-pane="sessoes"]')
    );
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

    return sessao.visibility_scope_label || "Default";
  }

  function criarBotaoAcaoSessoesLayout_v2(tipo, titulo) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appgenesis-sidebar-section-action-btn-v2";
    botao.dataset.sidebarSectionActionV2 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = titulo;
    return botao;
  }

  function atualizarEstadoBotoesSessoesLayout_v2(tbody) {
    const linhas = Array.from(tbody.querySelectorAll("tr.appgenesis-sidebar-section-row-v2"));

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
    const aviso = formulario.querySelector(".appgenesis-sidebar-section-change-note-v2");

    formulario.dataset.sidebarSectionsChangedV2 = "1";

    if (aviso) {
      aviso.hidden = false;
    }
  }

  function sincronizarLinhaSessoesLayout_v2(linha) {
    const labelInput = linha.querySelector('[name="section_label"]');
    const keyInput = linha.querySelector('[name="section_key"]');
    const sistemaCell = linha.querySelector(".appgenesis-sidebar-section-system-cell-v2");

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

    if (!detalhe || !detalhe.classList.contains("appgenesis-sidebar-section-detail-row-v2")) {
      return;
    }

    const keyInput = linha.querySelector('[name="section_key"]');
    const labelInput = linha.querySelector('[name="section_label"]');
    const scopeInput = linha.querySelector('[name="section_visibility_scope_mode"]');
    const texto = detalhe.querySelector(".appgenesis-sidebar-section-detail-text-v2");

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
      linha.nextElementSibling.classList.contains("appgenesis-sidebar-section-detail-row-v2")
      ? linha.nextElementSibling
      : null;

    if (direcao === "up") {
      const detalheAnterior = linha.previousElementSibling;
      const linhaAnterior = detalheAnterior && detalheAnterior.classList.contains("appgenesis-sidebar-section-detail-row-v2")
        ? detalheAnterior.previousElementSibling
        : detalheAnterior;

      if (linhaAnterior && linhaAnterior.classList.contains("appgenesis-sidebar-section-row-v2")) {
        tbody.insertBefore(linha, linhaAnterior);
        if (detalhe) {
          tbody.insertBefore(detalhe, linha.nextElementSibling);
        }
      }
    }

    if (direcao === "down") {
      const proximaLinha = detalhe ? detalhe.nextElementSibling : linha.nextElementSibling;

      if (proximaLinha && proximaLinha.classList.contains("appgenesis-sidebar-section-row-v2")) {
        const proximoDetalhe = proximaLinha.nextElementSibling &&
          proximaLinha.nextElementSibling.classList.contains("appgenesis-sidebar-section-detail-row-v2")
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

    if (!detalhe || !detalhe.classList.contains("appgenesis-sidebar-section-detail-row-v2")) {
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
    labelInput.classList.add("appgenesis-sidebar-section-label-input-editing-v2");
    labelInput.focus();
    labelInput.select();
  }

  //###################################################################################
  // (5) CRIAR TABELA
  //###################################################################################

  function criarLinhaTabelaSessoesLayout_v2(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appgenesis-sidebar-section-row-v2";
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
    labelInput.className = "appgenesis-sidebar-section-label-input-v2";

    const tdMenu = document.createElement("td");
    tdMenu.className = "appgenesis-sidebar-section-menu-cell-v2";
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(scopeInput);
    tdMenu.appendChild(statusInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appgenesis-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterSistemaSessoesLayout_v2(sessao);

    const tdEstado = document.createElement("td");
    tdEstado.className = "appgenesis-sidebar-section-state-cell-v2";

    const badge = document.createElement("span");
    const estadoSessao = normalizarEstadoSessoesCreate_v5(statusInput.value);
    badge.className = "appgenesis-sidebar-section-state-badge-v2 appgenesis-sidebar-section-state-badge-" + estadoSessao + "-v5";
    badge.textContent = obterLabelEstadoSessoesCreate_v5(estadoSessao);
    tdEstado.appendChild(badge);

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appgenesis-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "table-actions appgenesis-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("up", "Subir sessão"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("down", "Descer sessão"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("view", "Exibir detalhes"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v2("edit", "Editar informações"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    const detalhe = document.createElement("tr");
    detalhe.className = "appgenesis-sidebar-section-detail-row-v2";
    detalhe.hidden = true;

    const detalheCelula = document.createElement("td");
    detalheCelula.colSpan = 4;

    const detalheTexto = document.createElement("div");
    detalheTexto.className = "appgenesis-sidebar-section-detail-text-v2";
    detalheCelula.appendChild(detalheTexto);
    detalhe.appendChild(detalheCelula);

    labelInput.addEventListener("input", function () {
      sincronizarLinhaSessoesLayout_v2(tr);
      atualizarDetalheSessoesLayout_v2(tr);
      marcarAlteradoSessoesLayout_v2(tr.closest("form"));
    });

    labelInput.addEventListener("blur", function () {
      labelInput.readOnly = true;
      labelInput.classList.remove("appgenesis-sidebar-section-label-input-editing-v2");
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
    wrapper.className = "appgenesis-sidebar-sections-layout-v2";

    const cabecalho = document.createElement("div");
    cabecalho.className = "appgenesis-sidebar-sections-header-v2";

    const tituloBloco = document.createElement("div");
    tituloBloco.className = "appgenesis-sidebar-sections-title-block-v2";
const descricao = document.createElement("p");
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";
tituloBloco.appendChild(descricao);

    const criarBtn = document.createElement("button");
    criarBtn.type = "button";
    criarBtn.className = "appgenesis-sidebar-section-create-btn-v2";
    criarBtn.textContent = "Criar sessão";

    cabecalho.appendChild(tituloBloco);
    cabecalho.appendChild(criarBtn);

    const tableWrap = document.createElement("div");
    tableWrap.className = "appgenesis-sidebar-sections-table-wrap-v2";

    const table = document.createElement("table");
    table.className = "appgenesis-sidebar-sections-table-v2";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appgenesis-sidebar-sections-body-v2";

    sessoes.forEach(function (sessao) {
      const linha = criarLinhaTabelaSessoesLayout_v2(sessao);
      tbody.appendChild(linha.row);
      tbody.appendChild(linha.detailRow);
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);

    const footer = document.createElement("div");
    footer.className = "appgenesis-sidebar-sections-footer-v2";

    const nota = document.createElement("p");
    nota.className = "appgenesis-sidebar-section-change-note-v2";
    nota.hidden = true;
    nota.textContent = "Existem alterações por gravar.";

    const gravar = document.createElement("button");
    gravar.type = "submit";
    gravar.className = "action-btn";
    gravar.textContent = "Guardar";

    const cancelar = document.createElement("button");
    cancelar.type = "button";
    cancelar.className = "action-btn-cancel appgenesis-sidebar-section-cancel-btn-v3";
    cancelar.textContent = "Cancelar";

    footer.appendChild(gravar);
    if (typeof cancelar !== "undefined" && cancelar) {
      footer.appendChild(cancelar);
    }
    footer.appendChild(nota);

    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_menu", "sessoes"));
    wrapper.appendChild(criarCampoOcultoSessoesLayout_v2("redirect_target", "#admin-sidebar-sections-card"));
    wrapper.appendChild(cabecalho);

    const createEntrySlot = document.createElement("div");
    createEntrySlot.className = "appgenesis-create-entry-slot-v2";
    wrapper.appendChild(createEntrySlot);

    const listBlock = document.createElement("div");
    listBlock.className = "appgenesis-list-block-v2";
    listBlock.appendChild(tableWrap);
    listBlock.appendChild(footer);
    wrapper.appendChild(listBlock);

    criarBtn.addEventListener("click", function () {
      const contador = tbody.querySelectorAll("tr.appgenesis-sidebar-section-row-v2").length + 1;
      const novaSessao = {
        key: "nova_pasta_" + contador,
        label: "Nova pasta",
        visibility_scope_mode: "all",
        visibility_scope_label: "Default"
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
      const linha = botao.closest("tr.appgenesis-sidebar-section-row-v2");

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

    vincularReacaoCancelarGlobalSessoesV1(cancelar, wrapper, function () {
      const novoWrapper = criarTabelaSessoesLayout_v2(formulario, sessoes);
      wrapper.replaceWith(novoWrapper);
    });

    const cardListaSessoesV3 = formulario.closest(".card, section");
    moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardListaSessoesV3, wrapper);
    aplicarFormularioCriacaoCompletoSessoes_v4(formulario, wrapper);
    removerFooterListaSessoes_v5(wrapper);

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

    Array.from(tbody.querySelectorAll("tr.appgenesis-sidebar-section-row-v2")).forEach(function (linha) {
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

    const originalCreateBtn = wrapper.querySelector(".appgenesis-sidebar-section-create-btn-v2");
    const tableWrap = wrapper.querySelector(".appgenesis-sidebar-sections-table-wrap-v2");
    const tbody = wrapper.querySelector(".appgenesis-sidebar-sections-body-v2");

    if (!originalCreateBtn || !tableWrap || !tbody) {
      return;
    }

    wrapper.dataset.createEntryBlockV1 = "1";

    originalCreateBtn.hidden = true;
    originalCreateBtn.setAttribute("aria-hidden", "true");
    originalCreateBtn.classList.add("appgenesis-create-entry-original-hidden-v1");

    const createBlock = document.createElement("div");
    createBlock.className = "appgenesis-create-entry-block-v1";
    createBlock.dataset.createEntryBlock = "sessoes";

    const createToolbar = document.createElement("div");
    createToolbar.className = "appgenesis-create-entry-toolbar-v1";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appgenesis-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    createToolbar.appendChild(abrirBtn);

    const formPanel = document.createElement("div");
    formPanel.className = "appgenesis-create-entry-panel-v1";
    formPanel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appgenesis-create-entry-grid-v1";

    const field = document.createElement("div");
    field.className = "field appgenesis-create-entry-field-v1";

    const label = document.createElement("label");
    label.setAttribute("for", "appgenesis-create-entry-session-name-v1");
    label.textContent = "Nome da sessão *";

    const input = document.createElement("input");
    input.id = "appgenesis-create-entry-session-name-v1";
    input.type = "text";
    input.maxLength = 80;
    input.placeholder = "Informe o nome da sessão";

    const error = document.createElement("p");
    error.className = "appgenesis-create-entry-error-v1";
    error.hidden = true;
    error.textContent = "Informe o nome da sessão.";

    field.appendChild(label);
    field.appendChild(input);
    field.appendChild(error);
    grid.appendChild(field);

    const actions = document.createElement("div");
    actions.className = "appgenesis-create-entry-actions-v1";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appgenesis-create-entry-save-btn-v1";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appgenesis-create-entry-cancel-btn-v1";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    formPanel.appendChild(grid);
    formPanel.appendChild(actions);

    createBlock.appendChild(createToolbar);
    createBlock.appendChild(formPanel);

    const createEntrySlot = wrapper.querySelector(".appgenesis-create-entry-slot-v2");

    if (createEntrySlot) {
      createEntrySlot.appendChild(createBlock);
    } else {
      const createEntrySlot = wrapper.querySelector(".appgenesis-create-entry-slot-v2");

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
      input.classList.remove("appgenesis-create-entry-input-error-v1");
      input.focus();
    }

    function fecharFormularioCriacao() {
      input.value = "";
      error.hidden = true;
      input.classList.remove("appgenesis-create-entry-input-error-v1");
      formPanel.hidden = true;
      abrirBtn.hidden = false;
    }

    abrirBtn.addEventListener("click", abrirFormularioCriacao);
    vincularReacaoCancelarGlobalSessoesV1(cancelarBtn, createBlock, function () {
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
        input.classList.add("appgenesis-create-entry-input-error-v1");
        input.focus();
        return;
      }

      originalCreateBtn.click();

      const linhas = Array.from(tbody.querySelectorAll("tr.appgenesis-sidebar-section-row-v2"));
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
        labelInput.classList.remove("appgenesis-sidebar-section-label-input-editing-v2");
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
    // APPVERBO_GUARD_OBTER_CARD_CRIACAO_SESSOES_V32
    if (typeof existeServerRenderSessoes_v32 === "function" && existeServerRenderSessoes_v32()) {
      return null;
    }


if (!cardLista || !cardLista.parentElement) {
      return null;
    }

    let createCard = document.getElementById("admin-sidebar-sections-create-card");

    if (!createCard) {
      createCard = document.createElement("section");
      createCard.id = "admin-sidebar-sections-create-card";
      createCard.className = "card appgenesis-standard-create-card-v4 appgenesis-sessoes-create-card-v3";
      createCard.dataset.menuScope = "administrativo,sessoes";
      cardLista.parentElement.insertBefore(createCard, cardLista);
    }

    return createCard;
  }

  function moverBlocoCriacaoParaCardSeparadoSessoes_v3(cardLista, wrapper) {
    // APPVERBO_GUARD_MOVER_CARD_CRIACAO_SESSOES_V32
    if (typeof existeServerRenderSessoes_v32 === "function" && existeServerRenderSessoes_v32()) {
      return;
    }


const createBlock = wrapper && wrapper.querySelector(".appgenesis-create-entry-block-v1");

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

    const slotsVazios = Array.from(wrapper.querySelectorAll(".appgenesis-create-entry-slot-v2"));

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

    return "Default";
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
    field.className = "field appgenesis-create-entry-field-v5";

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

    Array.from(wrapper.querySelectorAll(".appgenesis-sidebar-sections-footer-v2")).forEach(function (footer) {
      footer.remove();
    });
  }

  function criarChaveUnicaSessoesCreate_v5(tbody, nomeSessao, linhaAtual) {
    const baseKey = criarChaveSessoesLayout_v2(nomeSessao) || "nova_sessao";
    const keysExistentes = new Set();

    Array.from(tbody.querySelectorAll("tr.appgenesis-sidebar-section-row-v2")).forEach(function (linha) {
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

    const tbody = wrapper.querySelector(".appgenesis-sidebar-sections-body-v2");
    const createBlock = document.querySelector("#admin-sidebar-sections-create-card .appgenesis-create-entry-block-v1") ||
      wrapper.querySelector(".appgenesis-create-entry-block-v1");

    if (!tbody || !createBlock) {
      removerFooterListaSessoes_v5(wrapper);
      return;
    }

    wrapper.dataset.createFieldsNomeSistemaEstadoV5 = "1";
    removerFooterListaSessoes_v5(wrapper);

    const toolbar = createBlock.querySelector(".appgenesis-create-entry-toolbar-v1") || document.createElement("div");
    toolbar.className = "appgenesis-create-entry-toolbar-v1";

    let abrirBtnAtual = toolbar.querySelector(".appgenesis-create-entry-open-btn-v1, .action-btn");

    if (!abrirBtnAtual) {
      abrirBtnAtual = document.createElement("button");
      abrirBtnAtual.type = "button";
      toolbar.appendChild(abrirBtnAtual);
    }

    const abrirBtn = abrirBtnAtual.cloneNode(true);
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appgenesis-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";
    abrirBtnAtual.replaceWith(abrirBtn);

    let formPanel = createBlock.querySelector(".appgenesis-create-entry-panel-v1");

    if (!formPanel) {
      formPanel = document.createElement("div");
      formPanel.className = "appgenesis-create-entry-panel-v1";
      createBlock.appendChild(formPanel);
    }

    formPanel.innerHTML = "";
    formPanel.hidden = true;

    if (!toolbar.parentElement) {
      createBlock.insertBefore(toolbar, createBlock.firstChild);
    }

    const grid = document.createElement("div");
    grid.className = "appgenesis-create-entry-grid-v5";

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";
    nomeInput.required = true;

    const sistemaSelect = document.createElement("select");
    sistemaSelect.required = true;

    [
      ["all", "Default"],
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
      "appgenesis-create-entry-session-name-v5",
      "Nome da sessão *",
      nomeInput
    ));

    grid.appendChild(criarFieldCriacaoSessoes_v5(
      "appgenesis-create-entry-session-system-v5",
      "Sistema *",
      sistemaSelect
    ));

    grid.appendChild(criarFieldCriacaoSessoes_v5(
      "appgenesis-create-entry-session-status-v5",
      "Estado *",
      estadoSelect
    ));

    const error = document.createElement("p");
    error.className = "appgenesis-create-entry-error-v5";
    error.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appgenesis-create-entry-actions-v5";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appgenesis-create-entry-save-btn-v5";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appgenesis-create-entry-cancel-btn-v5";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);

    formPanel.appendChild(grid);
    formPanel.appendChild(error);
    formPanel.appendChild(actions);

    function limparErros() {
      error.hidden = true;
      error.textContent = "";
      nomeInput.classList.remove("appgenesis-create-entry-input-error-v5");
      sistemaSelect.classList.remove("appgenesis-create-entry-input-error-v5");
      estadoSelect.classList.remove("appgenesis-create-entry-input-error-v5");
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
        nomeInput.classList.add("appgenesis-create-entry-input-error-v5");
        nomeInput.focus();
        return null;
      }

      if (!sistema) {
        error.textContent = "Informe o sistema da sessão.";
        error.hidden = false;
        sistemaSelect.classList.add("appgenesis-create-entry-input-error-v5");
        sistemaSelect.focus();
        return null;
      }

      if (!estado) {
        error.textContent = "Informe o estado da sessão.";
        error.hidden = false;
        estadoSelect.classList.add("appgenesis-create-entry-input-error-v5");
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
    vincularReacaoCancelarGlobalSessoesV1(cancelarBtn, formPanel, fecharFormulario);

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
    card.classList.add("appgenesis-sidebar-sections-card-v2");

    Array.from(card.querySelectorAll(".appgenesis-sidebar-sections-layout-v1, .appgenesis-sidebar-sections-layout-v2"))
      .forEach(function (elemento) {
        elemento.remove();
      });

    while (formulario.firstChild) {
      formulario.removeChild(formulario.firstChild);
    }

    formulario.appendChild(criarTabelaSessoesLayout_v2(formulario, sessoes));
  }

  function iniciarSessoesLayout_v2() {
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

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

    return fallback || "Default";
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
    const script = document.getElementById("appgenesis-sidebar-section-options-v2") ||
      document.getElementById("appgenesis-sidebar-section-options-v1");

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

  function criarBotaoAcaoSessoesV6(tipo, titulo) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appgenesis-sidebar-section-action-btn-v2 appgenesis-sidebar-section-action-btn-v6";
    botao.dataset.sidebarSectionActionV6 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = titulo;
    return botao;
  }

  // APPVERBO_SESSOES_EDIT_INLINE_V8_START
  function criarSelectSistemaSessoesV8(valorAtual) {
    const select = document.createElement("select");
    select.className = "appgenesis-sidebar-section-edit-select-v8";

    [
      ["all", "Default"],
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
    select.className = "appgenesis-sidebar-section-edit-select-v8";

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
    badge.className = "appgenesis-sidebar-section-state-badge-v2 appgenesis-sidebar-section-state-badge-" + estadoNormalizado + "-v6";
    badge.textContent = obterLabelEstadoSessoesV6(estadoNormalizado);
    return badge;
  }

  function restaurarAcoesLinhaSessoesV8(linha, tbody) {
    const tdAcoes = linha.querySelector(".appgenesis-sidebar-section-actions-cell-v2");

    if (!tdAcoes) {
      return;
    }

    tdAcoes.innerHTML = "";

    const actions = document.createElement("div");
    actions.className = "table-actions appgenesis-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoSessoesV6("up", "Subir sessão"));
    actions.appendChild(criarBotaoAcaoSessoesV6("down", "Descer sessão"));
    actions.appendChild(criarBotaoAcaoSessoesV6("view", "Exibir detalhes"));
    actions.appendChild(criarBotaoAcaoSessoesV6("edit", "Editar informações"));

    tdAcoes.appendChild(actions);
    atualizarEstadoBotoesSessoesV6(tbody);

    const tabela = linha.closest("table");
    if (tabela && window.AppVerboProcessShell && typeof window.AppVerboProcessShell.enhanceTableActionMenus === "function") {
      window.AppVerboProcessShell.enhanceTableActionMenus({ root: tabela, actionsSelector: ".table-actions" });
    }
  }

  function restaurarLinhaSessoesV8(linha, valores, tbody) {
    const campos = obterCamposLinhaSessoesV8(linha);
    const tdMenu = linha.querySelector(".appgenesis-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appgenesis-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appgenesis-sidebar-section-state-cell-v2");

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
    const tdMenu = linha.querySelector(".appgenesis-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appgenesis-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appgenesis-sidebar-section-state-cell-v2");
    const tdAcoes = linha.querySelector(".appgenesis-sidebar-section-actions-cell-v2");

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
    nomeInput.className = "appgenesis-sidebar-section-edit-input-v8";
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
    actions.className = "appgenesis-sidebar-section-edit-actions-v8";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appgenesis-sidebar-section-edit-save-v8";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appgenesis-sidebar-section-edit-cancel-v8";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);
    tdAcoes.appendChild(actions);

    function validarNome() {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        nomeInput.classList.add("appgenesis-sidebar-section-edit-input-error-v8");
        nomeInput.focus();
        return "";
      }

      nomeInput.classList.remove("appgenesis-sidebar-section-edit-input-error-v8");
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

    vincularReacaoCancelarGlobalSessoesV1(cancelarBtn, actions, function () {
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
    tr.className = "appgenesis-sidebar-section-row-v2 appgenesis-sidebar-section-row-v6";

    const keyInput = criarCampoOcultoSessoesV6("section_key", sessao.key);
    const labelInput = document.createElement("input");
    labelInput.type = "hidden";
    labelInput.name = "section_label";
    labelInput.value = sessao.label;

    const scopeInput = criarCampoOcultoSessoesV6("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");
    const statusInput = criarCampoOcultoSessoesV6("section_status", sessao.status || "ativo");

    const tdMenu = document.createElement("td");
    tdMenu.className = "appgenesis-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(scopeInput);
    tdMenu.appendChild(statusInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appgenesis-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterLabelSistemaSessoesV6(
      sessao.visibility_scope_mode,
      sessao.visibility_scope_label || "Default"
    );

    const tdEstado = document.createElement("td");
    tdEstado.className = "appgenesis-sidebar-section-state-cell-v2";

    const estado = normalizarEstadoSessoesV6(sessao.status);
    const badge = document.createElement("span");
    badge.className = "appgenesis-sidebar-section-state-badge-v2 appgenesis-sidebar-section-state-badge-" + estado + "-v6";
    badge.textContent = obterLabelEstadoSessoesV6(estado);
    tdEstado.appendChild(badge);

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appgenesis-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "table-actions appgenesis-sidebar-section-actions-v2";
    actions.appendChild(criarBotaoAcaoSessoesV6("up", "Subir sessão"));
    actions.appendChild(criarBotaoAcaoSessoesV6("down", "Descer sessão"));
    actions.appendChild(criarBotaoAcaoSessoesV6("view", "Exibir detalhes"));
    actions.appendChild(criarBotaoAcaoSessoesV6("edit", "Editar informações"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }

  function atualizarEstadoBotoesSessoesV6(tbody) {
    const linhas = Array.from(tbody.querySelectorAll("tr.appgenesis-sidebar-section-row-v6"));

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

      if (anterior && anterior.classList.contains("appgenesis-sidebar-section-row-v6")) {
        tbody.insertBefore(linha, anterior);
      }
    }

    if (direcao === "down") {
      const proxima = linha.nextElementSibling;

      if (proxima && proxima.classList.contains("appgenesis-sidebar-section-row-v6")) {
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

    formulario.appendChild(criarCampoOcultoSessoesV6("redirect_menu", "sessoes"));
    formulario.appendChild(criarCampoOcultoSessoesV6("redirect_target", "#admin-sidebar-sections-card"));

    const descricao = document.createElement("p");
    descricao.className = "appgenesis-sidebar-sections-list-description-v6";
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";

    const tableWrap = document.createElement("div");
    tableWrap.className = "appgenesis-sidebar-sections-table-wrap-v2 appgenesis-sidebar-sections-table-wrap-v6";

    const table = document.createElement("table");
    table.className = "appgenesis-sidebar-sections-table-v2 appgenesis-sidebar-sections-table-v6";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appgenesis-sidebar-sections-body-v2 appgenesis-sidebar-sections-body-v6";

    sessoes.forEach(function (sessao) {
      tbody.appendChild(criarLinhaSessoesV6(sessao));
    });

    tbody.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v6]");

      if (!botao) {
        return;
      }

      const linha = botao.closest("tr.appgenesis-sidebar-section-row-v6");
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

    if (window.AppVerboProcessShell && typeof window.AppVerboProcessShell.enhanceTableActionMenus === "function") {
      window.AppVerboProcessShell.enhanceTableActionMenus({ root: table, actionsSelector: ".table-actions" });
    }

    // Delegação document-level para clicks dentro do popup (após Process Shell fechar e devolver o popup à linha)
    if (!window.__appverboSessoesV6DocClickInstalled) {
      window.__appverboSessoesV6DocClickInstalled = true;
      document.addEventListener("click", function (event) {
        const botao = event.target.closest("[data-sidebar-section-action-v6]");
        if (!botao) {
          return;
        }
        const linha = botao.closest("tr.appgenesis-sidebar-section-row-v6");
        const acao = botao.dataset.sidebarSectionActionV6;
        if (!linha) {
          return;
        }
        const tbodyEl = linha.parentElement;
        const formularioEl = linha.closest("form");
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
          abrirEdicaoLinhaSessoesV8(linha, formularioEl, tbodyEl);
        }
      });
    }

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
      createCard.className = "card appgenesis-standard-create-card-v4 appgenesis-sessoes-create-card-v3";
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
    block.className = "appgenesis-create-entry-block-v1 appgenesis-create-entry-block-v6";

    const toolbar = document.createElement("div");
    toolbar.className = "appgenesis-create-entry-toolbar-v1";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appgenesis-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appgenesis-create-entry-panel-v1 appgenesis-create-entry-panel-v6";
    panel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appgenesis-create-entry-grid-v5 appgenesis-create-entry-grid-v6";

    const nomeField = document.createElement("div");
    nomeField.className = "field appgenesis-create-entry-field-v5";

    const nomeLabel = document.createElement("label");
    nomeLabel.textContent = "Nome da sessão *";

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";

    nomeField.appendChild(nomeLabel);
    nomeField.appendChild(nomeInput);

    const sistemaField = document.createElement("div");
    sistemaField.className = "field appgenesis-create-entry-field-v5";

    const sistemaLabel = document.createElement("label");
    sistemaLabel.textContent = "Sistema *";

    const sistemaSelect = document.createElement("select");
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV6("all", "Default"));
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV6("owner", "Owner"));
    sistemaSelect.appendChild(criarOpcaoSelectSessoesV6("legado", "Legado"));

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appgenesis-create-entry-field-v5";

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
    erro.className = "appgenesis-create-entry-error-v5";
    erro.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appgenesis-create-entry-actions-v5";

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

    vincularReacaoCancelarGlobalSessoesV1(cancelarBtn, block, limparCriacao);

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

    const linhasAtuais = card.querySelectorAll("tr.appgenesis-sidebar-section-row-v2, tr.appgenesis-sidebar-section-row-v6");

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
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

    window.setTimeout(function () {
      reidratarSessoesBdV6(false);
    }, 300);

    window.setTimeout(function () {
      const card = document.getElementById("admin-sidebar-sections-card");
      const linhas = card ? card.querySelectorAll("tr.appgenesis-sidebar-section-row-v2, tr.appgenesis-sidebar-section-row-v6") : [];

      if (!linhas || linhas.length === 0) {
        reidratarSessoesBdV6(true);
      }
    }, 900);

    window.setTimeout(function () {
      const card = document.getElementById("admin-sidebar-sections-card");
      const linhas = card ? card.querySelectorAll("tr.appgenesis-sidebar-section-row-v2, tr.appgenesis-sidebar-section-row-v6") : [];

      if (!linhas || linhas.length === 0) {
        reidratarSessoesBdV6(true);
      }
    }, 1600);

    document.addEventListener("click", function () {
      window.setTimeout(function () {
        const card = document.getElementById("admin-sidebar-sections-card");
        const linhas = card ? card.querySelectorAll("tr.appgenesis-sidebar-section-row-v2, tr.appgenesis-sidebar-section-row-v6") : [];

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

    return fallback || "Default";
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
    const script = document.getElementById("appgenesis-sidebar-section-options-v2") ||
      document.getElementById("appgenesis-sidebar-section-options-v1");

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
      createCard.className = "card appgenesis-standard-create-card-v4 appgenesis-sessoes-create-card-v3 appgenesis-sessoes-create-card-v9";
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
    botao.className = "appgenesis-sidebar-section-action-btn-v2 appgenesis-sidebar-section-action-btn-v9";
    botao.dataset.sidebarSectionActionV9 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function criarSelectSistemaEstadoV9(valorAtual) {
    const select = document.createElement("select");
    select.className = "appgenesis-sidebar-section-edit-select-v9";

    [
      ["all", "Default"],
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
    select.className = "appgenesis-sidebar-section-edit-select-v9";
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
    badge.className = "appgenesis-sidebar-section-state-badge-v2 appgenesis-sidebar-section-state-badge-" + estadoNormalizado + "-v9";
    badge.textContent = obterLabelEstadoSessoesEstadoV9(estadoNormalizado);
    return badge;
  }

  //###################################################################################
  // (5) LINHAS E TABELAS
  //###################################################################################

  function criarLinhaEstadoV9(sessao) {
    const tr = document.createElement("tr");
    tr.className = "appgenesis-sidebar-section-row-v2 appgenesis-sidebar-section-row-v9";
    tr.dataset.sectionKeyV9 = sessao.key;
    tr.dataset.sectionStatusV9 = normalizarEstadoSessoesEstadoV9(sessao.status);

    const keyInput = criarCampoOcultoSessoesEstadoV9("section_key", sessao.key);
    const labelInput = criarCampoOcultoSessoesEstadoV9("section_label", sessao.label);
    const scopeInput = criarCampoOcultoSessoesEstadoV9("section_visibility_scope_mode", sessao.visibility_scope_mode || "all");
    const statusInput = criarCampoOcultoSessoesEstadoV9("section_status", normalizarEstadoSessoesEstadoV9(sessao.status));

    const tdMenu = document.createElement("td");
    tdMenu.className = "appgenesis-sidebar-section-menu-cell-v2";
    tdMenu.textContent = sessao.label;
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(scopeInput);
    tdMenu.appendChild(statusInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appgenesis-sidebar-section-system-cell-v2";
    tdSistema.textContent = obterLabelSistemaSessoesEstadoV9(sessao.visibility_scope_mode, sessao.visibility_scope_label || "");

    const tdEstado = document.createElement("td");
    tdEstado.className = "appgenesis-sidebar-section-state-cell-v2";
    tdEstado.appendChild(criarBadgeEstadoV9(sessao.status));

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appgenesis-sidebar-section-actions-cell-v2";

    const actions = document.createElement("div");
    actions.className = "appgenesis-sidebar-section-actions-v2";
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
    bloco.className = "appgenesis-sidebar-section-list-block-v9 appgenesis-sidebar-section-list-block-" + tipo + "-v9";

    if (titulo) {
      const h3 = document.createElement("h3");
      h3.className = "appgenesis-sidebar-section-list-title-v9";
      h3.textContent = titulo;
      bloco.appendChild(h3);
    }

    const tableWrap = document.createElement("div");
    tableWrap.className = "appgenesis-sidebar-sections-table-wrap-v2 appgenesis-sidebar-sections-table-wrap-v9";

    const table = document.createElement("table");
    table.className = "appgenesis-sidebar-sections-table-v2 appgenesis-sidebar-sections-table-v9";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appgenesis-sidebar-sections-body-v2 appgenesis-sidebar-sections-body-v9";
    tbody.dataset.statusGroupV9 = tipo;

    sessoes.forEach(function (sessao) {
      tbody.appendChild(criarLinhaEstadoV9(sessao));
    });

    if (!sessoes.length) {
      const emptyRow = document.createElement("tr");
      emptyRow.className = "appgenesis-sidebar-section-empty-row-v9";

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
    const grupos = Array.from(container.querySelectorAll("tbody.appgenesis-sidebar-sections-body-v9"));

    grupos.forEach(function (tbody) {
      const linhas = Array.from(tbody.querySelectorAll("tr.appgenesis-sidebar-section-row-v9"));

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
    formulario.appendChild(criarCampoOcultoSessoesEstadoV9("redirect_menu", "sessoes"));
    formulario.appendChild(criarCampoOcultoSessoesEstadoV9("redirect_target", "#admin-sidebar-sections-card"));

    let titulo = cardLista.querySelector(".appgenesis-sidebar-section-list-main-title-v9");

    cardLista.innerHTML = "";

    titulo = document.createElement("h2");
    titulo.className = "appgenesis-sidebar-section-list-main-title-v9";
    titulo.textContent = "Sessoes do sidebar";

    const descricao = document.createElement("p");
    descricao.className = "appgenesis-sidebar-sections-list-description-v9";
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
    block.className = "appgenesis-create-entry-block-v1 appgenesis-create-entry-block-v9";

    const toolbar = document.createElement("div");
    toolbar.className = "appgenesis-create-entry-toolbar-v1 appgenesis-create-entry-toolbar-v9";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn appgenesis-create-entry-open-btn-v1";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appgenesis-create-entry-panel-v1 appgenesis-create-entry-panel-v9";
    panel.hidden = true;

    const grid = document.createElement("div");
    grid.className = "appgenesis-create-entry-grid-v5 appgenesis-create-entry-grid-v9";

    const nomeField = document.createElement("div");
    nomeField.className = "field appgenesis-create-entry-field-v5";

    const nomeLabel = document.createElement("label");
    nomeLabel.textContent = "Nome da sessão *";

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";

    nomeField.appendChild(nomeLabel);
    nomeField.appendChild(nomeInput);

    const sistemaField = document.createElement("div");
    sistemaField.className = "field appgenesis-create-entry-field-v5";

    const sistemaLabel = document.createElement("label");
    sistemaLabel.textContent = "Sistema *";

    const sistemaSelect = criarSelectSistemaEstadoV9("all");

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appgenesis-create-entry-field-v5";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = criarSelectEstadoEstadoV9("ativo");

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const erro = document.createElement("p");
    erro.className = "appgenesis-create-entry-error-v5 appgenesis-create-entry-error-v9";
    erro.hidden = true;

    const actions = document.createElement("div");
    actions.className = "appgenesis-create-entry-actions-v5 appgenesis-create-entry-actions-v9";

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

    vincularReacaoCancelarGlobalSessoesV1(cancelarBtn, block, fechar);

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

    const tdMenu = linha.querySelector(".appgenesis-sidebar-section-menu-cell-v2");
    const tdSistema = linha.querySelector(".appgenesis-sidebar-section-system-cell-v2");
    const tdEstado = linha.querySelector(".appgenesis-sidebar-section-state-cell-v2");
    const tdAcoes = linha.querySelector(".appgenesis-sidebar-section-actions-cell-v2");

    if (!tdMenu || !tdSistema || !tdEstado || !tdAcoes) {
      return;
    }

    const nomeInput = document.createElement("input");
    nomeInput.type = "text";
    nomeInput.className = "appgenesis-sidebar-section-edit-input-v9";
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
    actions.className = "appgenesis-sidebar-section-edit-actions-v9";

    const guardarBtn = document.createElement("button");
    guardarBtn.type = "button";
    guardarBtn.className = "action-btn appgenesis-sidebar-section-edit-save-v9";
    guardarBtn.textContent = "Guardar";

    const cancelarBtn = document.createElement("button");
    cancelarBtn.type = "button";
    cancelarBtn.className = "action-btn-cancel appgenesis-sidebar-section-edit-cancel-v9";
    cancelarBtn.textContent = "Cancelar";

    actions.appendChild(guardarBtn);
    actions.appendChild(cancelarBtn);
    tdAcoes.appendChild(actions);

    guardarBtn.addEventListener("click", function () {
      const nome = String(nomeInput.value || "").trim();

      if (!nome) {
        nomeInput.classList.add("appgenesis-sidebar-section-edit-input-error-v9");
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

    vincularReacaoCancelarGlobalSessoesV1(cancelarBtn, actions, function () {
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

      const linha = botao.closest("tr.appgenesis-sidebar-section-row-v9");

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
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

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
      Boolean(card.querySelector(".appgenesis-sidebar-section-row-v10, .appgenesis-sidebar-section-row-v9, .appgenesis-sidebar-section-row-v6, .appgenesis-sidebar-section-row-v2"));
  }

  function urlApontaParaSessoesV12() {
    const hash = normalizarTextoSessoesScopeV12(window.location.hash);
    const search = normalizarTextoSessoesScopeV12(window.location.search);
    const href = normalizarTextoSessoesScopeV12(window.location.href);

    return hash.includes("admin-sidebar-sections-card") ||
      search.includes("target=admin-sidebar-sections-card") ||
      search.includes("target=admin-sidebar-sections-form-card") ||
      search.includes("admin_tab=sessoes") ||
      search.includes("admin_tab=sessões") ||
      search.includes("sidebar_section_edit_key=") ||
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
      document.body.classList.add("appgenesis-admin-sessoes-active-v12");
      document.body.classList.remove("appgenesis-admin-sessoes-inactive-v12");
    }
    else {
      document.body.classList.remove("appgenesis-admin-sessoes-active-v12");
      document.body.classList.add("appgenesis-admin-sessoes-inactive-v12");
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
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

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
// Desativado pelo fluxo nativo V30.
// Motivo: renderizava card antigo por JS.
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
// Desativado pelo fluxo nativo V30.
// Motivo: controlava fluxo visual antigo.
// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END

// APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesPersistirEstadoV19(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function normalizarEstadoSessoesPersistirEstadoV19(valor) {
    const cleanValor = normalizarTextoSessoesPersistirEstadoV19(valor);

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(cleanValor)) {
      return "inativo";
    }

    return "ativo";
  }

  //###################################################################################
  // (2) URL DE RETORNO SEGURA DA ABA SESSOES
  //###################################################################################

  function obterReturnUrlSessoesPersistirEstadoV19() {
    const url = new URL(window.location.href);

    url.searchParams.delete("settings_edit_key");
    url.searchParams.delete("settings_action");
    url.searchParams.delete("settings_tab");
    url.searchParams.delete("sidebar_section_edit_key");
    url.searchParams.delete("sidebar_section_return_url");
    url.searchParams.delete("success");
    url.searchParams.delete("error");

    url.searchParams.set("menu", "sessoes");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (3) FORCAR STATUS NO FORMULARIO DEDICADO
  //###################################################################################

  function prepararFormularioSessaoPersistirEstadoV19(formulario) {
    if (!formulario) {
      return;
    }

    const action = String(formulario.getAttribute("action") || "");

    if (!action.includes("/settings/menu/sidebar-section-save")) {
      return;
    }

    const estadoSelect = formulario.querySelector('select[name="section_status"]');
    const estadoValue = normalizarEstadoSessoesPersistirEstadoV19(
      estadoSelect ? estadoSelect.value : "ativo"
    );

    Array.from(formulario.querySelectorAll('input[name="section_status_override_v19"]')).forEach(function (input) {
      input.remove();
    });

    const estadoOverride = document.createElement("input");
    estadoOverride.type = "hidden";
    estadoOverride.name = "section_status_override_v19";
    estadoOverride.value = estadoValue;
    formulario.appendChild(estadoOverride);

    let returnInput = formulario.querySelector('input[name="sidebar_section_return_url"]');

    if (!returnInput) {
      returnInput = document.createElement("input");
      returnInput.type = "hidden";
      returnInput.name = "sidebar_section_return_url";
      formulario.appendChild(returnInput);
    }

    returnInput.value = obterReturnUrlSessoesPersistirEstadoV19();
  }

  function instalarSubmitPersistirEstadoV19() {
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

    if (window.__appverboSessoesPersistirEstadoV19 === true) {
      return;
    }

    window.__appverboSessoesPersistirEstadoV19 = true;

    document.addEventListener("submit", function (event) {
      prepararFormularioSessaoPersistirEstadoV19(event.target);
    }, true);

    document.addEventListener("click", function (event) {
      const botaoSubmit = event.target.closest('button[type="submit"], input[type="submit"]');

      if (!botaoSubmit) {
        return;
      }

      const formulario = botaoSubmit.form || botaoSubmit.closest("form");

      prepararFormularioSessaoPersistirEstadoV19(formulario);
    }, true);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarSubmitPersistirEstadoV19);
  }
  else {
    instalarSubmitPersistirEstadoV19();
  }
})();
// APPVERBO_SESSOES_PERSISTIR_ESTADO_V19_END

// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START
// Desativado pelo fluxo nativo V30.
// Motivo: recriava lista por fetch.
// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END

// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START
// Desativado pelo fluxo nativo V30.
// Motivo: forçava URL/aba de Sessões.
// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END

// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START
// Desativado pelo fluxo nativo V30.
// Motivo: reconstruía cards por JS.
// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END

// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START
// Desativado pelo fluxo nativo V30.
// Motivo: reconstruía formulários/listas por JS.
// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END

// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_START
// Desativado pelo fluxo nativo V30.
// Motivo: hidratava ações antigas.
// APPVERBO_SESSOES_INATIVAS_ACOES_VISIVEIS_V24_END

// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_START
// Desativado pelo fluxo nativo V30.
// Motivo: controlava visibilidade paralela.
// APPVERBO_SESSOES_SERVER_RENDER_IGUAL_ENTIDADE_V25_END

// APPVERBO_SESSOES_ATIVAS_CARD_V23_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZAÇÃO
  //###################################################################################

  function normalizarTextoSessoesAtivasV23(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesAtivasV23(valor) {
    return normalizarTextoSessoesAtivasV23(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function estadoSessaoAtivaV23(sessao) {
    if (sessao && sessao.is_active === false) {
      return "inativo";
    }

    const estado = normalizarTextoSessoesAtivasV23(
      sessao ? (sessao.status || sessao.status_label || sessao.estado || "") : ""
    );

    if (["inativo", "inactive", "0", "false", "nao", "não", "off", "disabled"].includes(estado)) {
      return "inativo";
    }

    return "ativo";
  }

  function labelSistemaSessoesAtivasV23(valor, fallback) {
    const sistema = normalizarTextoSessoesAtivasV23(valor);

    if (sistema === "owner") {
      return "Owner";
    }

    if (sistema === "legado") {
      return "Legado";
    }

    return fallback || "Default";
  }

  function normalizarSessaoAtivaV23(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || sessao.menu_label || "").trim();
    const key = criarChaveSessoesAtivasV23(sessao.key || sessao.section_key || sessao.slug || label);

    if (!label || !key) {
      return null;
    }

    const status = estadoSessaoAtivaV23(sessao);
    const sistemaValor = String(sessao.visibility_scope_mode || sessao.scope_mode || sessao.system || sessao.sistema || "all").trim() || "all";

    return {
      key: key,
      label: label,
      visibility_scope_mode: sistemaValor,
      visibility_scope_label: sessao.visibility_scope_label || labelSistemaSessoesAtivasV23(sistemaValor, ""),
      status: status,
      status_label: status === "ativo" ? "Ativo" : "Inativo",
      is_active: status === "ativo"
    };
  }

  //###################################################################################
  // (2) DETETAR ABA SESSÕES
  //###################################################################################

  function abaSessoesAtivaV24() {
    const url = new URL(window.location.href);
    const adminTab = normalizarTextoSessoesAtivasV23(url.searchParams.get("admin_tab"));
    const sidebarTab = normalizarTextoSessoesAtivasV23(url.searchParams.get("sidebar_sections_tab"));

    if (adminTab === "sessoes") {
      return true;
    }

    if (sidebarTab === "sessoes") {
      return true;
    }

    const activeTab = Array.from(document.querySelectorAll("button, a, [role='tab']"))
      .find((element) => {
        const text = normalizarTextoSessoesAtivasV23(element.textContent);
        const className = String(element.className || "");
        return text === "sessoes" && (
          className.includes("active") ||
          element.getAttribute("aria-selected") === "true"
        );
      });

    return Boolean(activeTab);
  }

  function removerCardSessoesAtivasForaDoSubprocessoV24() {
    if (abaSessoesAtivaV24()) {
      return;
    }

    document.querySelectorAll("#admin-sidebar-sections-active-card-v23").forEach((element) => {
      element.remove();
    });
  }

  //###################################################################################
  // (3) LER DADOS DO BACKEND/HTML
  //###################################################################################

  function lerSplitBackendSessoesAtivasV23() {
    const script = document.getElementById("appgenesis-sidebar-section-split-v22");

    if (!script) {
      return {
        active: [],
        inactive: []
      };
    }

    try {
      const parsed = JSON.parse(script.textContent || "{}");

      return {
        active: Array.isArray(parsed.active) ? parsed.active : [],
        inactive: Array.isArray(parsed.inactive) ? parsed.inactive : []
      };
    }
    catch (error) {
      console.warn("APPVERBO V23: falha ao ler split backend de Sessões.", error);
      return {
        active: [],
        inactive: []
      };
    }
  }

  function lerOptionsBackendSessoesAtivasV23() {
    const script = document.getElementById("appgenesis-sidebar-section-options-v2");

    if (!script) {
      return [];
    }

    try {
      const parsed = JSON.parse(script.textContent || "[]");
      return Array.isArray(parsed) ? parsed : [];
    }
    catch (error) {
      console.warn("APPVERBO V23: falha ao ler opções de Sessões.", error);
      return [];
    }
  }

  function separarSessoesAtivasV23(lista) {
    const normalizadas = (Array.isArray(lista) ? lista : [])
      .map(normalizarSessaoAtivaV23)
      .filter(Boolean);

    return {
      active: normalizadas.filter((sessao) => sessao.status === "ativo"),
      inactive: normalizadas.filter((sessao) => sessao.status !== "ativo")
    };
  }

  function obterSessoesIniciaisV23() {
    const split = lerSplitBackendSessoesAtivasV23();
    const active = split.active.map(normalizarSessaoAtivaV23).filter(Boolean);
    const inactive = split.inactive.map(normalizarSessaoAtivaV23).filter(Boolean);

    if (active.length > 0 || inactive.length > 0) {
      return {
        active: active,
        inactive: inactive
      };
    }

    return separarSessoesAtivasV23(lerOptionsBackendSessoesAtivasV23());
  }

  function extrairListaRespostaSessoesAtivasV23(payload) {
    if (Array.isArray(payload)) {
      return payload;
    }

    if (!payload || typeof payload !== "object") {
      return [];
    }

    const possibleKeys = [
      "sidebar_sections",
      "sections",
      "items",
      "data",
      "results",
      "sidebar_section_options"
    ];

    for (const key of possibleKeys) {
      if (Array.isArray(payload[key])) {
        return payload[key];
      }
    }

    if (payload.data && typeof payload.data === "object") {
      for (const key of possibleKeys) {
        if (Array.isArray(payload.data[key])) {
          return payload.data[key];
        }
      }
    }

    return [];
  }

  //###################################################################################
  // (4) URL DE EDIÇÃO
  //###################################################################################

  function urlEditarSessaoAtivaV23(chave) {
    const url = new URL(window.location.href);

    [
      "dynamic_process_section",
      "settings_edit_key",
      "settings_action",
      "settings_tab",
      "sidebar_section_return_url",
      "appverbo_after_save",
      "success",
      "error"
    ].forEach((parametro) => {
      url.searchParams.delete(parametro);
    });

    url.searchParams.set("menu", "sessoes");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.searchParams.set("sidebar_section_edit_key", criarChaveSessoesAtivasV23(chave));
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (5) RENDERIZAR CARD DE SESSÕES ATIVAS
  //###################################################################################

  function encontrarCardInativasSessoesV23() {
    const direct = document.getElementById("admin-sidebar-sections-inactive-card");

    if (direct) {
      return direct;
    }

    return Array.from(document.querySelectorAll("section.card, .card"))
      .find((element) => normalizarTextoSessoesAtivasV23(element.textContent).includes("sessoes inativas")) || null;
  }

  function encontrarAncoraSessoesV23() {
    const inactiveCard = encontrarCardInativasSessoesV23();

    if (inactiveCard) {
      return inactiveCard;
    }

    return document.getElementById("admin-sidebar-sections-card") ||
      document.querySelector("[data-sidebar-sections-card]") ||
      document.querySelector(".appgenesis-sidebar-sections-card") ||
      document.querySelector(".content .container");
  }

  function criarBotaoEditarSessaoAtivaV23(sessao) {
    const link = document.createElement("a");
    link.className = "appgenesis-sidebar-section-action-btn-v23";
    link.href = urlEditarSessaoAtivaV23(sessao.key);
    link.title = "Editar sessão";
    link.setAttribute("aria-label", "Editar sessão");
    link.textContent = "✎";
    return link;
  }

  function criarBadgeSessaoAtivaV23() {
    const badge = document.createElement("span");
    badge.className = "appgenesis-sidebar-section-state-badge-v23 appgenesis-sidebar-section-state-badge-ativo-v23";
    badge.textContent = "Ativo";
    return badge;
  }

  function renderizarCardSessoesAtivasV23(sessoesAtivas) {
    if (!abaSessoesAtivaV24()) {
      return;
    }

    const anchor = encontrarAncoraSessoesV23();

    if (!anchor || !anchor.parentElement) {
      return;
    }

    document.querySelectorAll("#admin-sidebar-sections-active-card-v23").forEach((element) => {
      element.remove();
    });

    const card = document.createElement("section");
    card.id = "admin-sidebar-sections-active-card-v23";
    card.className = "card appgenesis-sidebar-sections-active-card-v23";
    card.dataset.menuScope = "administrativo,sessoes";

    const title = document.createElement("h2");
    title.textContent = "Sessões ativas";
    card.appendChild(title);

    if (!Array.isArray(sessoesAtivas) || sessoesAtivas.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty appgenesis-sidebar-section-empty-v23";
      empty.textContent = "Sem sessões ativas.";
      card.appendChild(empty);
    }
    else {
      const table = document.createElement("table");
      table.className = "appgenesis-sidebar-sections-table-v23";

      const thead = document.createElement("thead");
      thead.innerHTML = "<tr><th>Menu lateral</th><th>Sistema</th><th>Estado</th><th>Ações</th></tr>";
      table.appendChild(thead);

      const tbody = document.createElement("tbody");

      sessoesAtivas.forEach((sessao) => {
        const row = document.createElement("tr");

        const tdName = document.createElement("td");
        tdName.textContent = sessao.label;

        const tdSystem = document.createElement("td");
        tdSystem.textContent = sessao.visibility_scope_label || labelSistemaSessoesAtivasV23(sessao.visibility_scope_mode, "");

        const tdStatus = document.createElement("td");
        tdStatus.appendChild(criarBadgeSessaoAtivaV23());

        const tdActions = document.createElement("td");
        tdActions.className = "appgenesis-sidebar-section-actions-cell-v23";
        tdActions.appendChild(criarBotaoEditarSessaoAtivaV23(sessao));

        row.appendChild(tdName);
        row.appendChild(tdSystem);
        row.appendChild(tdStatus);
        row.appendChild(tdActions);

        tbody.appendChild(row);
      });

      table.appendChild(tbody);
      card.appendChild(table);
    }

    anchor.parentElement.insertBefore(card, anchor);
  }

  //###################################################################################
  // (6) EXECUÇÃO
  //###################################################################################

  function iniciarSessoesAtivasV23() {
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

    if (!abaSessoesAtivaV24()) {
      removerCardSessoesAtivasForaDoSubprocessoV24();
      return;
    }

    const initial = obterSessoesIniciaisV23();
    renderizarCardSessoesAtivasV23(initial.active);

    fetch("/settings/menu/sidebar-sections-data", {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Accept": "application/json"
      }
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
      })
      .then((payload) => {
        const lista = extrairListaRespostaSessoesAtivasV23(payload);
        const split = separarSessoesAtivasV23(lista);

        if (split.active.length > 0 || split.inactive.length > 0) {
          renderizarCardSessoesAtivasV23(split.active);
        }
      })
      .catch((error) => {
        console.warn("APPVERBO V23: fallback usado para sessões ativas.", error);
      });
  }

  document.addEventListener("DOMContentLoaded", iniciarSessoesAtivasV23);

  window.addEventListener("popstate", () => {
    window.setTimeout(iniciarSessoesAtivasV23, 100);
  });

  document.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const tab = target.closest("button, a, [role='tab']");

    if (!tab) {
      return;
    }

    if (normalizarTextoSessoesAtivasV23(tab.textContent) === "sessoes") {
      window.setTimeout(iniciarSessoesAtivasV23, 250);
    }
  });
}());
// APPVERBO_SESSOES_ATIVAS_CARD_V23_END

// APPVERBO_SESSOES_APENAS_SUBPROCESSO_V25_START
(function () {
  "use strict";

  function normalizarTextoSessaoOnlyV25(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterTextoBotaoAdminAtivoV25() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab']"));

    const ativo = candidatos.find((elemento) => {
      const texto = normalizarTextoSessaoOnlyV25(elemento.textContent);

      if (!["entidade", "utilizador", "menu", "sessoes"].includes(texto)) {
        return false;
      }

      const className = String(elemento.className || "");
      const ariaSelected = elemento.getAttribute("aria-selected");
      const ariaCurrent = elemento.getAttribute("aria-current");

      return (
        className.includes("active") ||
        className.includes("is-active") ||
        className.includes("selected") ||
        ariaSelected === "true" ||
        ariaCurrent === "page"
      );
    });

    return ativo ? normalizarTextoSessaoOnlyV25(ativo.textContent) : "";
  }

  function estaNoSubprocessoSessoesRealV25() {
    const textoAtivo = obterTextoBotaoAdminAtivoV25();

    if (textoAtivo) {
      return textoAtivo === "sessoes";
    }

    const url = new URL(window.location.href);
    const adminTab = normalizarTextoSessaoOnlyV25(url.searchParams.get("admin_tab"));
    const sidebarTab = normalizarTextoSessaoOnlyV25(url.searchParams.get("sidebar_sections_tab"));

    return adminTab === "sessoes" && sidebarTab === "sessoes";
  }

  function obterCardsSessoesV25() {
    const cards = Array.from(document.querySelectorAll("section.card, div.card, .card"));

    return cards.filter((card) => {
      const titulo = Array.from(card.querySelectorAll("h1, h2, h3, .card-title"))
        .map((elemento) => normalizarTextoSessaoOnlyV25(elemento.textContent))
        .find(Boolean) || "";

      return titulo === "sessoes ativas" || titulo === "sessoes inativas";
    });
  }

  function aplicarVisibilidadeCardsSessoesV25() {
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

    const deveMostrar = estaNoSubprocessoSessoesRealV25();

    obterCardsSessoesV25().forEach((card) => {
      if (deveMostrar) {
        card.removeAttribute("hidden");
        card.style.display = "";
      }
      else {
        card.setAttribute("hidden", "hidden");
        card.style.display = "none";
      }
    });

    if (!deveMostrar) {
      document.querySelectorAll("#admin-sidebar-sections-active-card-v23").forEach((card) => {
        card.remove();
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    aplicarVisibilidadeCardsSessoesV25();
    window.setTimeout(aplicarVisibilidadeCardsSessoesV25, 100);
    window.setTimeout(aplicarVisibilidadeCardsSessoesV25, 400);
    window.setTimeout(aplicarVisibilidadeCardsSessoesV25, 900);
  });

  document.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const tab = target.closest("button, a, [role='tab']");

    if (!tab) {
      return;
    }

    const texto = normalizarTextoSessaoOnlyV25(tab.textContent);

    if (["entidade", "utilizador", "menu", "sessoes"].includes(texto)) {
      window.setTimeout(aplicarVisibilidadeCardsSessoesV25, 50);
      window.setTimeout(aplicarVisibilidadeCardsSessoesV25, 250);
      window.setTimeout(aplicarVisibilidadeCardsSessoesV25, 700);
    }
  });

  window.addEventListener("popstate", () => {
    window.setTimeout(aplicarVisibilidadeCardsSessoesV25, 100);
  });

  window.AppVerboAplicarVisibilidadeCardsSessoesV25 = aplicarVisibilidadeCardsSessoesV25;
}());
// APPVERBO_SESSOES_APENAS_SUBPROCESSO_V25_END


// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_START
// Desativado pelo fluxo nativo V30.
// Motivo: forçava reaparecimento por JS.
// APPVERBO_SESSOES_REEXIBIR_CRIAR_AO_RETORNAR_V27_END

// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_START
// Desativado pelo fluxo nativo V30.
// Motivo: controlava visibilidade paralela.
// APPVERBO_SESSOES_CORRIGIR_V28_REMOVER_DUPLICADOS_V29_END

// APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_START
(function () {
  "use strict";

  //###################################################################################
  // (1) VISUALIZAR DETALHES
  //###################################################################################

  function instalarVisualizarSessaoV30() {
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

    if (window.__appverboSessoesVisualizarV30 === true) {
      return;
    }

    window.__appverboSessoesVisualizarV30 = true;

    document.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sessao-view-v30]");

      if (!botao) {
        return;
      }

      event.preventDefault();

      alert(
        "Nome da sessão: " + (botao.dataset.sessaoLabel || "") +
        "\nSistema: " + (botao.dataset.sessaoSistema || "") +
        "\nEstado: " + (botao.dataset.sessaoEstado || "")
      );
    });
  }

  //###################################################################################
  // (2) INICIAR
  //###################################################################################

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarVisualizarSessaoV30);
  }
  else {
    instalarVisualizarSessaoV30();
  }
})();
// APPVERBO_SESSOES_FLUXO_NATIVO_IGUAL_ENTIDADE_V30_END

// APPVERBO_SESSOES_SEM_PISCAR_V26_START
(function () {
  "use strict";

  function normalizarTextoSessoesSemPiscarV26(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function obterSubprocessoAtivoSessoesSemPiscarV26() {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab']"));

    const ativo = candidatos.find((elemento) => {
      const texto = normalizarTextoSessoesSemPiscarV26(elemento.textContent);

      if (!["entidade", "utilizador", "menu", "sessoes"].includes(texto)) {
        return false;
      }

      const className = String(elemento.className || "");
      return (
        className.includes("active") ||
        className.includes("is-active") ||
        className.includes("selected") ||
        elemento.getAttribute("aria-selected") === "true" ||
        elemento.getAttribute("aria-current") === "page"
      );
    });

    return ativo ? normalizarTextoSessoesSemPiscarV26(ativo.textContent) : "";
  }

  function estaNoSubprocessoSessoesSemPiscarV26() {
    const subprocessoAtivo = obterSubprocessoAtivoSessoesSemPiscarV26();

    if (subprocessoAtivo) {
      return subprocessoAtivo === "sessoes";
    }

    const url = new URL(window.location.href);
    const adminTab = normalizarTextoSessoesSemPiscarV26(url.searchParams.get("admin_tab"));
    const sidebarTab = normalizarTextoSessoesSemPiscarV26(url.searchParams.get("sidebar_sections_tab"));

    return adminTab === "sessoes" && sidebarTab === "sessoes";
  }

  function cardEhSessoesSemPiscarV26(card) {
    if (!card || !card.querySelectorAll) {
      return false;
    }

    if (
      card.id === "admin-sidebar-sections-active-card-v23" ||
      card.id === "admin-sidebar-sections-inactive-card" ||
      card.classList.contains("appgenesis-sidebar-sections-active-card-v23") ||
      card.getAttribute("data-appgenesis-sessoes-card-v26") === "1"
    ) {
      return true;
    }

    const titulo = Array.from(card.querySelectorAll("h1, h2, h3, .card-title"))
      .map((elemento) => normalizarTextoSessoesSemPiscarV26(elemento.textContent))
      .find(Boolean) || "";

    return titulo === "sessoes ativas" || titulo === "sessoes inativas";
  }

  function obterCardsSessoesSemPiscarV26(root) {
    const base = root && root.querySelectorAll ? root : document;
    const cards = Array.from(base.querySelectorAll("section.card, div.card, .card"));

    if (root && root.matches && root.matches("section.card, div.card, .card")) {
      cards.unshift(root);
    }

    return cards.filter(cardEhSessoesSemPiscarV26);
  }

  function aplicarClassesHtmlSessoesSemPiscarV26() {
    const deveMostrar = estaNoSubprocessoSessoesSemPiscarV26();

    document.documentElement.classList.toggle("appgenesis-subprocesso-sessoes-v26", deveMostrar);
    document.documentElement.classList.toggle("appgenesis-subprocesso-nao-sessoes-v26", !deveMostrar);

    return deveMostrar;
  }

  function aplicarVisibilidadeSessoesSemPiscarV26(root) {
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

    const deveMostrar = aplicarClassesHtmlSessoesSemPiscarV26();
    const cards = obterCardsSessoesSemPiscarV26(root);

    cards.forEach((card) => {
      card.setAttribute("data-appgenesis-sessoes-card-v26", "1");

      if (deveMostrar) {
        card.removeAttribute("hidden");
        card.style.removeProperty("display");
        card.style.removeProperty("visibility");
      }
      else {
        card.setAttribute("hidden", "hidden");
        card.style.setProperty("display", "none", "important");
        card.style.setProperty("visibility", "hidden", "important");
      }
    });
  }

  function removerParametrosSessoesQuandoNaoSessoesV26(nomeSubprocesso) {
    const subprocesso = normalizarTextoSessoesSemPiscarV26(nomeSubprocesso);

    if (!subprocesso || subprocesso === "sessoes") {
      return;
    }

    const url = new URL(window.location.href);
    let alterou = false;

    ["sidebar_sections_tab", "sidebar_section_edit_key", "target"].forEach((parametro) => {
      if (url.searchParams.has(parametro)) {
        url.searchParams.delete(parametro);
        alterou = true;
      }
    });

    if (normalizarTextoSessoesSemPiscarV26(url.searchParams.get("admin_tab")) === "sessoes") {
      url.searchParams.set("admin_tab", subprocesso);
      alterou = true;
    }

    if (url.hash === "#admin-sidebar-sections-card") {
      url.hash = "";
      alterou = true;
    }

    if (alterou) {
      window.history.replaceState(window.history.state, document.title, url.pathname + url.search + url.hash);
    }
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      Array.from(mutation.addedNodes || []).forEach((node) => {
        if (node && node.nodeType === 1) {
          aplicarVisibilidadeSessoesSemPiscarV26(node);
        }
      });
    });
  });

  function iniciarSessoesSemPiscarV26() {
    if (typeof shouldDisableLegacySidebarSectionsRuntimeV1 === "function" && shouldDisableLegacySidebarSectionsRuntimeV1()) {
      return;
    }

    aplicarVisibilidadeSessoesSemPiscarV26(document);

    if (!observer.__appverboStartedV26) {
      observer.observe(document.documentElement, {
        childList: true,
        subtree: true
      });
      observer.__appverboStartedV26 = true;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    iniciarSessoesSemPiscarV26();
    window.setTimeout(() => aplicarVisibilidadeSessoesSemPiscarV26(document), 0);
    window.setTimeout(() => aplicarVisibilidadeSessoesSemPiscarV26(document), 50);
    window.setTimeout(() => aplicarVisibilidadeSessoesSemPiscarV26(document), 150);
    window.setTimeout(() => aplicarVisibilidadeSessoesSemPiscarV26(document), 400);
  });

  document.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;

    if (!target) {
      return;
    }

    const tab = target.closest("button, a, [role='tab']");

    if (!tab) {
      return;
    }

    const texto = normalizarTextoSessoesSemPiscarV26(tab.textContent);

    if (["entidade", "utilizador", "menu", "sessoes"].includes(texto)) {
      removerParametrosSessoesQuandoNaoSessoesV26(texto);
      aplicarVisibilidadeSessoesSemPiscarV26(document);
      window.setTimeout(() => aplicarVisibilidadeSessoesSemPiscarV26(document), 0);
      window.setTimeout(() => aplicarVisibilidadeSessoesSemPiscarV26(document), 50);
      window.setTimeout(() => aplicarVisibilidadeSessoesSemPiscarV26(document), 200);
    }
  }, true);

  window.addEventListener("popstate", () => {
    window.setTimeout(() => aplicarVisibilidadeSessoesSemPiscarV26(document), 50);
  });

  iniciarSessoesSemPiscarV26();
  window.AppVerboAplicarVisibilidadeSessoesSemPiscarV26 = aplicarVisibilidadeSessoesSemPiscarV26;
}());
// APPVERBO_SESSOES_SEM_PISCAR_V26_END
