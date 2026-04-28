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

        linha.appendChild(colunaLista);

        function atualizarVisibilidade() {
          colunaLista.style.display = selectTipo.value === "list" ? "" : "none";
        }

        selectTipo.addEventListener("change", atualizarVisibilidade);
        atualizarVisibilidade();
      });
    });
  }

  function inicializar_v5() {
    ligarBotaoAdicionarLista_v5();
    melhorarFormularioCamposAdicionais_v5();
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

