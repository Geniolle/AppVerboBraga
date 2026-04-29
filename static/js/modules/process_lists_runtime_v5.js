//###################################################################################
// APPVERBOBRAGA - LISTAS V5
//###################################################################################

(function () {
  "use strict";

  function normalizarChave_v5(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function obterBootstrap_v5() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function obterUrlParam_v5(nome) {
    try {
      return new URL(window.location.href).searchParams.get(nome) || "";
    } catch (erro) {
      return "";
    }
  }

  function obterProcessoAtual_v5() {
    const chave = normalizarChave_v5(obterUrlParam_v5("settings_edit_key") || obterBootstrap_v5().settingsEditKey);
    const settings = Array.isArray(obterBootstrap_v5().sidebarMenuSettings)
      ? obterBootstrap_v5().sidebarMenuSettings
      : [];

    return settings.find(function (setting) {
      return normalizarChave_v5(setting.key) === chave;
    }) || null;
  }

  function obterListasProcesso_v5() {
    const processo = obterProcessoAtual_v5();

    return processo && Array.isArray(processo.process_lists)
      ? processo.process_lists
      : [];
  }

  function obterCamposProcesso_v5() {
    const processo = obterProcessoAtual_v5();

    return processo && Array.isArray(processo.process_field_options)
      ? processo.process_field_options
      : [];
  }

  function ligarBotaoAdicionarLista_v5() {
    const botao = document.getElementById("add-process-list-row-v5");
    const container = document.querySelector(".process-lists-rows-v5");

    if (!botao || !container || botao.dataset.listaBoundV5 === "1") {
      return;
    }

    botao.dataset.listaBoundV5 = "1";

    botao.addEventListener("click", function () {
      const linha = document.createElement("div");
      linha.className = "process-list-row-v5";
      linha.innerHTML = [
        '<input type="hidden" name="process_list_key" value="">',
        '<div class="field">',
        '  <label>Nome da lista</label>',
        '  <input name="process_list_label" >',
        '</div>',
        '<div class="field full">',
        '  <label>Itens da lista separados por vírgula</label>',
        '  <input name="process_list_items_csv" placeholder="Ativo, Inativo, Pendente, Em acompanhamento">',
        '</div>',
        '<div class="field process-list-actions-v5">',
        '  <button type="button" class="action-btn-cancel" data-remover-lista-v5>Remover</button>',
        '</div>'
      ].join("");

      linha.querySelector("[data-remover-lista-v5]").addEventListener("click", function () {
        linha.remove();
      });

      container.appendChild(linha);
    });
  }

  function criarSelectLista_v5(valorSelecionado) {
    const select = document.createElement("select");
    select.name = "additional_field_list_key";

    const opcaoVazia = document.createElement("option");
    opcaoVazia.value = "";
    opcaoVazia.textContent = obterListasProcesso_v5().length
      ? "Selecione a lista"
      : "Crie uma lista na aba Listas";
    select.appendChild(opcaoVazia);

    obterListasProcesso_v5().forEach(function (lista) {
      const option = document.createElement("option");
      option.value = normalizarChave_v5(lista.key);
      option.textContent = lista.label || lista.key;

      if (normalizarChave_v5(valorSelecionado) === normalizarChave_v5(lista.key)) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function melhorarFormularioCamposAdicionais_v5() {
    const formularios = Array.from(
      document.querySelectorAll("form[action*='/settings/menu/process-additional-fields']")
    );

    if (!formularios.length) {
      return;
    }

    const campos = obterCamposProcesso_v5();

    formularios.forEach(function (formulario) {
      const selectsTipo = Array.from(formulario.querySelectorAll("select[name='additional_field_type']"));

      selectsTipo.forEach(function (selectTipo, indice) {
        if (!selectTipo.querySelector("option[value='list']")) {
          const option = document.createElement("option");
          option.value = "list";
          option.textContent = "Lista";
          selectTipo.appendChild(option);
        }

        const linha = selectTipo.closest(".additional-field-row-equalized")
          || (selectTipo.closest(".field") ? selectTipo.closest(".field").parentElement : null)
          || selectTipo.parentElement;

        if (!linha || linha.querySelector("[data-lista-picker-v5]")) {
          return;
        }

        const meta = campos[indice] || {};
        const colunaLista = document.createElement("div");
        colunaLista.className = "field additional-field-list-col-v5";
        colunaLista.setAttribute("data-lista-picker-v5", "1");

        const label = document.createElement("label");
        label.textContent = "Lista";
        colunaLista.appendChild(label);
        colunaLista.appendChild(criarSelectLista_v5(meta.list_key || meta.listKey || ""));

        const colunaMover = linha.querySelector(".field-move-buttons");
        const botaoRemover = linha.querySelector(".process-additional-field-remove-btn");

        if (colunaMover) {
          linha.insertBefore(colunaLista, colunaMover);
        } else if (botaoRemover) {
          linha.insertBefore(colunaLista, botaoRemover);
        } else {
          linha.appendChild(colunaLista);
        }

        const selectLista = colunaLista.querySelector("select[name='additional_field_list_key']");

        function atualizarVisibilidade() {
          const isLista = selectTipo.value === "list";
          colunaLista.classList.toggle("is-disabled", !isLista);
          if (selectLista) {
            selectLista.disabled = !isLista;
          }
        }

        selectTipo.addEventListener("change", atualizarVisibilidade);
        atualizarVisibilidade();
      });
    });
  }

  function criarLinhaListaVazia_v7() {
    const linha = document.createElement("div");
    linha.className = "process-list-row-v7 process-list-row-create-v7";
    linha.innerHTML = [
      '<input type="hidden" name="process_list_key" value="">',
      '<div class="field">',
      '  <label>Nome da lista</label>',
      '  <input name="process_list_label">',
      '</div>',
      '<div class="field">',
      '  <label>Conteúdo da lista</label>',
      '  <input name="process_list_items_csv">',
      '</div>'
    ].join("");
    return linha;
  }

  function garantirBotaoRemoverLista_v7(linha) {
    if (!linha || linha.querySelector(".process-list-remove-btn-v7")) {
      return;
    }

    const coluna = document.createElement("div");
    coluna.className = "process-list-actions-col-v7";
    coluna.innerHTML = [
      '<button',
      '  type="button"',
      '  class="table-icon-btn table-icon-btn-danger process-list-remove-btn-v7"',
      '  title="Eliminar lista"',
      '  aria-label="Eliminar lista"',
      '>',
      '  &#10005;',
      '</button>'
    ].join("");

    const botao = coluna.querySelector(".process-list-remove-btn-v7");
    if (botao) {
      botao.addEventListener("click", function () {
        linha.remove();
      });
    }

    linha.appendChild(coluna);
  }

  function montarBlocoListasV7(formulario) {
    if (!formulario || formulario.dataset.processListsV7Bound === "1") {
      return;
    }

    const containerOriginal = formulario.querySelector(".process-lists-rows-v7");
    if (!containerOriginal) {
      return;
    }

    const linhas = Array.from(containerOriginal.querySelectorAll(".process-list-row-v7"));
    if (!linhas.length) {
      return;
    }

    const blocoCriacao = document.createElement("div");
    blocoCriacao.className = "process-lists-block-v7";
    blocoCriacao.innerHTML = '<h4>Criar nova lista</h4><div class="process-lists-rows-v7"></div>';

    const blocoExistentes = document.createElement("div");
    blocoExistentes.className = "process-lists-block-v7 process-lists-existing-block-v7";
    blocoExistentes.innerHTML = '<h4>Listas criadas</h4><div class="process-lists-rows-v7"></div>';
    const acoes = formulario.querySelector(".process-lists-actions-v7");

    const containerCriacao = blocoCriacao.querySelector(".process-lists-rows-v7");
    const containerExistentes = blocoExistentes.querySelector(".process-lists-rows-v7");

    let linhaCriacao = null;

    linhas.forEach(function (linha) {
      const keyInput = linha.querySelector("input[name='process_list_key']");
      const keyValue = String(keyInput ? keyInput.value : "").trim();

      if (!keyValue && !linhaCriacao) {
        linhaCriacao = linha;
        linha.classList.add("process-list-row-create-v7");
        const colunaAcao = linha.querySelector(".process-list-actions-col-v7");
        if (colunaAcao) {
          colunaAcao.remove();
        }
        containerCriacao.appendChild(linha);
        return;
      }

      linha.classList.remove("process-list-row-create-v7");
      garantirBotaoRemoverLista_v7(linha);
      containerExistentes.appendChild(linha);
    });

    if (!linhaCriacao) {
      linhaCriacao = criarLinhaListaVazia_v7();
      containerCriacao.appendChild(linhaCriacao);
    }

    const parent = containerOriginal.parentNode;
    parent.insertBefore(blocoCriacao, containerOriginal);
    if (acoes) {
      blocoCriacao.appendChild(acoes);
    }
    parent.insertBefore(blocoExistentes, containerOriginal);
    containerOriginal.remove();

    if (!containerExistentes.children.length) {
      const vazio = document.createElement("p");
      vazio.className = "empty process-lists-empty-v7";
      vazio.textContent = "Sem listas criadas ainda.";
      blocoExistentes.appendChild(vazio);
    }

    formulario.dataset.processListsV7Bound = "1";
  }

  function inicializar_v5() {
    ligarBotaoAdicionarLista_v5();
    melhorarFormularioCamposAdicionais_v5();
    Array.from(document.querySelectorAll("form[action*='/settings/menu/process-lists']")).forEach(montarBlocoListasV7);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v5);
  } else {
    inicializar_v5();
  }

  window.setTimeout(inicializar_v5, 100);
  window.setTimeout(inicializar_v5, 400);
  window.setTimeout(inicializar_v5, 1000);
})();

