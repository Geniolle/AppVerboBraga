(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesLayout_v1(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesLayout_v1(valor) {
    return normalizarTextoSessoesLayout_v1(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function textoVisivelSessoesLayout_v1(valor, textoPadrao) {
    const texto = String(valor || "").trim();
    return texto || textoPadrao || "";
  }

  function dispararEventoSessoesLayout_v1(elemento, nomeEvento) {
    if (!elemento) {
      return;
    }

    elemento.dispatchEvent(new Event(nomeEvento, {
      bubbles: true,
      cancelable: true
    }));
  }

  //###################################################################################
  // (2) LOCALIZAR CARD E FORMULARIO
  //###################################################################################

  function obterCardSessoesLayout_v1() {
    const cardPorId = document.getElementById("admin-sidebar-sections-card");

    if (cardPorId) {
      return cardPorId;
    }

    const cards = Array.from(document.querySelectorAll(".card, section"));

    return cards.find(function (card) {
      const textos = Array.from(card.querySelectorAll("h1, h2, h3, h4, strong"))
        .map(function (item) {
          return normalizarTextoSessoesLayout_v1(item.textContent);
        })
        .join(" ");

      return textos.includes("sessoes do sidebar") ||
        textos.includes("sessoes criadas") ||
        textos.includes("sessoes");
    }) || null;
  }

  function obterFormularioSessoesLayout_v1(card) {
    if (!card) {
      return null;
    }

    return card.querySelector('form[action*="/settings/menu/sidebar-sections"]') ||
      card.querySelector('form[action*="sidebar-sections"]') ||
      card.querySelector("form");
  }

  function obterLinhaOriginalSessoesLayout_v1(elemento) {
    if (!elemento) {
      return null;
    }

    return elemento.closest("tr") ||
      elemento.closest(".sidebar-section-row") ||
      elemento.closest(".settings-row") ||
      elemento.closest(".menu-row") ||
      elemento.closest(".field") ||
      elemento.parentElement;
  }

  //###################################################################################
  // (3) RECOLHER CAMPOS EXISTENTES
  //###################################################################################

  function obterCampoLabelPorIndiceSessoesLayout_v1(formulario, indice) {
    const campos = Array.from(formulario.querySelectorAll('input[name="section_label"], input[name*="section_label"]'));
    return campos[indice] || null;
  }

  function obterCampoChavePorIndiceSessoesLayout_v1(formulario, indice) {
    const campos = Array.from(formulario.querySelectorAll('input[name="section_key"], input[name*="section_key"]'));
    return campos[indice] || null;
  }

  function obterCampoVisibilidadePorIndiceSessoesLayout_v1(formulario, indice) {
    const campos = Array.from(formulario.querySelectorAll(
      'select[name="section_visibility_scope_mode"], select[name*="section_visibility_scope_mode"], input[name="section_visibility_scope_mode"], input[name*="section_visibility_scope_mode"]'
    ));
    return campos[indice] || null;
  }

  function criarCampoOcultoSessoesLayout_v1(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  function criarCampoLabelSessoesLayout_v1(valor) {
    const input = document.createElement("input");
    input.type = "text";
    input.name = "section_label";
    input.value = valor || "";
    input.className = "appverbo-sidebar-section-label-input-v1";
    input.placeholder = "Nome da sessão";
    return input;
  }

  function criarCampoChaveSessoesLayout_v1(valor) {
    return criarCampoOcultoSessoesLayout_v1("section_key", valor || "");
  }

  function criarCampoVisibilidadeSessoesLayout_v1(valor) {
    return criarCampoOcultoSessoesLayout_v1("section_visibility_scope_mode", valor || "all");
  }

  function recolherLinhasSessoesLayout_v1(formulario) {
    const labels = Array.from(formulario.querySelectorAll('input[name="section_label"], input[name*="section_label"]'));
    const linhas = [];

    labels.forEach(function (labelInput, indice) {
      const keyInput = obterCampoChavePorIndiceSessoesLayout_v1(formulario, indice) ||
        criarCampoChaveSessoesLayout_v1("");

      const visibilityInput = obterCampoVisibilidadePorIndiceSessoesLayout_v1(formulario, indice) ||
        criarCampoVisibilidadeSessoesLayout_v1("all");

      const linhaOriginal = obterLinhaOriginalSessoesLayout_v1(labelInput);

      linhas.push({
        keyInput: keyInput,
        labelInput: labelInput,
        visibilityInput: visibilityInput,
        originalRow: linhaOriginal
      });
    });

    return linhas;
  }

  function removerEstruturaOriginalSessoesLayout_v1(linhas) {
    const removidos = new Set();

    linhas.forEach(function (linha) {
      if (linha.originalRow && linha.originalRow.parentElement && !removidos.has(linha.originalRow)) {
        removidos.add(linha.originalRow);
        linha.originalRow.remove();
      }
    });
  }

  function moverCamposOcultosGlobaisSessoesLayout_v1(formulario, destino) {
    const campos = Array.from(formulario.querySelectorAll("input[type='hidden']"));

    campos.forEach(function (campo) {
      const nome = String(campo.name || "");

      if (
        nome.includes("section_key") ||
        nome.includes("section_label") ||
        nome.includes("section_visibility_scope_mode")
      ) {
        return;
      }

      destino.appendChild(campo);
    });
  }

  //###################################################################################
  // (4) SISTEMA, ESTADO E ACOES
  //###################################################################################

  function obterSistemaSessoesLayout_v1(chave, label) {
    const texto = normalizarTextoSessoesLayout_v1(chave || label);

    if (["home", "perfil", "meu_perfil", "empresa", "dados_gerais", "igreja"].includes(texto)) {
      return "Owner e Legado";
    }

    if (["administrativo", "sistema"].includes(texto)) {
      return "Owner";
    }

    return "Owner";
  }

  function criarBotaoAcaoSessoesLayout_v1(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v1";
    botao.dataset.sidebarSectionActionV1 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function atualizarEstadoBotoesSessoesLayout_v1(tbody) {
    const linhas = Array.from(tbody.querySelectorAll("tr.appverbo-sidebar-section-row-v1"));

    linhas.forEach(function (linha, indice) {
      const botaoSubir = linha.querySelector('[data-sidebar-section-action-v1="up"]');
      const botaoDescer = linha.querySelector('[data-sidebar-section-action-v1="down"]');

      if (botaoSubir) {
        botaoSubir.disabled = indice === 0;
      }

      if (botaoDescer) {
        botaoDescer.disabled = indice === linhas.length - 1;
      }
    });
  }

  function atualizarDetalheSessoesLayout_v1(linha) {
    const detalhe = linha.nextElementSibling;

    if (!detalhe || !detalhe.classList.contains("appverbo-sidebar-section-detail-row-v1")) {
      return;
    }

    const keyInput = linha.querySelector('input[name="section_key"], input[name*="section_key"]');
    const labelInput = linha.querySelector('input[name="section_label"], input[name*="section_label"]');
    const visibilityInput = linha.querySelector('[name="section_visibility_scope_mode"], [name*="section_visibility_scope_mode"]');

    const chave = textoVisivelSessoesLayout_v1(keyInput && keyInput.value, criarChaveSessoesLayout_v1(labelInput && labelInput.value));
    const visibilidade = textoVisivelSessoesLayout_v1(visibilityInput && visibilityInput.value, "all");

    detalhe.querySelector(".appverbo-sidebar-section-detail-text-v1").textContent =
      "Chave: " + chave + " | Visibilidade: " + visibilidade;
  }

  function sincronizarChaveSessoesLayout_v1(linha) {
    const keyInput = linha.querySelector('input[name="section_key"], input[name*="section_key"]');
    const labelInput = linha.querySelector('input[name="section_label"], input[name*="section_label"]');

    if (!keyInput || !labelInput) {
      return;
    }

    const chaveAtual = String(keyInput.value || "").trim();
    const chaveOriginal = String(keyInput.dataset.originalKeyV1 || "").trim();

    if (!chaveAtual || !chaveOriginal) {
      keyInput.value = criarChaveSessoesLayout_v1(labelInput.value);
    }

    atualizarDetalheSessoesLayout_v1(linha);
  }

  function moverLinhaSessoesLayout_v1(linha, direcao) {
    const tbody = linha && linha.parentElement;

    if (!tbody) {
      return;
    }

    const detalhe = linha.nextElementSibling &&
      linha.nextElementSibling.classList.contains("appverbo-sidebar-section-detail-row-v1")
      ? linha.nextElementSibling
      : null;

    if (direcao === "up") {
      const detalheAnterior = linha.previousElementSibling;
      const linhaAnterior = detalheAnterior && detalheAnterior.classList.contains("appverbo-sidebar-section-detail-row-v1")
        ? detalheAnterior.previousElementSibling
        : detalheAnterior;

      if (linhaAnterior && linhaAnterior.classList.contains("appverbo-sidebar-section-row-v1")) {
        tbody.insertBefore(linha, linhaAnterior);
        if (detalhe) {
          tbody.insertBefore(detalhe, linha.nextElementSibling);
        }
      }
    }

    if (direcao === "down") {
      const detalheAtual = detalhe;
      const proximaLinha = detalheAtual ? detalheAtual.nextElementSibling : linha.nextElementSibling;

      if (proximaLinha && proximaLinha.classList.contains("appverbo-sidebar-section-row-v1")) {
        const proximoDetalhe = proximaLinha.nextElementSibling &&
          proximaLinha.nextElementSibling.classList.contains("appverbo-sidebar-section-detail-row-v1")
          ? proximaLinha.nextElementSibling
          : null;

        tbody.insertBefore(proximaLinha, linha);
        if (proximoDetalhe) {
          tbody.insertBefore(proximoDetalhe, linha);
        }
      }
    }

    atualizarEstadoBotoesSessoesLayout_v1(tbody);
    marcarAlteradoSessoesLayout_v1(linha.closest("form"));
  }

  function alternarDetalheSessoesLayout_v1(linha) {
    const detalhe = linha.nextElementSibling;

    if (!detalhe || !detalhe.classList.contains("appverbo-sidebar-section-detail-row-v1")) {
      return;
    }

    atualizarDetalheSessoesLayout_v1(linha);
    detalhe.hidden = !detalhe.hidden;
  }

  function editarLinhaSessoesLayout_v1(linha) {
    const labelInput = linha.querySelector('input[name="section_label"], input[name*="section_label"]');

    if (!labelInput) {
      return;
    }

    labelInput.readOnly = false;
    labelInput.classList.add("appverbo-sidebar-section-label-input-editing-v1");
    labelInput.focus();
    labelInput.select();
  }

  function marcarAlteradoSessoesLayout_v1(formulario) {
    if (!formulario) {
      return;
    }

    formulario.dataset.sidebarSectionsChangedV1 = "1";

    const aviso = formulario.querySelector(".appverbo-sidebar-section-change-note-v1");

    if (aviso) {
      aviso.hidden = false;
    }
  }

  //###################################################################################
  // (5) CRIAR TABELA
  //###################################################################################

  function criarLinhaTabelaSessoesLayout_v1(linhaDados) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v1";

    const labelInput = linhaDados.labelInput || criarCampoLabelSessoesLayout_v1("");
    const keyInput = linhaDados.keyInput || criarCampoChaveSessoesLayout_v1("");
    const visibilityInput = linhaDados.visibilityInput || criarCampoVisibilidadeSessoesLayout_v1("all");

    labelInput.classList.add("appverbo-sidebar-section-label-input-v1");
    labelInput.readOnly = true;

    if (!keyInput.value) {
      keyInput.value = criarChaveSessoesLayout_v1(labelInput.value);
    }

    keyInput.dataset.originalKeyV1 = String(keyInput.value || "");

    const tdMenu = document.createElement("td");
    tdMenu.className = "appverbo-sidebar-section-menu-cell-v1";
    tdMenu.appendChild(labelInput);
    tdMenu.appendChild(keyInput);
    tdMenu.appendChild(visibilityInput);

    const tdSistema = document.createElement("td");
    tdSistema.className = "appverbo-sidebar-section-system-cell-v1";
    tdSistema.textContent = obterSistemaSessoesLayout_v1(keyInput.value, labelInput.value);

    const tdEstado = document.createElement("td");
    tdEstado.className = "appverbo-sidebar-section-state-cell-v1";

    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v1";
    badge.textContent = "Ativo";
    tdEstado.appendChild(badge);

    const tdAcoes = document.createElement("td");
    tdAcoes.className = "appverbo-sidebar-section-actions-cell-v1";

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v1";
    actions.appendChild(criarBotaoAcaoSessoesLayout_v1("up", "Subir sessão", "↑"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v1("down", "Descer sessão", "↓"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v1("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoSessoesLayout_v1("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    const detalhe = document.createElement("tr");
    detalhe.className = "appverbo-sidebar-section-detail-row-v1";
    detalhe.hidden = true;

    const detalheCelula = document.createElement("td");
    detalheCelula.colSpan = 4;

    const detalheTexto = document.createElement("div");
    detalheTexto.className = "appverbo-sidebar-section-detail-text-v1";
    detalheCelula.appendChild(detalheTexto);
    detalhe.appendChild(detalheCelula);

    labelInput.addEventListener("input", function () {
      sincronizarChaveSessoesLayout_v1(tr);
      tdSistema.textContent = obterSistemaSessoesLayout_v1(keyInput.value, labelInput.value);
      marcarAlteradoSessoesLayout_v1(tr.closest("form"));
    });

    labelInput.addEventListener("blur", function () {
      labelInput.readOnly = true;
      labelInput.classList.remove("appverbo-sidebar-section-label-input-editing-v1");
      sincronizarChaveSessoesLayout_v1(tr);
    });

    atualizarDetalheSessoesLayout_v1(tr);

    return {
      row: tr,
      detailRow: detalhe
    };
  }

  function criarTabelaSessoesLayout_v1(formulario, linhas) {
    const wrapper = document.createElement("div");
    wrapper.className = "appverbo-sidebar-sections-layout-v1";

    const cabecalho = document.createElement("div");
    cabecalho.className = "appverbo-sidebar-sections-header-v1";

    const tituloBloco = document.createElement("div");
    tituloBloco.className = "appverbo-sidebar-sections-title-block-v1";

    const titulo = document.createElement("h2");
    titulo.textContent = "Definições";

    const descricao = document.createElement("p");
    descricao.textContent = "Ative os processos do menu lateral. Um menu só aparece quando estiver ativo aqui.";

    tituloBloco.appendChild(titulo);
    tituloBloco.appendChild(descricao);

    const criarBtn = document.createElement("button");
    criarBtn.type = "button";
    criarBtn.className = "appverbo-sidebar-section-create-btn-v1";
    criarBtn.textContent = "Criar pasta";
    criarBtn.dataset.sidebarSectionActionV1 = "create";

    cabecalho.appendChild(tituloBloco);
    cabecalho.appendChild(criarBtn);

    const hiddenSlot = document.createElement("div");
    hiddenSlot.className = "appverbo-sidebar-sections-hidden-v1";
    hiddenSlot.hidden = true;

    moverCamposOcultosGlobaisSessoesLayout_v1(formulario, hiddenSlot);

    const tableWrap = document.createElement("div");
    tableWrap.className = "appverbo-sidebar-sections-table-wrap-v1";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v1";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");
    tbody.className = "appverbo-sidebar-sections-body-v1";

    linhas.forEach(function (linha) {
      const novaLinha = criarLinhaTabelaSessoesLayout_v1(linha);
      tbody.appendChild(novaLinha.row);
      tbody.appendChild(novaLinha.detailRow);
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);

    const nota = document.createElement("p");
    nota.className = "appverbo-sidebar-section-change-note-v1";
    nota.hidden = true;
    nota.textContent = "Existem alterações por gravar.";

    const footer = document.createElement("div");
    footer.className = "appverbo-sidebar-sections-footer-v1";

    const gravar = document.createElement("button");
    gravar.type = "submit";
    gravar.className = "action-btn";
    gravar.textContent = "Gravar alterações";

    footer.appendChild(nota);
    footer.appendChild(gravar);

    wrapper.appendChild(cabecalho);
    wrapper.appendChild(hiddenSlot);
    wrapper.appendChild(tableWrap);
    wrapper.appendChild(footer);

    criarBtn.addEventListener("click", function () {
      const novoLabel = criarCampoLabelSessoesLayout_v1("Nova pasta");
      const novaChave = criarCampoChaveSessoesLayout_v1("nova_pasta");
      const novaVisibilidade = criarCampoVisibilidadeSessoesLayout_v1("all");

      const novaLinha = criarLinhaTabelaSessoesLayout_v1({
        keyInput: novaChave,
        labelInput: novoLabel,
        visibilityInput: novaVisibilidade
      });

      tbody.appendChild(novaLinha.row);
      tbody.appendChild(novaLinha.detailRow);

      atualizarEstadoBotoesSessoesLayout_v1(tbody);
      editarLinhaSessoesLayout_v1(novaLinha.row);
      marcarAlteradoSessoesLayout_v1(formulario);
    });

    tbody.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v1]");

      if (!botao) {
        return;
      }

      const acao = botao.dataset.sidebarSectionActionV1;
      const linha = botao.closest("tr.appverbo-sidebar-section-row-v1");

      if (acao === "up" || acao === "down") {
        moverLinhaSessoesLayout_v1(linha, acao);
      }

      if (acao === "view") {
        alternarDetalheSessoesLayout_v1(linha);
      }

      if (acao === "edit") {
        editarLinhaSessoesLayout_v1(linha);
      }
    });

    atualizarEstadoBotoesSessoesLayout_v1(tbody);

    return wrapper;
  }

  //###################################################################################
  // (6) INSTALAR LAYOUT
  //###################################################################################

  function instalarLayoutSessoes_v1() {
    const card = obterCardSessoesLayout_v1();

    if (!card || card.dataset.sidebarSectionsLayoutV1 === "1") {
      return;
    }

    const formulario = obterFormularioSessoesLayout_v1(card);

    if (!formulario) {
      return;
    }

    const linhas = recolherLinhasSessoesLayout_v1(formulario);

    if (!linhas.length) {
      return;
    }

    card.dataset.sidebarSectionsLayoutV1 = "1";
    card.classList.add("appverbo-sidebar-sections-card-v1");

    removerEstruturaOriginalSessoesLayout_v1(linhas);

    const submitExistente = formulario.querySelector('button[type="submit"], input[type="submit"]');

    if (submitExistente && submitExistente.parentElement) {
      submitExistente.parentElement.remove();
    }

    const wrapper = criarTabelaSessoesLayout_v1(formulario, linhas);

    while (formulario.firstChild) {
      formulario.removeChild(formulario.firstChild);
    }

    formulario.appendChild(wrapper);

    dispararEventoSessoesLayout_v1(formulario, "change");
  }

  function instalarObservadoresSessoesLayout_v1() {
    instalarLayoutSessoes_v1();

    window.setTimeout(instalarLayoutSessoes_v1, 100);
    window.setTimeout(instalarLayoutSessoes_v1, 300);
    window.setTimeout(instalarLayoutSessoes_v1, 700);

    document.addEventListener("click", function () {
      window.setTimeout(instalarLayoutSessoes_v1, 50);
    });

    if (typeof MutationObserver !== "undefined") {
      const observer = new MutationObserver(function () {
        instalarLayoutSessoes_v1();
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarObservadoresSessoesLayout_v1);
  } else {
    instalarObservadoresSessoesLayout_v1();
  }
})();
