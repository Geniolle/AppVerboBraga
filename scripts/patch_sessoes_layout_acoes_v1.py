from pathlib import Path
import re
import sys

ROOT = Path.cwd()

TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

CSS_HREF = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-layout-v1"
SCRIPT_SRC = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-layout-v1"


def fail_v1(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) VALIDAR FICHEIROS BASE
####################################################################################

if not TEMPLATE_PATH.exists():
    fail_v1(f"ficheiro não encontrado: {TEMPLATE_PATH}")

JS_PATH.parent.mkdir(parents=True, exist_ok=True)
CSS_PATH.parent.mkdir(parents=True, exist_ok=True)


####################################################################################
# (2) CONTEUDO JAVASCRIPT
####################################################################################

JS_CONTENT = r'''(function () {
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
'''


####################################################################################
# (3) CONTEUDO CSS
####################################################################################

CSS_CONTENT = r'''/* APPVERBO_SIDEBAR_SECTIONS_LAYOUT_V1_START */

.appverbo-sidebar-sections-card-v1 {
  overflow: hidden;
}

.appverbo-sidebar-sections-layout-v1 {
  width: 100%;
}

.appverbo-sidebar-sections-header-v1 {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.appverbo-sidebar-sections-title-block-v1 h2 {
  margin: 0 0 8px;
  font-size: 20px;
}

.appverbo-sidebar-sections-title-block-v1 p {
  margin: 0;
  color: #52607a;
  font-size: 13px;
}

.appverbo-sidebar-section-create-btn-v1 {
  border: 1px solid #b9cef4;
  background: #edf4ff;
  color: #153f8f;
  font-weight: 700;
  border-radius: 5px;
  padding: 8px 12px;
  cursor: pointer;
  white-space: nowrap;
}

.appverbo-sidebar-section-create-btn-v1:hover {
  background: #dceaff;
}

.appverbo-sidebar-sections-table-wrap-v1 {
  width: 100%;
  overflow-x: auto;
}

.appverbo-sidebar-sections-table-v1 {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.appverbo-sidebar-sections-table-v1 th {
  color: #243557;
  font-size: 10px;
  font-weight: 700;
  text-align: left;
  text-transform: uppercase;
  padding: 10px 6px;
  border-bottom: 1px solid #d5dceb;
}

.appverbo-sidebar-sections-table-v1 td {
  padding: 8px 6px;
  border-bottom: 1px solid #d5dceb;
  vertical-align: middle;
  font-size: 12px;
}

.appverbo-sidebar-sections-table-v1 th:nth-child(1),
.appverbo-sidebar-sections-table-v1 td:nth-child(1) {
  width: 34%;
}

.appverbo-sidebar-sections-table-v1 th:nth-child(2),
.appverbo-sidebar-sections-table-v1 td:nth-child(2) {
  width: 36%;
}

.appverbo-sidebar-sections-table-v1 th:nth-child(3),
.appverbo-sidebar-sections-table-v1 td:nth-child(3) {
  width: 16%;
}

.appverbo-sidebar-sections-table-v1 th:nth-child(4),
.appverbo-sidebar-sections-table-v1 td:nth-child(4) {
  width: 14%;
  text-align: right;
}

.appverbo-sidebar-section-label-input-v1 {
  width: 100%;
  border: 1px solid transparent;
  background: transparent;
  color: #12213a;
  font-size: 12px;
  padding: 6px;
  border-radius: 5px;
}

.appverbo-sidebar-section-label-input-v1:read-only {
  cursor: default;
}

.appverbo-sidebar-section-label-input-editing-v1,
.appverbo-sidebar-section-label-input-v1:focus {
  border-color: #b9cef4;
  background: #ffffff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(36, 84, 176, 0.12);
}

.appverbo-sidebar-section-state-badge-v1 {
  display: inline-flex;
  align-items: center;
  border: 1px solid #9fd9b6;
  background: #e7f8ed;
  color: #04743a;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 700;
}

.appverbo-sidebar-section-actions-v1 {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  white-space: nowrap;
}

.appverbo-sidebar-section-action-btn-v1 {
  width: 28px;
  height: 28px;
  border: 1px solid #c2d4f7;
  background: #eef5ff;
  color: #1d4f9f;
  border-radius: 7px;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.appverbo-sidebar-section-action-btn-v1:hover:not(:disabled) {
  background: #dceaff;
}

.appverbo-sidebar-section-action-btn-v1:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.appverbo-sidebar-section-detail-row-v1 td {
  background: #f8fbff;
  color: #52607a;
  font-size: 12px;
  padding: 10px 8px;
}

.appverbo-sidebar-sections-footer-v1 {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 14px;
}

.appverbo-sidebar-section-change-note-v1 {
  margin: 0;
  color: #8a5a00;
  font-size: 12px;
}

@media (max-width: 900px) {
  .appverbo-sidebar-sections-header-v1 {
    flex-direction: column;
    align-items: stretch;
  }

  .appverbo-sidebar-sections-table-v1 {
    min-width: 760px;
  }
}

/* APPVERBO_SIDEBAR_SECTIONS_LAYOUT_V1_END */
'''


####################################################################################
# (4) FUNCOES DE INSERCAO NO TEMPLATE
####################################################################################

def inserir_css_v1(template: str) -> str:
    if CSS_HREF in template:
        return template

    css_link = f'  <link rel="stylesheet" href="{CSS_HREF}">\n'

    alvo = re.search(
        r'(?m)^.*<link rel="stylesheet" href="/static/css/modules/configurable_items_manager_v1\.css[^"]*">.*\n?',
        template,
    )

    if alvo:
        return template[:alvo.end()] + css_link + template[alvo.end():]

    endblock = re.search(r"{% endblock %}", template)

    if not endblock:
        fail_v1("não encontrei {% endblock %} para inserir CSS.")

    return template[:endblock.start()] + css_link + template[endblock.start():]


def inserir_js_v1(template: str) -> str:
    if SCRIPT_SRC in template:
        return template

    script_tag = f'<script src="{SCRIPT_SRC}"></script>\n'

    alvo = re.search(
        r'(?m)^.*<script src="/static/js/modules/top_menu_active_v1\.js[^"]*"></script>.*\n?',
        template,
    )

    if alvo:
        return template[:alvo.end()] + script_tag + template[alvo.end():]

    endblock = re.search(r"{% endblock %}", template)

    if not endblock:
        fail_v1("não encontrei {% endblock %} para inserir JS.")

    return template[:endblock.start()] + script_tag + template[endblock.start():]


####################################################################################
# (5) APLICAR ALTERACOES
####################################################################################

template = TEMPLATE_PATH.read_text(encoding="utf-8")
template = inserir_css_v1(template)
template = inserir_js_v1(template)

JS_PATH.write_text(JS_CONTENT, encoding="utf-8")
CSS_PATH.write_text(CSS_CONTENT, encoding="utf-8")
TEMPLATE_PATH.write_text(template, encoding="utf-8")


####################################################################################
# (6) VALIDAR CONTEUDO
####################################################################################

template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")

if CSS_HREF not in template_validado:
    fail_v1("CSS sidebar_sections_layout_v1 não foi incluído no template.")

if SCRIPT_SRC not in template_validado:
    fail_v1("JS sidebar_sections_layout_v1 não foi incluído no template.")

if "function instalarLayoutSessoes_v1" not in js_validado:
    fail_v1("função instalarLayoutSessoes_v1 não foi criada no JS.")

if "admin-sidebar-sections-card" not in js_validado:
    fail_v1("JS não contém referência ao card de sessões.")

if "APPVERBO_SIDEBAR_SECTIONS_LAYOUT_V1_START" not in css_validado:
    fail_v1("marcador CSS não foi criado.")

print("OK: template atualizado com CSS/JS do layout de Sessões.")
print("OK: static/js/modules/sidebar_sections_layout_v1.js criado/atualizado.")
print("OK: static/css/modules/sidebar_sections_layout_v1.css criado/atualizado.")
print("OK: patch_sessoes_layout_acoes_v1 concluído.")
