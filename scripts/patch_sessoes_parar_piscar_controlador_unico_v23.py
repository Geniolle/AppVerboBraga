from pathlib import Path
import ast
import re
import sys

ROOT = Path.cwd()

AGENTS_UPPER_PATH = ROOT / "AGENTS.md"
AGENTS_TITLE_PATH = ROOT / "Agents.md"
TEMPLATE_PATH = ROOT / "templates" / "new_user.html"
PAGE_HANDLER_PATH = ROOT / "appverbo" / "routes" / "profile" / "page_handler.py"
SETTINGS_HANDLERS_PATH = ROOT / "appverbo" / "routes" / "profile" / "settings_handlers.py"
JS_PATH = ROOT / "static" / "js" / "modules" / "sidebar_sections_layout_v1.js"
CSS_PATH = ROOT / "static" / "css" / "modules" / "sidebar_sections_layout_v1.css"

AGENTS_MARKER_START = "<!-- APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START -->"
AGENTS_MARKER_END = "<!-- APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END -->"

JS_MARKER_START = "// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START"
JS_MARKER_END = "// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END"

CSS_MARKER_START = "/* APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START */"
CSS_MARKER_END = "/* APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END */"

JS_CACHE = "/static/js/modules/sidebar_sections_layout_v1.js?v=20260505-sessoes-controlador-unico-v23"
CSS_CACHE = "/static/css/modules/sidebar_sections_layout_v1.css?v=20260505-sessoes-controlador-unico-v23"


def fail_v23(message: str) -> None:
    print(f"ERRO: {message}")
    sys.exit(1)


####################################################################################
# (1) RESOLVER AGENTS.md
####################################################################################

def resolve_agents_path_v23() -> Path:
    if AGENTS_UPPER_PATH.exists():
        return AGENTS_UPPER_PATH

    if AGENTS_TITLE_PATH.exists():
        return AGENTS_TITLE_PATH

    AGENTS_UPPER_PATH.write_text("# AGENTS.md\n\n", encoding="utf-8")
    return AGENTS_UPPER_PATH


####################################################################################
# (2) VALIDAR FICHEIROS
####################################################################################

for file_path in [TEMPLATE_PATH, PAGE_HANDLER_PATH, SETTINGS_HANDLERS_PATH, JS_PATH, CSS_PATH]:
    if not file_path.exists():
        fail_v23(f"ficheiro não encontrado: {file_path}")


####################################################################################
# (3) ATUALIZAR AGENTS.md
####################################################################################

agents_path = resolve_agents_path_v23()
agents_content = agents_path.read_text(encoding="utf-8")

agents_rule = f"""{AGENTS_MARKER_START}
## Regra definitiva para Sessões sem piscar

A aba **Sessões** deve ter apenas um controlador visual ativo.

Regras:

1. Não usar `MutationObserver` para renderizar continuamente os cards de Sessões.
2. Não reescrever `innerHTML` repetidamente se os dados não mudaram.
3. Não forçar a URL para `admin_tab=sessoes` quando o utilizador clicar noutro subprocesso.
4. O renderizador de Sessões só pode atuar quando a aba **Sessões** estiver realmente ativa.
5. O split ativo/inativo deve vir do backend, igual ao padrão da Entidade.
6. O card **Sessões do sidebar** deve renderizar apenas sessões ativas.
7. O card **Sessões inativas** deve renderizar apenas sessões inativas.
8. O card **Sessões inativas** deve permanecer visível mesmo vazio.
9. Os blocos antigos V15, V18, V20, V21 e V22 não podem continuar a observar/mexer no DOM.
10. A ação **Editar** deve usar `sidebar_section_edit_key`, sem `dynamic_process_section`.
{AGENTS_MARKER_END}"""

if AGENTS_MARKER_START in agents_content and AGENTS_MARKER_END in agents_content:
    agents_content = re.sub(
        re.escape(AGENTS_MARKER_START) + r"[\s\S]*?" + re.escape(AGENTS_MARKER_END),
        agents_rule,
        agents_content,
        count=1,
    )
else:
    agents_content = agents_content.rstrip() + "\n\n" + agents_rule + "\n"

agents_path.write_text(agents_content, encoding="utf-8")

print(f"OK: AGENTS.md atualizado em {agents_path}")


####################################################################################
# (4) GARANTIR BACKEND SESSOES NO PAGE_HANDLER
####################################################################################

page_content = PAGE_HANDLER_PATH.read_text(encoding="utf-8-sig")

if 'resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes"}' not in page_content:
    page_content = page_content.replace(
        'resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes"}',
        'resolved_admin_tab not in {"utilizador", "entidade", "contas", "definicoes", "sessoes"}',
    )

if 'if resolved_admin_tab == "sessoes":' not in page_content:
    anchor = '''    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query
'''
    insert = '''    if clean_dynamic_section_from_query:
        initial_dynamic_process_section = clean_dynamic_section_from_query

    if resolved_admin_tab == "sessoes":
        initial_menu_target = "#admin-sidebar-sections-card"
        initial_dynamic_process_section = ""
        clean_dynamic_section_from_query = ""
'''
    if anchor in page_content:
        page_content = page_content.replace(anchor, insert, 1)
    else:
        print("AVISO: não encontrei âncora para limpeza de dynamic_process_section no page_handler.")

try:
    ast.parse(page_content)
except SyntaxError as exc:
    fail_v23(f"page_handler.py ficaria inválido: {exc}")

PAGE_HANDLER_PATH.write_text(page_content, encoding="utf-8")

print("OK: page_handler.py validado.")


####################################################################################
# (5) GARANTIR BACKEND NAO PRESERVA dynamic_process_section
####################################################################################

settings_content = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")

if '"dynamic_process_section",' not in settings_content:
    settings_content = settings_content.replace(
        '"sidebar_section_return_url",',
        '"sidebar_section_return_url",\n        "dynamic_process_section",',
        1,
    )

if '"appverbo_after_save",' not in settings_content:
    settings_content = settings_content.replace(
        '"dynamic_process_section",',
        '"dynamic_process_section",\n        "appverbo_after_save",',
        1,
    )

try:
    ast.parse(settings_content)
except SyntaxError as exc:
    fail_v23(f"settings_handlers.py ficaria inválido: {exc}")

SETTINGS_HANDLERS_PATH.write_text(settings_content, encoding="utf-8")

print("OK: settings_handlers.py validado.")


####################################################################################
# (6) GARANTIR JSON BACKEND SPLIT NO TEMPLATE
####################################################################################

template_content = TEMPLATE_PATH.read_text(encoding="utf-8")

if "appverbo-sidebar-section-split-v22" not in template_content:
    template_block = '''<!-- APPVERBO_SESSOES_BACKEND_SPLIT_JSON_V22_START -->
        <script id="appverbo-sidebar-section-split-v22" type="application/json">{{ {
          "active": active_sidebar_sections|default([]),
          "inactive": inactive_sidebar_sections|default([]),
          "edit_key": sidebar_section_edit_key|default(""),
          "edit_data": sidebar_section_edit_data|default(none)
        }|tojson }}</script>
        <!-- APPVERBO_SESSOES_BACKEND_SPLIT_JSON_V22_END -->'''

    anchor = '<!-- APPVERBO_SIDEBAR_SECTIONS_JSON_V2_END -->'

    if anchor not in template_content:
        fail_v23("não encontrei APPVERBO_SIDEBAR_SECTIONS_JSON_V2_END no template.")

    template_content = template_content.replace(anchor, anchor + "\n" + template_block, 1)

if "static/js/modules/sidebar_sections_layout_v1.js" in template_content:
    template_content = re.sub(
        r"/static/js/modules/sidebar_sections_layout_v1\.js\?v=[^\"]+",
        JS_CACHE,
        template_content,
    )
else:
    fail_v23("não encontrei sidebar_sections_layout_v1.js no template.")

if "static/css/modules/sidebar_sections_layout_v1.css" in template_content:
    template_content = re.sub(
        r"/static/css/modules/sidebar_sections_layout_v1\.css\?v=[^\"]+",
        CSS_CACHE,
        template_content,
    )
else:
    fail_v23("não encontrei sidebar_sections_layout_v1.css no template.")

TEMPLATE_PATH.write_text(template_content, encoding="utf-8")

print("OK: template atualizado.")


####################################################################################
# (7) DESATIVAR CONTROLADORES ANTIGOS E INSTALAR V23
####################################################################################

js_content = JS_PATH.read_text(encoding="utf-8")

def disable_block_v23(content: str, start_marker: str, end_marker: str, reason: str) -> str:
    if start_marker not in content or end_marker not in content:
        return content

    replacement = f"""{start_marker}
// Desativado pelo controlador único V23.
// Motivo: {reason}
{end_marker}"""

    return re.sub(
        re.escape(start_marker) + r"[\s\S]*?" + re.escape(end_marker),
        replacement,
        content,
        count=1,
    )


blocks_to_disable = [
    (
        "// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_START",
        "// APPVERBO_SESSOES_INATIVAS_CARD_FORA_V15_END",
        "usava MutationObserver e competia com o split backend."
    ),
    (
        "// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_START",
        "// APPVERBO_SESSOES_PADRAO_ENTIDADE_V18_END",
        "forçava aba/URL e mantinha observador ativo."
    ),
    (
        "// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START",
        "// APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_END",
        "fazia fetch/render repetido e competia com o backend split."
    ),
    (
        "// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START",
        "// APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_END",
        "forçava contexto Sessões e dificultava sair da aba."
    ),
    (
        "// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START",
        "// APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_END",
        "reescrevia o DOM dentro de MutationObserver, causando piscar."
    ),
]

for start_marker, end_marker, reason in blocks_to_disable:
    js_content = disable_block_v23(js_content, start_marker, end_marker, reason)

js_block = r'''// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START
(function () {
  "use strict";

  //###################################################################################
  // (1) NORMALIZACAO
  //###################################################################################

  function normalizarTextoSessoesV23(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim()
      .toLowerCase();
  }

  function criarChaveSessoesV23(valor) {
    return normalizarTextoSessoesV23(valor)
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function estadoSessaoV23(sessao) {
    if (sessao && sessao.is_active === false) {
      return "inativo";
    }

    const status = normalizarTextoSessoesV23(
      sessao ? (sessao.status || sessao.status_label || "") : ""
    );

    if (["inativo", "inactive", "0", "false", "nao", "não", "off"].includes(status)) {
      return "inativo";
    }

    return "ativo";
  }

  function labelSistemaSessoesV23(valor, fallback) {
    const sistema = normalizarTextoSessoesV23(valor);

    if (sistema === "owner") {
      return "Owner";
    }

    if (sistema === "legado") {
      return "Legado";
    }

    return fallback || "Owner e Legado";
  }

  //###################################################################################
  // (2) CONTEXTO DA ABA SESSOES SEM FORCAR SAIDA/ENTRADA
  //###################################################################################

  function elementoVisivelSessoesV23(elemento) {
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

  function elementoAtivoSessoesV23(elemento) {
    const className = normalizarTextoSessoesV23(elemento.className || "");
    const parentClass = elemento.parentElement
      ? normalizarTextoSessoesV23(elemento.parentElement.className || "")
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

  function tabAtivaPorTextoSessoesV23(textoEsperado) {
    const candidatos = Array.from(document.querySelectorAll("button, a, [role='tab'], [data-admin-tab], .tab-button, .admin-tab"));

    return candidatos.some(function (elemento) {
      return normalizarTextoSessoesV23(elemento.textContent) === textoEsperado &&
        elementoVisivelSessoesV23(elemento) &&
        elementoAtivoSessoesV23(elemento);
    });
  }

  function abaSessoesAtivaV23() {
    if (tabAtivaPorTextoSessoesV23("entidade") ||
        tabAtivaPorTextoSessoesV23("utilizador") ||
        tabAtivaPorTextoSessoesV23("menu") ||
        tabAtivaPorTextoSessoesV23("contas")) {
      return false;
    }

    if (tabAtivaPorTextoSessoesV23("sessoes")) {
      return true;
    }

    const url = new URL(window.location.href);

    if (
      url.searchParams.get("admin_tab") === "sessoes" ||
      url.searchParams.get("sidebar_sections_tab") === "sessoes" ||
      url.searchParams.has("sidebar_section_edit_key")
    ) {
      return true;
    }

    const card = document.getElementById("admin-sidebar-sections-card");

    return Boolean(card && elementoVisivelSessoesV23(card));
  }

  function limparApenasUrlSessoesV23() {
    if (!abaSessoesAtivaV23()) {
      return;
    }

    const url = new URL(window.location.href);
    let mudou = false;

    [
      "dynamic_process_section",
      "settings_edit_key",
      "settings_action",
      "settings_tab",
      "sidebar_section_return_url",
      "appverbo_after_save"
    ].forEach(function (parametro) {
      if (url.searchParams.has(parametro)) {
        url.searchParams.delete(parametro);
        mudou = true;
      }
    });

    if (mudou) {
      window.history.replaceState({}, document.title, url.pathname + url.search + url.hash);
    }
  }

  //###################################################################################
  // (3) DADOS BACKEND
  //###################################################################################

  function lerSplitBackendSessoesV23() {
    const script = document.getElementById("appverbo-sidebar-section-split-v22");

    if (script) {
      try {
        const parsed = JSON.parse(script.textContent || "{}");

        return {
          active: Array.isArray(parsed.active) ? parsed.active : [],
          inactive: Array.isArray(parsed.inactive) ? parsed.inactive : [],
          edit_key: parsed.edit_key || "",
          edit_data: parsed.edit_data || null
        };
      }
      catch (error) {
        console.warn("APPVERBO V23: falha ao ler split backend.", error);
      }
    }

    const fallbackScript = document.getElementById("appverbo-sidebar-section-options-v2") ||
      document.getElementById("appverbo-sidebar-section-options-v1");

    if (!fallbackScript) {
      return {
        active: [],
        inactive: [],
        edit_key: "",
        edit_data: null
      };
    }

    try {
      const parsed = JSON.parse(fallbackScript.textContent || "[]");
      const rows = Array.isArray(parsed) ? parsed : [];

      return {
        active: rows.filter(function (row) {
          return estadoSessaoV23(row) === "ativo";
        }),
        inactive: rows.filter(function (row) {
          return estadoSessaoV23(row) !== "ativo";
        }),
        edit_key: "",
        edit_data: null
      };
    }
    catch (error) {
      return {
        active: [],
        inactive: [],
        edit_key: "",
        edit_data: null
      };
    }
  }

  function normalizarSessaoV23(sessao) {
    if (!sessao || typeof sessao !== "object") {
      return null;
    }

    const label = String(sessao.label || sessao.name || sessao.title || "").trim();
    const key = criarChaveSessoesV23(sessao.key || sessao.section_key || label);

    if (!label || !key) {
      return null;
    }

    const status = estadoSessaoV23(sessao);
    const sistema = String(sessao.visibility_scope_mode || sessao.scope_mode || "all").trim() || "all";

    return {
      key: key,
      label: label,
      visibility_scope_mode: sistema,
      visibility_scope_label: sessao.visibility_scope_label || labelSistemaSessoesV23(sistema, ""),
      status: status,
      is_active: status === "ativo",
      status_label: status === "inativo" ? "Inativo" : "Ativo"
    };
  }

  //###################################################################################
  // (4) URLS DE EDITAR/CANCELAR
  //###################################################################################

  function obterUrlEditarSessaoV23(chave) {
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
    ].forEach(function (parametro) {
      url.searchParams.delete(parametro);
    });

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.searchParams.set("sidebar_section_edit_key", criarChaveSessoesV23(chave));
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  function obterUrlRetornoSessaoV23() {
    const url = new URL(window.location.href);

    [
      "dynamic_process_section",
      "settings_edit_key",
      "settings_action",
      "settings_tab",
      "sidebar_section_return_url",
      "sidebar_section_edit_key",
      "appverbo_after_save",
      "success",
      "error"
    ].forEach(function (parametro) {
      url.searchParams.delete(parametro);
    });

    url.searchParams.set("menu", "administrativo");
    url.searchParams.set("admin_tab", "sessoes");
    url.searchParams.set("sidebar_sections_tab", "sessoes");
    url.searchParams.set("target", "admin-sidebar-sections-card");
    url.hash = "admin-sidebar-sections-card";

    return url.pathname + url.search + url.hash;
  }

  //###################################################################################
  // (5) FORMULARIO SUPERIOR CRIAR/EDITAR
  //###################################################################################

  function criarHiddenV23(nome, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nome;
    input.value = valor || "";
    return input;
  }

  function criarOpcaoV23(valor, texto, atual) {
    const option = document.createElement("option");
    option.value = valor;
    option.textContent = texto;

    if (valor === atual) {
      option.selected = true;
    }

    return option;
  }

  function obterOuCriarCardCriarV23(cardLista) {
    let card = document.getElementById("admin-sidebar-sections-create-card");

    if (!card) {
      card = document.createElement("section");
      card.id = "admin-sidebar-sections-create-card";
    }

    card.className = "card appverbo-sessoes-create-card-v23";
    card.hidden = false;
    card.style.display = "";
    card.style.visibility = "";

    if (card.parentElement !== cardLista.parentElement) {
      cardLista.parentElement.insertBefore(card, cardLista);
    }
    else if (card.nextElementSibling !== cardLista) {
      cardLista.parentElement.insertBefore(card, cardLista);
    }

    return card;
  }

  function renderizarCardCriarEditarV23(cardLista, split, todasSessoes) {
    const card = obterOuCriarCardCriarV23(cardLista);
    const url = new URL(window.location.href);
    const editKeyUrl = criarChaveSessoesV23(url.searchParams.get("sidebar_section_edit_key") || "");
    const editKey = criarChaveSessoesV23(split.edit_key || editKeyUrl);
    const editData = normalizarSessaoV23(split.edit_data) ||
      todasSessoes.find(function (sessao) {
        return criarChaveSessoesV23(sessao.key) === editKey;
      }) ||
      null;

    const modo = editKey && editData ? "edit" : "create";
    const assinatura = JSON.stringify({
      modo: modo,
      key: editData ? editData.key : "",
      label: editData ? editData.label : "",
      sistema: editData ? editData.visibility_scope_mode : "",
      status: editData ? editData.status : ""
    });

    if (card.dataset.renderSignatureV23 === assinatura) {
      return;
    }

    card.dataset.renderSignatureV23 = assinatura;
    card.innerHTML = "";

    const wrapper = document.createElement("div");
    wrapper.className = "appverbo-sessoes-create-wrapper-v23";

    const toolbar = document.createElement("div");
    toolbar.className = "appverbo-sessoes-create-toolbar-v23";

    const abrirBtn = document.createElement("button");
    abrirBtn.type = "button";
    abrirBtn.className = "action-btn";
    abrirBtn.textContent = "Criar sessão";

    toolbar.appendChild(abrirBtn);

    const panel = document.createElement("div");
    panel.className = "appverbo-sessoes-create-panel-v23";
    panel.hidden = modo !== "edit";

    if (modo === "edit") {
      toolbar.hidden = true;
    }

    const title = document.createElement("h2");
    title.className = "appverbo-sessoes-form-title-v23";
    title.textContent = modo === "edit" ? "Editar sessão" : "Criar sessão";

    const form = document.createElement("form");
    form.method = "post";
    form.action = "/settings/menu/sidebar-section-save";
    form.className = "appverbo-sessoes-form-v23";

    form.appendChild(criarHiddenV23("section_mode", modo));
    form.appendChild(criarHiddenV23("original_section_key", editData ? editData.key : ""));
    form.appendChild(criarHiddenV23("sidebar_section_return_url", obterUrlRetornoSessaoV23()));

    const grid = document.createElement("div");
    grid.className = "appverbo-sessoes-grid-v23";

    const nomeField = document.createElement("div");
    nomeField.className = "field appverbo-sessoes-field-v23";

    const nomeLabel = document.createElement("label");
    nomeLabel.textContent = "Nome da sessão *";

    const nomeInput = document.createElement("input");
    nomeInput.name = "section_label";
    nomeInput.required = true;
    nomeInput.maxLength = 80;
    nomeInput.placeholder = "Informe o nome da sessão";
    nomeInput.value = editData ? editData.label : "";

    nomeField.appendChild(nomeLabel);
    nomeField.appendChild(nomeInput);

    const sistemaField = document.createElement("div");
    sistemaField.className = "field appverbo-sessoes-field-v23";

    const sistemaLabel = document.createElement("label");
    sistemaLabel.textContent = "Sistema *";

    const sistemaSelect = document.createElement("select");
    sistemaSelect.name = "section_visibility_scope_mode";

    const sistemaAtual = editData ? editData.visibility_scope_mode : "all";
    sistemaSelect.appendChild(criarOpcaoV23("all", "Owner e Legado", sistemaAtual));
    sistemaSelect.appendChild(criarOpcaoV23("owner", "Owner", sistemaAtual));
    sistemaSelect.appendChild(criarOpcaoV23("legado", "Legado", sistemaAtual));

    sistemaField.appendChild(sistemaLabel);
    sistemaField.appendChild(sistemaSelect);

    const estadoField = document.createElement("div");
    estadoField.className = "field appverbo-sessoes-field-v23";

    const estadoLabel = document.createElement("label");
    estadoLabel.textContent = "Estado *";

    const estadoSelect = document.createElement("select");
    estadoSelect.name = "section_status";

    const estadoAtual = editData ? editData.status : "ativo";
    estadoSelect.appendChild(criarOpcaoV23("ativo", "Ativo", estadoAtual));
    estadoSelect.appendChild(criarOpcaoV23("inativo", "Inativo", estadoAtual));

    estadoField.appendChild(estadoLabel);
    estadoField.appendChild(estadoSelect);

    grid.appendChild(nomeField);
    grid.appendChild(sistemaField);
    grid.appendChild(estadoField);

    const actions = document.createElement("div");
    actions.className = "appverbo-sessoes-actions-v23";

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

    wrapper.appendChild(toolbar);
    wrapper.appendChild(panel);
    card.appendChild(wrapper);

    abrirBtn.addEventListener("click", function () {
      toolbar.hidden = true;
      panel.hidden = false;
      nomeInput.focus();
    });

    cancelarBtn.addEventListener("click", function () {
      if (modo === "edit") {
        window.location.href = obterUrlRetornoSessaoV23();
        return;
      }

      form.reset();
      panel.hidden = true;
      toolbar.hidden = false;
    });

    form.addEventListener("submit", function () {
      const returnInput = form.querySelector('[name="sidebar_section_return_url"]');

      if (returnInput) {
        returnInput.value = obterUrlRetornoSessaoV23();
      }
    });

    if (modo === "edit") {
      window.setTimeout(function () {
        nomeInput.focus();
        nomeInput.select();
      }, 100);
    }
  }

  //###################################################################################
  // (6) TABELAS ATIVO/INATIVO
  //###################################################################################

  function criarBotaoAcaoV23(tipo, titulo, texto) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "appverbo-sidebar-section-action-btn-v23";
    botao.dataset.sidebarSectionActionV23 = tipo;
    botao.title = titulo;
    botao.setAttribute("aria-label", titulo);
    botao.textContent = texto;
    return botao;
  }

  function criarBadgeV23(status) {
    const badge = document.createElement("span");
    badge.className = "appverbo-sidebar-section-state-badge-v23 " +
      (status === "inativo" ? "appverbo-sidebar-section-state-badge-inativo-v23" : "appverbo-sidebar-section-state-badge-ativo-v23");
    badge.textContent = status === "inativo" ? "Inativo" : "Ativo";
    return badge;
  }

  function criarLinhaV23(sessao, statusGrupo) {
    const tr = document.createElement("tr");
    tr.className = "appverbo-sidebar-section-row-v23";
    tr.dataset.sectionKeyV23 = sessao.key;

    const tdMenu = document.createElement("td");
    tdMenu.textContent = sessao.label;

    const tdSistema = document.createElement("td");
    tdSistema.textContent = sessao.visibility_scope_label || labelSistemaSessoesV23(sessao.visibility_scope_mode, "");

    const tdEstado = document.createElement("td");
    tdEstado.appendChild(criarBadgeV23(statusGrupo));

    const tdAcoes = document.createElement("td");

    const actions = document.createElement("div");
    actions.className = "appverbo-sidebar-section-actions-v23";

    if (statusGrupo === "ativo") {
      actions.appendChild(criarBotaoAcaoV23("up", "Subir sessão", "↑"));
      actions.appendChild(criarBotaoAcaoV23("down", "Descer sessão", "↓"));
    }

    actions.appendChild(criarBotaoAcaoV23("view", "Visualizar detalhes", "👁"));
    actions.appendChild(criarBotaoAcaoV23("edit", "Editar sessão", "✎"));

    tdAcoes.appendChild(actions);

    tr.appendChild(tdMenu);
    tr.appendChild(tdSistema);
    tr.appendChild(tdEstado);
    tr.appendChild(tdAcoes);

    return tr;
  }

  function criarTabelaV23(sessoes, statusGrupo) {
    const wrap = document.createElement("div");
    wrap.className = "appverbo-sidebar-sections-table-wrap-v23";

    const table = document.createElement("table");
    table.className = "appverbo-sidebar-sections-table-v23";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>MENU LATERAL</th><th>SISTEMA</th><th>ESTADO</th><th>AÇÕES</th></tr>";

    const tbody = document.createElement("tbody");

    sessoes.forEach(function (sessao) {
      tbody.appendChild(criarLinhaV23(sessao, statusGrupo));
    });

    table.appendChild(thead);
    table.appendChild(tbody);
    wrap.appendChild(table);

    return wrap;
  }

  function renderizarListaCardV23(card, tituloTexto, descricaoTexto, sessoes, statusGrupo, textoVazio) {
    const assinatura = JSON.stringify({
      titulo: tituloTexto,
      sessoes: sessoes.map(function (sessao) {
        return [sessao.key, sessao.label, sessao.visibility_scope_mode, sessao.status];
      })
    });

    if (card.dataset.renderSignatureV23 === assinatura) {
      return;
    }

    card.dataset.renderSignatureV23 = assinatura;
    card.innerHTML = "";

    const titulo = document.createElement("h2");
    titulo.className = "appverbo-sidebar-section-title-v23";
    titulo.textContent = tituloTexto;

    card.appendChild(titulo);

    if (descricaoTexto) {
      const descricao = document.createElement("p");
      descricao.className = "appverbo-sidebar-section-description-v23";
      descricao.textContent = descricaoTexto;
      card.appendChild(descricao);
    }

    if (sessoes.length) {
      card.appendChild(criarTabelaV23(sessoes, statusGrupo));
    }
    else {
      const vazio = document.createElement("p");
      vazio.className = "appverbo-sidebar-section-empty-v23";
      vazio.textContent = textoVazio;
      card.appendChild(vazio);
    }
  }

  //###################################################################################
  // (7) RENDER PRINCIPAL IDPOTENTE
  //###################################################################################

  function obterCardListaV23() {
    return document.getElementById("admin-sidebar-sections-card");
  }

  function obterOuCriarCardInativasV23(cardLista) {
    let card = document.getElementById("admin-sidebar-sections-inactive-card");

    if (!card) {
      card = document.createElement("section");
      card.id = "admin-sidebar-sections-inactive-card";
    }

    card.className = "card appverbo-sidebar-sections-inactive-card-v23";
    card.hidden = false;
    card.style.display = "";
    card.style.visibility = "";

    if (card.parentElement !== cardLista.parentElement) {
      cardLista.parentElement.insertBefore(card, cardLista.nextSibling);
    }
    else if (card.previousElementSibling !== cardLista) {
      cardLista.parentElement.insertBefore(card, cardLista.nextSibling);
    }

    return card;
  }

  function limparCardsQuandoForaDaAbaV23() {
    if (abaSessoesAtivaV23()) {
      return;
    }

    const cardCreate = document.getElementById("admin-sidebar-sections-create-card");
    const cardInactive = document.getElementById("admin-sidebar-sections-inactive-card");

    if (cardCreate && cardCreate.classList.contains("appverbo-sessoes-create-card-v23")) {
      cardCreate.hidden = true;
      cardCreate.style.display = "none";
    }

    if (cardInactive && cardInactive.classList.contains("appverbo-sidebar-sections-inactive-card-v23")) {
      cardInactive.hidden = true;
      cardInactive.style.display = "none";
    }
  }

  function renderizarSessoesV23() {
    if (!abaSessoesAtivaV23()) {
      limparCardsQuandoForaDaAbaV23();
      return;
    }

    limparApenasUrlSessoesV23();

    const cardLista = obterCardListaV23();

    if (!cardLista || !cardLista.parentElement) {
      return;
    }

    const split = lerSplitBackendSessoesV23();

    const ativas = split.active
      .map(normalizarSessaoV23)
      .filter(Boolean)
      .filter(function (sessao) {
        return sessao.status === "ativo";
      });

    const inativas = split.inactive
      .map(normalizarSessaoV23)
      .filter(Boolean)
      .filter(function (sessao) {
        return sessao.status !== "ativo" || sessao.is_active === false;
      });

    const todasSessoes = ativas.concat(inativas);

    cardLista.className = "card appverbo-sidebar-sections-active-card-v23";

    renderizarCardCriarEditarV23(cardLista, split, todasSessoes);

    renderizarListaCardV23(
      cardLista,
      "Sessões do sidebar",
      "Defina e organize apenas as sessões do menu lateral.",
      ativas,
      "ativo",
      "Sem sessões ativas."
    );

    const cardInativas = obterOuCriarCardInativasV23(cardLista);

    renderizarListaCardV23(
      cardInativas,
      "Sessões inativas",
      "",
      inativas,
      "inativo",
      "Sem sessões inativas."
    );
  }

  //###################################################################################
  // (8) EVENTOS SEM MUTATIONOBSERVER
  //###################################################################################

  function instalarEventosV23() {
    if (window.__appverboSessoesControladorUnicoV23 === true) {
      return;
    }

    window.__appverboSessoesControladorUnicoV23 = true;

    document.addEventListener("click", function (event) {
      const botao = event.target.closest("[data-sidebar-section-action-v23]");

      if (botao) {
        const linha = botao.closest("tr.appverbo-sidebar-section-row-v23");

        if (!linha) {
          return;
        }

        const acao = botao.dataset.sidebarSectionActionV23;
        const chave = linha.dataset.sectionKeyV23 || "";
        const cells = Array.from(linha.querySelectorAll("td"));

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        if (acao === "view") {
          alert(
            "Nome da sessão: " + (cells[0] ? cells[0].textContent.trim() : "") +
            "\nSistema: " + (cells[1] ? cells[1].textContent.trim() : "") +
            "\nEstado: " + (cells[2] ? cells[2].textContent.trim() : "")
          );
          return;
        }

        if (acao === "edit") {
          window.location.href = obterUrlEditarSessaoV23(chave);
          return;
        }

        return;
      }

      window.setTimeout(renderizarSessoesV23, 180);
      window.setTimeout(renderizarSessoesV23, 500);
    }, true);

    window.addEventListener("hashchange", function () {
      window.setTimeout(renderizarSessoesV23, 180);
    });

    window.addEventListener("popstate", function () {
      window.setTimeout(renderizarSessoesV23, 180);
    });

    document.addEventListener("submit", function (event) {
      const form = event.target;

      if (!form || !String(form.getAttribute("action") || "").includes("/settings/menu/sidebar-section-save")) {
        return;
      }

      let returnInput = form.querySelector('input[name="sidebar_section_return_url"]');

      if (!returnInput) {
        returnInput = document.createElement("input");
        returnInput.type = "hidden";
        returnInput.name = "sidebar_section_return_url";
        form.appendChild(returnInput);
      }

      returnInput.value = obterUrlRetornoSessaoV23();
    }, true);
  }

  function instalarV23() {
    instalarEventosV23();

    window.setTimeout(renderizarSessoesV23, 120);
    window.setTimeout(renderizarSessoesV23, 420);
    window.setTimeout(renderizarSessoesV23, 900);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", instalarV23);
  }
  else {
    instalarV23();
  }
})();
// APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_END
'''

if JS_MARKER_START in js_content and JS_MARKER_END in js_content:
    js_content = re.sub(
        re.escape(JS_MARKER_START) + r"[\s\S]*?" + re.escape(JS_MARKER_END),
        js_block,
        js_content,
        count=1,
    )
else:
    js_content = js_content.rstrip() + "\n\n" + js_block + "\n"

JS_PATH.write_text(js_content, encoding="utf-8")

print("OK: JS V23 instalado e controladores antigos desativados.")


####################################################################################
# (8) CSS V23
####################################################################################

css_content = CSS_PATH.read_text(encoding="utf-8")

css_block = f'''{CSS_MARKER_START}

.appverbo-sessoes-create-card-v23,
.appverbo-sidebar-sections-active-card-v23,
.appverbo-sidebar-sections-inactive-card-v23 {{
  display: block !important;
  visibility: visible !important;
  width: 100% !important;
  padding: 16px !important;
  border: 1px solid #d5dceb !important;
  border-radius: 12px !important;
  box-sizing: border-box !important;
}}

.appverbo-sessoes-create-card-v23 {{
  margin: 0 0 12px !important;
  background: #f3f6fb !important;
}}

.appverbo-sidebar-sections-active-card-v23,
.appverbo-sidebar-sections-inactive-card-v23 {{
  background: #ffffff !important;
}}

.appverbo-sidebar-sections-inactive-card-v23 {{
  margin-top: 12px !important;
}}

.appverbo-sessoes-create-toolbar-v23[hidden],
.appverbo-sessoes-create-panel-v23[hidden] {{
  display: none !important;
}}

.appverbo-sessoes-form-title-v23,
.appverbo-sidebar-section-title-v23 {{
  margin: 0 0 12px !important;
  color: #12213a !important;
  font-size: 22px !important;
  font-weight: 800 !important;
}}

.appverbo-sidebar-section-description-v23 {{
  margin: 0 0 12px !important;
  color: #52607a !important;
  font-size: 13px !important;
}}

.appverbo-sidebar-section-empty-v23 {{
  margin: 0 !important;
  color: #52607a !important;
  font-size: 14px !important;
}}

.appverbo-sessoes-grid-v23 {{
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(220px, 260px) minmax(160px, 220px);
  gap: 12px;
  align-items: end;
  width: 100%;
}}

.appverbo-sessoes-field-v23 label {{
  display: block;
  margin-bottom: 6px;
  color: #12213a;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}}

.appverbo-sessoes-field-v23 input,
.appverbo-sessoes-field-v23 select {{
  width: 100%;
  min-height: 38px;
  border: 1px solid #c6d0e2;
  border-radius: 7px;
  background: #ffffff;
  color: #12213a;
  padding: 8px 10px;
  box-sizing: border-box;
  font-size: 13px;
}}

.appverbo-sessoes-actions-v23 {{
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-top: 12px;
}}

.appverbo-sessoes-actions-v23 .action-btn,
.appverbo-sessoes-actions-v23 .action-btn-cancel {{
  min-width: 112px !important;
  width: 112px !important;
  height: 38px !important;
  min-height: 38px !important;
}}

.appverbo-sidebar-sections-table-wrap-v23,
.appverbo-sidebar-sections-table-v23 {{
  width: 100% !important;
}}

.appverbo-sidebar-sections-table-v23 {{
  border-collapse: collapse !important;
}}

.appverbo-sidebar-sections-table-v23 th,
.appverbo-sidebar-sections-table-v23 td {{
  padding: 10px 12px !important;
  border-bottom: 1px solid #e3e8f2 !important;
  text-align: left !important;
  vertical-align: middle !important;
}}

.appverbo-sidebar-section-actions-v23 {{
  display: flex !important;
  gap: 6px !important;
  align-items: center !important;
}}

.appverbo-sidebar-section-action-btn-v23 {{
  min-width: 30px !important;
  height: 30px !important;
  border: 1px solid #c6d0e2 !important;
  border-radius: 7px !important;
  background: #ffffff !important;
  cursor: pointer !important;
}}

.appverbo-sidebar-section-state-badge-v23 {{
  display: inline-flex !important;
  align-items: center !important;
  min-height: 24px !important;
  padding: 3px 9px !important;
  border: 1px solid transparent !important;
  border-radius: 999px !important;
  font-size: 12px !important;
  font-weight: 700 !important;
}}

.appverbo-sidebar-section-state-badge-inativo-v23 {{
  border-color: #f0c36d !important;
  background: #fff7e0 !important;
  color: #8a5a00 !important;
}}

.appverbo-sidebar-section-state-badge-ativo-v23 {{
  border-color: #badbcc !important;
  background: #e9f7ef !important;
  color: #0f5132 !important;
}}

@media (max-width: 1100px) {{
  .appverbo-sessoes-grid-v23 {{
    grid-template-columns: 1fr;
  }}
}}

{CSS_MARKER_END}'''

if CSS_MARKER_START in css_content and CSS_MARKER_END in css_content:
    css_content = re.sub(
        re.escape(CSS_MARKER_START) + r"[\s\S]*?" + re.escape(CSS_MARKER_END),
        css_block,
        css_content,
        count=1,
    )
else:
    css_content = css_content.rstrip() + "\n\n" + css_block + "\n"

CSS_PATH.write_text(css_content, encoding="utf-8")

print("OK: CSS V23 aplicado.")


####################################################################################
# (9) VALIDAR CONTEUDO
####################################################################################

agents_validado = agents_path.read_text(encoding="utf-8")
page_validado = PAGE_HANDLER_PATH.read_text(encoding="utf-8")
settings_validado = SETTINGS_HANDLERS_PATH.read_text(encoding="utf-8")
template_validado = TEMPLATE_PATH.read_text(encoding="utf-8")
js_validado = JS_PATH.read_text(encoding="utf-8")
css_validado = CSS_PATH.read_text(encoding="utf-8")

validacoes = {
    "APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START": agents_validado,
    '"sessoes"': page_validado,
    '"dynamic_process_section",': settings_validado,
    "appverbo-sidebar-section-split-v22": template_validado,
    "APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START": js_validado,
    "renderizarSessoesV23": js_validado,
    "sem MutationObserver": agents_validado,
    "APPVERBO_SESSOES_CONTROLADOR_UNICO_V23_START": css_validado,
    "appverbo-sessoes-create-card-v23": css_validado,
    "20260505-sessoes-controlador-unico-v23": template_validado,
}

for termo, conteudo in validacoes.items():
    if termo not in conteudo:
        fail_v23(f"validação falhou, termo ausente: {termo}")

for forbidden in [
    "APPVERBO_SESSOES_BACKEND_SPLIT_ENTIDADE_V22_START\n(function",
    "APPVERBO_SESSOES_LIMPAR_DYNAMIC_ENTIDADE_V21_START\n(function",
    "APPVERBO_SESSOES_INATIVAS_RENDER_BD_V20_START\n(function",
]:
    if forbidden in js_validado:
        fail_v23(f"controlador antigo ainda ativo: {forbidden.splitlines()[0]}")

try:
    ast.parse(page_validado)
    ast.parse(settings_validado)
except SyntaxError as exc:
    fail_v23(f"Python final inválido: {exc}")

print("OK: patch_sessoes_parar_piscar_controlador_unico_v23 concluído.")
