//###################################################################################
// APPVERBOBRAGA - LISTA V3
//###################################################################################

(function () {
  "use strict";

  //###################################################################################
  // (1) AUXILIARES
  //###################################################################################

  function normalizarChave_v3(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_|_$/g, "");
  }

  function obterBootstrap_v3() {
    return window.__APPVERBO_BOOTSTRAP__ || {};
  }

  function obterUrlParam_v3(nome) {
    try {
      return new URL(window.location.href).searchParams.get(nome) || "";
    } catch (erro) {
      return "";
    }
  }

  function obterProcessoAtual_v3() {
    const chave = normalizarChave_v3(obterUrlParam_v3("settings_edit_key") || obterBootstrap_v3().settingsEditKey);
    const settings = Array.isArray(obterBootstrap_v3().sidebarMenuSettings)
      ? obterBootstrap_v3().sidebarMenuSettings
      : [];

    return settings.find(function (setting) {
      return normalizarChave_v3(setting.key) === chave;
    }) || null;
  }

  function obterListasProcesso_v3() {
    const processo = obterProcessoAtual_v3();

    return processo && Array.isArray(processo.process_lists)
      ? processo.process_lists
      : [];
  }

  function obterCamposProcesso_v3() {
    const processo = obterProcessoAtual_v3();

    return processo && Array.isArray(processo.process_field_options)
      ? processo.process_field_options
      : [];
  }

  //###################################################################################
  // (2) ADICIONAR LINHA NA ABA LISTA
  //###################################################################################

  function ligarBotaoAdicionarLista_v3() {
    const botao = document.getElementById("add-process-list-row-v3");
    const container = document.querySelector(".process-lists-rows-v3");

    if (!botao || !container || botao.dataset.listaBoundV3 === "1") {
      return;
    }

    botao.dataset.listaBoundV3 = "1";

    botao.addEventListener("click", function () {
      const linha = document.createElement("div");
      linha.className = "process-list-row-v3";
      linha.innerHTML = [
        '<input type="hidden" name="process_list_key" value="">',
        '<div class="field">',
        '  <label>Nome da lista</label>',
        '  <input name="process_list_label" placeholder="Ex.: Estado">',
        '</div>',
        '<div class="field full">',
        '  <label>Itens da lista separados por vírgula</label>',
        '  <input name="process_list_items_csv" placeholder="Ativo, Inativo, Pendente, Em acompanhamento">',
        '</div>',
        '<div class="field process-list-actions-v3">',
        '  <button type="button" class="action-btn-cancel" data-remover-lista-v3>Remover</button>',
        '</div>'
      ].join("");

      linha.querySelector("[data-remover-lista-v3]").addEventListener("click", function () {
        linha.remove();
      });

      container.appendChild(linha);
    });
  }

  //###################################################################################
  // (3) MOSTRAR SELECT "LISTA" NA CONFIGURAÇÃO DO CAMPO
  //###################################################################################

  function criarSelectLista_v3(valorSelecionado) {
    const select = document.createElement("select");
    select.name = "additional_field_list_key";

    const opcaoVazia = document.createElement("option");
    opcaoVazia.value = "";
    opcaoVazia.textContent = obterListasProcesso_v3().length
      ? "Selecione a lista"
      : "Crie uma lista na aba Listas";
    select.appendChild(opcaoVazia);

    obterListasProcesso_v3().forEach(function (lista) {
      const option = document.createElement("option");
      option.value = normalizarChave_v3(lista.key);
      option.textContent = lista.label || lista.key;

      if (normalizarChave_v3(valorSelecionado) === normalizarChave_v3(lista.key)) {
        option.selected = true;
      }

      select.appendChild(option);
    });

    return select;
  }

  function melhorarFormularioCamposAdicionais_v3() {
    const formularios = Array.from(
      document.querySelectorAll("form[action*='/settings/menu/process-additional-fields']")
    );

    if (!formularios.length) {
      return;
    }

    const campos = obterCamposProcesso_v3();

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

        if (!linha || linha.querySelector("[data-lista-picker-v3]")) {
          return;
        }

        const meta = campos[indice] || {};

        const colunaLista = document.createElement("div");
        colunaLista.className = "field additional-field-list-col-v3";
        colunaLista.setAttribute("data-lista-picker-v3", "1");

        const label = document.createElement("label");
        label.textContent = "Lista";
        colunaLista.appendChild(label);
        colunaLista.appendChild(criarSelectLista_v3(meta.list_key || meta.listKey || ""));

        linha.appendChild(colunaLista);

        function atualizarVisibilidade() {
          colunaLista.style.display = selectTipo.value === "list" ? "" : "none";
        }

        selectTipo.addEventListener("change", atualizarVisibilidade);
        atualizarVisibilidade();
      });
    });
  }

  //###################################################################################
  // (4) INICIALIZAÇÃO
  //###################################################################################

  function inicializar_v3() {
    ligarBotaoAdicionarLista_v3();
    melhorarFormularioCamposAdicionais_v3();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicializar_v3);
  } else {
    inicializar_v3();
  }

  window.setTimeout(inicializar_v3, 100);
  window.setTimeout(inicializar_v3, 400);
  window.setTimeout(inicializar_v3, 1000);
  window.setTimeout(inicializar_v3, 1800);
})();
